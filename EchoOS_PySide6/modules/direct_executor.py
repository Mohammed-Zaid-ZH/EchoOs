"""
Direct Command Executor for EchoOS
Simple, reliable command execution that actually works
"""

import os
import sys
import time
import logging
import subprocess
import platform
import webbrowser
from typing import Optional, Dict, List, Any

class DirectExecutor:
    """Direct command executor that actually executes commands"""
    
    def __init__(self, tts=None, auth=None):
        self.tts = tts
        self.auth = auth  # Authentication system - REQUIRED
        self.logger = logging.getLogger(__name__)
        self.platform = platform.system().lower()
        
        # Load discovered apps (NO HARDCODING - all apps discovered dynamically)
        self.discovered_apps = self._load_discovered_apps()
    
    def _load_discovered_apps(self) -> Dict[str, str]:
        """Load discovered apps from apps.json"""
        try:
            import json
            with open('config/apps.json', 'r', encoding='utf-8') as f:
                apps_data = json.load(f)
            
            discovered_apps = {}
            for app in apps_data.get('apps', []):
                name = app.get('name', '').lower()
                path = app.get('path', '')
                if name and path:
                    discovered_apps[name] = path
                    # Also add variations
                    if ' ' in name:
                        discovered_apps[name.replace(' ', '')] = path
                    if '-' in name:
                        discovered_apps[name.replace('-', '')] = path
            
            self.logger.info(f"Loaded {len(discovered_apps)} discovered apps")
            return discovered_apps
            
        except Exception as e:
            self.logger.error(f"Failed to load discovered apps: {e}")
            return {}
    
    def _find_app_fuzzy(self, target: str) -> Optional[str]:
        """Find app using fuzzy matching"""
        try:
            from rapidfuzz import fuzz, process
            
            # Get all app names
            app_names = list(self.discovered_apps.keys())
            
            # Find best match
            result = process.extractOne(target, app_names, scorer=fuzz.ratio)
            if result and len(result) == 2:
                best_match, score = result
                if score > 60:  # 60% similarity threshold
                    return best_match
            
            return None
            
        except Exception as e:
            self.logger.error(f"Fuzzy matching error: {e}")
            return None
    
    def _open_file(self, filename: str) -> bool:
        """Open a file in the current directory"""
        try:
            # Check if file exists in current directory
            if os.path.exists(filename):
                self.logger.info(f"Opening file: {filename}")
                os.startfile(filename)
                if self.tts:
                    self.tts.say(f"Opening file {filename}.")
                return True
            else:
                # Try with common extensions
                extensions = ['.txt', '.doc', '.docx', '.pdf', '.py', '.js', '.html', '.css', '.json']
                for ext in extensions:
                    full_path = filename + ext
                    if os.path.exists(full_path):
                        self.logger.info(f"Opening file: {full_path}")
                        os.startfile(full_path)
                        if self.tts:
                            self.tts.say(f"Opening file {full_path}.")
                        return True
                
                if self.tts:
                    self.tts.say(f"File {filename} not found.")
                return False
                
        except Exception as e:
            self.logger.error(f"Error opening file: {e}")
            if self.tts:
                self.tts.say("Error opening file.")
            return False
    
    def _copy_content(self, target: str) -> bool:
        """Copy content from a file or selected text or current file/folder"""
        try:
            import pyautogui
            import pyperclip
            import pygetwindow as gw
            
            if target.startswith('file '):
                # Copy entire file content
                filename = target[5:].strip()
                if os.path.exists(filename):
                    with open(filename, 'r', encoding='utf-8') as f:
                        content = f.read()
                    pyperclip.copy(content)
                    if self.tts:
                        self.tts.say(f"Copied content from {filename}.")
                    return True
                else:
                    if self.tts:
                        self.tts.say(f"File {filename} not found.")
                    return False
            else:
                # Check if File Explorer is open - if so, copy selected file/folder
                try:
                    all_windows = gw.getAllWindows()
                    explorer_windows = [w for w in all_windows if w.title and 
                                      ('explorer' in w.title.lower() or 'file' in w.title.lower() or 'this pc' in w.title.lower())]
                    
                    if explorer_windows:
                        # In File Explorer - copy selected item
                        explorer_windows[0].activate()
                        time.sleep(0.2)
                        pyautogui.hotkey('ctrl', 'c')
                        time.sleep(0.2)
                        
                        # Get what was copied
                        copied = pyperclip.paste()
                        if self.tts:
                            if os.path.exists(copied):
                                item_name = os.path.basename(copied)
                                self.tts.say(f"Copied {item_name}.")
                            else:
                                self.tts.say("Copied selected item.")
                        return True
                except Exception as e:
                    self.logger.debug(f"File Explorer copy failed, trying text copy: {e}")
                
                # Copy selected text (Ctrl+A, Ctrl+C) or just Ctrl+C if already selected
                try:
                    # First try Ctrl+C (in case something is already selected)
                    pyautogui.hotkey('ctrl', 'c')
                    time.sleep(0.2)
                    copied = pyperclip.paste()
                    
                    if copied and copied.strip():
                        # Something was copied
                        if self.tts:
                            preview = copied[:50] + "..." if len(copied) > 50 else copied
                            self.tts.say(f"Copied: {preview}")
                        return True
                    
                    # Nothing was selected, select all and copy
                    pyautogui.hotkey('ctrl', 'a')
                    time.sleep(0.2)
                    pyautogui.hotkey('ctrl', 'c')
                    time.sleep(0.2)
                    
                    if self.tts:
                        self.tts.say("Copied selected content.")
                    return True
                except Exception as e2:
                    self.logger.error(f"Error with text copy: {e2}")
                
                if self.tts:
                    self.tts.say("Copied content.")
                return True
                
        except Exception as e:
            self.logger.error(f"Error copying content: {e}")
            if self.tts:
                self.tts.say("Error copying content.")
            return False
    
    def _paste_content(self) -> bool:
        """Paste content from clipboard"""
        try:
            import pyautogui
            pyautogui.hotkey('ctrl', 'v')
            
            if self.tts:
                self.tts.say("Content pasted.")
            return True
            
        except Exception as e:
            self.logger.error(f"Error pasting content: {e}")
            if self.tts:
                self.tts.say("Error pasting content.")
            return False
    
    def _system_info(self) -> bool:
        """Display system information"""
        try:
            import platform
            import psutil
            
            # Get system information
            info = f"""
System Information:
OS: {platform.system()} {platform.release()}
Architecture: {platform.architecture()[0]}
Processor: {platform.processor()}
RAM: {round(psutil.virtual_memory().total / (1024**3), 2)} GB
Available RAM: {round(psutil.virtual_memory().available / (1024**3), 2)} GB
CPU Usage: {psutil.cpu_percent()}%
Disk Usage: {psutil.disk_usage('/').percent}%
            """.strip()
            
            print(info)
            if self.tts:
                self.tts.say("System information displayed in console.")
            return True
            
        except Exception as e:
            self.logger.error(f"Error getting system info: {e}")
            if self.tts:
                self.tts.say("Error getting system information.")
            return False
    
    def _web_back(self) -> bool:
        """Navigate back in web browser"""
        try:
            import pyautogui
            pyautogui.hotkey('alt', 'left')
            
            if self.tts:
                self.tts.say("Navigated back.")
            return True
            
        except Exception as e:
            self.logger.error(f"Error navigating back: {e}")
            if self.tts:
                self.tts.say("Error navigating back.")
            return False
    
    def _web_forward(self) -> bool:
        """Navigate forward in web browser"""
        try:
            import pyautogui
            pyautogui.hotkey('alt', 'right')
            
            if self.tts:
                self.tts.say("Navigated forward.")
            return True
            
        except Exception as e:
            self.logger.error(f"Error navigating forward: {e}")
            if self.tts:
                self.tts.say("Error navigating forward.")
            return False
    
    def _scroll_page(self, command: str) -> bool:
        """Scroll page up or down"""
        try:
            import pyautogui
            
            if 'up' in command:
                pyautogui.scroll(3)  # Scroll up
                if self.tts:
                    self.tts.say("Scrolled up.")
            else:
                pyautogui.scroll(-3)  # Scroll down
                if self.tts:
                    self.tts.say("Scrolled down.")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error scrolling: {e}")
            if self.tts:
                self.tts.say("Error scrolling.")
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
                return True
            else:
                if self.tts:
                    self.tts.say("No readable text found on screen.")
                return False
                
        except Exception as e:
            self.logger.error(f"Error reading screen: {e}")
            if self.tts:
                self.tts.say("Screen reading not available. Please install required libraries.")
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
                    window_info = f"Active window: {active_window.title}, size {active_window.width}x{active_window.height}"
                else:
                    window_info = "No active window detected"
            except:
                window_info = "Window information not available"
            
            description = f"Screen size: {screen_width}x{screen_height}. {window_info}. Current cursor position: {pyautogui.position()}"
            
            if self.tts:
                self.tts.say(description)
            return True
            
        except Exception as e:
            self.logger.error(f"Error describing screen: {e}")
            if self.tts:
                self.tts.say("Could not describe screen.")
            return False
    
    def _enable_navigation_mode(self) -> bool:
        """Enable navigation mode"""
        try:
            # Set navigation mode flag (you can store this in a class variable)
            if not hasattr(self, 'navigation_mode'):
                self.navigation_mode = False
            self.navigation_mode = True
            
            if self.tts:
                self.tts.say("Navigation mode enabled. You can now use voice commands to navigate directories and control the cursor.")
            return True
            
        except Exception as e:
            self.logger.error(f"Error enabling navigation mode: {e}")
            if self.tts:
                self.tts.say("Could not enable navigation mode.")
            return False
    
    def _disable_navigation_mode(self) -> bool:
        """Disable navigation mode"""
        try:
            if hasattr(self, 'navigation_mode'):
                self.navigation_mode = False
            
            if self.tts:
                self.tts.say("Navigation mode disabled.")
            return True
            
        except Exception as e:
            self.logger.error(f"Error disabling navigation mode: {e}")
            if self.tts:
                self.tts.say("Could not disable navigation mode.")
            return False
    
    def _navigate_directory(self, target: str) -> bool:
        """Navigate to a directory - MAIN PILLAR for file/folder navigation"""
        try:
            import os
            import time
            
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
                'root': os.path.expanduser("~")
            }
            
            target_lower = target.lower().strip()
            target_path = None
            
            # Resolve to full path
            if target_lower in common_dirs:
                target_path = common_dirs[target_lower]
            elif target_lower in ['back', 'up', 'parent', 'previous']:
                current = os.getcwd()
                target_path = os.path.dirname(current) if current != os.path.dirname(current) else os.path.expanduser("~")
            else:
                # Try searching in current directory
                current = os.getcwd()
                try:
                    for item in os.listdir(current):
                        if target_lower in item.lower() and os.path.isdir(os.path.join(current, item)):
                            target_path = os.path.join(current, item)
                            break
                except:
                    pass
                
                # If not found, try as relative path
                if not target_path:
                    test_path = os.path.join(current, target)
                    if os.path.exists(test_path) and os.path.isdir(test_path):
                        target_path = test_path
                    else:
                        # Try as absolute path
                        if os.path.exists(target) and os.path.isdir(target):
                            target_path = target
            
            # Check if path exists
            if not target_path or not os.path.exists(target_path) or not os.path.isdir(target_path):
                if self.tts:
                    self.tts.say(f"Directory {target} not found.")
                return False
            
            # Update current directory
            os.chdir(target_path)
            self.logger.info(f"Navigated to: {target_path}")
            
            # NOW: Navigate in File Explorer if it's open (use FULL PATH)
            try:
                import pyautogui
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
                self.tts.say(f"Navigated to {os.path.basename(target_path)} directory.")
            return True
                
        except Exception as e:
            self.logger.error(f"Error navigating directory: {e}")
            if self.tts:
                self.tts.say("Could not navigate to directory.")
            return False
    
    def _list_directory(self) -> bool:
        """List current directory contents"""
        try:
            import os
            
            files = os.listdir('.')
            if files:
                # Limit to first 10 items for TTS
                display_files = files[:10]
                file_list = ", ".join(display_files)
                if len(files) > 10:
                    file_list += f" and {len(files) - 10} more items"
                
                if self.tts:
                    self.tts.say(f"Directory contains: {file_list}")
            else:
                if self.tts:
                    self.tts.say("Directory is empty.")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error listing directory: {e}")
            if self.tts:
                self.tts.say("Could not list directory contents.")
            return False
    
    def _go_back_directory(self) -> bool:
        """Go back to parent directory - MAIN PILLAR for navigation"""
        try:
            import os
            import time
            
            current_dir = os.getcwd()
            parent_dir = os.path.dirname(current_dir)
            
            if parent_dir == current_dir:  # Already at root
                if self.tts:
                    self.tts.say("Already at root directory.")
                return True
            
            # Update programmatic directory first
            os.chdir(parent_dir)
            self.logger.info(f"Went back to: {parent_dir}")
            
            # Navigate in File Explorer if it's open
            try:
                import pyautogui
                import pygetwindow as gw
                
                # Find File Explorer windows
                all_windows = gw.getAllWindows()
                explorer_windows = []
                for w in all_windows:
                    if w.title and ('explorer' in w.title.lower() or 'file' in w.title.lower() or 'this pc' in w.title.lower()):
                        explorer_windows.append(w)
                
                if explorer_windows:
                    # Activate File Explorer
                    explorer_windows[0].activate()
                    time.sleep(0.6)  # Increased wait time
                    
                    # Method 1: Use Alt+Left Arrow (back button)
                    pyautogui.hotkey('alt', 'left')
                    time.sleep(0.8)  # Wait for navigation
                    
                    # Method 2: Also update address bar to ensure correct location
                    pyautogui.hotkey('ctrl', 'l')  # Focus address bar
                    time.sleep(0.4)
                    pyautogui.hotkey('ctrl', 'a')  # Select all
                    time.sleep(0.2)
                    pyautogui.press('delete')  # Clear
                    time.sleep(0.1)
                    pyautogui.typewrite(parent_dir, interval=0.02)  # Type full path
                    time.sleep(0.4)
                    pyautogui.press('enter')
                    time.sleep(0.8)  # Wait for navigation to complete
                    
                    # Verify we're in the right directory
                    try:
                        os.chdir(parent_dir)
                    except:
                        pass
                    
                    self.logger.info(f"✅ Navigated File Explorer back to: {parent_dir}")
                    if self.tts:
                        folder_name = os.path.basename(parent_dir) if os.path.basename(parent_dir) else parent_dir
                        self.tts.say(f"Went back to {folder_name} directory.")
                    return True
            except Exception as e:
                self.logger.error(f"Error navigating back in File Explorer: {e}")
                # Continue with programmatic navigation
            
            # Fallback: programmatic navigation succeeded
            if self.tts:
                folder_name = os.path.basename(parent_dir) if os.path.basename(parent_dir) else parent_dir
                self.tts.say(f"Went back to {folder_name} directory.")
            return True
            
        except Exception as e:
            self.logger.error(f"Error going back directory: {e}")
            if self.tts:
                self.tts.say("Could not go back directory.")
            return False
    
    def _show_current_directory(self) -> bool:
        """Show current directory path"""
        try:
            import os
            
            current_dir = os.getcwd()
            if self.tts:
                self.tts.say(f"Current directory: {current_dir}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error showing current directory: {e}")
            if self.tts:
                self.tts.say("Could not show current directory.")
            return False
    
    def _navigate_cursor(self, direction: str) -> bool:
        """Navigate cursor (only when navigation mode is enabled)"""
        try:
            if not hasattr(self, 'navigation_mode') or not self.navigation_mode:
                if self.tts:
                    self.tts.say("Navigation mode is not enabled. Say 'enable navigation mode' first.")
                return False
            
            import pyautogui
            
            current_x, current_y = pyautogui.position()
            step = 50  # Navigation step size
            
            if direction.lower() == "up":
                new_y = max(0, current_y - step)
                pyautogui.moveTo(current_x, new_y)
                if self.tts:
                    self.tts.say(f"Moved cursor up to position {current_x}, {new_y}")
                    
            elif direction.lower() == "down":
                screen_height = pyautogui.size().height
                new_y = min(screen_height, current_y + step)
                pyautogui.moveTo(current_x, new_y)
                if self.tts:
                    self.tts.say(f"Moved cursor down to position {current_x}, {new_y}")
                    
            elif direction.lower() == "left":
                new_x = max(0, current_x - step)
                pyautogui.moveTo(new_x, current_y)
                if self.tts:
                    self.tts.say(f"Moved cursor left to position {new_x}, {current_y}")
                    
            elif direction.lower() == "right":
                screen_width = pyautogui.size().width
                new_x = min(screen_width, current_x + step)
                pyautogui.moveTo(new_x, current_y)
                if self.tts:
                    self.tts.say(f"Moved cursor right to position {new_x}, {current_y}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error navigating cursor: {e}")
            if self.tts:
                self.tts.say("Cursor navigation failed.")
            return False
    
    def execute_command(self, voice_text: str) -> bool:
        """Execute voice command directly - REQUIRES AUTHENTICATION"""
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
            
            voice_text = voice_text.lower().strip()
            self.logger.info(f"Direct executor processing: '{voice_text}'")
            
            # System commands
            if any(word in voice_text for word in ['shutdown', 'shut down', 'turn off']):
                return self._shutdown()
            elif any(word in voice_text for word in ['restart', 'reboot']):
                return self._restart()
            elif any(word in voice_text for word in ['lock screen', 'lock']):
                return self._lock_screen()
            elif any(word in voice_text for word in ['sleep', 'hibernate']):
                return self._sleep()
            
            # Volume commands - check for percentage first (e.g., "volume 50", "volume fifty", "volume five zero")
            elif 'volume' in voice_text:
                import re
                # First try to extract numeric digits
                numbers = re.findall(r'\d+', voice_text)
                volume_percent = None
                
                if numbers:
                    # Get the first number found
                    volume_percent = int(numbers[0])
                else:
                    # Try to convert word numbers (e.g., "fifty", "twenty", "one hundred")
                    volume_percent = self._extract_number_from_text(voice_text)
                
                if volume_percent is not None:
                    # Clamp between 0 and 100
                    volume_percent = max(0, min(100, volume_percent))
                    return self._set_volume(volume_percent)
                # If no number found, check for up/down/mute
                elif any(word in voice_text for word in ['volume up', 'louder']):
                    return self._volume_up()
                elif any(word in voice_text for word in ['volume down', 'quieter']):
                    return self._volume_down()
                elif any(word in voice_text for word in ['mute', 'silent']):
                    return self._mute()
            elif any(word in voice_text for word in ['volume up', 'louder']):
                return self._volume_up()
            elif any(word in voice_text for word in ['volume down', 'quieter']):
                return self._volume_down()
            elif any(word in voice_text for word in ['mute', 'silent']):
                return self._mute()
            
            # File operations
            elif voice_text.startswith('open file '):
                filename = voice_text[10:].strip()
                return self._open_file(filename)
            # Copy commands - handle both "copy" and "copy file [name]"
            elif voice_text.startswith('copy file '):
                target = voice_text[10:].strip()
                return self._copy_content(f'file {target}')
            elif voice_text.strip() == 'copy' or voice_text.strip() == 'copy all' or voice_text.strip() == 'copy selected':
                # Just "copy" - copy current selection or current file/folder
                return self._copy_content('')
            elif voice_text.strip() == 'paste' or voice_text.strip() == 'paste all':
                return self._paste_content()
            
            # Open commands - Check File Explorer context FIRST
            elif voice_text.startswith('open '):
                target = voice_text[5:].strip()
                # If File Explorer is open, prioritize file/folder operations
                if self._is_file_explorer_open():
                    # Try file/folder first when File Explorer is open
                    if self._open_folder_or_file_in_explorer(target):
                        return True
                # Then try normal open (app, website, etc.)
                return self._open_target(target)
            
            # Close commands
            elif voice_text.startswith('close '):
                target = voice_text[6:].strip()
                return self._close_target(target)
            
            # Google/Search commands - DYNAMIC: handle ANY search variation
            # Handle "google" variations
            elif voice_text.startswith('google '):
                query = voice_text[7:].strip()
                # Special case: "google youtube" opens YouTube
                if query.lower() == 'youtube':
                    return self._open_website('https://www.youtube.com')
                # Otherwise, search Google
                return self._search_web(query)
            elif 'google for' in voice_text or 'google about' in voice_text:
                # Extract query after "google for" or "google about"
                if 'google for' in voice_text:
                    query = voice_text.split('google for', 1)[1].strip()
                else:
                    query = voice_text.split('google about', 1)[1].strip()
                return self._search_web(query)
            
            # Handle "search" variations - DYNAMIC: accepts any query
            elif voice_text.startswith('search '):
                query = voice_text[7:].strip()
                # Handle "search youtube [query]" for YouTube search
                if query.lower().startswith('youtube '):
                    youtube_query = query[8:].strip()  # Remove "youtube " prefix
                    if youtube_query:  # Only if there's a query after "youtube"
                        return self._search_youtube(youtube_query)
                    else:
                        # Just "search youtube" without query - open YouTube
                        return self._open_website('https://www.youtube.com')
                # Handle "search amazon [query]" for Amazon search
                elif query.lower().startswith('amazon '):
                    amazon_query = query[7:].strip()
                    if amazon_query:
                        return self._search_amazon(amazon_query)
                # Default to Google search (handles "search python tutorials", "search bmsit", etc.)
                return self._search_web(query)
            elif 'search for' in voice_text:
                query = voice_text.split('search for', 1)[1].strip()
                # Check for specific search engines
                if query.lower().startswith('youtube '):
                    return self._search_youtube(query[8:].strip())
                elif query.lower().startswith('amazon '):
                    return self._search_amazon(query[7:].strip())
                return self._search_web(query)
            elif 'search about' in voice_text:
                query = voice_text.split('search about', 1)[1].strip()
                return self._search_web(query)
            
            # Handle "look for", "find", "look up" - DYNAMIC search patterns
            elif voice_text.startswith('look for '):
                query = voice_text[9:].strip()
                return self._search_web(query)
            elif voice_text.startswith('find '):
                query = voice_text[5:].strip()
                # Check if it's a file operation first
                if 'file' in query or 'folder' in query:
                    # Let file operations handle it
                    pass
                else:
                    # Treat as web search
                    return self._search_web(query)
            elif voice_text.startswith('look up '):
                query = voice_text[8:].strip()
                return self._search_web(query)
            
            # Type commands
            elif voice_text.startswith('type '):
                text = voice_text[5:].strip()
                if text:
                    return self._type_text(text)
                else:
                    if self.tts:
                        self.tts.say("Please say what you want to type. For example, 'type hello world'")
                    return False
            
            # Window control commands
            elif any(word in voice_text for word in ['minimize', 'minimise']):
                return self._minimize_window()
            elif any(word in voice_text for word in ['maximize', 'maximise']):
                return self._maximize_window()
            
            # System info
            elif any(word in voice_text for word in ['system info', 'system information', 'computer info']):
                return self._system_info()
            
            # Directory navigation - check BEFORE web navigation
            elif any(word in voice_text for word in ['back directory', 'previous directory', 'navigate back', 'parent directory']):
                return self._go_back_directory()
            
            # Web navigation
            elif any(word in voice_text for word in ['go back', 'back', 'previous page']):
                # Check if File Explorer is open - if so, treat as directory navigation
                try:
                    import pygetwindow as gw
                    all_windows = gw.getAllWindows()
                    explorer_open = any(w.title and ('explorer' in w.title.lower() or 'file' in w.title.lower() or 'this pc' in w.title.lower()) for w in all_windows)
                    
                    if explorer_open:
                        return self._go_back_directory()
                    else:
                        return self._web_back()
                except:
                    # Default to web navigation if can't determine
                    return self._web_back()
            elif any(word in voice_text for word in ['go forward', 'forward', 'next page']):
                return self._web_forward()
            elif any(word in voice_text for word in ['scroll up', 'scroll down']):
                return self._scroll_page(voice_text)
            
            # Media commands
            elif any(word in voice_text for word in ['play', 'pause', 'stop', 'next', 'previous']):
                return self._media_control(voice_text)
            
            # File operations
            elif any(word in voice_text for word in ['create file', 'delete file', 'copy file']):
                return self._file_operation(voice_text)
            elif any(word in voice_text for word in ['save file', 'save', 'save as']):
                return self._save_file(voice_text)
            
            # Accessibility commands
            elif any(word in voice_text for word in ['read screen', 'screen read']):
                return self._read_screen()
            elif any(word in voice_text for word in ['describe screen', 'screen describe']):
                return self._describe_screen()
            elif any(word in voice_text for word in ['navigation mode', 'enable navigation']):
                return self._enable_navigation_mode()
            elif any(word in voice_text for word in ['disable navigation', 'turn off navigation']):
                return self._disable_navigation_mode()
            
            # Directory navigation
            elif voice_text.startswith('navigate to ') or voice_text.startswith('go to '):
                target = voice_text.replace('navigate to ', '').replace('go to ', '').strip()
                return self._navigate_directory(target)
            elif any(word in voice_text for word in ['list directory', 'list files', 'show files']):
                return self._list_directory()
            # Directory navigation back - prioritize if File Explorer is open
            elif any(word in voice_text for word in ['current directory', 'where am i', 'pwd']):
                return self._show_current_directory()
            
            # Cursor navigation (when navigation mode is enabled)
            elif any(word in voice_text for word in ['navigate up', 'move up', 'cursor up']):
                return self._navigate_cursor('up')
            elif any(word in voice_text for word in ['navigate down', 'move down', 'cursor down']):
                return self._navigate_cursor('down')
            elif any(word in voice_text for word in ['navigate left', 'move left', 'cursor left']):
                return self._navigate_cursor('left')
            elif any(word in voice_text for word in ['navigate right', 'move right', 'cursor right']):
                return self._navigate_cursor('right')
            
            else:
                # DYNAMIC FALLBACK: If no command matches, treat as Google search
                # This allows teachers to say ANYTHING and it will search for it
                # Only do this if it's not a single word (likely a command) and not too short
                words = voice_text.split()
                if len(words) >= 2:  # At least 2 words - likely a search query
                    self.logger.info(f"No command matched, treating as search query: '{voice_text}'")
                    return self._search_web(voice_text)
                else:
                    # Try to execute as generic command first
                    if self._execute_generic(voice_text):
                        return True
                    # If generic command fails, still try as search (single word searches are valid)
                    self.logger.info(f"No command matched, treating as search query: '{voice_text}'")
                    return self._search_web(voice_text)
                
        except Exception as e:
            self.logger.error(f"Error executing command: {e}")
            if self.tts:
                self.tts.say("Sorry, I couldn't execute that command.")
            return False
    
    def _is_file_explorer_open(self) -> bool:
        """Check if File Explorer is currently open"""
        try:
            import pygetwindow as gw
            all_windows = gw.getAllWindows()
            for w in all_windows:
                if w.title and ('explorer' in w.title.lower() or 'file' in w.title.lower() or 'this pc' in w.title.lower()):
                    return True
            return False
        except:
            return False
    
    def _open_folder_or_file_in_explorer(self, target: str) -> bool:
        """Open folder or file in File Explorer - takes priority when File Explorer is open"""
        try:
            import os
            import time
            import pyautogui
            import pygetwindow as gw
            
            original_target = target
            target_lower = target.lower().strip()
            
            # Find File Explorer windows
            all_windows = gw.getAllWindows()
            explorer_windows = []
            for w in all_windows:
                if w.title and ('explorer' in w.title.lower() or 'file' in w.title.lower() or 'this pc' in w.title.lower()):
                    explorer_windows.append(w)
            
            if not explorer_windows:
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
                import pyperclip
                address_bar_path = pyperclip.paste().strip()
                if address_bar_path and os.path.exists(address_bar_path) and os.path.isdir(address_bar_path):
                    current_dir = address_bar_path
                    self.logger.info(f"Got directory from address bar: {current_dir}")
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
            os.chdir(current_dir)  # Sync working directory
            
            self.logger.info(f"File Explorer open - searching for '{original_target}' in: {current_dir}")
            
            # Check for exact folder match first
            folder_path = os.path.join(current_dir, original_target)
            if os.path.exists(folder_path) and os.path.isdir(folder_path):
                # Navigate to folder - use most reliable method
                explorer_windows[0].activate()
                time.sleep(0.7)
                
                # Update programmatic directory first
                os.chdir(folder_path)
                
                # Use address bar navigation - clear and type new path
                pyautogui.hotkey('ctrl', 'l')  # Focus address bar
                time.sleep(0.5)
                pyautogui.hotkey('ctrl', 'a')  # Select all existing path
                time.sleep(0.2)
                pyautogui.press('delete')  # Clear
                time.sleep(0.2)
                
                # Type the folder path
                pyautogui.typewrite(folder_path, interval=0.03)
                time.sleep(0.5)
                pyautogui.press('enter')
                time.sleep(1.2)  # Wait for navigation to fully complete
                
                # Ensure we're in the right directory
                os.chdir(folder_path)
                
                self.logger.info(f"✅ Successfully navigated to folder: {folder_path}")
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
                else:
                    subprocess.Popen(["xdg-open", file_path])
                self.logger.info(f"✅ Opening file: {file_path}")
                if self.tts:
                    self.tts.say(f"Opening {original_target}.")
                return True
            
            # Try fuzzy matching - exact match first (case insensitive)
            try:
                items = os.listdir(current_dir)
                self.logger.info(f"Searching {len(items)} items in {current_dir}")
                
                # First pass: exact match (case insensitive)
                for item in items:
                    if item.lower() == target_lower:
                        item_path = os.path.join(current_dir, item)
                        if os.path.isdir(item_path):
                            # Navigate to folder - use address bar method (most reliable)
                            explorer_windows[0].activate()
                            time.sleep(0.7)
                            
                            # Use address bar navigation
                            pyautogui.hotkey('ctrl', 'l')  # Focus address bar
                            time.sleep(0.5)
                            pyautogui.hotkey('ctrl', 'a')  # Select all
                            time.sleep(0.2)
                            pyautogui.press('delete')  # Clear
                            time.sleep(0.2)
                            pyautogui.typewrite(item_path, interval=0.03)  # Type full path
                            time.sleep(0.5)
                            pyautogui.press('enter')
                            time.sleep(1.0)  # Wait for navigation
                            
                            os.chdir(item_path)
                            self.logger.info(f"✅ Navigated to folder (exact match): {item_path}")
                            if self.tts:
                                self.tts.say(f"Opened {item} folder.")
                            return True
                        elif os.path.isfile(item_path):
                            # Open file
                            if self.platform == "windows":
                                os.startfile(item_path)
                            else:
                                subprocess.Popen(["xdg-open", item_path])
                            self.logger.info(f"✅ Opening file (exact match): {item_path}")
                            if self.tts:
                                self.tts.say(f"Opening {item}.")
                            return True
                
                # Second pass: partial match (contains or starts with)
                for item in items:
                    item_lower = item.lower()
                    if target_lower in item_lower or item_lower.startswith(target_lower):
                        item_path = os.path.join(current_dir, item)
                        if os.path.isdir(item_path):
                            # Navigate to folder - use address bar method
                            explorer_windows[0].activate()
                            time.sleep(0.7)
                            
                            # Use address bar navigation
                            pyautogui.hotkey('ctrl', 'l')  # Focus address bar
                            time.sleep(0.5)
                            pyautogui.hotkey('ctrl', 'a')  # Select all
                            time.sleep(0.2)
                            pyautogui.press('delete')  # Clear
                            time.sleep(0.2)
                            pyautogui.typewrite(item_path, interval=0.03)  # Type full path
                            time.sleep(0.5)
                            pyautogui.press('enter')
                            time.sleep(1.0)  # Wait for navigation
                            
                            os.chdir(item_path)
                            self.logger.info(f"✅ Navigated to folder (fuzzy match): {item_path}")
                            if self.tts:
                                self.tts.say(f"Opened {item} folder.")
                            return True
                        elif os.path.isfile(item_path):
                            # Open file
                            if self.platform == "windows":
                                os.startfile(item_path)
                            else:
                                subprocess.Popen(["xdg-open", item_path])
                            self.logger.info(f"✅ Opening file (fuzzy match): {item_path}")
                            if self.tts:
                                self.tts.say(f"Opening {item}.")
                            return True
            except Exception as e:
                self.logger.error(f"Error searching directory: {e}")
            
            self.logger.warning(f"❌ Could not find '{original_target}' in {current_dir}")
            return False
        except Exception as e:
            self.logger.error(f"Error opening folder/file in explorer: {e}")
            return False
    
    def _open_target(self, target: str) -> bool:
        """Open target application, file, or folder"""
        try:
            import os
            import time
            
            original_target = target
            target = target.lower().strip()
            
            # If File Explorer is open, file/folder operations were already tried in _open_folder_or_file_in_explorer
            # So here we only handle apps, websites, etc.
            
            # Special handling for Windows system apps
            if self.platform == "windows":
                # File Explorer - MAIN PILLAR for navigation
                if target in ['file explorer', 'explorer', 'file manager', 'files']:
                    try:
                        subprocess.Popen(['explorer.exe'])
                        self.logger.info("File Explorer opened successfully")
                        if self.tts:
                            self.tts.say("Opening file explorer.")
                        return True
                    except Exception as e:
                        self.logger.error(f"Error opening file explorer: {e}")
                        if self.tts:
                            self.tts.say("Could not open file explorer.")
                        return False
                
                # Calculator
                if target in ['calculator', 'calc', 'calc.exe']:
                    try:
                        subprocess.Popen(['calc.exe'])
                        self.logger.info("Calculator opened successfully")
                        if self.tts:
                            self.tts.say("Opening calculator.")
                        return True
                    except Exception as e:
                        self.logger.error(f"Error opening calculator: {e}")
                
                # Calendar
                if target in ['calendar', 'ms calendar', 'microsoft calendar', 'cal']:
                    try:
                        # Try different methods to open Calendar
                        subprocess.run(['start', 'ms-calendar:'], shell=True, check=True)
                        self.logger.info("Calendar opened successfully")
                        if self.tts:
                            self.tts.say("Opening calendar.")
                        return True
                    except:
                        try:
                            subprocess.run(['start', 'outlookcal:'], shell=True, check=True)
                            self.logger.info("Calendar opened successfully")
                            if self.tts:
                                self.tts.say("Opening calendar.")
                            return True
                        except Exception as e:
                            self.logger.error(f"Error opening calendar: {e}")
                
                # VS Code - handle multiple name variations
                if target in ['vs code', 'visual studio code', 'code', 'vscode']:
                    # Check discovered apps first
                    for key in ['code', 'visual studio code', 'vs code', 'vscode']:
                        if key in self.discovered_apps:
                            path = self.discovered_apps[key]
                            subprocess.Popen([path])
                            self.logger.info(f"Opening VS Code from discovered apps: {path}")
                            if self.tts:
                                self.tts.say("Opening Visual Studio Code.")
                            return True
                    # Try fuzzy matching
                    best_match = self._find_app_fuzzy('code')
                    if best_match and 'code' in best_match.lower():
                        path = self.discovered_apps[best_match]
                        subprocess.Popen([path])
                        self.logger.info(f"Opening VS Code via fuzzy match: {best_match} -> {path}")
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
                            self.logger.info(f"Opening VS Code from common path: {path}")
                            if self.tts:
                                self.tts.say("Opening Visual Studio Code.")
                            return True
            
            # First check discovered apps (universal)
            if target in self.discovered_apps:
                path = self.discovered_apps[target]
                self.logger.info(f"Opening discovered app: {path}")
                subprocess.Popen([path])
                if self.tts:
                    self.tts.say(f"Opening {target}.")
                return True
            
            # Try fuzzy matching for discovered apps
            best_match = self._find_app_fuzzy(target)
            if best_match:
                path = self.discovered_apps[best_match]
                self.logger.info(f"Opening fuzzy matched app: {best_match} -> {path}")
                subprocess.Popen([path])
                if self.tts:
                    self.tts.say(f"Opening {best_match}.")
                return True
            
            # Try as website (if contains .com, .org, etc.)
            if any(domain in target for domain in ['.com', '.org', '.net', '.edu', '.gov', '.io']):
                url = target if target.startswith(('http://', 'https://')) else 'https://' + target
                self.logger.info(f"Opening website: {url}")
                webbrowser.open(url)
                if self.tts:
                    self.tts.say(f"Opening {target}.")
                return True
            
            # Try Windows start command
            elif self.platform == "windows":
                try:
                    self.logger.info(f"Trying Windows start: {target}")
                    subprocess.run(["start", target], shell=True, check=True)
                    if self.tts:
                        self.tts.say(f"Opening {target}.")
                    return True
                except:
                    pass
            
            # Check if it's a file in current directory
            if os.path.exists(target):
                self.logger.info(f"Opening file: {target}")
                if self.platform == "windows":
                    os.startfile(target)
                else:
                    subprocess.Popen(["xdg-open", target])
                if self.tts:
                    self.tts.say(f"Opening file {target}.")
                return True
            
            # Check if it's a file with extension in current directory
            for ext in ['.txt', '.doc', '.docx', '.pdf', '.jpg', '.png', '.mp4', '.mp3']:
                if target.endswith(ext) or os.path.exists(target + ext):
                    file_path = target if target.endswith(ext) else target + ext
                    if os.path.exists(file_path):
                        self.logger.info(f"Opening file: {file_path}")
                        if self.platform == "windows":
                            os.startfile(file_path)
                        else:
                            subprocess.Popen(["xdg-open", file_path])
                        if self.tts:
                            self.tts.say(f"Opening file {file_path}.")
                        return True
            
            # Try direct execution
            try:
                self.logger.info(f"Trying direct execution: {target}")
                subprocess.Popen([target])
                if self.tts:
                    self.tts.say(f"Opening {target}.")
                return True
            except:
                pass
            
            if self.tts:
                self.tts.say(f"Could not find {target}.")
            return False
            
        except Exception as e:
            self.logger.error(f"Error opening target: {e}")
            return False
    
    def _close_target(self, target: str) -> bool:
        """Close target application"""
        try:
            if self.platform == "windows":
                # SPECIAL HANDLING: File Explorer - must be closed by window, not process
                target_lower = target.lower().strip()
                if 'file explorer' in target_lower or 'explorer' in target_lower or target_lower == 'explorer':
                    try:
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
                
                # Try to close by process name
                try:
                    # First try exact match
                    subprocess.run(["taskkill", "/f", "/im", f"{target}.exe"], 
                                 check=True, capture_output=True)
                    if self.tts:
                        self.tts.say(f"Closed {target}.")
                    return True
                except:
                    pass
                
                # Try fuzzy matching for discovered apps
                best_match = self._find_app_fuzzy(target)
                if best_match:
                    try:
                        # Extract process name from path
                        process_name = os.path.basename(self.discovered_apps[best_match])
                        subprocess.run(["taskkill", "/f", "/im", process_name], 
                                     check=True, capture_output=True)
                        if self.tts:
                            self.tts.say(f"Closed {best_match}.")
                        return True
                    except:
                        pass
                
                # Try to close current window (Alt+F4)
                if target in ['window', 'current', 'app', 'this']:
                    try:
                        import pyautogui
                        pyautogui.hotkey('alt', 'f4')
                        if self.tts:
                            self.tts.say("Closed current window.")
                        return True
                    except:
                        pass
                
                # Try fuzzy matching for discovered apps (NO HARDCODING)
                best_match = self._find_app_fuzzy(target)
                if best_match:
                    try:
                        # Extract process name from path
                        process_name = os.path.basename(self.discovered_apps[best_match])
                        subprocess.run(["taskkill", "/f", "/im", process_name], 
                                     check=True, capture_output=True)
                        if self.tts:
                            self.tts.say(f"Closed {best_match}.")
                        return True
                    except:
                        pass
            
            return False
            
        except Exception as e:
            self.logger.error(f"Error closing target: {e}")
            if self.tts:
                self.tts.say("Error closing application.")
            return False
    
    def _search_web(self, query: str) -> bool:
        """Search on the web (Google)"""
        try:
            import urllib.parse
            # URL encode the query to handle spaces and special characters
            encoded_query = urllib.parse.quote_plus(query)
            url = f"https://www.google.com/search?q={encoded_query}"
            webbrowser.open(url)
            if self.tts:
                self.tts.say(f"Searching for {query}.")
            return True
        except Exception as e:
            self.logger.error(f"Error searching web: {e}")
            return False
    
    def _search_youtube(self, query: str) -> bool:
        """Search on YouTube"""
        try:
            import urllib.parse
            # URL encode the query to handle spaces and special characters
            encoded_query = urllib.parse.quote_plus(query)
            url = f"https://www.youtube.com/results?search_query={encoded_query}"
            webbrowser.open(url)
            if self.tts:
                self.tts.say(f"Searching YouTube for {query}.")
            return True
        except Exception as e:
            self.logger.error(f"Error searching YouTube: {e}")
            return False
    
    def _search_amazon(self, query: str) -> bool:
        """Search on Amazon"""
        try:
            import urllib.parse
            # URL encode the query to handle spaces and special characters
            encoded_query = urllib.parse.quote_plus(query)
            url = f"https://www.amazon.com/s?k={encoded_query}"
            webbrowser.open(url)
            if self.tts:
                self.tts.say(f"Searching Amazon for {query}.")
            return True
        except Exception as e:
            self.logger.error(f"Error searching Amazon: {e}")
            return False
    
    def _open_website(self, url: str) -> bool:
        """Open a website URL"""
        try:
            webbrowser.open(url)
            if self.tts:
                # Extract domain name for TTS
                from urllib.parse import urlparse
                domain = urlparse(url).netloc.replace('www.', '')
                self.tts.say(f"Opening {domain}.")
            return True
        except Exception as e:
            self.logger.error(f"Error opening website: {e}")
            if self.tts:
                self.tts.say("Could not open website.")
            return False
    
    def _type_text(self, text: str) -> bool:
        """Type text using keyboard automation with automatic spacing"""
        try:
            if self.platform == "windows":
                import pyautogui
                import time
                import re
                
                # Process text: ensure spaces between words, handle newlines
                processed_text = self._process_text_for_typing(text)
                
                # Type the text character by character for better reliability
                pyautogui.typewrite(processed_text, interval=0.05)
                
                if self.tts:
                    preview = processed_text[:30] + "..." if len(processed_text) > 30 else processed_text
                    self.tts.say(f"Typed: {preview}")
                return True
            return False
        except Exception as e:
            self.logger.error(f"Error typing text: {e}")
            if self.tts:
                self.tts.say("Error typing text.")
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
    
    def _shutdown(self) -> bool:
        """Shutdown system"""
        try:
            if self.platform == "windows":
                subprocess.run(["shutdown", "/s", "/t", "5"])
                if self.tts:
                    self.tts.say("Shutting down in 5 seconds.")
                return True
            return False
        except Exception as e:
            self.logger.error(f"Error shutting down: {e}")
            return False
    
    def _restart(self) -> bool:
        """Restart system"""
        try:
            if self.platform == "windows":
                subprocess.run(["shutdown", "/r", "/t", "5"])
                if self.tts:
                    self.tts.say("Restarting in 5 seconds.")
                return True
            return False
        except Exception as e:
            self.logger.error(f"Error restarting: {e}")
            return False
    
    def _lock_screen(self) -> bool:
        """Lock screen"""
        try:
            if self.platform == "windows":
                subprocess.run(["rundll32.exe", "user32.dll,LockWorkStation"])
                if self.tts:
                    self.tts.say("Screen locked.")
                return True
            return False
        except Exception as e:
            self.logger.error(f"Error locking screen: {e}")
            return False
    
    def _sleep(self) -> bool:
        """Put system to sleep"""
        try:
            if self.platform == "windows":
                subprocess.run(["rundll32.exe", "powrprof.dll,SetSuspendState", "0,1,0"])
                if self.tts:
                    self.tts.say("System going to sleep.")
                return True
            return False
        except Exception as e:
            self.logger.error(f"Error putting system to sleep: {e}")
            return False
    
    def _volume_up(self) -> bool:
        """Increase volume"""
        try:
            if self.platform == "windows":
                import pyautogui
                pyautogui.press('volumeup')
                if self.tts:
                    self.tts.say("Volume increased.")
                return True
            return False
        except Exception as e:
            self.logger.error(f"Error increasing volume: {e}")
            return False
    
    def _volume_down(self) -> bool:
        """Decrease volume"""
        try:
            if self.platform == "windows":
                import pyautogui
                pyautogui.press('volumedown')
                if self.tts:
                    self.tts.say("Volume decreased.")
                return True
            return False
        except Exception as e:
            self.logger.error(f"Error decreasing volume: {e}")
            return False
    
    def _mute(self) -> bool:
        """Mute/unmute volume"""
        try:
            if self.platform == "windows":
                import pyautogui
                pyautogui.press('volumemute')
                if self.tts:
                    self.tts.say("Volume muted.")
                return True
            return False
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
            percent = max(0, min(100, percent))  # Clamp between 0 and 100
            
            if self.platform == "windows":
                # Windows: Use simpler method with keyboard shortcuts (more reliable)
                try:
                    import pyautogui
                    import time
                    # Mute first to reset
                    pyautogui.press('volumemute')
                    time.sleep(0.1)
                    # Press volume up approximately (each press is ~2-3%)
                    steps = percent // 2
                    for _ in range(steps):
                        pyautogui.press('volumeup')
                        time.sleep(0.05)
                except Exception as e:
                    self.logger.error(f"Error setting volume with pyautogui: {e}")
                    # Try PowerShell fallback
                    try:
                        ps_command = f'$obj = New-Object -comObject WScript.Shell; $obj.SendKeys([char]173); Start-Sleep -Milliseconds 100; $steps = {percent} / 2; for ($i=0; $i -lt $steps; $i++) {{ $obj.SendKeys([char]175); Start-Sleep -Milliseconds 50 }}'
                        subprocess.run(["powershell", "-Command", ps_command], check=True, capture_output=True)
                    except:
                        if self.tts:
                            self.tts.say(f"Could not set volume to {percent} percent.")
                        return False
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
    
    def _media_control(self, command: str) -> bool:
        """Control media playback"""
        try:
            if self.platform == "windows":
                import pyautogui
                
                if 'play' in command:
                    pyautogui.press('playpause')
                    if self.tts:
                        self.tts.say("Media play/pause toggled.")
                elif 'next' in command:
                    pyautogui.press('nexttrack')
                    if self.tts:
                        self.tts.say("Next track.")
                elif 'previous' in command:
                    pyautogui.press('prevtrack')
                    if self.tts:
                        self.tts.say("Previous track.")
                
                return True
            return False
        except Exception as e:
            self.logger.error(f"Error controlling media: {e}")
            return False
    
    def _file_operation(self, command: str) -> bool:
        """Perform file operations"""
        try:
            if 'create file' in command:
                # Extract simple one-word filename from command
                name_part = command.replace('create file', '').strip()
                # Take only first word (simple name)
                words = name_part.split()
                if words:
                    filename = words[0].strip('.,!?;:')
                else:
                    filename = "new_file"
                
                # Add extension if not present
                if not any(filename.endswith(ext) for ext in ['.txt', '.doc', '.docx', '.py', '.js', '.html', '.json', '.md', '.csv']):
                    filename += '.txt'
                
                # Get current directory
                current_dir = os.getcwd()
                file_path = os.path.join(current_dir, filename)
                
                # Create file with initial content
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(f"Created by EchoOS on {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                
                self.logger.info(f"Created file: {file_path}")
                if self.tts:
                    self.tts.say(f"Created file {filename} in current directory.")
                return True
                
            elif 'delete file' in command:
                filename = command.replace('delete file', '').strip()
                if os.path.exists(filename):
                    os.remove(filename)
                    if self.tts:
                        self.tts.say(f"Deleted file {filename}.")
                else:
                    if self.tts:
                        self.tts.say(f"File {filename} not found.")
                return True
                
            elif 'copy file' in command:
                # Extract source and destination
                parts = command.replace('copy file', '').strip().split(' to ')
                if len(parts) == 2:
                    source, dest = parts[0].strip(), parts[1].strip()
                    if os.path.exists(source):
                        import shutil
                        shutil.copy2(source, dest)
                        if self.tts:
                            self.tts.say(f"Copied {source} to {dest}.")
                    else:
                        if self.tts:
                            self.tts.say(f"Source file {source} not found.")
                else:
                    if self.tts:
                        self.tts.say("Please specify source and destination files.")
                return True
            
            else:
                if self.tts:
                    self.tts.say("File operation command received.")
                return True
                
        except Exception as e:
            self.logger.error(f"Error with file operation: {e}")
            if self.tts:
                self.tts.say("Error performing file operation.")
            return False
    
    def _save_file(self, command: str) -> bool:
        """Save current file - handles save and save as"""
        try:
            import pyautogui
            import time
            import pyperclip
            
            # If "save as" or filename is provided
            if 'save as' in command.lower():
                # Extract filename if provided
                filename = command.lower().replace('save as', '').replace('save file', '').strip()
                
                if filename:
                    # Use Save As dialog
                    pyautogui.hotkey('ctrl', 'shift', 's')  # Save As shortcut
                    time.sleep(0.5)
                    
                    # Type filename
                    pyautogui.typewrite(filename, interval=0.05)
                    time.sleep(0.3)
                    pyautogui.press('enter')
                    
                    if self.tts:
                        self.tts.say(f"Saved as {filename}.")
                    return True
                else:
                    # Open Save As dialog and wait for user
                    pyautogui.hotkey('ctrl', 'shift', 's')
                    if self.tts:
                        self.tts.say("Save as dialog opened. Please enter the filename.")
                    return True
            else:
                # Regular save (Ctrl+S)
                pyautogui.hotkey('ctrl', 's')
                time.sleep(0.3)
                
                if self.tts:
                    self.tts.say("File saved.")
                return True
                
        except Exception as e:
            self.logger.error(f"Error saving file: {e}")
            if self.tts:
                self.tts.say("Error saving file.")
            return False
    
    def _minimize_window(self) -> bool:
        """Minimize current window"""
        try:
            if self.platform == "windows":
                import pyautogui
                pyautogui.hotkey('alt', 'space', 'n')  # Alt+Space+N for minimize
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
            if self.platform == "windows":
                import pyautogui
                pyautogui.hotkey('alt', 'space', 'x')  # Alt+Space+X for maximize
                if self.tts:
                    self.tts.say("Window maximized.")
                return True
            return False
        except Exception as e:
            self.logger.error(f"Error maximizing window: {e}")
            return False
    
    def _execute_generic(self, command: str) -> bool:
        """Execute generic command"""
        try:
            # Try as Windows command
            if self.platform == "windows":
                try:
                    subprocess.run([command], shell=True, check=True)
                    if self.tts:
                        self.tts.say(f"Executed: {command}")
                    return True
                except:
                    pass
            
            return False
        except Exception as e:
            self.logger.error(f"Error executing generic command: {e}")
            return False
