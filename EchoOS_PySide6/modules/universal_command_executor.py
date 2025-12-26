"""
Universal Command Executor for EchoOS
Can execute ANY command by understanding screen context and user intent
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
from typing import Optional, Dict, List, Any, Tuple
from pathlib import Path

# Platform-specific imports
try:
    import pyautogui
    pyautogui.FAILSAFE = False
    pyautogui.PAUSE = 0.1
    PYAUTOGUI_AVAILABLE = True
except ImportError:
    PYAUTOGUI_AVAILABLE = False

try:
    import cv2
    import numpy as np
    from PIL import Image, ImageGrab
    IMAGE_PROCESSING_AVAILABLE = True
except ImportError:
    IMAGE_PROCESSING_AVAILABLE = False

try:
    import pytesseract
    OCR_AVAILABLE = True
except ImportError:
    OCR_AVAILABLE = False

try:
    import pygetwindow as gw
    WINDOW_MANAGEMENT_AVAILABLE = True
except ImportError:
    WINDOW_MANAGEMENT_AVAILABLE = False

class UniversalCommandExecutor:
    """Universal command executor that can handle ANY voice command"""
    
    def __init__(self, tts=None, auth=None):
        self.tts = tts
        self.auth = auth
        self.logger = logging.getLogger(__name__)
        self.platform = platform.system().lower()
        
        # Command patterns with fuzzy matching
        self.command_patterns = self._build_command_patterns()
        
        # Screen analysis cache
        self.last_screen_analysis = None
        self.screen_analysis_timeout = 2.0  # seconds
        
        # Current context
        self.current_context = None
        
    def _build_command_patterns(self) -> Dict[str, Dict]:
        """Build comprehensive command patterns for universal recognition"""
        return {
            # File Operations
            'file_operations': {
                'open': ['open', 'launch', 'start', 'run', 'execute', 'double click'],
                'create': ['create', 'make', 'new', 'add'],
                'delete': ['delete', 'remove', 'trash', 'erase', 'destroy'],
                'copy': ['copy', 'duplicate', 'clone'],
                'move': ['move', 'cut', 'transfer'],
                'paste': ['paste', 'insert', 'place'],
                'rename': ['rename', 'change name', 'rechristen'],
                'navigate': ['go to', 'navigate', 'enter', 'open folder', 'cd'],
                'list': ['list', 'show', 'display', 'view', 'ls', 'dir']
            },
            
            # Application Control
            'app_control': {
                'launch': ['open', 'launch', 'start', 'run', 'execute'],
                'close': ['close', 'quit', 'exit', 'terminate', 'kill'],
                'minimize': ['minimize', 'minimize window', 'hide window'],
                'maximize': ['maximize', 'maximize window', 'full screen'],
                'restore': ['restore', 'unminimize', 'show window'],
                'switch': ['switch to', 'go to', 'bring to front', 'activate'],
                'new_tab': ['new tab', 'open tab', 'create tab'],
                'close_tab': ['close tab', 'close current tab'],
                'next_tab': ['next tab', 'switch tab', 'tab right'],
                'prev_tab': ['previous tab', 'tab left', 'back tab']
            },
            
            # System Control
            'system_control': {
                'shutdown': ['shutdown', 'shut down', 'power off', 'turn off'],
                'restart': ['restart', 'reboot', 'reset'],
                'sleep': ['sleep', 'hibernate', 'suspend'],
                'lock': ['lock', 'lock screen', 'lock computer'],
                'logout': ['logout', 'log out', 'sign out'],
                'volume_up': ['volume up', 'increase volume', 'louder'],
                'volume_down': ['volume down', 'decrease volume', 'quieter'],
                'mute': ['mute', 'silence', 'unmute', 'unmute volume'],
                'brightness_up': ['brightness up', 'increase brightness', 'brighter'],
                'brightness_down': ['brightness down', 'decrease brightness', 'dimmer']
            },
            
            # Web Operations
            'web_operations': {
                'search': ['search', 'find', 'look for', 'google', 'bing'],
                'navigate': ['go to', 'visit', 'open website', 'navigate to'],
                'back': ['go back', 'back', 'previous page'],
                'forward': ['go forward', 'forward', 'next page'],
                'refresh': ['refresh', 'reload', 'refresh page'],
                'bookmark': ['bookmark', 'save', 'favorite', 'add bookmark'],
                'download': ['download', 'save file', 'save as']
            },
            
            # Media Control
            'media_control': {
                'play': ['play', 'start', 'begin', 'resume'],
                'pause': ['pause', 'stop', 'halt'],
                'next': ['next', 'skip', 'next track', 'next song'],
                'previous': ['previous', 'back', 'previous track', 'previous song'],
                'volume_up': ['volume up', 'louder', 'increase volume'],
                'volume_down': ['volume down', 'quieter', 'decrease volume'],
                'mute': ['mute', 'silence', 'unmute'],
                'seek': ['seek', 'jump to', 'go to', 'skip to'],
                'fullscreen': ['fullscreen', 'full screen', 'maximize video']
            },
            
            # Text Operations
            'text_operations': {
                'type': ['type', 'write', 'enter', 'input', 'say'],
                'select_all': ['select all', 'select everything', 'highlight all'],
                'copy': ['copy', 'copy text', 'copy selected'],
                'cut': ['cut', 'cut text', 'move text'],
                'paste': ['paste', 'paste text', 'insert text'],
                'find': ['find', 'search', 'look for text'],
                'replace': ['replace', 'find and replace', 'substitute'],
                'undo': ['undo', 'reverse', 'go back'],
                'redo': ['redo', 'repeat', 'forward']
            },
            
            # Navigation
            'navigation': {
                'click': ['click', 'tap', 'press', 'select'],
                'double_click': ['double click', 'double tap', 'open'],
                'right_click': ['right click', 'context menu', 'menu'],
                'scroll_up': ['scroll up', 'scroll', 'page up'],
                'scroll_down': ['scroll down', 'page down'],
                'zoom_in': ['zoom in', 'magnify', 'enlarge'],
                'zoom_out': ['zoom out', 'reduce', 'shrink'],
                'drag': ['drag', 'move', 'pull', 'slide']
            },
            
            # Command Line
            'command_line': {
                'cmd': ['command prompt', 'cmd', 'terminal', 'powershell'],
                'execute': ['execute', 'run command', 'run', 'do'],
                'type_command': ['type', 'enter command', 'input command']
            }
        }
    
    def execute_command(self, voice_text: str) -> bool:
        """Execute any voice command by understanding intent and context"""
        try:
            # Normalize input
            text = voice_text.lower().strip()
            self.logger.info(f"Processing universal command: '{text}'")
            
            # Analyze current screen context
            context = self._analyze_current_context()
            
            # Determine command intent
            intent = self._determine_intent(text, context)
            
            if not intent:
                self._handle_unknown_command(text)
                return False
            
            # Execute based on intent
            return self._execute_intent(intent, text, context)
            
        except Exception as e:
            self.logger.error(f"Error executing command: {e}")
            if self.tts:
                self.tts.say("Sorry, I encountered an error processing that command.")
            return False
    
    def _analyze_current_context(self) -> Dict[str, Any]:
        """Analyze current screen and application context"""
        try:
            # Check if we need fresh analysis
            current_time = time.time()
            if (self.last_screen_analysis and 
                current_time - self.last_screen_analysis.get('timestamp', 0) < self.screen_analysis_timeout):
                return self.last_screen_analysis
            
            context = {
                'timestamp': current_time,
                'active_window': self._get_active_window_info(),
                'screen_text': self._extract_screen_text(),
                'ui_elements': self._detect_ui_elements(),
                'current_app': None,
                'available_actions': []
            }
            
            # Determine current application
            if context['active_window']:
                context['current_app'] = self._identify_application(context['active_window'])
                context['available_actions'] = self._get_available_actions(context['current_app'])
            
            self.last_screen_analysis = context
            return context
            
        except Exception as e:
            self.logger.error(f"Error analyzing context: {e}")
            return {'timestamp': time.time(), 'active_window': None, 'screen_text': '', 'ui_elements': [], 'current_app': None, 'available_actions': []}
    
    def _get_active_window_info(self) -> Optional[Dict]:
        """Get information about currently active window"""
        try:
            if WINDOW_MANAGEMENT_AVAILABLE:
                active_windows = gw.getActiveWindow()
                if active_windows:
                    return {
                        'title': active_windows.title,
                        'app_name': self._extract_app_name(active_windows.title),
                        'rect': (active_windows.left, active_windows.top, active_windows.width, active_windows.height)
                    }
            return None
        except Exception as e:
            self.logger.error(f"Error getting window info: {e}")
            return None
    
    def _extract_app_name(self, window_title: str) -> str:
        """Extract application name from window title"""
        # Common patterns for extracting app names
        if ' - ' in window_title:
            return window_title.split(' - ')[-1].strip()
        elif ' | ' in window_title:
            return window_title.split(' | ')[-1].strip()
        else:
            return window_title.strip()
    
    def _extract_screen_text(self) -> str:
        """Extract text from current screen using OCR"""
        try:
            if not OCR_AVAILABLE or not IMAGE_PROCESSING_AVAILABLE:
                return ""
            
            # Capture screen
            screenshot = ImageGrab.grab()
            
            # Extract text using OCR
            text = pytesseract.image_to_string(screenshot)
            return text.strip()
            
        except Exception as e:
            # Don't log OCR errors as they're expected if Tesseract isn't installed
            return ""
    
    def _detect_ui_elements(self) -> List[Dict]:
        """Detect UI elements on screen"""
        try:
            if not IMAGE_PROCESSING_AVAILABLE:
                return []
            
            # Capture screen
            screenshot = ImageGrab.grab()
            cv_image = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)
            
            # Detect buttons, text areas, etc.
            elements = []
            
            # Simple button detection
            gray = cv2.cvtColor(cv_image, cv2.COLOR_BGR2GRAY)
            edges = cv2.Canny(gray, 50, 150)
            contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            for contour in contours:
                x, y, w, h = cv2.boundingRect(contour)
                if 50 <= w <= 300 and 20 <= h <= 100:  # Button-like size
                    elements.append({
                        'type': 'button',
                        'rect': (x, y, w, h),
                        'center': (x + w//2, y + h//2)
                    })
            
            return elements
            
        except Exception as e:
            self.logger.error(f"Error detecting UI elements: {e}")
            return []
    
    def _identify_application(self, window_info: Dict) -> str:
        """Identify current application type"""
        if not window_info:
            return 'unknown'
        
        app_name = window_info.get('app_name', '').lower()
        title = window_info.get('title', '').lower()
        
        # File Explorer
        if any(keyword in app_name for keyword in ['explorer', 'finder', 'files']):
            return 'file_explorer'
        
        # Browser
        if any(keyword in app_name for keyword in ['chrome', 'firefox', 'edge', 'safari', 'browser']):
            return 'browser'
        
        # Text Editor
        if any(keyword in app_name for keyword in ['notepad', 'code', 'sublime', 'atom', 'vim', 'word']):
            return 'text_editor'
        
        # Media Player
        if any(keyword in app_name for keyword in ['vlc', 'media player', 'quicktime', 'windows media']):
            return 'media_player'
        
        # Terminal/Command Prompt
        if any(keyword in app_name for keyword in ['cmd', 'powershell', 'terminal', 'bash']):
            return 'terminal'
        
        return 'generic'
    
    def _get_available_actions(self, app_type: str) -> List[str]:
        """Get available actions for current application"""
        action_map = {
            'file_explorer': ['navigate', 'create', 'delete', 'copy', 'move', 'rename', 'open'],
            'browser': ['navigate', 'search', 'new_tab', 'close_tab', 'bookmark', 'download'],
            'text_editor': ['type', 'save', 'open', 'find', 'replace', 'copy', 'paste'],
            'media_player': ['play', 'pause', 'next', 'previous', 'volume', 'seek', 'fullscreen'],
            'terminal': ['execute', 'type_command', 'clear'],
            'generic': ['click', 'type', 'scroll', 'close', 'minimize', 'maximize']
        }
        
        return action_map.get(app_type, action_map['generic'])
    
    def _determine_intent(self, text: str, context: Dict) -> Optional[Dict]:
        """Determine user intent from voice text and context"""
        try:
            # Check for exact matches first
            intent = self._check_exact_matches(text)
            if intent:
                return intent
            
            # Check for fuzzy matches
            intent = self._check_fuzzy_matches(text, context)
            if intent:
                return intent
            
            # Check for context-aware matches
            intent = self._check_context_aware_matches(text, context)
            if intent:
                return intent
            
            # Check for natural language patterns
            intent = self._check_natural_language(text, context)
            if intent:
                return intent
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error determining intent: {e}")
            return None
    
    def _check_exact_matches(self, text: str) -> Optional[Dict]:
        """Check for exact command matches"""
        # Direct system commands
        if text in ['lock', 'lock screen']:
            return {'action': 'lock_screen', 'confidence': 1.0}
        elif text in ['shutdown', 'shut down']:
            return {'action': 'shutdown', 'confidence': 1.0}
        elif text in ['restart', 'reboot']:
            return {'action': 'restart', 'confidence': 1.0}
        elif text in ['sleep', 'hibernate']:
            return {'action': 'sleep', 'confidence': 1.0}
        elif text in ['volume up']:
            return {'action': 'volume_up', 'confidence': 1.0}
        elif text in ['volume down']:
            return {'action': 'volume_down', 'confidence': 1.0}
        elif text in ['mute']:
            return {'action': 'mute', 'confidence': 1.0}
        
        return None
    
    def _check_fuzzy_matches(self, text: str, context: Dict) -> Optional[Dict]:
        """Check for fuzzy command matches"""
        # Check each command category
        for category, patterns in self.command_patterns.items():
            for action, keywords in patterns.items():
                for keyword in keywords:
                    if keyword in text:
                        # Extract target if applicable
                        target = self._extract_target(text, keyword)
                        return {
                            'action': action,
                            'target': target,
                            'category': category,
                            'confidence': 0.8
                        }
        
        return None
    
    def _check_context_aware_matches(self, text: str, context: Dict) -> Optional[Dict]:
        """Check for context-aware command matches"""
        current_app = context.get('current_app', 'unknown')
        screen_text = context.get('screen_text', '').lower()
        
        # File operations in file explorer
        if current_app == 'file_explorer':
            if any(word in text for word in ['open', 'double click']):
                # Find file/folder to open from screen text
                target = self._find_matching_file(text, screen_text)
                if target:
                    return {
                        'action': 'open_file',
                        'target': target,
                        'confidence': 0.9
                    }
        
        # Browser operations
        elif current_app == 'browser':
            if 'search' in text:
                query = self._extract_search_query(text)
                return {
                    'action': 'search_web',
                    'query': query,
                    'confidence': 0.9
                }
        
        # Media player operations
        elif current_app == 'media_player':
            if any(word in text for word in ['play', 'pause', 'stop']):
                action = 'play' if 'play' in text else 'pause' if 'pause' in text else 'stop'
                return {
                    'action': action,
                    'confidence': 0.9
                }
        
        return None
    
    def _check_natural_language(self, text: str, context: Dict) -> Optional[Dict]:
        """Check for natural language patterns"""
        # "Open [something]" patterns
        if text.startswith('open '):
            target = text[5:].strip()
            return {
                'action': 'open_generic',
                'target': target,
                'confidence': 0.7
            }
        
        # "Close [something]" patterns
        if text.startswith('close '):
            target = text[6:].strip()
            return {
                'action': 'close_generic',
                'target': target,
                'confidence': 0.7
            }
        
        # "Type [something]" patterns
        if text.startswith('type ') or text.startswith('write ') or text.startswith('enter '):
            text_to_type = text.split(' ', 1)[1] if ' ' in text else ''
            return {
                'action': 'type_text',
                'text': text_to_type,
                'confidence': 0.8
            }
        
        # "Search for [something]" patterns
        if 'search' in text and 'for' in text:
            query = text.split('for', 1)[1].strip() if 'for' in text else ''
            return {
                'action': 'search_web',
                'query': query,
                'confidence': 0.8
            }
        
        # "Click on [something]" patterns
        if 'click' in text and ('on' in text or 'at' in text):
            target = text.split('on', 1)[1].strip() if 'on' in text else text.split('at', 1)[1].strip()
            return {
                'action': 'click_element',
                'target': target,
                'confidence': 0.8
            }
        
        return None
    
    def _extract_target(self, text: str, keyword: str) -> str:
        """Extract target from command text"""
        # Remove the keyword and clean up
        target = text.replace(keyword, '').strip()
        # Remove common words
        target = re.sub(r'\b(the|a|an|this|that)\b', '', target).strip()
        return target
    
    def _find_matching_file(self, text: str, screen_text: str) -> Optional[str]:
        """Find matching file/folder from screen text"""
        # Extract what user wants to open
        if 'open' in text:
            target = text.split('open', 1)[1].strip()
        else:
            target = text.strip()
        
        # Look for matching files in screen text
        lines = screen_text.split('\n')
        for line in lines:
            if target.lower() in line.lower():
                # Extract filename from line
                words = line.split()
                for word in words:
                    if target.lower() in word.lower():
                        return word.strip()
        
        return None
    
    def _extract_search_query(self, text: str) -> str:
        """Extract search query from search command"""
        if 'search' in text and 'for' in text:
            return text.split('for', 1)[1].strip()
        elif 'search' in text:
            return text.split('search', 1)[1].strip()
        return text.strip()
    
    def _execute_intent(self, intent: Dict, original_text: str, context: Dict) -> bool:
        """Execute command based on determined intent"""
        try:
            action = intent['action']
            confidence = intent.get('confidence', 0.5)
            
            # Lower confidence threshold to be more permissive
            if confidence < 0.4:
                self._handle_low_confidence(intent, original_text)
                return False
            
            # Execute the action
            success = False
            
            if action == 'lock_screen':
                success = self._lock_screen()
            elif action == 'shutdown':
                success = self._shutdown()
            elif action == 'restart':
                success = self._restart()
            elif action == 'sleep':
                success = self._sleep()
            elif action == 'volume_up':
                success = self._volume_up()
            elif action == 'volume_down':
                success = self._volume_down()
            elif action == 'mute':
                success = self._mute()
            elif action == 'open_generic':
                success = self._open_generic(intent.get('target', ''))
            elif action == 'close_generic':
                success = self._close_generic(intent.get('target', ''))
            elif action == 'type_text':
                success = self._type_text(intent.get('text', ''))
            elif action == 'search_web':
                success = self._search_web(intent.get('query', ''))
            elif action == 'click_element':
                success = self._click_element(intent.get('target', ''))
            elif action == 'open_file':
                success = self._open_file(intent.get('target', ''))
            elif action == 'play':
                success = self._media_play()
            elif action == 'pause':
                success = self._media_pause()
            elif action == 'next':
                success = self._media_next()
            elif action == 'previous':
                success = self._media_previous()
            else:
                # Try to execute as generic command
                success = self._execute_generic_command(action, intent, context)
            
            if success:
                if self.tts:
                    self.tts.say("Command executed successfully.")
                return True
            else:
                if self.tts:
                    self.tts.say("Could not execute that command.")
                return False
            
        except Exception as e:
            self.logger.error(f"Error executing intent: {e}")
            if self.tts:
                self.tts.say("Sorry, I encountered an error.")
            return False
    
    def _lock_screen(self) -> bool:
        """Lock the screen"""
        try:
            if self.platform == "windows":
                subprocess.run(["rundll32.exe", "user32.dll,LockWorkStation"], check=True)
            elif self.platform == "darwin":
                subprocess.run(["pmset", "displaysleepnow"], check=True)
            else:  # Linux
                subprocess.run(["gnome-screensaver-command", "-l"], check=True)
            
            if self.tts:
                self.tts.say("Screen locked.")
            return True
        except Exception as e:
            self.logger.error(f"Error locking screen: {e}")
            return False
    
    def _shutdown(self) -> bool:
        """Shutdown the system"""
        try:
            if self.platform == "windows":
                subprocess.run(["shutdown", "/s", "/t", "10"], check=True)
            elif self.platform == "darwin":
                subprocess.run(["sudo", "shutdown", "-h", "now"], check=True)
            else:  # Linux
                subprocess.run(["sudo", "shutdown", "-h", "now"], check=True)
            
            if self.tts:
                self.tts.say("System will shutdown in 10 seconds.")
            return True
        except Exception as e:
            self.logger.error(f"Error shutting down: {e}")
            return False
    
    def _restart(self) -> bool:
        """Restart the system"""
        try:
            if self.platform == "windows":
                subprocess.run(["shutdown", "/r", "/t", "10"], check=True)
            elif self.platform == "darwin":
                subprocess.run(["sudo", "shutdown", "-r", "now"], check=True)
            else:  # Linux
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
            else:  # Linux
                subprocess.run(["systemctl", "suspend"], check=True)
            
            if self.tts:
                self.tts.say("System going to sleep.")
            return True
        except Exception as e:
            self.logger.error(f"Error putting system to sleep: {e}")
            return False
    
    def _volume_up(self) -> bool:
        """Increase system volume"""
        try:
            if self.platform == "windows":
                subprocess.run(["powershell", "-c", "(New-Object -comObject WScript.Shell).SendKeys([char]175)"], check=True)
            elif self.platform == "darwin":
                subprocess.run(["osascript", "-e", "set volume output volume (output volume of (get volume settings) + 10)"], check=True)
            else:  # Linux
                subprocess.run(["amixer", "set", "Master", "10%+"], check=True)
            
            if self.tts:
                self.tts.say("Volume increased.")
            return True
        except Exception as e:
            self.logger.error(f"Error increasing volume: {e}")
            return False
    
    def _volume_down(self) -> bool:
        """Decrease system volume"""
        try:
            if self.platform == "windows":
                subprocess.run(["powershell", "-c", "(New-Object -comObject WScript.Shell).SendKeys([char]174)"], check=True)
            elif self.platform == "darwin":
                subprocess.run(["osascript", "-e", "set volume output volume (output volume of (get volume settings) - 10)"], check=True)
            else:  # Linux
                subprocess.run(["amixer", "set", "Master", "10%-"], check=True)
            
            if self.tts:
                self.tts.say("Volume decreased.")
            return True
        except Exception as e:
            self.logger.error(f"Error decreasing volume: {e}")
            return False
    
    def _mute(self) -> bool:
        """Mute/unmute system volume"""
        try:
            if self.platform == "windows":
                subprocess.run(["powershell", "-c", "(New-Object -comObject WScript.Shell).SendKeys([char]173)"], check=True)
            elif self.platform == "darwin":
                subprocess.run(["osascript", "-e", "set volume output volume 0"], check=True)
            else:  # Linux
                subprocess.run(["amixer", "set", "Master", "mute"], check=True)
            
            if self.tts:
                self.tts.say("Volume muted.")
            return True
        except Exception as e:
            self.logger.error(f"Error muting volume: {e}")
            return False
    
    def _open_generic(self, target: str) -> bool:
        """Open generic target (app, file, website)"""
        try:
            if not target:
                if self.tts:
                    self.tts.say("What would you like me to open?")
                return False
            
            # Try to open as application first
            if self._try_open_app(target):
                return True
            
            # Try to open as file
            if self._try_open_file(target):
                return True
            
            # Try to open as website
            if self._try_open_website(target):
                return True
            
            # If nothing worked, try system commands
            if self._try_system_command(target):
                return True
            
            if self.tts:
                self.tts.say(f"Could not open {target}.")
            return False
            
        except Exception as e:
            self.logger.error(f"Error opening generic target: {e}")
            return False
    
    def _try_open_app(self, app_name: str) -> bool:
        """Try to open as application"""
        try:
            # Common app mappings
            app_mappings = {
                'notepad': 'notepad.exe',
                'paint': 'mspaint.exe',
                'calculator': 'calc.exe',
                'chrome': 'chrome.exe',
                'firefox': 'firefox.exe',
                'edge': 'msedge.exe',
                'cmd': 'cmd.exe',
                'powershell': 'powershell.exe',
                'file explorer': 'explorer.exe',
                'explorer': 'explorer.exe',
                'task manager': 'taskmgr.exe'
            }
            
            app_name_lower = app_name.lower().strip()
            
            # Check direct mappings first
            if app_name_lower in app_mappings:
                exe_name = app_mappings[app_name_lower]
                self.logger.info(f"Opening {exe_name}")
                subprocess.Popen([exe_name])
                if self.tts:
                    self.tts.say(f"Opened {app_name}.")
                return True
            
            # Try Windows start command for anything else
            if self.platform == "windows":
                try:
                    self.logger.info(f"Trying to start: {app_name}")
                    subprocess.run(["start", app_name], shell=True, check=True)
                    if self.tts:
                        self.tts.say(f"Opened {app_name}.")
                    return True
                except Exception as e:
                    self.logger.error(f"Failed to start {app_name}: {e}")
            
            return False
            
        except Exception as e:
            self.logger.error(f"Error opening app: {e}")
            return False
    
    def _try_open_file(self, filename: str) -> bool:
        """Try to open as file"""
        try:
            if os.path.exists(filename):
                if self.platform == "windows":
                    os.startfile(filename)
                elif self.platform == "darwin":
                    subprocess.run(["open", filename])
                else:  # Linux
                    subprocess.run(["xdg-open", filename])
                
                if self.tts:
                    self.tts.say(f"Opened {filename}.")
                return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"Error opening file: {e}")
            return False
    
    def _try_open_website(self, url: str) -> bool:
        """Try to open as website"""
        try:
            # Add protocol if missing
            if not url.startswith(('http://', 'https://')):
                url = 'https://' + url
            
            webbrowser.open(url)
            if self.tts:
                self.tts.say(f"Opened {url}.")
            return True
            
        except Exception as e:
            self.logger.error(f"Error opening website: {e}")
            return False
    
    def _try_system_command(self, command: str) -> bool:
        """Try to execute as system command"""
        try:
            # Only allow safe commands
            safe_commands = ['dir', 'ls', 'pwd', 'whoami', 'date', 'time']
            
            if command.lower() in safe_commands:
                result = subprocess.run([command], shell=True, capture_output=True, text=True)
                if self.tts and result.stdout:
                    self.tts.say(f"Command result: {result.stdout[:100]}...")
                return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"Error executing system command: {e}")
            return False
    
    def _close_generic(self, target: str) -> bool:
        """Close generic target"""
        try:
            if not target:
                if self.tts:
                    self.tts.say("What would you like me to close?")
                return False
            
            # Try to close window
            if PYAUTOGUI_AVAILABLE:
                pyautogui.hotkey('alt', 'f4')
                if self.tts:
                    self.tts.say(f"Closed {target}.")
                return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"Error closing target: {e}")
            return False
    
    def _type_text(self, text: str) -> bool:
        """Type text at current cursor position"""
        try:
            if PYAUTOGUI_AVAILABLE and text:
                pyautogui.typewrite(text)
                if self.tts:
                    self.tts.say(f"Typed: {text[:50]}...")
                return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"Error typing text: {e}")
            return False
    
    def _search_web(self, query: str) -> bool:
        """Search on web"""
        try:
            if not query:
                if self.tts:
                    self.tts.say("What would you like me to search for?")
                return False
            
            search_url = f"https://www.google.com/search?q={query}"
            webbrowser.open(search_url)
            
            if self.tts:
                self.tts.say(f"Searching for {query}.")
            return True
            
        except Exception as e:
            self.logger.error(f"Error searching web: {e}")
            return False
    
    def _click_element(self, target: str) -> bool:
        """Click on screen element"""
        try:
            # For now, click at center of screen
            # In a full implementation, this would find the actual element
            if PYAUTOGUI_AVAILABLE:
                screen_width, screen_height = pyautogui.size()
                pyautogui.click(screen_width // 2, screen_height // 2)
                
                if self.tts:
                    self.tts.say(f"Clicked on {target}.")
                return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"Error clicking element: {e}")
            return False
    
    def _open_file(self, filename: str) -> bool:
        """Open specific file"""
        try:
            if self.platform == "windows":
                os.startfile(filename)
            elif self.platform == "darwin":
                subprocess.run(["open", filename])
            else:  # Linux
                subprocess.run(["xdg-open", filename])
            
            if self.tts:
                self.tts.say(f"Opened {filename}.")
            return True
            
        except Exception as e:
            self.logger.error(f"Error opening file: {e}")
            return False
    
    def _media_play(self) -> bool:
        """Play media"""
        try:
            if PYAUTOGUI_AVAILABLE:
                pyautogui.press('space')  # Common play/pause key
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
                pyautogui.press('space')  # Common play/pause key
                if self.tts:
                    self.tts.say("Paused media.")
                return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"Error pausing media: {e}")
            return False
    
    def _media_next(self) -> bool:
        """Next media track"""
        try:
            if PYAUTOGUI_AVAILABLE:
                pyautogui.press('right')  # Common next key
                if self.tts:
                    self.tts.say("Next track.")
                return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"Error skipping to next track: {e}")
            return False
    
    def _media_previous(self) -> bool:
        """Previous media track"""
        try:
            if PYAUTOGUI_AVAILABLE:
                pyautogui.press('left')  # Common previous key
                if self.tts:
                    self.tts.say("Previous track.")
                return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"Error going to previous track: {e}")
            return False
    
    def _execute_generic_command(self, action: str, intent: Dict, context: Dict) -> bool:
        """Execute generic command"""
        try:
            # Try common keyboard shortcuts
            shortcut_map = {
                'save': 'ctrl+s',
                'open': 'ctrl+o',
                'new': 'ctrl+n',
                'copy': 'ctrl+c',
                'paste': 'ctrl+v',
                'cut': 'ctrl+x',
                'undo': 'ctrl+z',
                'redo': 'ctrl+y',
                'find': 'ctrl+f',
                'select_all': 'ctrl+a',
                'close': 'alt+f4',
                'minimize': 'alt+space n',
                'maximize': 'alt+space x'
            }
            
            if action in shortcut_map and PYAUTOGUI_AVAILABLE:
                shortcut = shortcut_map[action]
                pyautogui.hotkey(*shortcut.split('+'))
                
                if self.tts:
                    self.tts.say(f"Executed {action}.")
                return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"Error executing generic command: {e}")
            return False
    
    def _handle_unknown_command(self, text: str) -> None:
        """Handle unknown commands"""
        # Don't say anything - let other executors try
        pass
    
    def _handle_low_confidence(self, intent: Dict, original_text: str) -> None:
        """Handle low confidence commands"""
        # Don't say anything for low confidence - let other executors try
        pass
    
    def get_status(self) -> Dict[str, Any]:
        """Get executor status"""
        return {
            'platform': self.platform,
            'pyautogui_available': PYAUTOGUI_AVAILABLE,
            'image_processing_available': IMAGE_PROCESSING_AVAILABLE,
            'ocr_available': OCR_AVAILABLE,
            'window_management_available': WINDOW_MANAGEMENT_AVAILABLE,
            'command_patterns_loaded': len(self.command_patterns),
            'last_context_time': self.last_screen_analysis.get('timestamp', 0) if self.last_screen_analysis else 0
        }
