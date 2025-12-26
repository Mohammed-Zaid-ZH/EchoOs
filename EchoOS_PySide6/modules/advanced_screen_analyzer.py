"""
Advanced Screen Analyzer for EchoOS
Uses OCR and image processing to understand screen content dynamically
"""

import os
import sys
import time
import logging
import platform
import re
from typing import Optional, Dict, List, Any, Tuple
from pathlib import Path

# Image processing imports
try:
    import pyautogui
    import cv2
    import numpy as np
    from PIL import Image, ImageGrab
    IMAGE_PROCESSING_AVAILABLE = True
except ImportError:
    IMAGE_PROCESSING_AVAILABLE = False

# OCR imports
try:
    import pytesseract
    OCR_AVAILABLE = True
except ImportError:
    OCR_AVAILABLE = False

# Window management
try:
    import pygetwindow as gw
    WINDOW_MANAGEMENT_AVAILABLE = True
except ImportError:
    WINDOW_MANAGEMENT_AVAILABLE = False

# Windows-specific
if platform.system() == "Windows":
    try:
        import win32gui
        import win32con
        import win32process
        import psutil
        WINDOWS_APIS_AVAILABLE = True
    except ImportError:
        WINDOWS_APIS_AVAILABLE = False
else:
    WINDOWS_APIS_AVAILABLE = False

class AdvancedScreenAnalyzer:
    """Advanced screen analyzer with OCR and context understanding"""
    
    def __init__(self, tts=None):
        self.tts = tts
        self.logger = logging.getLogger(__name__)
        self.platform = platform.system().lower()
        
        # Cache settings
        self.last_analysis = None
        self.analysis_cache_time = 1.0  # seconds
        
        # OCR settings
        self.ocr_config = '--psm 6'  # Assume uniform block of text
        
    def analyze_screen(self) -> Dict[str, Any]:
        """Perform comprehensive screen analysis"""
        try:
            current_time = time.time()
            
            # Check cache
            if (self.last_analysis and 
                current_time - self.last_analysis.get('timestamp', 0) < self.analysis_cache_time):
                return self.last_analysis
            
            # Get active window info
            window_info = self._get_active_window_info()
            
            # Extract screen text using OCR
            screen_text = self._extract_screen_text()
            
            # Detect files and folders on screen
            files_on_screen = self._detect_files_on_screen(screen_text)
            
            # Detect UI elements (buttons, links, etc.)
            ui_elements = self._detect_ui_elements()
            
            # Identify current application
            current_app = self._identify_application(window_info, screen_text)
            
            # Get available actions based on context
            available_actions = self._get_available_actions(current_app, files_on_screen)
            
            context = {
                'timestamp': current_time,
                'active_window': window_info,
                'screen_text': screen_text,
                'files_on_screen': files_on_screen,
                'ui_elements': ui_elements,
                'current_app': current_app,
                'available_actions': available_actions,
                'context_type': current_app
            }
            
            self.last_analysis = context
            return context
            
        except Exception as e:
            self.logger.error(f"Error analyzing screen: {e}")
            return {
                'timestamp': time.time(),
                'active_window': None,
                'screen_text': '',
                'files_on_screen': [],
                'ui_elements': [],
                'current_app': 'unknown',
                'available_actions': [],
                'context_type': 'unknown'
            }
    
    def _get_active_window_info(self) -> Optional[Dict]:
        """Get information about currently active window"""
        try:
            if WINDOWS_APIS_AVAILABLE:
                return self._analyze_window_windows()
            elif WINDOW_MANAGEMENT_AVAILABLE:
                return self._analyze_window_pygetwindow()
            else:
                return None
        except Exception as e:
            self.logger.error(f"Error getting window info: {e}")
            return None
    
    def _analyze_window_windows(self) -> Optional[Dict]:
        """Analyze window using Windows APIs"""
        try:
            hwnd = win32gui.GetForegroundWindow()
            window_text = win32gui.GetWindowText(hwnd)
            rect = win32gui.GetWindowRect(hwnd)
            
            # Get process information
            try:
                _, pid = win32process.GetWindowThreadProcessId(hwnd)
                process = psutil.Process(pid)
                process_name = process.name()
                process_path = process.exe()
            except:
                process_name = "Unknown"
                process_path = ""
            
            return {
                'title': window_text,
                'hwnd': hwnd,
                'rect': rect,
                'process_name': process_name,
                'process_path': process_path,
                'app_name': self._extract_app_name(window_text, process_name)
            }
        except Exception as e:
            self.logger.error(f"Error analyzing window with Windows APIs: {e}")
            return None
    
    def _analyze_window_pygetwindow(self) -> Optional[Dict]:
        """Analyze window using pygetwindow"""
        try:
            active_windows = gw.getActiveWindow()
            if active_windows:
                return {
                    'title': active_windows.title,
                    'rect': (active_windows.left, active_windows.top, 
                            active_windows.width, active_windows.height),
                    'app_name': self._extract_app_name(active_windows.title, "")
                }
            return None
        except Exception as e:
            self.logger.error(f"Error analyzing window with pygetwindow: {e}")
            return None
    
    def _extract_app_name(self, window_title: str, process_name: str) -> str:
        """Extract application name from window title and process"""
        # Try to extract from window title first
        if ' - ' in window_title:
            return window_title.split(' - ')[-1].strip()
        elif ' | ' in window_title:
            return window_title.split(' | ')[-1].strip()
        
        # Fall back to process name
        if process_name:
            return process_name.replace('.exe', '').strip()
        
        return window_title.strip()
    
    def _extract_screen_text(self) -> str:
        """Extract text from current screen using OCR"""
        try:
            if not OCR_AVAILABLE or not IMAGE_PROCESSING_AVAILABLE:
                return ""
            
            # Capture screen
            screenshot = ImageGrab.grab()
            
            # Convert to OpenCV format
            img_array = np.array(screenshot)
            img = cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR)
            
            # Preprocess image for better OCR
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            
            # Apply thresholding
            _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            
            # Perform OCR
            text = pytesseract.image_to_string(thresh, config=self.ocr_config)
            
            return text.strip()
            
        except Exception as e:
            self.logger.debug(f"OCR error (expected if Tesseract not installed): {e}")
            return ""
    
    def _detect_files_on_screen(self, screen_text: str) -> List[Dict[str, Any]]:
        """Detect files and folders visible on screen"""
        files = []
        
        if not screen_text:
            return files
        
        # Common file patterns
        file_patterns = [
            # File extensions
            r'\b\w+\.(txt|doc|docx|pdf|py|js|html|css|json|xml|csv|xlsx|pptx|mp4|mp3|jpg|png|gif|zip|rar|exe|msi)\b',
            # Folder patterns (often end with / or \)
            r'\b\w+[\\/]\s*$',
            # Common folder names
            r'\b(Desktop|Documents|Downloads|Pictures|Videos|Music|Videos)\b',
        ]
        
        lines = screen_text.split('\n')
        for line_num, line in enumerate(lines):
            line = line.strip()
            if not line:
                continue
            
            # Check for file patterns
            for pattern in file_patterns:
                matches = re.finditer(pattern, line, re.IGNORECASE)
                for match in matches:
                    file_name = match.group(0).strip()
                    
                    # Clean up file name
                    file_name = re.sub(r'[^\w\.\-\\/]', '', file_name)
                    
                    if file_name and len(file_name) > 1:
                        files.append({
                            'name': file_name,
                            'line': line_num,
                            'full_line': line,
                            'type': 'file' if '.' in file_name else 'folder'
                        })
            
            # Also check for common file/folder indicators
            if any(indicator in line.lower() for indicator in ['folder', 'file', 'directory', 'documents']):
                # Extract potential file/folder names
                words = line.split()
                for word in words:
                    if len(word) > 2 and not word.lower() in ['the', 'and', 'for', 'with', 'from']:
                        files.append({
                            'name': word,
                            'line': line_num,
                            'full_line': line,
                            'type': 'unknown'
                        })
        
        # Remove duplicates
        seen = set()
        unique_files = []
        for file_info in files:
            if file_info['name'] not in seen:
                seen.add(file_info['name'])
                unique_files.append(file_info)
        
        return unique_files
    
    def _detect_ui_elements(self) -> List[Dict[str, Any]]:
        """Detect UI elements like buttons, links, etc."""
        elements = []
        
        if not IMAGE_PROCESSING_AVAILABLE:
            return elements
        
        try:
            # Capture screen
            screenshot = ImageGrab.grab()
            img_array = np.array(screenshot)
            img = cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR)
            
            # Convert to grayscale
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            
            # Detect edges
            edges = cv2.Canny(gray, 50, 150)
            
            # Find contours
            contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            for contour in contours:
                x, y, w, h = cv2.boundingRect(contour)
                
                # Filter for button-like elements
                if 50 <= w <= 400 and 20 <= h <= 100:
                    elements.append({
                        'type': 'button',
                        'rect': (x, y, w, h),
                        'center': (x + w//2, y + h//2),
                        'area': w * h
                    })
            
            # Sort by area (larger elements first)
            elements.sort(key=lambda x: x['area'], reverse=True)
            
        except Exception as e:
            self.logger.error(f"Error detecting UI elements: {e}")
        
        return elements
    
    def _identify_application(self, window_info: Optional[Dict], screen_text: str) -> str:
        """Identify current application type"""
        if not window_info:
            return 'unknown'
        
        app_name = window_info.get('app_name', '').lower()
        title = window_info.get('title', '').lower()
        process_name = window_info.get('process_name', '').lower()
        screen_lower = screen_text.lower()
        
        # File Explorer / File Manager
        if any(keyword in app_name for keyword in ['explorer', 'finder', 'files', 'file manager']):
            return 'file_explorer'
        if 'this pc' in title or 'computer' in title or 'file explorer' in title:
            return 'file_explorer'
        
        # Browser
        if any(keyword in app_name for keyword in ['chrome', 'firefox', 'edge', 'safari', 'opera', 'browser']):
            return 'browser'
        if 'http' in screen_lower or 'www' in screen_lower or 'search' in screen_lower:
            return 'browser'
        
        # Text Editor
        if any(keyword in app_name for keyword in ['notepad', 'code', 'sublime', 'atom', 'vim', 'word', 'writer']):
            return 'text_editor'
        if 'document' in screen_lower or 'edit' in screen_lower:
            return 'text_editor'
        
        # Media Player
        if any(keyword in app_name for keyword in ['vlc', 'media player', 'quicktime', 'windows media', 'spotify']):
            return 'media_player'
        if 'play' in screen_lower and 'pause' in screen_lower:
            return 'media_player'
        
        # Terminal / Command Prompt
        if any(keyword in app_name for keyword in ['cmd', 'powershell', 'terminal', 'bash', 'command']):
            return 'terminal'
        if 'c:\\' in screen_lower or '>' in screen_lower or '$' in screen_lower:
            return 'terminal'
        
        # Image Viewer
        if any(keyword in app_name for keyword in ['photo', 'image', 'viewer', 'gallery']):
            return 'image_viewer'
        
        # Video Player
        if any(keyword in app_name for keyword in ['video', 'player', 'movie']):
            return 'video_player'
        
        return 'generic'
    
    def _get_available_actions(self, app_type: str, files_on_screen: List[Dict]) -> List[str]:
        """Get available actions for current application"""
        action_map = {
            'file_explorer': ['navigate', 'create', 'delete', 'copy', 'move', 'rename', 'open', 'select'],
            'browser': ['navigate', 'search', 'new_tab', 'close_tab', 'bookmark', 'download', 'scroll', 'click'],
            'text_editor': ['type', 'save', 'open', 'find', 'replace', 'copy', 'paste', 'select_all'],
            'media_player': ['play', 'pause', 'next', 'previous', 'volume', 'seek', 'fullscreen', 'stop'],
            'terminal': ['execute', 'type_command', 'clear', 'navigate'],
            'image_viewer': ['zoom', 'next', 'previous', 'rotate'],
            'video_player': ['play', 'pause', 'seek', 'volume', 'fullscreen'],
            'generic': ['click', 'type', 'scroll', 'close', 'minimize', 'maximize']
        }
        
        actions = action_map.get(app_type, action_map['generic'])
        
        # Add file-specific actions if files are visible
        if files_on_screen:
            actions.extend(['open_file', 'select_file', 'delete_file'])
        
        return list(set(actions))  # Remove duplicates
    
    def find_file_on_screen(self, file_name: str) -> Optional[Dict[str, Any]]:
        """Find a specific file on screen"""
        context = self.analyze_screen()
        files = context.get('files_on_screen', [])
        
        # Fuzzy match
        from rapidfuzz import fuzz, process
        
        if not files:
            return None
        
        file_names = [f['name'] for f in files]
        result = process.extractOne(file_name.lower(), file_names, scorer=fuzz.ratio)
        
        if result and len(result) == 2:
            best_match, score = result
            if score > 60:  # 60% similarity threshold
                # Find the file info
                for file_info in files:
                    if file_info['name'].lower() == best_match.lower():
                        return file_info
        
        return None
    
    def get_screen_context_summary(self) -> str:
        """Get a human-readable summary of screen context"""
        context = self.analyze_screen()
        
        summary_parts = []
        
        if context.get('current_app') != 'unknown':
            summary_parts.append(f"Application: {context['current_app']}")
        
        files = context.get('files_on_screen', [])
        if files:
            file_names = [f['name'] for f in files[:5]]  # First 5 files
            summary_parts.append(f"Files visible: {', '.join(file_names)}")
        
        if context.get('active_window'):
            title = context['active_window'].get('title', '')
            if title:
                summary_parts.append(f"Window: {title[:50]}")
        
        return ". ".join(summary_parts) if summary_parts else "Screen context unknown"
    
    def get_status(self) -> Dict[str, Any]:
        """Get analyzer status"""
        return {
            'image_processing_available': IMAGE_PROCESSING_AVAILABLE,
            'ocr_available': OCR_AVAILABLE,
            'window_management_available': WINDOW_MANAGEMENT_AVAILABLE,
            'windows_apis_available': WINDOWS_APIS_AVAILABLE,
            'last_analysis_time': self.last_analysis.get('timestamp', 0) if self.last_analysis else 0
        }

