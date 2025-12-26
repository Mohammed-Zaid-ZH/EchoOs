"""
Universal Command Executor V2 for EchoOS
Truly universal command execution using screen context and dynamic discovery
"""

import os
import sys
import subprocess
import webbrowser
import time
import logging
import platform
import psutil
import re
import json
from typing import Optional, Dict, List, Any, Tuple
from pathlib import Path

# UI Automation
try:
    import pyautogui
    pyautogui.FAILSAFE = False
    pyautogui.PAUSE = 0.1
    PYAUTOGUI_AVAILABLE = True
except ImportError:
    PYAUTOGUI_AVAILABLE = False

# Fuzzy matching
try:
    from rapidfuzz import fuzz, process
    FUZZY_AVAILABLE = True
except ImportError:
    FUZZY_AVAILABLE = False

# Window management
try:
    from .window_manager import WindowManager
    WINDOW_MANAGER_AVAILABLE = True
except ImportError:
    WINDOW_MANAGER_AVAILABLE = False

class UniversalExecutorV2:
    """Universal command executor that works on any system"""
    
    def __init__(self, tts=None, screen_analyzer=None, app_discovery=None, auth=None):
        self.tts = tts
        self.screen_analyzer = screen_analyzer
        self.app_discovery = app_discovery
        self.auth = auth  # Authentication system - REQUIRED
        self.logger = logging.getLogger(__name__)
        self.platform = platform.system().lower()
        
        # Load discovered apps
        self.discovered_apps = self._load_discovered_apps()
        
        # Initialize window manager
        if WINDOW_MANAGER_AVAILABLE:
            self.window_manager = WindowManager(tts=tts)
        else:
            self.window_manager = None
        
        # Current directory tracking
        self.current_directory = os.getcwd()
        
        # Command prompt state
        self.cmd_window = None
        
        # Pending deletion confirmation
        self.pending_deletion = None  # Stores (file_name, file_path, context) for pending deletion
        
    def _load_discovered_apps(self) -> Dict[str, str]:
        """Load discovered applications dynamically"""
        apps = {}
        
        try:
            apps_file = Path("config/apps.json")
            if apps_file.exists():
                with open(apps_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for app in data.get('apps', []):
                        name = app.get('name', '').lower()
                        exec_path = app.get('exec', '')
                        if name and exec_path and os.path.exists(exec_path):
                            apps[name] = exec_path
                            # Also add aliases
                            for alias in app.get('aliases', []):
                                apps[alias.lower()] = exec_path
        except Exception as e:
            self.logger.error(f"Error loading discovered apps: {e}")
        
        return apps
    
    def execute_command(self, voice_text: str) -> bool:
        """Execute any voice command using screen context - REQUIRES AUTHENTICATION"""
        try:
            # CRITICAL: Check authentication first - this is a main pillar of the project
            if self.auth:
                if not self.auth.is_authenticated():
                    self.logger.warning("Command execution blocked: User not authenticated")
                    if self.tts:
                        self.tts.say("Please authenticate first by clicking 'Wake / Authenticate'")
                    return False
                
                # Check session validity
                if not self.auth.is_session_valid():
                    self.logger.warning("Command execution blocked: Session expired")
                    if self.tts:
                        self.tts.say("Session expired. Please authenticate again.")
                    return False
                
                # Log authenticated user
                current_user = self.auth.get_current_user()
                self.logger.info(f"Command execution authorized for user: {current_user}")
            
            text = voice_text.lower().strip()
            self.logger.info(f"Universal executor V2 processing: '{text}'")
            
            # Check for deletion confirmation first
            if self.pending_deletion:
                if any(word in text for word in ['yes', 'confirm', 'confirm delete', 'proceed', 'delete it']):
                    # User confirmed deletion
                    file_name, file_path, context = self.pending_deletion
                    self.pending_deletion = None
                    return self._execute_deletion(file_name, file_path, context)
                elif any(word in text for word in ['no', 'cancel', 'abort', 'stop']):
                    # User cancelled deletion
                    self.pending_deletion = None
                    if self.tts:
                        self.tts.say("Deletion cancelled.")
                    return True
                else:
                    # Still waiting for confirmation, remind user
                    if self.tts:
                        self.tts.say("Please say 'yes' to confirm deletion or 'no' to cancel.")
                    return True
            
            # Get screen context
            context = None
            if self.screen_analyzer:
                context = self.screen_analyzer.analyze_screen()
            
            # System commands (highest priority)
            if self._is_system_command(text):
                return self._execute_system_command(text)
            
            # Check if File Explorer is open - if so, prioritize file operations
            file_explorer_open = self._is_file_explorer_open()
            
            # CRITICAL: Handle "go back" early - prioritize directory navigation over web navigation
            if any(word in text for word in ['go back', 'back directory', 'previous directory', 'navigate back', 'go up', 'parent directory']):
                # Check if File Explorer is open - if so, definitely directory navigation
                if file_explorer_open:
                    return self._execute_file_operation(text, context)
                # Otherwise, try directory navigation first (more common than web navigation)
                if self._is_file_operation(text):
                    result = self._execute_file_operation(text, context)
                    if result:
                        return True
                # Fallback to web navigation if directory navigation fails
                # (will be handled by web operations section below)
            
            # File operations (check first if File Explorer is open)
            if self._is_file_operation(text) or (file_explorer_open and text.startswith('open ')):
                result = self._execute_file_operation(text, context)
                if result:
                    return True
                # If file operation failed and File Explorer is open, don't try app control
                if file_explorer_open and text.startswith('open '):
                    return False  # File/folder not found in current directory
            
            # Application control (only if File Explorer is NOT open, or if explicit "open app")
            if self._is_app_control(text) and not (file_explorer_open and text.startswith('open ') and 'open app' not in text):
                return self._execute_app_control(text)
            
            # Media control
            if self._is_media_control(text):
                return self._execute_media_control(text)
            
            # Text operations
            if self._is_text_operation(text):
                return self._execute_text_operation(text)
            
            # Accessibility operations (check before navigation)
            if self._is_accessibility(text):
                return self._execute_accessibility(text)
            
            # Navigation/UI operations
            if self._is_navigation(text):
                return self._execute_navigation(text)
            
            # Web operations
            if self._is_web_operation(text):
                return self._execute_web_operation(text)
            
            # Command prompt operations
            if self._is_cmd_operation(text):
                return self._execute_cmd_operation(text)
            
            # Generic open command
            if text.startswith('open '):
                return self._open_generic(text[5:].strip(), context)
            
            # Generic close command
            if text.startswith('close '):
                return self._close_generic(text[6:].strip())
            
            # Try as generic command
            return self._try_generic_execution(text, context)
            
        except Exception as e:
            self.logger.error(f"Error executing command: {e}")
            if self.tts:
                self.tts.say("Sorry, I couldn't execute that command.")
            return False
    
    def _is_system_command(self, text: str) -> bool:
        """Check if command is a system command"""
        system_keywords = [
            'shutdown', 'restart', 'reboot', 'sleep', 'hibernate',
            'lock screen', 'lock', 'logout', 'log out',
            'volume up', 'volume down', 'mute', 'unmute',
            'system info', 'battery', 'disk space', 'memory', 'cpu'
        ]
        return any(keyword in text for keyword in system_keywords)
    
    def _is_file_operation(self, text: str) -> bool:
        """Check if command is a file operation"""
        file_keywords = [
            'open file', 'create file', 'delete file', 'copy file', 'move file',
            'rename file', 'create folder', 'delete folder', 'navigate to',
            'go to', 'list files', 'show files', 'save file', 'open file explorer',
            'file explorer', 'explorer', 'go back', 'back directory', 'previous directory',
            'navigate back', 'go up', 'parent directory', 'current directory'
        ]
        # Also check if "open [something]" might be a folder/file when File Explorer is open
        if text.startswith('open ') and not any(kw in text for kw in ['open file ', 'open app ', 'open file explorer']):
            # Check if File Explorer is open - if so, treat as potential file operation
            try:
                import pygetwindow as gw
                all_windows = gw.getAllWindows()
                for w in all_windows:
                    if w.title and ('explorer' in w.title.lower() or 'file' in w.title.lower() or 'this pc' in w.title.lower()):
                        return True  # File Explorer is open, treat as file operation
            except:
                pass
        return any(keyword in text for keyword in file_keywords)
    
    def _is_app_control(self, text: str) -> bool:
        """Check if command is application control"""
        app_keywords = [
            'open app', 'close app', 'minimize', 'maximize', 'restore',
            'switch to', 'switch app', 'go to app', 'bring to front',
            'close all apps', 'close all', 'next app', 'previous app',
            'list apps', 'list open apps'
        ]
        # Don't treat "open [folder]" as app control if it might be a file operation
        if text.startswith('open ') and not any(kw in text for kw in ['open file ', 'open app ']):
            # Check if it might be a folder/file - let file operations handle it first
            return False
        return any(keyword in text for keyword in app_keywords)
    
    def _is_media_control(self, text: str) -> bool:
        """Check if command is media control"""
        media_keywords = ['play', 'pause', 'stop', 'next', 'previous', 'seek', 'start from beginning']
        return any(keyword in text for keyword in media_keywords)
    
    def _is_text_operation(self, text: str) -> bool:
        """Check if command is text operation"""
        text_keywords = [
            'type', 'write', 'enter', 'select all', 'copy all', 'paste all',
            'copy', 'paste', 'cut', 'undo', 'redo'
        ]
        return any(keyword in text for keyword in text_keywords)
    
    def _is_navigation(self, text: str) -> bool:
        """Check if command is navigation"""
        nav_keywords = [
            'click', 'double click', 'right click', 'scroll up', 'scroll down',
            'zoom in', 'zoom out', 'navigate up', 'navigate down'
        ]
        return any(keyword in text for keyword in nav_keywords)
    
    def _is_accessibility(self, text: str) -> bool:
        """Check if command is accessibility feature"""
        accessibility_keywords = [
            'read screen', 'screen read', 'describe screen', 'screen describe',
            'navigation mode', 'enable navigation', 'disable navigation'
        ]
        return any(keyword in text for keyword in accessibility_keywords)
    
    def _is_web_operation(self, text: str) -> bool:
        """Check if command is web operation"""
        web_keywords = [
            'search', 'google', 'youtube', 'amazon', 'open website', 'go to website',
            'next tab', 'previous tab', 'switch tab', 'close tab', 'new tab',
            'list tabs', 'tab number'
        ]
        return any(keyword in text for keyword in web_keywords)
    
    def _is_cmd_operation(self, text: str) -> bool:
        """Check if command is command prompt operation"""
        cmd_keywords = [
            'command prompt', 'cmd', 'powershell', 'terminal', 'execute command',
            'run command', 'type command'
        ]
        return any(keyword in text for keyword in cmd_keywords)
    
    # System command execution
    def _execute_system_command(self, text: str) -> bool:
        """Execute system commands"""
        try:
            if 'shutdown' in text or 'shut down' in text:
                return self._shutdown()
            elif 'restart' in text or 'reboot' in text:
                return self._restart()
            elif 'sleep' in text or 'hibernate' in text:
                return self._sleep()
            elif 'lock' in text:
                return self._lock_screen()
            elif 'logout' in text or 'log out' in text:
                return self._logout()
            elif 'volume' in text:
                import re
                # First try to extract numeric digits
                numbers = re.findall(r'\d+', text)
                volume_percent = None
                
                if numbers:
                    # Get the first number found
                    volume_percent = int(numbers[0])
                else:
                    # Try to convert word numbers (e.g., "fifty", "twenty", "one hundred")
                    volume_percent = self._extract_number_from_text(text)
                
                if volume_percent is not None:
                    # Clamp between 0 and 100
                    volume_percent = max(0, min(100, volume_percent))
                    return self._set_volume(volume_percent)
                # If no number found, check for up/down/mute
                elif 'volume up' in text or 'louder' in text:
                    return self._volume_up()
                elif 'volume down' in text or 'quieter' in text:
                    return self._volume_down()
                elif 'mute' in text:
                    return self._mute()
            elif 'volume up' in text or 'louder' in text:
                return self._volume_up()
            elif 'volume down' in text or 'quieter' in text:
                return self._volume_down()
            elif 'mute' in text:
                return self._mute()
            elif 'system info' in text:
                return self._system_info()
            elif 'battery' in text:
                return self._battery_status()
            elif 'disk space' in text:
                return self._disk_space()
            elif 'memory' in text:
                return self._memory_usage()
            elif 'cpu' in text:
                return self._cpu_usage()
            return False
        except Exception as e:
            self.logger.error(f"Error executing system command: {e}")
            return False
    
    def _shutdown(self) -> bool:
        """Shutdown system"""
        try:
            if self.platform == "windows":
                subprocess.run(["shutdown", "/s", "/t", "10"], check=True)
            elif self.platform == "darwin":
                subprocess.run(["sudo", "shutdown", "-h", "now"], check=True)
            else:
                subprocess.run(["sudo", "shutdown", "-h", "now"], check=True)
            if self.tts:
                self.tts.say("System will shutdown in 10 seconds.")
            return True
        except Exception as e:
            self.logger.error(f"Error shutting down: {e}")
            return False
    
    def _restart(self) -> bool:
        """Restart system"""
        try:
            if self.platform == "windows":
                subprocess.run(["shutdown", "/r", "/t", "10"], check=True)
            elif self.platform == "darwin":
                subprocess.run(["sudo", "shutdown", "-r", "now"], check=True)
            else:
                subprocess.run(["sudo", "shutdown", "-r", "now"], check=True)
            if self.tts:
                self.tts.say("System will restart in 10 seconds.")
            return True
        except Exception as e:
            self.logger.error(f"Error restarting: {e}")
            return False
    
    def _sleep(self) -> bool:
        """Put system to sleep"""
        try:
            if self.platform == "windows":
                subprocess.run(["rundll32.exe", "powrprof.dll,SetSuspendState", "0,1,0"], check=True)
            elif self.platform == "darwin":
                subprocess.run(["pmset", "sleepnow"], check=True)
            else:
                subprocess.run(["systemctl", "suspend"], check=True)
            if self.tts:
                self.tts.say("System going to sleep.")
            return True
        except Exception as e:
            self.logger.error(f"Error putting system to sleep: {e}")
            return False
    
    def _lock_screen(self) -> bool:
        """Lock screen"""
        try:
            if self.platform == "windows":
                subprocess.run(["rundll32.exe", "user32.dll,LockWorkStation"], check=True)
            elif self.platform == "darwin":
                subprocess.run(["pmset", "displaysleepnow"], check=True)
            else:
                subprocess.run(["gnome-screensaver-command", "-l"], check=True)
            if self.tts:
                self.tts.say("Screen locked.")
            return True
        except Exception as e:
            self.logger.error(f"Error locking screen: {e}")
            return False
    
    def _logout(self) -> bool:
        """Logout current user"""
        try:
            if self.platform == "windows":
                subprocess.run(["shutdown", "/l"], check=True)
            elif self.platform == "darwin":
                subprocess.run(["osascript", "-e", 'tell application "System Events" to log out'], check=True)
            else:
                subprocess.run(["gnome-session-quit", "--logout", "--no-prompt"], check=True)
            if self.tts:
                self.tts.say("Logging out.")
            return True
        except Exception as e:
            self.logger.error(f"Error logging out: {e}")
            return False
    
    def _volume_up(self) -> bool:
        """Increase volume"""
        try:
            if PYAUTOGUI_AVAILABLE:
                pyautogui.press('volumeup')
            elif self.platform == "windows":
                subprocess.run(["powershell", "-c", "(New-Object -comObject WScript.Shell).SendKeys([char]175)"], check=True)
            if self.tts:
                self.tts.say("Volume increased.")
            return True
        except Exception as e:
            self.logger.error(f"Error increasing volume: {e}")
            return False
    
    def _volume_down(self) -> bool:
        """Decrease volume"""
        try:
            if PYAUTOGUI_AVAILABLE:
                pyautogui.press('volumedown')
            elif self.platform == "windows":
                subprocess.run(["powershell", "-c", "(New-Object -comObject WScript.Shell).SendKeys([char]174)"], check=True)
            if self.tts:
                self.tts.say("Volume decreased.")
            return True
        except Exception as e:
            self.logger.error(f"Error decreasing volume: {e}")
            return False
    
    def _mute(self) -> bool:
        """Mute/unmute volume"""
        try:
            if PYAUTOGUI_AVAILABLE:
                pyautogui.press('volumemute')
            elif self.platform == "windows":
                subprocess.run(["powershell", "-c", "(New-Object -comObject WScript.Shell).SendKeys([char]173)"], check=True)
            if self.tts:
                self.tts.say("Volume muted.")
            return True
        except Exception as e:
            self.logger.error(f"Error muting volume: {e}")
            return False
    
    def _extract_number_from_text(self, text: str) -> int:
        """Extract number from text, handling word numbers and spoken digits"""
        import re
        
        # Word number mappings
        word_numbers = {
            'zero': 0, 'one': 1, 'two': 2, 'three': 3, 'four': 4, 'five': 5,
            'six': 6, 'seven': 7, 'eight': 8, 'nine': 9, 'ten': 10,
            'eleven': 11, 'twelve': 12, 'thirteen': 13, 'fourteen': 14, 'fifteen': 15,
            'sixteen': 16, 'seventeen': 17, 'eighteen': 18, 'nineteen': 19, 'twenty': 20,
            'thirty': 30, 'forty': 40, 'fifty': 50, 'sixty': 60, 'seventy': 70,
            'eighty': 80, 'ninety': 90, 'hundred': 100
        }
        
        text_lower = text.lower()
        
        # Check for "hundred" first
        if 'hundred' in text_lower:
            if 'one hundred' in text_lower:
                return 100
            return 100  # Default to 100 if just "hundred"
        
        # Check for single word numbers (e.g., "fifty", "twenty")
        for word, num in word_numbers.items():
            if word in text_lower and word != 'hundred':
                # Make sure it's not part of a larger word
                pattern = r'\b' + word + r'\b'
                if re.search(pattern, text_lower):
                    return num
        
        # Check for spoken digits (e.g., "five zero" -> 50, "two zero" -> 20)
        digit_words = ['zero', 'one', 'two', 'three', 'four', 'five', 'six', 'seven', 'eight', 'nine']
        words = text_lower.split()
        
        # Look for patterns like "five zero", "two zero", etc.
        for i in range(len(words) - 1):
            if words[i] in digit_words and words[i+1] in digit_words:
                tens = digit_words.index(words[i])
                ones = digit_words.index(words[i+1])
                number = tens * 10 + ones
                if 0 <= number <= 100:
                    return number
        
        # Look for "volume [word]" pattern
        if 'volume' in text_lower:
            # Extract text after "volume"
            after_volume = text_lower.split('volume', 1)[1].strip()
            words_after = after_volume.split()
            
            if words_after:
                first_word = words_after[0]
                if first_word in word_numbers:
                    return word_numbers[first_word]
                
                # Check for two-word numbers (e.g., "five zero")
                if len(words_after) >= 2:
                    if words_after[0] in digit_words and words_after[1] in digit_words:
                        tens = digit_words.index(words_after[0])
                        ones = digit_words.index(words_after[1])
                        number = tens * 10 + ones
                        if 0 <= number <= 100:
                            return number
        
        return None
    
    def _set_volume(self, percent: int) -> bool:
        """Set volume to specific percentage (0-100)"""
        try:
            import subprocess
            import time
            percent = max(0, min(100, percent))  # Clamp between 0 and 100
            
            if self.platform == "windows":
                if PYAUTOGUI_AVAILABLE:
                    # Use keyboard shortcuts: mute first, then volume up
                    pyautogui.press('volumemute')
                    time.sleep(0.1)
                    # Press volume up approximately (each press is ~2-3%)
                    steps = percent // 2
                    for _ in range(steps):
                        pyautogui.press('volumeup')
                        time.sleep(0.05)
                else:
                    # Fallback: Use PowerShell
                    ps_command = f"""
                    $obj = New-Object -comObject WScript.Shell
                    $obj.SendKeys([char]173)  # Mute first
                    Start-Sleep -Milliseconds 100
                    $steps = {percent} / 2
                    for ($i=0; $i -lt $steps; $i++) {{
                        $obj.SendKeys([char]175)  # Volume up
                        Start-Sleep -Milliseconds 50
                    }}
                    """
                    subprocess.run(["powershell", "-Command", ps_command], check=True)
            elif self.platform == "darwin":
                # macOS: Use osascript (0-100 scale)
                subprocess.run(["osascript", "-e", f"set volume output volume {percent}"], check=True)
            else:
                # Linux: Use amixer (0-100 scale)
                subprocess.run(["amixer", "set", "Master", f"{percent}%"], check=True)
            
            if self.tts:
                self.tts.say(f"Volume set to {percent} percent.")
            self.logger.info(f"Volume set to {percent}%")
            return True
        except Exception as e:
            self.logger.error(f"Error setting volume: {e}")
            if self.tts:
                self.tts.say(f"Could not set volume to {percent} percent.")
            return False
    
    def _system_info(self) -> bool:
        """Get system information"""
        try:
            info = f"System: {platform.system()} {platform.release()}, "
            info += f"Processor: {platform.processor()}, "
            info += f"Python: {platform.python_version()}"
            
            # Add system resources
            memory = psutil.virtual_memory()
            info += f" Memory: {memory.percent}% used"
            
            if self.tts:
                self.tts.say(info)
            return True
        except Exception as e:
            self.logger.error(f"Error getting system info: {e}")
            return False
    
    def _battery_status(self) -> bool:
        """Get battery status"""
        try:
            battery = psutil.sensors_battery()
            if battery:
                percent = battery.percent
                plugged = "plugged in" if battery.power_plugged else "not plugged in"
                if self.tts:
                    self.tts.say(f"Battery is at {percent}% and {plugged}.")
            else:
                if self.tts:
                    self.tts.say("Battery information not available.")
            return True
        except Exception as e:
            self.logger.error(f"Error getting battery status: {e}")
            return False
    
    def _disk_space(self) -> bool:
        """Get disk space"""
        try:
            disk = psutil.disk_usage('/')
            total = disk.total // (1024**3)
            used = disk.used // (1024**3)
            free = disk.free // (1024**3)
            if self.tts:
                self.tts.say(f"Disk space: {used} GB used, {free} GB free out of {total} GB total.")
            return True
        except Exception as e:
            self.logger.error(f"Error getting disk space: {e}")
            return False
    
    def _memory_usage(self) -> bool:
        """Get memory usage"""
        try:
            memory = psutil.virtual_memory()
            total = memory.total // (1024**3)
            available = memory.available // (1024**3)
            percent = memory.percent
            if self.tts:
                self.tts.say(f"Memory usage: {percent}% used, {available} GB available out of {total} GB total.")
            return True
        except Exception as e:
            self.logger.error(f"Error getting memory usage: {e}")
            return False
    
    def _cpu_usage(self) -> bool:
        """Get CPU usage"""
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            cpu_count = psutil.cpu_count()
            if self.tts:
                self.tts.say(f"CPU usage: {cpu_percent}% across {cpu_count} cores.")
            return True
        except Exception as e:
            self.logger.error(f"Error getting CPU usage: {e}")
            return False
    
    # File operations
    def _execute_file_operation(self, text: str, context: Optional[Dict]) -> bool:
        """Execute file operations"""
        try:
            # File Explorer - MAIN PILLAR for navigation
            if 'open file explorer' in text or text == 'file explorer' or text == 'explorer':
                path = None
                # Check if a path is specified
                if 'open file explorer' in text:
                    remaining = text.replace('open file explorer', '').strip()
                    if remaining:
                        path = remaining
                elif 'file explorer' in text:
                    remaining = text.replace('file explorer', '').strip()
                    if remaining:
                        path = remaining
                
                if self.platform == "windows":
                    try:
                        if path:
                            # Open File Explorer to specific path
                            subprocess.Popen(['explorer.exe', path])
                            self.logger.info(f"Opening File Explorer to: {path}")
                        else:
                            # Open File Explorer to current directory
                            subprocess.Popen(['explorer.exe', self.current_directory])
                            self.logger.info(f"Opening File Explorer to: {self.current_directory}")
                        if self.tts:
                            self.tts.say("Opening file explorer.")
                        return True
                    except Exception as e:
                        self.logger.error(f"Error opening file explorer: {e}")
                        if self.tts:
                            self.tts.say("Could not open file explorer.")
                        return False
                return False
            elif text.startswith('open ') and not 'open file ' in text and not 'open app ' in text:
                # Handle "open [folder/file]" when File Explorer is open
                target = text.replace('open ', '').strip()
                # If File Explorer is open, try to open folder/file first
                if self._is_file_explorer_open():
                    if self._open_folder_or_file_in_explorer(target):
                        return True
                    # If not found in File Explorer, return False (don't try app)
                    if self.tts:
                        self.tts.say(f"Could not find {target} in current directory.")
                    return False
                # If File Explorer not open, this will be handled by app control
                return False
            elif 'open file' in text:
                file_name = text.replace('open file', '').strip()
                return self._open_file(file_name, context)
            elif 'create file' in text:
                # Extract simple one-word filename
                file_name = self._extract_simple_name(text, 'create file')
                return self._create_file(file_name)
            elif 'delete file' in text:
                file_name = text.replace('delete file', '').strip()
                return self._delete_file(file_name, context)
            elif 'create folder' in text:
                # Extract simple one-word folder name
                folder_name = self._extract_simple_name(text, 'create folder')
                return self._create_folder(folder_name)
            elif 'delete folder' in text:
                folder_name = text.replace('delete folder', '').strip()
                return self._delete_folder(folder_name, context)
            elif 'navigate to' in text or 'go to' in text:
                target = text.replace('navigate to', '').replace('go to', '').strip()
                return self._navigate_directory(target)
            elif any(word in text for word in ['go back', 'back directory', 'previous directory', 'navigate back', 'go up']):
                # Handle go back - navigate to parent directory
                current = self.current_directory if self.current_directory else os.getcwd()
                parent = os.path.dirname(current)
                if parent != current:
                    return self._navigate_directory('back')
                else:
                    if self.tts:
                        self.tts.say("Already at root directory.")
                    return True
            elif 'list files' in text or 'show files' in text:
                return self._list_files()
            elif 'save file' in text:
                return self._save_file()
            return False
        except Exception as e:
            self.logger.error(f"Error executing file operation: {e}")
            return False
    
    def _open_file(self, file_name: str, context: Optional[Dict]) -> bool:
        """Open a file - first check screen, then current directory, then search"""
        try:
            # First, check if file is visible on screen
            if context and self.screen_analyzer:
                file_info = self.screen_analyzer.find_file_on_screen(file_name)
                if file_info:
                    # File found on screen - try to open it
                    # Use keyboard navigation or clicking
                    if PYAUTOGUI_AVAILABLE:
                        # Try to click on the file (approximate)
                        pyautogui.press('tab')  # Navigate to file list
                        time.sleep(0.2)
                        # Type file name to select
                        pyautogui.typewrite(file_info['name'], interval=0.1)
                        time.sleep(0.3)
                        pyautogui.press('enter')  # Open file
                        if self.tts:
                            self.tts.say(f"Opening {file_info['name']}.")
                        return True
            
            # Check current directory
            file_path = os.path.join(self.current_directory, file_name)
            if os.path.exists(file_path):
                if self.platform == "windows":
                    os.startfile(file_path)
                elif self.platform == "darwin":
                    subprocess.run(["open", file_path])
                else:
                    subprocess.run(["xdg-open", file_path])
                if self.tts:
                    self.tts.say(f"Opening {file_name}.")
                return True
            
            # Try with common extensions
            extensions = ['.txt', '.doc', '.docx', '.pdf', '.py', '.js', '.html', '.mp4', '.mp3', '.jpg', '.png']
            for ext in extensions:
                test_path = file_path + ext
                if os.path.exists(test_path):
                    if self.platform == "windows":
                        os.startfile(test_path)
                    elif self.platform == "darwin":
                        subprocess.run(["open", test_path])
                    else:
                        subprocess.run(["xdg-open", test_path])
                    if self.tts:
                        self.tts.say(f"Opening {file_name}{ext}.")
                    return True
            
            # Search in common directories
            search_dirs = [
                os.path.expanduser("~/Desktop"),
                os.path.expanduser("~/Documents"),
                os.path.expanduser("~/Downloads"),
                os.path.expanduser("~/Pictures"),
                os.path.expanduser("~/Videos")
            ]
            
            for search_dir in search_dirs:
                if not os.path.exists(search_dir):
                    continue
                for root, dirs, files in os.walk(search_dir):
                    for file in files:
                        if file_name.lower() in file.lower():
                            found_path = os.path.join(root, file)
                            if self.platform == "windows":
                                os.startfile(found_path)
                            elif self.platform == "darwin":
                                subprocess.run(["open", found_path])
                            else:
                                subprocess.run(["xdg-open", found_path])
                            if self.tts:
                                self.tts.say(f"Opening {file}.")
                            return True
            
            if self.tts:
                self.tts.say(f"File {file_name} not found.")
            return False
            
        except Exception as e:
            self.logger.error(f"Error opening file: {e}")
            return False
    
    def _extract_simple_name(self, text: str, command: str) -> str:
        """Extract simple one-word name from command"""
        # Remove command phrase
        name = text.replace(command, '').strip()
        # Take only first word (simple name)
        words = name.split()
        if words:
            # Get first word, remove any special characters
            simple_name = words[0].strip('.,!?;:')
            return simple_name
        return "new"
    
    def _create_file(self, file_name: str) -> bool:
        """Create a new file"""
        try:
            if not file_name:
                file_name = "new_file.txt"
            else:
                # Clean up the name - remove extra words, keep only first word
                words = file_name.split()
                if words:
                    file_name = words[0].strip('.,!?;:')
                # Add extension if not present
                if not any(file_name.endswith(ext) for ext in ['.txt', '.doc', '.py', '.js', '.html', '.md']):
                    file_name += '.txt'
            
            file_path = os.path.join(self.current_directory, file_name)
            with open(file_path, 'w') as f:
                f.write(f"Created by EchoOS on {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
            
            if self.tts:
                self.tts.say(f"Created file {file_name}.")
            return True
        except Exception as e:
            self.logger.error(f"Error creating file: {e}")
            return False
    
    def _delete_file(self, file_name: str, context: Optional[Dict]) -> bool:
        """Delete a file - requires permission confirmation"""
        try:
            file_path = None
            
            # Check screen first
            if context and self.screen_analyzer:
                file_info = self.screen_analyzer.find_file_on_screen(file_name)
                if file_info:
                    file_path = file_info.get('path') or os.path.join(self.current_directory, file_info['name'])
                    file_name = file_info['name']
            
            # Check current directory if not found on screen
            if not file_path:
                file_path = os.path.join(self.current_directory, file_name)
            
            if not os.path.exists(file_path):
                if self.tts:
                    self.tts.say(f"File {file_name} not found.")
                return False
            
            # Request permission confirmation
            self.pending_deletion = (file_name, file_path, context)
            if self.tts:
                self.tts.say(f"Are you sure you want to delete {file_name}? Say 'yes' to confirm or 'no' to cancel.")
            self.logger.info(f"Deletion pending confirmation for: {file_name}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error preparing deletion: {e}")
            self.pending_deletion = None
            return False
    
    def _execute_deletion(self, file_name: str, file_path: str, context: Optional[Dict]) -> bool:
        """Actually execute the deletion after confirmation (works for both files and folders)"""
        try:
            is_folder = os.path.isdir(file_path) if os.path.exists(file_path) else False
            
            # Try screen-based deletion first if context available
            if context and self.screen_analyzer and PYAUTOGUI_AVAILABLE:
                file_info = self.screen_analyzer.find_file_on_screen(file_name)
                if file_info:
                    # Select file/folder on screen
                    pyautogui.typewrite(file_info['name'], interval=0.1)
                    time.sleep(0.2)
                    pyautogui.press('delete')
                    item_type = "folder" if is_folder else "file"
                    if self.tts:
                        self.tts.say(f"Deleted {file_info['name']}.")
                    return True
            
            # Direct file system deletion
            if os.path.exists(file_path):
                if is_folder:
                    import shutil
                    shutil.rmtree(file_path)
                    item_type = "folder"
                else:
                    os.remove(file_path)
                    item_type = "file"
                if self.tts:
                    self.tts.say(f"Deleted {item_type} {file_name}.")
                self.logger.info(f"Successfully deleted: {file_path}")
                return True
            else:
                item_type = "folder" if is_folder else "file"
                if self.tts:
                    self.tts.say(f"{item_type.capitalize()} {file_name} no longer exists.")
                return False
                
        except Exception as e:
            self.logger.error(f"Error executing deletion: {e}")
            if self.tts:
                self.tts.say(f"Could not delete {file_name}. Error: {str(e)}")
            return False
    
    def _create_folder(self, folder_name: str) -> bool:
        """Create a new folder"""
        try:
            if not folder_name:
                folder_name = "New Folder"
            else:
                # Clean up the name - remove extra words, keep only first word
                words = folder_name.split()
                if words:
                    folder_name = words[0].strip('.,!?;:')
            
            folder_path = os.path.join(self.current_directory, folder_name)
            os.makedirs(folder_path, exist_ok=True)
            
            if self.tts:
                self.tts.say(f"Created folder {folder_name}.")
            return True
        except Exception as e:
            self.logger.error(f"Error creating folder: {e}")
            return False
    
    def _delete_folder(self, folder_name: str, context: Optional[Dict]) -> bool:
        """Delete a folder - requires permission confirmation"""
        try:
            folder_path = None
            
            # Check screen first
            if context and self.screen_analyzer:
                folder_info = self.screen_analyzer.find_file_on_screen(folder_name)
                if folder_info:
                    folder_path = folder_info.get('path') or os.path.join(self.current_directory, folder_info['name'])
                    folder_name = folder_info['name']
            
            # Check current directory if not found on screen
            if not folder_path:
                folder_path = os.path.join(self.current_directory, folder_name)
            
            if not os.path.exists(folder_path) or not os.path.isdir(folder_path):
                if self.tts:
                    self.tts.say(f"Folder {folder_name} not found.")
                return False
            
            # Request permission confirmation
            self.pending_deletion = (folder_name, folder_path, context)
            if self.tts:
                self.tts.say(f"Are you sure you want to delete folder {folder_name}? Say 'yes' to confirm or 'no' to cancel.")
            self.logger.info(f"Folder deletion pending confirmation for: {folder_name}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error preparing folder deletion: {e}")
            self.pending_deletion = None
            return False
    
    def _navigate_directory(self, target: str) -> bool:
        """Navigate to a directory - MAIN PILLAR for file/folder navigation"""
        try:
            # FIRST: Resolve target to full path
            common_dirs = {
                'desktop': os.path.expanduser("~/Desktop"),
                'documents': os.path.expanduser("~/Documents"),
                'downloads': os.path.expanduser("~/Downloads"),
                'pictures': os.path.expanduser("~/Pictures"),
                'videos': os.path.expanduser("~/Videos"),
                'music': os.path.expanduser("~/Music"),
                'home': os.path.expanduser("~"),
                'user': os.path.expanduser("~"),
                'root': os.path.expanduser("~"),
                'current': self.current_directory,
                'parent': os.path.dirname(self.current_directory) if self.current_directory else os.path.expanduser("~")
            }
            
            target_lower = target.lower().strip()
            target_path = None
            
            # Resolve to full path
            if target_lower in common_dirs:
                target_path = common_dirs[target_lower]
            elif target_lower in ['back', 'up', 'parent', 'previous']:
                target_path = os.path.dirname(self.current_directory) if self.current_directory else os.path.expanduser("~")
            else:
                # Try as relative path from current directory
                target_path = os.path.join(self.current_directory, target)
                if not os.path.exists(target_path):
                    # Try searching in current directory
                    try:
                        for item in os.listdir(self.current_directory):
                            if target_lower in item.lower() and os.path.isdir(os.path.join(self.current_directory, item)):
                                target_path = os.path.join(self.current_directory, item)
                                break
                    except:
                        pass
                
                # If still not found, try as absolute path
                if not os.path.exists(target_path):
                    target_path = target
            
            # Check if path exists
            if not target_path or not os.path.exists(target_path) or not os.path.isdir(target_path):
                if self.tts:
                    self.tts.say(f"Directory {target} not found.")
                return False
            
            # Update current directory
            self.current_directory = target_path
            os.chdir(target_path)
            self.logger.info(f"Navigated to: {target_path}")
            
            # NOW: Navigate in File Explorer if it's open (use FULL PATH)
            if PYAUTOGUI_AVAILABLE:
                try:
                    import pygetwindow as gw
                    
                    # Find File Explorer windows (check all windows, not just active)
                    all_windows = gw.getAllWindows()
                    explorer_windows = []
                    for w in all_windows:
                        if w.title and ('explorer' in w.title.lower() or 'file' in w.title.lower() or 'this pc' in w.title.lower()):
                            explorer_windows.append(w)
                    
                    if explorer_windows:
                        # Activate the first File Explorer window
                        explorer_windows[0].activate()
                        time.sleep(0.5)  # Give it time to activate
                        
                        # For "go back" commands, use Alt+Left first
                        if target_lower in ['back', 'up', 'parent', 'previous']:
                            pyautogui.hotkey('alt', 'left')
                            time.sleep(0.3)
                        
                        # Navigate using address bar with FULL PATH
                        pyautogui.hotkey('ctrl', 'l')  # Focus address bar
                        time.sleep(0.3)
                        pyautogui.hotkey('ctrl', 'a')  # Select all (clear existing)
                        time.sleep(0.1)
                        pyautogui.write(target_path, interval=0.01)  # Type FULL PATH
                        time.sleep(0.3)
                        pyautogui.press('enter')
                        self.logger.info(f"Navigated File Explorer to: {target_path}")
                        if self.tts:
                            self.tts.say(f"Navigated to {os.path.basename(target_path)}.")
                        return True
                except Exception as e:
                    self.logger.error(f"Error navigating in File Explorer: {e}")
                    # Continue with programmatic navigation even if File Explorer navigation fails
            
            # Fallback: programmatic navigation succeeded
            if self.tts:
                self.tts.say(f"Navigated to {os.path.basename(target_path)}.")
            return True
        except Exception as e:
            self.logger.error(f"Error navigating directory: {e}")
            if self.tts:
                self.tts.say("Could not navigate to directory.")
            return False
    
    def _list_files(self) -> bool:
        """List files in current directory"""
        try:
            files = os.listdir(self.current_directory)
            if not files:
                if self.tts:
                    self.tts.say("Directory is empty.")
                return True
            
            # Limit to first 10 for TTS
            display_files = files[:10]
            file_list = ", ".join(display_files)
            if len(files) > 10:
                file_list += f" and {len(files) - 10} more items"
            
            if self.tts:
                self.tts.say(f"Directory contains: {file_list}")
            return True
        except Exception as e:
            self.logger.error(f"Error listing files: {e}")
            return False
    
    def _save_file(self) -> bool:
        """Save current file"""
        try:
            if PYAUTOGUI_AVAILABLE:
                pyautogui.hotkey('ctrl', 's')
                if self.tts:
                    self.tts.say("File saved.")
                return True
            return False
        except Exception as e:
            self.logger.error(f"Error saving file: {e}")
            return False
    
    def _is_file_explorer_open(self) -> bool:
        """Check if File Explorer is currently open"""
        try:
            if not PYAUTOGUI_AVAILABLE:
                return False
            import pygetwindow as gw
            all_windows = gw.getAllWindows()
            for w in all_windows:
                if w.title and ('explorer' in w.title.lower() or 'file' in w.title.lower() or 'this pc' in w.title.lower()):
                    return True
            return False
        except:
            return False
    
    def _open_folder_or_file_in_explorer(self, target: str) -> bool:
        """Open folder or file in File Explorer when it's open - PRIORITY when File Explorer is open"""
        try:
            if not PYAUTOGUI_AVAILABLE:
                return False
            
            import pygetwindow as gw
            
            # Find File Explorer windows
            all_windows = gw.getAllWindows()
            explorer_windows = []
            for w in all_windows:
                if w.title and ('explorer' in w.title.lower() or 'file' in w.title.lower() or 'this pc' in w.title.lower()):
                    explorer_windows.append(w)
            
            if not explorer_windows:
                self.logger.warning("File Explorer not open, cannot navigate")
                return False  # File Explorer not open
            
            # Activate File Explorer to get current context
            explorer_windows[0].activate()
            time.sleep(0.4)
            
            # Get current directory - try multiple methods
            current_dir = os.getcwd()  # Default to working directory
            
            # Method 1: Try to read from File Explorer address bar
            try:
                pyautogui.hotkey('ctrl', 'l')  # Focus address bar
                time.sleep(0.2)
                pyautogui.hotkey('ctrl', 'a')  # Select all
                time.sleep(0.1)
                pyautogui.hotkey('ctrl', 'c')  # Copy address
                time.sleep(0.2)
                try:
                    import pyperclip
                    address_bar_path = pyperclip.paste().strip()
                    if address_bar_path and os.path.exists(address_bar_path) and os.path.isdir(address_bar_path):
                        current_dir = address_bar_path
                        self.logger.info(f"Got directory from address bar: {current_dir}")
                except:
                    pass
            except Exception as e:
                self.logger.debug(f"Could not read address bar: {e}")
            
            # Method 2: Try to get directory from File Explorer window title
            try:
                window_title = explorer_windows[0].title
                # File Explorer titles: "Folder Name - File Explorer" or "C:\Path - File Explorer"
                if ' - ' in window_title:
                    possible_path = window_title.split(' - ')[0]
                    # Check if it's a full path (contains :\ or starts with /)
                    if (':\\' in possible_path or possible_path.startswith('/') or 
                        (os.path.exists(possible_path) and os.path.isdir(possible_path))):
                        if os.path.exists(possible_path) and os.path.isdir(possible_path):
                            current_dir = possible_path
                            self.logger.info(f"Got directory from window title: {current_dir}")
            except Exception as e:
                self.logger.debug(f"Could not read window title: {e}")
            
            # Update tracked directory
            self.current_directory = current_dir
            os.chdir(current_dir)  # Sync working directory
            
            target_lower = target.lower().strip()
            original_target = target
            
            self.logger.info(f"File Explorer open - searching for '{original_target}' in: {current_dir}")
            
            # Check for exact folder match first
            folder_path = os.path.join(current_dir, original_target)
            if os.path.exists(folder_path) and os.path.isdir(folder_path):
                # Navigate to folder - use reliable method
                explorer_windows[0].activate()
                time.sleep(0.7)
                
                # Update programmatic directory first
                os.chdir(folder_path)
                self.current_directory = folder_path
                
                # Use address bar navigation
                pyautogui.hotkey('ctrl', 'l')  # Focus address bar
                time.sleep(0.5)
                pyautogui.hotkey('ctrl', 'a')  # Select all
                time.sleep(0.2)
                pyautogui.press('delete')  # Clear existing path
                time.sleep(0.2)
                pyautogui.typewrite(folder_path, interval=0.03)  # Type full path
                time.sleep(0.5)
                pyautogui.press('enter')
                time.sleep(1.2)  # Wait for navigation to fully complete
                
                self.logger.info(f"✅ Navigated to folder: {folder_path}")
                if self.tts:
                    folder_name = os.path.basename(folder_path) if os.path.basename(folder_path) else original_target
                    self.tts.say(f"Opened {folder_name} folder.")
                return True
            
            # Check for exact file match
            file_path = os.path.join(current_dir, original_target)
            if os.path.exists(file_path) and os.path.isfile(file_path):
                # Open file
                if self.platform == "windows":
                    os.startfile(file_path)
                elif self.platform == "darwin":
                    subprocess.run(["open", file_path])
                else:
                    subprocess.run(["xdg-open", file_path])
                self.logger.info(f"Opening file: {file_path}")
                if self.tts:
                    self.tts.say(f"Opening {original_target}.")
                return True
            
            # Try fuzzy matching for folders/files in current directory
            try:
                items = os.listdir(current_dir)
                self.logger.info(f"Searching in directory with {len(items)} items")
                
                # First try: exact match (case insensitive)
                for item in items:
                    if item.lower() == target_lower:
                        item_path = os.path.join(current_dir, item)
                        if os.path.isdir(item_path):
                            # Navigate to folder - update directory first
                            os.chdir(item_path)
                            self.current_directory = item_path
                            
                            # Navigate in File Explorer
                            explorer_windows[0].activate()
                            time.sleep(0.7)
                            pyautogui.hotkey('ctrl', 'l')  # Focus address bar
                            time.sleep(0.5)
                            pyautogui.hotkey('ctrl', 'a')  # Select all
                            time.sleep(0.2)
                            pyautogui.press('delete')  # Clear
                            time.sleep(0.2)
                            pyautogui.typewrite(item_path, interval=0.03)  # Type full path
                            time.sleep(0.5)
                            pyautogui.press('enter')
                            time.sleep(1.2)  # Wait for navigation
                            
                            self.logger.info(f"✅ Navigated to folder (exact match): {item_path}")
                            if self.tts:
                                self.tts.say(f"Opened {item} folder.")
                            return True
                        elif os.path.isfile(item_path):
                            # Open file
                            if self.platform == "windows":
                                os.startfile(item_path)
                            elif self.platform == "darwin":
                                subprocess.run(["open", item_path])
                            else:
                                subprocess.run(["xdg-open", item_path])
                            self.logger.info(f"Opening file (exact match): {item_path}")
                            if self.tts:
                                self.tts.say(f"Opening {item}.")
                            return True
                
                # Second try: partial match (contains or starts with)
                for item in items:
                    item_lower = item.lower()
                    if target_lower in item_lower or item_lower.startswith(target_lower):
                        item_path = os.path.join(current_dir, item)
                        if os.path.isdir(item_path):
                            # Navigate to folder - update directory first
                            os.chdir(item_path)
                            self.current_directory = item_path
                            
                            # Navigate in File Explorer
                            explorer_windows[0].activate()
                            time.sleep(0.7)
                            pyautogui.hotkey('ctrl', 'l')  # Focus address bar
                            time.sleep(0.5)
                            pyautogui.hotkey('ctrl', 'a')  # Select all
                            time.sleep(0.2)
                            pyautogui.press('delete')  # Clear existing path
                            time.sleep(0.2)
                            pyautogui.typewrite(item_path, interval=0.03)  # Type full path
                            time.sleep(0.5)
                            pyautogui.press('enter')
                            time.sleep(1.2)  # Wait for navigation to complete
                            
                            self.logger.info(f"✅ Navigated to folder (fuzzy match): {item_path}")
                            if self.tts:
                                self.tts.say(f"Opened {item} folder.")
                            return True
                        elif os.path.isfile(item_path):
                            # Open file
                            if self.platform == "windows":
                                os.startfile(item_path)
                            elif self.platform == "darwin":
                                subprocess.run(["open", item_path])
                            else:
                                subprocess.run(["xdg-open", item_path])
                            self.logger.info(f"Opening file (fuzzy match): {item_path}")
                            if self.tts:
                                self.tts.say(f"Opening {item}.")
                            return True
            except Exception as e:
                self.logger.error(f"Error searching directory: {e}")
            
            self.logger.warning(f"Could not find folder or file: {original_target} in {current_dir}")
            if self.tts:
                self.tts.say(f"Could not find {original_target}.")
            return False
        except Exception as e:
            self.logger.error(f"Error opening folder/file in explorer: {e}")
            return False
    
    # Application control
    def _execute_app_control(self, text: str) -> bool:
        """Execute application control commands"""
        try:
            if 'close all apps' in text or 'close all' in text:
                return self._close_all_apps()
            elif 'close app' in text or text.startswith('close '):
                target = text.replace('close app', '').replace('close', '').strip()
                return self._close_app(target)
            elif 'switch to' in text or 'switch app' in text or 'go to app' in text or 'bring to front' in text:
                # Extract app name
                if 'switch to' in text:
                    target = text.split('switch to', 1)[1].strip()
                elif 'switch app' in text:
                    target = text.split('switch app', 1)[1].strip()
                elif 'go to app' in text:
                    target = text.split('go to app', 1)[1].strip()
                elif 'bring to front' in text:
                    target = text.split('bring to front', 1)[1].strip()
                else:
                    target = ""
                return self._switch_to_app(target)
            elif 'next app' in text:
                return self._switch_to_next_app()
            elif 'previous app' in text:
                return self._switch_to_previous_app()
            elif 'list apps' in text or 'list open apps' in text:
                return self._list_open_apps()
            elif 'minimize' in text:
                return self._minimize_window()
            elif 'maximize' in text:
                return self._maximize_window()
            elif 'open app' in text or text.startswith('open '):
                target = text.replace('open app', '').replace('open', '').strip()
                return self._open_app(target)
            return False
        except Exception as e:
            self.logger.error(f"Error executing app control: {e}")
            return False
    
    def _open_app(self, app_name: str) -> bool:
        """Open an application dynamically"""
        try:
            app_name_lower = app_name.lower().strip()
            
            # Special handling for Windows system apps
            if self.platform == "windows":
                # File Explorer - MAIN PILLAR for navigation
                if app_name_lower in ['file explorer', 'explorer', 'file manager', 'files']:
                    try:
                        subprocess.Popen(['explorer.exe'])
                        if self.tts:
                            self.tts.say("Opening file explorer.")
                        self.logger.info("File Explorer opened successfully")
                        return True
                    except Exception as e:
                        self.logger.error(f"Error opening file explorer: {e}")
                        if self.tts:
                            self.tts.say("Could not open file explorer.")
                        return False
                
                # Calculator
                if app_name_lower in ['calculator', 'calc', 'calc.exe']:
                    try:
                        subprocess.Popen(['calc.exe'])
                        if self.tts:
                            self.tts.say("Opening calculator.")
                        return True
                    except Exception as e:
                        self.logger.error(f"Error opening calculator: {e}")
                
                # Calendar
                if app_name_lower in ['calendar', 'ms calendar', 'microsoft calendar', 'cal']:
                    try:
                        # Try different methods to open Calendar
                        subprocess.run(['start', 'ms-calendar:'], shell=True, check=True)
                        if self.tts:
                            self.tts.say("Opening calendar.")
                        return True
                    except:
                        try:
                            subprocess.run(['start', 'outlookcal:'], shell=True, check=True)
                            if self.tts:
                                self.tts.say("Opening calendar.")
                            return True
                        except Exception as e:
                            self.logger.error(f"Error opening calendar: {e}")
                
                # VS Code - handle multiple name variations
                if app_name_lower in ['vs code', 'visual studio code', 'code', 'vscode']:
                    # Check discovered apps first
                    for key in ['code', 'visual studio code', 'vs code', 'vscode']:
                        if key in self.discovered_apps:
                            app_path = self.discovered_apps[key]
                            subprocess.Popen([app_path])
                            if self.tts:
                                self.tts.say("Opening Visual Studio Code.")
                            return True
                    # Try common VS Code paths
                    common_paths = [
                        os.path.expanduser("~/AppData/Local/Programs/Microsoft VS Code/Code.exe"),
                        "C:\\Program Files\\Microsoft VS Code\\Code.exe",
                        "C:\\Program Files (x86)\\Microsoft VS Code\\Code.exe"
                    ]
                    for path in common_paths:
                        if os.path.exists(path):
                            subprocess.Popen([path])
                            if self.tts:
                                self.tts.say("Opening Visual Studio Code.")
                            return True
            
            # First check discovered apps
            if app_name_lower in self.discovered_apps:
                app_path = self.discovered_apps[app_name_lower]
                subprocess.Popen([app_path])
                if self.tts:
                    self.tts.say(f"Opening {app_name}.")
                return True
            
            # Try fuzzy matching
            if FUZZY_AVAILABLE and self.discovered_apps:
                app_names = list(self.discovered_apps.keys())
                result = process.extractOne(app_name_lower, app_names, scorer=fuzz.ratio)
                if result and len(result) == 2:
                    best_match, score = result
                    if score > 60:
                        app_path = self.discovered_apps[best_match]
                        subprocess.Popen([app_path])
                        if self.tts:
                            self.tts.say(f"Opening {best_match}.")
                        return True
            
            # Try Windows start command
            if self.platform == "windows":
                try:
                    subprocess.run(["start", app_name], shell=True, check=True)
                    if self.tts:
                        self.tts.say(f"Opening {app_name}.")
                    return True
                except:
                    pass
            
            # Try as executable
            if os.path.exists(app_name):
                subprocess.Popen([app_name])
                if self.tts:
                    self.tts.say(f"Opening {app_name}.")
                return True
            
            if self.tts:
                self.tts.say(f"Could not find application {app_name}.")
            return False
        except Exception as e:
            self.logger.error(f"Error opening app: {e}")
            return False
    
    def _close_app(self, app_name: str) -> bool:
        """Close an application"""
        try:
            if self.platform == "windows":
                # SPECIAL HANDLING: File Explorer - must be closed by window, not process
                if app_name:
                    app_name_lower = app_name.lower().strip()
                    if 'file explorer' in app_name_lower or 'explorer' in app_name_lower or app_name_lower == 'explorer':
                        try:
                            if not PYAUTOGUI_AVAILABLE:
                                if self.tts:
                                    self.tts.say("Cannot close file explorer - pyautogui not available.")
                                return False
                            
                            import pygetwindow as gw
                            import time
                            all_windows = gw.getAllWindows()
                            explorer_windows = []
                            
                            # Find all File Explorer windows
                            for w in all_windows:
                                if w.title and ('explorer' in w.title.lower() or 'file' in w.title.lower() or 'this pc' in w.title.lower()):
                                    # Exclude system windows that contain "explorer" but aren't File Explorer
                                    if 'file explorer' in w.title.lower() or ' - ' in w.title:
                                        explorer_windows.append(w)
                            
                            if explorer_windows:
                                # Activate the first File Explorer window first
                                explorer_windows[0].activate()
                                time.sleep(0.3)  # Wait for window to activate
                                
                                # Close the File Explorer window specifically
                                explorer_windows[0].close()
                                time.sleep(0.2)  # Wait for close
                                
                                if self.tts:
                                    self.tts.say("Closed file explorer.")
                                self.logger.info(f"Closed File Explorer window: {explorer_windows[0].title}")
                                return True
                            else:
                                if self.tts:
                                    self.tts.say("File explorer is not open.")
                                return False
                        except Exception as e:
                            self.logger.error(f"Error closing File Explorer: {e}")
                            if self.tts:
                                self.tts.say("Error closing file explorer.")
                            return False
                
                # Try to find process
                if app_name:
                    # Try exact match
                    try:
                        subprocess.run(["taskkill", "/f", "/im", f"{app_name}.exe"], 
                                     check=True, capture_output=True)
                        if self.tts:
                            self.tts.say(f"Closed {app_name}.")
                        return True
                    except:
                        pass
                
                # Try fuzzy match
                if FUZZY_AVAILABLE and app_name:
                    for discovered_name, app_path in self.discovered_apps.items():
                        if app_name.lower() in discovered_name.lower():
                            process_name = os.path.basename(app_path)
                            try:
                                subprocess.run(["taskkill", "/f", "/im", process_name], 
                                             check=True, capture_output=True)
                                if self.tts:
                                    self.tts.say(f"Closed {discovered_name}.")
                                return True
                            except:
                                pass
                
                # DO NOT close current window automatically - this was causing Cursor to close!
                # Only close if explicitly requested (e.g., "close window" or "close current")
                # if PYAUTOGUI_AVAILABLE:
                #     pyautogui.hotkey('alt', 'f4')
                #     if self.tts:
                #         self.tts.say("Closed current window.")
                #     return True
            
            return False
        except Exception as e:
            self.logger.error(f"Error closing app: {e}")
            return False
    
    def _close_all_apps(self) -> bool:
        """Close all applications except EchoOS - dynamically"""
        try:
            if self.platform == "windows":
                # Get current process name
                current_process = psutil.Process().name()
                
                # Get all running processes dynamically
                for proc in psutil.process_iter(['pid', 'name']):
                    try:
                        proc_name = proc.info['name']
                        # Skip system processes and EchoOS
                        if (proc_name and 
                            proc_name != current_process and
                            not self._is_system_process(proc_name)):
                            try:
                                subprocess.run(["taskkill", "/f", "/im", proc_name], 
                                             capture_output=True, timeout=1)
                            except:
                                pass
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        continue
                
                if self.tts:
                    self.tts.say("Closed all applications except EchoOS.")
                return True
            return False
        except Exception as e:
            self.logger.error(f"Error closing all apps: {e}")
            return False
    
    def _is_system_process(self, process_name: str) -> bool:
        """Check if process is a system process"""
        system_processes = {
            'svchost', 'winlogon', 'csrss', 'lsass', 'smss', 'wininit',
            'dwm', 'explorer', 'conhost', 'audiodg', 'spoolsv', 'services',
            'system', 'python', 'pythonw', 'echoos', 'main.py'
        }
        return process_name.lower() in system_processes
    
    def _minimize_window(self) -> bool:
        """Minimize current window"""
        try:
            if PYAUTOGUI_AVAILABLE:
                pyautogui.hotkey('win', 'down')
                if self.tts:
                    self.tts.say("Window minimized.")
                return True
            return False
        except Exception as e:
            self.logger.error(f"Error minimizing window: {e}")
            return False
    
    def _maximize_window(self) -> bool:
        """Maximize current window"""
        try:
            if PYAUTOGUI_AVAILABLE:
                pyautogui.hotkey('win', 'up')
                if self.tts:
                    self.tts.say("Window maximized.")
                return True
            return False
        except Exception as e:
            self.logger.error(f"Error maximizing window: {e}")
            return False
    
    def _switch_to_app(self, app_name: str) -> bool:
        """Switch to a specific application"""
        try:
            if self.window_manager:
                return self.window_manager.switch_to_app(app_name)
            elif PYAUTOGUI_AVAILABLE:
                # Fallback: use Alt+Tab
                pyautogui.hotkey('alt', 'tab')
                if self.tts:
                    self.tts.say(f"Switching to {app_name}.")
                return True
            return False
        except Exception as e:
            self.logger.error(f"Error switching to app: {e}")
            return False
    
    def _switch_to_next_app(self) -> bool:
        """Switch to next application"""
        try:
            if self.window_manager:
                return self.window_manager.switch_to_next_app()
            elif PYAUTOGUI_AVAILABLE:
                pyautogui.hotkey('alt', 'tab')
                if self.tts:
                    self.tts.say("Switched to next app.")
                return True
            return False
        except Exception as e:
            self.logger.error(f"Error switching to next app: {e}")
            return False
    
    def _switch_to_previous_app(self) -> bool:
        """Switch to previous application"""
        try:
            if self.window_manager:
                return self.window_manager.switch_to_previous_app()
            elif PYAUTOGUI_AVAILABLE:
                pyautogui.hotkey('alt', 'shift', 'tab')
                if self.tts:
                    self.tts.say("Switched to previous app.")
                return True
            return False
        except Exception as e:
            self.logger.error(f"Error switching to previous app: {e}")
            return False
    
    def _list_open_apps(self) -> bool:
        """List all open applications"""
        try:
            if self.window_manager:
                apps = self.window_manager.list_open_apps()
                if apps:
                    app_list = ", ".join(apps[:10])  # First 10
                    if len(apps) > 10:
                        app_list += f" and {len(apps) - 10} more"
                    if self.tts:
                        self.tts.say(f"Open apps: {app_list}")
                    return True
                else:
                    if self.tts:
                        self.tts.say("No apps are currently open.")
                    return True
            return False
        except Exception as e:
            self.logger.error(f"Error listing apps: {e}")
            return False
    
    def _switch_to_next_tab(self) -> bool:
        """Switch to next tab"""
        try:
            if self.window_manager:
                return self.window_manager.switch_to_next_tab()
            elif PYAUTOGUI_AVAILABLE:
                pyautogui.hotkey('ctrl', 'tab')
                if self.tts:
                    self.tts.say("Switched to next tab.")
                return True
            return False
        except Exception as e:
            self.logger.error(f"Error switching to next tab: {e}")
            return False
    
    def _switch_to_previous_tab(self) -> bool:
        """Switch to previous tab"""
        try:
            if self.window_manager:
                return self.window_manager.switch_to_previous_tab()
            elif PYAUTOGUI_AVAILABLE:
                pyautogui.hotkey('ctrl', 'shift', 'tab')
                if self.tts:
                    self.tts.say("Switched to previous tab.")
                return True
            return False
        except Exception as e:
            self.logger.error(f"Error switching to previous tab: {e}")
            return False
    
    def _switch_to_tab_number(self, tab_number: int) -> bool:
        """Switch to specific tab number"""
        try:
            if self.window_manager:
                return self.window_manager.switch_to_tab_number(tab_number)
            elif PYAUTOGUI_AVAILABLE:
                pyautogui.hotkey('ctrl', str(tab_number))
                if self.tts:
                    self.tts.say(f"Switched to tab {tab_number}.")
                return True
            return False
        except Exception as e:
            self.logger.error(f"Error switching to tab number: {e}")
            return False
    
    def _close_tab(self) -> bool:
        """Close current tab"""
        try:
            if PYAUTOGUI_AVAILABLE:
                pyautogui.hotkey('ctrl', 'w')
                if self.tts:
                    self.tts.say("Closed tab.")
                return True
            return False
        except Exception as e:
            self.logger.error(f"Error closing tab: {e}")
            return False
    
    def _new_tab(self) -> bool:
        """Open new tab"""
        try:
            if PYAUTOGUI_AVAILABLE:
                pyautogui.hotkey('ctrl', 't')
                if self.tts:
                    self.tts.say("Opened new tab.")
                return True
            return False
        except Exception as e:
            self.logger.error(f"Error opening new tab: {e}")
            return False
    
    def _list_tabs(self) -> bool:
        """List open tabs"""
        try:
            if self.window_manager:
                tabs = self.window_manager.list_open_tabs()
                if tabs:
                    tab_list = ", ".join(tabs[:5])  # First 5
                    if len(tabs) > 5:
                        tab_list += f" and {len(tabs) - 5} more"
                    if self.tts:
                        self.tts.say(f"Open tabs: {tab_list}")
                    return True
                else:
                    if self.tts:
                        self.tts.say("No tabs are currently open.")
                    return True
            return False
        except Exception as e:
            self.logger.error(f"Error listing tabs: {e}")
            return False
    
    # Media control
    def _execute_media_control(self, text: str) -> bool:
        """Execute media control commands"""
        try:
            if 'play' in text:
                return self._media_play()
            elif 'pause' in text:
                return self._media_pause()
            elif 'stop' in text:
                return self._media_stop()
            elif 'next' in text:
                return self._media_next()
            elif 'previous' in text:
                return self._media_previous()
            elif 'start from beginning' in text:
                return self._media_restart()
            return False
        except Exception as e:
            self.logger.error(f"Error executing media control: {e}")
            return False
    
    def _media_play(self) -> bool:
        """Play media"""
        try:
            if PYAUTOGUI_AVAILABLE:
                pyautogui.press('space')  # Common play/pause
                if self.tts:
                    self.tts.say("Playing media.")
                return True
            return False
        except Exception as e:
            self.logger.error(f"Error playing media: {e}")
            return False
    
    def _media_pause(self) -> bool:
        """Pause media"""
        try:
            if PYAUTOGUI_AVAILABLE:
                pyautogui.press('space')  # Common play/pause
                if self.tts:
                    self.tts.say("Paused media.")
                return True
            return False
        except Exception as e:
            self.logger.error(f"Error pausing media: {e}")
            return False
    
    def _media_stop(self) -> bool:
        """Stop media"""
        try:
            if PYAUTOGUI_AVAILABLE:
                pyautogui.press('stop')  # Media stop key
                if self.tts:
                    self.tts.say("Stopped media.")
                return True
            return False
        except Exception as e:
            self.logger.error(f"Error stopping media: {e}")
            return False
    
    def _media_next(self) -> bool:
        """Next track"""
        try:
            if PYAUTOGUI_AVAILABLE:
                pyautogui.press('nexttrack')
                if self.tts:
                    self.tts.say("Next track.")
                return True
            return False
        except Exception as e:
            self.logger.error(f"Error skipping to next track: {e}")
            return False
    
    def _media_previous(self) -> bool:
        """Previous track"""
        try:
            if PYAUTOGUI_AVAILABLE:
                pyautogui.press('prevtrack')
                if self.tts:
                    self.tts.say("Previous track.")
                return True
            return False
        except Exception as e:
            self.logger.error(f"Error going to previous track: {e}")
            return False
    
    def _media_restart(self) -> bool:
        """Restart media from beginning"""
        try:
            if PYAUTOGUI_AVAILABLE:
                pyautogui.press('home')  # Go to beginning
                if self.tts:
                    self.tts.say("Restarted from beginning.")
                return True
            return False
        except Exception as e:
            self.logger.error(f"Error restarting media: {e}")
            return False
    
    # Text operations
    def _execute_text_operation(self, text: str) -> bool:
        """Execute text operations"""
        try:
            if 'type' in text or 'write' in text or 'enter' in text:
                # Extract text to type
                if 'type' in text:
                    text_to_type = text.split('type', 1)[1].strip()
                elif 'write' in text:
                    text_to_type = text.split('write', 1)[1].strip()
                elif 'enter' in text:
                    text_to_type = text.split('enter', 1)[1].strip()
                else:
                    text_to_type = ""
                
                return self._type_text(text_to_type)
            elif 'select all' in text:
                return self._select_all()
            elif 'copy all' in text or 'copy' in text:
                return self._copy_all()
            elif 'paste all' in text or 'paste' in text:
                return self._paste_all()
            elif 'cut' in text:
                return self._cut_text()
            elif 'undo' in text:
                return self._undo()
            elif 'redo' in text:
                return self._redo()
            return False
        except Exception as e:
            self.logger.error(f"Error executing text operation: {e}")
            return False
    
    def _type_text(self, text: str) -> bool:
        """Type text at current cursor position with automatic spacing"""
        try:
            if PYAUTOGUI_AVAILABLE and text:
                # Process text: ensure spaces between words, handle newlines
                processed_text = self._process_text_for_typing(text)
                pyautogui.typewrite(processed_text, interval=0.05)
                if self.tts:
                    preview = processed_text[:50] + "..." if len(processed_text) > 50 else processed_text
                    self.tts.say(f"Typed: {preview}")
                return True
            return False
        except Exception as e:
            self.logger.error(f"Error typing text: {e}")
            return False
    
    def _process_text_for_typing(self, text: str) -> str:
        """Process text for typing: add spaces between words, handle newlines"""
        if not text:
            return text
        
        # Handle newlines
        text = text.replace(' new line ', '\n').replace(' newline ', '\n')
        
        # Split by newlines to process each line separately
        lines = text.split('\n')
        processed_lines = []
        
        for line in lines:
            # Split into words (handles multiple spaces)
            words = line.split()
            if words:
                # Join words with single space
                processed_lines.append(' '.join(words))
            else:
                # Empty line
                processed_lines.append('')
        
        # Join lines back with newlines
        return '\n'.join(processed_lines)
    
    def _select_all(self) -> bool:
        """Select all text"""
        try:
            if PYAUTOGUI_AVAILABLE:
                pyautogui.hotkey('ctrl', 'a')
                if self.tts:
                    self.tts.say("Selected all.")
                return True
            return False
        except Exception as e:
            self.logger.error(f"Error selecting all: {e}")
            return False
    
    def _copy_all(self) -> bool:
        """Copy all text"""
        try:
            if PYAUTOGUI_AVAILABLE:
                pyautogui.hotkey('ctrl', 'a')
                time.sleep(0.1)
                pyautogui.hotkey('ctrl', 'c')
                if self.tts:
                    self.tts.say("Copied all.")
                return True
            return False
        except Exception as e:
            self.logger.error(f"Error copying all: {e}")
            return False
    
    def _paste_all(self) -> bool:
        """Paste text"""
        try:
            if PYAUTOGUI_AVAILABLE:
                pyautogui.hotkey('ctrl', 'v')
                if self.tts:
                    self.tts.say("Pasted.")
                return True
            return False
        except Exception as e:
            self.logger.error(f"Error pasting: {e}")
            return False
    
    def _cut_text(self) -> bool:
        """Cut text"""
        try:
            if PYAUTOGUI_AVAILABLE:
                pyautogui.hotkey('ctrl', 'x')
                if self.tts:
                    self.tts.say("Cut.")
                return True
            return False
        except Exception as e:
            self.logger.error(f"Error cutting text: {e}")
            return False
    
    def _undo(self) -> bool:
        """Undo"""
        try:
            if PYAUTOGUI_AVAILABLE:
                pyautogui.hotkey('ctrl', 'z')
                if self.tts:
                    self.tts.say("Undone.")
                return True
            return False
        except Exception as e:
            self.logger.error(f"Error undoing: {e}")
            return False
    
    def _redo(self) -> bool:
        """Redo"""
        try:
            if PYAUTOGUI_AVAILABLE:
                pyautogui.hotkey('ctrl', 'y')
                if self.tts:
                    self.tts.say("Redone.")
                return True
            return False
        except Exception as e:
            self.logger.error(f"Error redoing: {e}")
            return False
    
    # Accessibility
    def _execute_accessibility(self, text: str) -> bool:
        """Execute accessibility commands"""
        try:
            if 'read screen' in text or 'screen read' in text:
                return self._read_screen()
            elif 'describe screen' in text or 'screen describe' in text:
                return self._describe_screen()
            elif 'navigation mode' in text or 'enable navigation' in text:
                return self._enable_navigation_mode()
            elif 'disable navigation' in text or 'turn off navigation' in text:
                return self._disable_navigation_mode()
            return False
        except Exception as e:
            self.logger.error(f"Error executing accessibility command: {e}")
            return False
    
    def _read_screen(self) -> bool:
        """Read screen content using OCR"""
        try:
            import pyautogui
            import cv2
            import pytesseract
            from PIL import Image
            import numpy as np
            
            # Take screenshot
            screenshot = pyautogui.screenshot()
            img = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)
            
            # Perform OCR
            text = pytesseract.image_to_string(img)
            
            if text.strip():
                # Limit text length for TTS
                display_text = text[:300] + "..." if len(text) > 300 else text
                if self.tts:
                    self.tts.say(f"Screen content: {display_text}")
                self.logger.info(f"Screen read: {text[:100]}...")
                return True
            else:
                if self.tts:
                    self.tts.say("No readable text found on screen.")
                return False
                
        except ImportError as e:
            self.logger.error(f"Required libraries not installed for screen reading: {e}")
            if self.tts:
                self.tts.say("Screen reading requires Tesseract OCR. Please install it.")
            return False
        except Exception as e:
            self.logger.error(f"Error reading screen: {e}")
            if self.tts:
                self.tts.say("Could not read screen content. Please check if Tesseract OCR is installed.")
            return False
    
    def _describe_screen(self) -> bool:
        """Describe current screen layout"""
        try:
            import pyautogui
            import pygetwindow as gw
            
            # Get screen info
            screen_width, screen_height = pyautogui.size()
            
            # Get active window
            try:
                active_window = gw.getActiveWindow()
                if active_window:
                    window_info = f"Active window: {active_window.title}, size {active_window.width} by {active_window.height} pixels"
                else:
                    window_info = "No active window detected"
            except:
                window_info = "Could not detect active window"
            
            description = f"Screen size: {screen_width} by {screen_height} pixels. {window_info}."
            
            if self.tts:
                self.tts.say(description)
            self.logger.info(description)
            return True
            
        except Exception as e:
            self.logger.error(f"Error describing screen: {e}")
            if self.tts:
                self.tts.say("Could not describe screen.")
            return False
    
    def _enable_navigation_mode(self) -> bool:
        """Enable navigation mode for cursor control"""
        try:
            if self.tts:
                self.tts.say("Navigation mode enabled. Use navigate up, down, left, or right to move cursor.")
            self.logger.info("Navigation mode enabled")
            return True
        except Exception as e:
            self.logger.error(f"Error enabling navigation mode: {e}")
            return False
    
    def _disable_navigation_mode(self) -> bool:
        """Disable navigation mode"""
        try:
            if self.tts:
                self.tts.say("Navigation mode disabled.")
            self.logger.info("Navigation mode disabled")
            return True
        except Exception as e:
            self.logger.error(f"Error disabling navigation mode: {e}")
            return False
    
    # Navigation
    def _execute_navigation(self, text: str) -> bool:
        """Execute navigation commands"""
        try:
            if 'scroll up' in text:
                return self._scroll_up()
            elif 'scroll down' in text:
                return self._scroll_down()
            elif 'click' in text:
                return self._click()
            elif 'double click' in text:
                return self._double_click()
            elif 'right click' in text:
                return self._right_click()
            elif 'zoom in' in text:
                return self._zoom_in()
            elif 'zoom out' in text:
                return self._zoom_out()
            return False
        except Exception as e:
            self.logger.error(f"Error executing navigation: {e}")
            return False
    
    def _scroll_up(self) -> bool:
        """Scroll up"""
        try:
            if PYAUTOGUI_AVAILABLE:
                pyautogui.scroll(3)
                if self.tts:
                    self.tts.say("Scrolled up.")
                return True
            return False
        except Exception as e:
            self.logger.error(f"Error scrolling up: {e}")
            return False
    
    def _scroll_down(self) -> bool:
        """Scroll down"""
        try:
            if PYAUTOGUI_AVAILABLE:
                pyautogui.scroll(-3)
                if self.tts:
                    self.tts.say("Scrolled down.")
                return True
            return False
        except Exception as e:
            self.logger.error(f"Error scrolling down: {e}")
            return False
    
    def _click(self) -> bool:
        """Click at current cursor position"""
        try:
            if PYAUTOGUI_AVAILABLE:
                pyautogui.click()
                if self.tts:
                    self.tts.say("Clicked.")
                return True
            return False
        except Exception as e:
            self.logger.error(f"Error clicking: {e}")
            return False
    
    def _double_click(self) -> bool:
        """Double click"""
        try:
            if PYAUTOGUI_AVAILABLE:
                pyautogui.doubleClick()
                if self.tts:
                    self.tts.say("Double clicked.")
                return True
            return False
        except Exception as e:
            self.logger.error(f"Error double clicking: {e}")
            return False
    
    def _right_click(self) -> bool:
        """Right click"""
        try:
            if PYAUTOGUI_AVAILABLE:
                pyautogui.rightClick()
                if self.tts:
                    self.tts.say("Right clicked.")
                return True
            return False
        except Exception as e:
            self.logger.error(f"Error right clicking: {e}")
            return False
    
    def _zoom_in(self) -> bool:
        """Zoom in"""
        try:
            if PYAUTOGUI_AVAILABLE:
                pyautogui.hotkey('ctrl', '+')
                if self.tts:
                    self.tts.say("Zoomed in.")
                return True
            return False
        except Exception as e:
            self.logger.error(f"Error zooming in: {e}")
            return False
    
    def _zoom_out(self) -> bool:
        """Zoom out"""
        try:
            if PYAUTOGUI_AVAILABLE:
                pyautogui.hotkey('ctrl', '-')
                if self.tts:
                    self.tts.say("Zoomed out.")
                return True
            return False
        except Exception as e:
            self.logger.error(f"Error zooming out: {e}")
            return False
    
    # Web operations
    def _execute_web_operation(self, text: str) -> bool:
        """Execute web operations"""
        try:
            if 'next tab' in text or 'switch to next tab' in text:
                return self._switch_to_next_tab()
            elif 'previous tab' in text or 'switch to previous tab' in text:
                return self._switch_to_previous_tab()
            elif 'switch tab' in text:
                # Try to extract tab number or name
                if 'tab number' in text or 'tab' in text:
                    # Extract number
                    import re
                    numbers = re.findall(r'\d+', text)
                    if numbers:
                        return self._switch_to_tab_number(int(numbers[0]))
                    else:
                        return self._switch_to_next_tab()
            elif 'close tab' in text:
                return self._close_tab()
            elif 'new tab' in text:
                return self._new_tab()
            elif 'list tabs' in text:
                return self._list_tabs()
            elif 'google' in text and text.startswith('google '):
                # Handle "google [query]" commands
                query = text[7:].strip()  # Remove "google " prefix
                # Special case: "google youtube" opens YouTube
                if query.lower() == 'youtube':
                    webbrowser.open('https://www.youtube.com')
                    if self.tts:
                        self.tts.say("Opening YouTube.")
                    return True
                # Otherwise, search Google
                import urllib.parse
                encoded_query = urllib.parse.quote_plus(query)
                url = f"https://www.google.com/search?q={encoded_query}"
                webbrowser.open(url)
                if self.tts:
                    self.tts.say(f"Searching for {query}.")
                return True
            elif 'google for' in text or 'google about' in text:
                # Extract query after "google for" or "google about"
                import urllib.parse
                if 'google for' in text:
                    query = text.split('google for', 1)[1].strip()
                else:
                    query = text.split('google about', 1)[1].strip()
                encoded_query = urllib.parse.quote_plus(query)
                url = f"https://www.google.com/search?q={encoded_query}"
                webbrowser.open(url)
                if self.tts:
                    self.tts.say(f"Searching for {query}.")
                return True
            elif text.startswith('look for ') or text.startswith('look up '):
                # Handle "look for [query]" and "look up [query]"
                import urllib.parse
                if text.startswith('look for '):
                    query = text[9:].strip()
                else:
                    query = text[8:].strip()
                encoded_query = urllib.parse.quote_plus(query)
                url = f"https://www.google.com/search?q={encoded_query}"
                webbrowser.open(url)
                if self.tts:
                    self.tts.say(f"Searching for {query}.")
                return True
            elif text.startswith('find ') and 'file' not in text and 'folder' not in text:
                # Handle "find [query]" - but not if it's about files/folders
                import urllib.parse
                query = text[5:].strip()
                encoded_query = urllib.parse.quote_plus(query)
                url = f"https://www.google.com/search?q={encoded_query}"
                webbrowser.open(url)
                if self.tts:
                    self.tts.say(f"Searching for {query}.")
                return True
            elif 'search' in text:
                # Extract search query - handle different patterns
                query = ""
                if 'search for' in text:
                    query = text.split('search for', 1)[1].strip()
                elif 'search youtube' in text:
                    query = text.split('search youtube', 1)[1].strip()
                    if query:  # If there's a query after "youtube"
                        # Search YouTube
                        import urllib.parse
                        encoded_query = urllib.parse.quote_plus(query)
                        url = f"https://www.youtube.com/results?search_query={encoded_query}"
                        webbrowser.open(url)
                        if self.tts:
                            self.tts.say(f"Searching YouTube for {query}.")
                        return True
                    else:
                        # Just "search youtube" without query - open YouTube
                        webbrowser.open('https://www.youtube.com')
                        if self.tts:
                            self.tts.say("Opening YouTube.")
                        return True
                elif 'search amazon' in text:
                    query = text.split('search amazon', 1)[1].strip()
                    if query:
                        import urllib.parse
                        encoded_query = urllib.parse.quote_plus(query)
                        url = f"https://www.amazon.com/s?k={encoded_query}"
                        webbrowser.open(url)
                        if self.tts:
                            self.tts.say(f"Searching Amazon for {query}.")
                        return True
                elif 'search' in text:
                    query = text.split('search', 1)[1].strip()
                
                # If query is empty, ask what to search
                if not query:
                    if self.tts:
                        self.tts.say("What would you like me to search for?")
                    return False
                
                # Default to Google search (handles "search python tutorials", "search bmsit", etc.)
                import urllib.parse
                encoded_query = urllib.parse.quote_plus(query)
                url = f"https://www.google.com/search?q={encoded_query}"
                webbrowser.open(url)
                if self.tts:
                    self.tts.say(f"Searching for {query}.")
                return True
            elif 'open website' in text or 'go to website' in text:
                url = text.replace('open website', '').replace('go to website', '').strip()
                if not url.startswith(('http://', 'https://')):
                    url = 'https://' + url
                webbrowser.open(url)
                if self.tts:
                    self.tts.say(f"Opening {url}.")
                return True
            return False
        except Exception as e:
            self.logger.error(f"Error executing web operation: {e}")
            return False
    
    # Command prompt operations
    def _execute_cmd_operation(self, text: str) -> bool:
        """Execute command prompt operations"""
        try:
            if 'command prompt' in text or 'cmd' in text or 'powershell' in text:
                # Open command prompt
                if self.platform == "windows":
                    if 'powershell' in text:
                        subprocess.Popen(["powershell.exe"])
                    else:
                        subprocess.Popen(["cmd.exe"])
                    if self.tts:
                        self.tts.say("Opened command prompt.")
                    return True
            elif 'execute command' in text or 'run command' in text:
                # Extract command
                if 'execute command' in text:
                    command = text.split('execute command', 1)[1].strip()
                elif 'run command' in text:
                    command = text.split('run command', 1)[1].strip()
                else:
                    command = ""
                
                if command:
                    # Execute in command prompt
                    if self.platform == "windows":
                        subprocess.run(["cmd.exe", "/c", command], shell=True)
                        if self.tts:
                            self.tts.say(f"Executed command: {command}.")
                        return True
            elif 'type command' in text:
                # Type command in current terminal
                if 'type command' in text:
                    command = text.split('type command', 1)[1].strip()
                else:
                    command = ""
                
                if command and PYAUTOGUI_AVAILABLE:
                    pyautogui.typewrite(command, interval=0.05)
                    time.sleep(0.2)
                    pyautogui.press('enter')
                    if self.tts:
                        self.tts.say(f"Typed command: {command}.")
                    return True
            return False
        except Exception as e:
            self.logger.error(f"Error executing cmd operation: {e}")
            return False
    
    # Generic operations
    def _open_generic(self, target: str, context: Optional[Dict]) -> bool:
        """Try to open target as app, file, or website"""
        # Try as app first
        if self._open_app(target):
            return True
        
        # Try as file
        if self._open_file(target, context):
            return True
        
        # Try as website
        try:
            if not target.startswith(('http://', 'https://')):
                target = 'https://' + target
            webbrowser.open(target)
            if self.tts:
                self.tts.say(f"Opening {target}.")
            return True
        except:
            pass
        
        return False
    
    def _close_generic(self, target: str) -> bool:
        """Close generic target"""
        return self._close_app(target)
    
    def _try_generic_execution(self, text: str, context: Optional[Dict]) -> bool:
        """Try to execute as generic command"""
        # CRITICAL: Don't treat "go back" as search - it should have been handled already
        if any(word in text for word in ['go back', 'back directory', 'previous directory', 'navigate back', 'go up']):
            # This should have been handled in file operations - try it as directory navigation
            self.logger.warning(f"'Go back' command reached generic handler - attempting directory navigation")
            if self._is_file_operation(text):
                return self._execute_file_operation(text, context)
            return False
        
        # Try keyboard shortcuts
        shortcut_map = {
            'save': ('ctrl', 's'),
            'open': ('ctrl', 'o'),
            'new': ('ctrl', 'n'),
            'find': ('ctrl', 'f'),
        }
        
        for keyword, shortcut in shortcut_map.items():
            if keyword in text:
                if PYAUTOGUI_AVAILABLE:
                    pyautogui.hotkey(*shortcut)
                    if self.tts:
                        self.tts.say(f"Executed {keyword}.")
                    return True
        
        # DYNAMIC FALLBACK: If no command matches, treat as Google search
        # This allows teachers to say ANYTHING and it will search for it
        # BUT: Exclude known commands that should have been handled
        exclude_patterns = ['go back', 'create file', 'delete file', 'open file']
        if any(pattern in text for pattern in exclude_patterns):
            self.logger.warning(f"Command '{text}' should have been handled earlier - not treating as search")
            return False
        
        words = text.split()
        if len(words) >= 1:  # Any text - treat as search query
            self.logger.info(f"No command matched, treating as search query: '{text}'")
            import urllib.parse
            encoded_query = urllib.parse.quote_plus(text)
            url = f"https://www.google.com/search?q={encoded_query}"
            webbrowser.open(url)
            if self.tts:
                self.tts.say(f"Searching for {text}.")
            return True
        
        return False

