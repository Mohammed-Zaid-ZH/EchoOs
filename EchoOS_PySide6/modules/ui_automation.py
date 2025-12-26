"""
Universal UI Automation Module for EchoOS
Provides cross-platform UI automation capabilities for complete hands-free computing
"""

import os
import sys
import time
import logging
import platform
from typing import Optional, List, Dict, Tuple, Any
from pathlib import Path

# Platform-specific imports
try:
    import pyautogui
    pyautogui.FAILSAFE = True
    pyautogui.PAUSE = 0.1
    PYAUTOGUI_AVAILABLE = True
except ImportError:
    PYAUTOGUI_AVAILABLE = False
    print("PyAutoGUI not available - UI automation will be limited")

try:
    import pygetwindow as gw
    WINDOW_MANAGEMENT_AVAILABLE = True
except ImportError:
    WINDOW_MANAGEMENT_AVAILABLE = False
    print("Window management not available")

try:
    import cv2
    import numpy as np
    from PIL import Image, ImageGrab
    IMAGE_PROCESSING_AVAILABLE = True
except ImportError:
    IMAGE_PROCESSING_AVAILABLE = False
    print("Image processing not available - screen analysis will be limited")

try:
    import pytesseract
    OCR_AVAILABLE = True
except ImportError:
    OCR_AVAILABLE = False
    print("OCR not available - text recognition will be limited")

# Platform-specific imports
if platform.system() == "Windows":
    try:
        import win32gui
        import win32con
        import win32api
        import win32ui
        WINDOWS_APIS_AVAILABLE = True
    except ImportError:
        WINDOWS_APIS_AVAILABLE = False
        print("Windows APIs not available")

elif platform.system() == "Darwin":  # macOS
    try:
        import Quartz
        MACOS_APIS_AVAILABLE = True
    except ImportError:
        MACOS_APIS_AVAILABLE = False
        print("macOS APIs not available")

class ScreenContext:
    """Represents the current screen context"""
    def __init__(self):
        self.active_window = None
        self.active_app = None
        self.screen_elements = []
        self.available_actions = []
        self.current_text = ""
        self.timestamp = time.time()

class UIElement:
    """Represents a UI element on screen"""
    def __init__(self, x: int, y: int, width: int, height: int, 
                 element_type: str, text: str = "", confidence: float = 0.0):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.element_type = element_type  # button, text, input, menu, etc.
        self.text = text
        self.confidence = confidence
        self.center_x = x + width // 2
        self.center_y = y + height // 2

class UniversalUIAutomator:
    """Universal UI automation for cross-platform support"""
    
    def __init__(self, tts=None):
        self.tts = tts
        self.logger = logging.getLogger(__name__)
        self.platform = platform.system().lower()
        self.current_context = ScreenContext()
        
        # Initialize platform-specific components
        self._initialize_platform_components()
        
        # Screen analysis settings
        self.screen_analysis_enabled = True
        self.element_detection_confidence = 0.7
        
    def _initialize_platform_components(self):
        """Initialize platform-specific components"""
        if self.platform == "windows":
            self._init_windows()
        elif self.platform == "darwin":
            self._init_macos()
        else:
            self._init_linux()
    
    def _init_windows(self):
        """Initialize Windows-specific components"""
        self.window_apis_available = WINDOWS_APIS_AVAILABLE
        self._setup_windows_automation()
    
    def _init_macos(self):
        """Initialize macOS-specific components"""
        self.window_apis_available = MACOS_APIS_AVAILABLE
        self._setup_macos_automation()
    
    def _init_linux(self):
        """Initialize Linux-specific components"""
        self.window_apis_available = False
        self._setup_linux_automation()
    
    def _setup_windows_automation(self):
        """Setup Windows-specific automation"""
        if WINDOWS_APIS_AVAILABLE:
            self._get_active_window_windows = self._get_active_window_win32
            self._click_element_windows = self._click_element_win32
        else:
            self._get_active_window_windows = self._get_active_window_pyautogui
            self._click_element_windows = self._click_element_pyautogui
    
    def _setup_macos_automation(self):
        """Setup macOS-specific automation"""
        if MACOS_APIS_AVAILABLE:
            self._get_active_window_macos = self._get_active_window_quartz
            self._click_element_macos = self._click_element_quartz
        else:
            self._get_active_window_macos = self._get_active_window_pyautogui
            self._click_element_macos = self._click_element_pyautogui
    
    def _setup_linux_automation(self):
        """Setup Linux-specific automation"""
        self._get_active_window_linux = self._get_active_window_pyautogui
        self._click_element_linux = self._click_element_pyautogui
    
    def analyze_screen(self) -> ScreenContext:
        """Analyze current screen and return context"""
        try:
            # Capture screen
            screenshot = self._capture_screen()
            if screenshot is None:
                return self.current_context
            
            # Get active window info
            self.current_context.active_window = self._get_active_window()
            
            # Detect UI elements
            self.current_context.screen_elements = self._detect_ui_elements(screenshot)
            
            # Extract text content
            self.current_context.current_text = self._extract_text(screenshot)
            
            # Update available actions
            self.current_context.available_actions = self._get_available_actions()
            
            self.current_context.timestamp = time.time()
            
            return self.current_context
            
        except Exception as e:
            # Silently return empty context for analysis errors
            return ScreenContext(
                active_window=None,
                screen_elements=[],
                current_text="",
                context_type="unknown"
            )
            raise e
    
    def _capture_screen(self) -> Optional[Image.Image]:
        """Capture current screen"""
        try:
            if IMAGE_PROCESSING_AVAILABLE:
                return ImageGrab.grab()
            return None
        except Exception as e:
            self.logger.error(f"Error capturing screen: {e}")
            return None
    
    def _get_active_window(self) -> Optional[Dict]:
        """Get information about currently active window"""
        try:
            if self.platform == "windows":
                return self._get_active_window_windows()
            elif self.platform == "darwin":
                return self._get_active_window_macos()
            else:
                return self._get_active_window_linux()
        except Exception as e:
            self.logger.error(f"Error getting active window: {e}")
            return None
    
    def _get_active_window_win32(self) -> Optional[Dict]:
        """Get active window info using Windows APIs"""
        if not WINDOWS_APIS_AVAILABLE:
            return None
        
        try:
            hwnd = win32gui.GetForegroundWindow()
            window_text = win32gui.GetWindowText(hwnd)
            rect = win32gui.GetWindowRect(hwnd)
            
            return {
                'title': window_text,
                'hwnd': hwnd,
                'rect': rect,
                'app_name': self._get_app_name_from_hwnd(hwnd)
            }
        except Exception as e:
            self.logger.error(f"Error getting Windows window info: {e}")
            return None
    
    def _get_app_name_from_hwnd(self, hwnd):
        """Get application name from window handle"""
        try:
            if WINDOWS_APIS_AVAILABLE:
                import win32process
                import psutil
                
                # Get process ID from window handle
                _, pid = win32process.GetWindowThreadProcessId(hwnd)
                
                # Get process name
                process = psutil.Process(pid)
                return process.name()
            else:
                return "Unknown"
        except Exception as e:
            self.logger.error(f"Error getting app name from hwnd: {e}")
            return "Unknown"
    
    def _get_active_window_quartz(self) -> Optional[Dict]:
        """Get active window info using macOS Quartz"""
        if not MACOS_APIS_AVAILABLE:
            return None
        
        try:
            # This is a simplified version - full implementation would use Quartz APIs
            return {
                'title': 'Unknown',
                'app_name': 'Unknown'
            }
        except Exception as e:
            self.logger.error(f"Error getting macOS window info: {e}")
            return None
    
    def _get_active_window_pyautogui(self) -> Optional[Dict]:
        """Get active window info using pyautogui (fallback)"""
        try:
            if WINDOW_MANAGEMENT_AVAILABLE:
                active_windows = gw.getActiveWindow()
                if active_windows:
                    return {
                        'title': active_windows.title,
                        'app_name': active_windows.title.split(' - ')[-1] if ' - ' in active_windows.title else active_windows.title
                    }
            return None
        except Exception as e:
            self.logger.error(f"Error getting window info with pyautogui: {e}")
            return None
    
    def _detect_ui_elements(self, screenshot: Image.Image) -> List[UIElement]:
        """Detect UI elements on screen"""
        elements = []
        
        try:
            # Convert PIL image to OpenCV format
            if IMAGE_PROCESSING_AVAILABLE:
                cv_image = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)
                
                # Detect buttons (rectangular elements)
                elements.extend(self._detect_buttons(cv_image))
                
                # Detect text areas
                elements.extend(self._detect_text_areas(cv_image))
                
                # Detect input fields
                elements.extend(self._detect_input_fields(cv_image))
            
        except Exception as e:
            self.logger.error(f"Error detecting UI elements: {e}")
        
        return elements
    
    def _detect_buttons(self, cv_image: np.ndarray) -> List[UIElement]:
        """Detect button-like elements on screen"""
        buttons = []
        
        try:
            # Convert to grayscale
            gray = cv2.cvtColor(cv_image, cv2.COLOR_BGR2GRAY)
            
            # Edge detection
            edges = cv2.Canny(gray, 50, 150)
            
            # Find contours
            contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            for contour in contours:
                # Approximate contour to polygon
                epsilon = 0.02 * cv2.arcLength(contour, True)
                approx = cv2.approxPolyDP(contour, epsilon, True)
                
                # Check if it's roughly rectangular (button-like)
                if len(approx) >= 4:
                    x, y, w, h = cv2.boundingRect(contour)
                    
                    # Filter by size (reasonable button size)
                    if 50 <= w <= 300 and 20 <= h <= 100:
                        button = UIElement(x, y, w, h, "button", confidence=0.7)
                        buttons.append(button)
        
        except Exception as e:
            self.logger.error(f"Error detecting buttons: {e}")
        
        return buttons
    
    def _detect_text_areas(self, cv_image: np.ndarray) -> List[UIElement]:
        """Detect text areas on screen"""
        text_areas = []
        
        try:
            # This is a simplified implementation
            # A full implementation would use more sophisticated text detection
            gray = cv2.cvtColor(cv_image, cv2.COLOR_BGR2GRAY)
            
            # Use morphological operations to detect text regions
            kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (9, 1))
            dilated = cv2.dilate(gray, kernel, iterations=1)
            
            # Find contours of text regions
            contours, _ = cv2.findContours(dilated, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            for contour in contours:
                x, y, w, h = cv2.boundingRect(contour)
                
                # Filter by aspect ratio (text is usually wider than tall)
                aspect_ratio = w / h
                if 2 <= aspect_ratio <= 20 and w >= 100 and h >= 10:
                    text_area = UIElement(x, y, w, h, "text", confidence=0.6)
                    text_areas.append(text_area)
        
        except Exception as e:
            self.logger.error(f"Error detecting text areas: {e}")
        
        return text_areas
    
    def _detect_input_fields(self, cv_image: np.ndarray) -> List[UIElement]:
        """Detect input field elements on screen"""
        input_fields = []
        
        try:
            # This is a simplified implementation
            # A full implementation would use more sophisticated detection
            gray = cv2.cvtColor(cv_image, cv2.COLOR_BGR2GRAY)
            
            # Detect rectangular elements that could be input fields
            edges = cv2.Canny(gray, 50, 150)
            contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            for contour in contours:
                x, y, w, h = cv2.boundingRect(contour)
                
                # Input fields are usually rectangular and medium-sized
                if 100 <= w <= 500 and 20 <= h <= 50:
                    input_field = UIElement(x, y, w, h, "input", confidence=0.5)
                    input_fields.append(input_field)
        
        except Exception as e:
            self.logger.error(f"Error detecting input fields: {e}")
        
        return input_fields
    
    def _extract_text(self, screenshot: Image.Image) -> str:
        """Extract text from screenshot using OCR"""
        try:
            if OCR_AVAILABLE:
                return pytesseract.image_to_string(screenshot)
            return ""
        except Exception as e:
            # Silently return empty string for OCR errors
            return ""
            raise e
    
    def _get_available_actions(self) -> List[str]:
        """Get list of available actions based on current context"""
        actions = []
        
        # Basic actions always available
        actions.extend([
            "click", "double click", "right click",
            "type", "scroll up", "scroll down",
            "press enter", "press escape", "press tab"
        ])
        
        # Context-specific actions
        if self.current_context.active_window:
            app_name = self.current_context.active_window.get('app_name', '').lower()
            
            if 'chrome' in app_name or 'firefox' in app_name or 'edge' in app_name:
                actions.extend([
                    "new tab", "close tab", "refresh page",
                    "go back", "go forward", "bookmark page"
                ])
            elif 'explorer' in app_name or 'finder' in app_name:
                actions.extend([
                    "new folder", "delete file", "rename file",
                    "copy file", "paste file", "select all"
                ])
            elif 'notepad' in app_name or 'textedit' in app_name:
                actions.extend([
                    "save file", "open file", "new file",
                    "find text", "replace text", "select all"
                ])
        
        return actions
    
    def click_element(self, element: UIElement) -> bool:
        """Click on a UI element"""
        try:
            if self.platform == "windows":
                return self._click_element_windows(element)
            elif self.platform == "darwin":
                return self._click_element_macos(element)
            else:
                return self._click_element_linux(element)
        except Exception as e:
            self.logger.error(f"Error clicking element: {e}")
            return False
    
    def _click_element_pyautogui(self, element: UIElement) -> bool:
        """Click element using pyautogui"""
        if not PYAUTOGUI_AVAILABLE:
            return False
        
        try:
            pyautogui.click(element.center_x, element.center_y)
            return True
        except Exception as e:
            self.logger.error(f"Error clicking with pyautogui: {e}")
            return False
    
    def _click_element_win32(self, element: UIElement) -> bool:
        """Click element using Windows APIs"""
        if not WINDOWS_APIS_AVAILABLE:
            return self._click_element_pyautogui(element)
        
        try:
            # Get active window
            hwnd = win32gui.GetForegroundWindow()
            
            # Convert screen coordinates to window coordinates
            rect = win32gui.GetWindowRect(hwnd)
            x = element.center_x - rect[0]
            y = element.center_y - rect[1]
            
            # Send click message
            lParam = win32api.MAKELONG(x, y)
            win32gui.SendMessage(hwnd, win32con.WM_LBUTTONDOWN, win32con.MK_LBUTTON, lParam)
            win32gui.SendMessage(hwnd, win32con.WM_LBUTTONUP, 0, lParam)
            
            return True
        except Exception as e:
            self.logger.error(f"Error clicking with Windows APIs: {e}")
            return self._click_element_pyautogui(element)
    
    def _click_element_quartz(self, element: UIElement) -> bool:
        """Click element using macOS Quartz"""
        if not MACOS_APIS_AVAILABLE:
            return self._click_element_pyautogui(element)
        
        try:
            # Simplified implementation - full version would use Quartz APIs
            return self._click_element_pyautogui(element)
        except Exception as e:
            self.logger.error(f"Error clicking with macOS APIs: {e}")
            return self._click_element_pyautogui(element)
    
    def type_text(self, text: str) -> bool:
        """Type text at current cursor position"""
        try:
            if PYAUTOGUI_AVAILABLE:
                pyautogui.typewrite(text)
                return True
            return False
        except Exception as e:
            self.logger.error(f"Error typing text: {e}")
            return False
    
    def press_key(self, key: str) -> bool:
        """Press a key"""
        try:
            if PYAUTOGUI_AVAILABLE:
                pyautogui.press(key)
                return True
            return False
        except Exception as e:
            self.logger.error(f"Error pressing key: {e}")
            return False
    
    def scroll(self, direction: str, amount: int = 3) -> bool:
        """Scroll in specified direction"""
        try:
            if PYAUTOGUI_AVAILABLE:
                if direction.lower() == "up":
                    pyautogui.scroll(amount)
                elif direction.lower() == "down":
                    pyautogui.scroll(-amount)
                return True
            return False
        except Exception as e:
            self.logger.error(f"Error scrolling: {e}")
            return False
    
    def find_element_by_text(self, text: str) -> Optional[UIElement]:
        """Find UI element containing specified text"""
        try:
            # Analyze screen first
            self.analyze_screen()
            
            # Look for text in extracted content
            if text.lower() in self.current_context.current_text.lower():
                # Find approximate position (simplified)
                # A full implementation would use OCR with bounding boxes
                return UIElement(100, 100, 200, 30, "text", text, 0.8)
            
            return None
        except Exception as e:
            self.logger.error(f"Error finding element by text: {e}")
            return None
    
    def get_status(self) -> Dict[str, Any]:
        """Get current automation status"""
        return {
            'platform': self.platform,
            'pyautogui_available': PYAUTOGUI_AVAILABLE,
            'window_management_available': WINDOW_MANAGEMENT_AVAILABLE,
            'image_processing_available': IMAGE_PROCESSING_AVAILABLE,
            'ocr_available': OCR_AVAILABLE,
            'windows_apis_available': WINDOWS_APIS_AVAILABLE if self.platform == "windows" else False,
            'macos_apis_available': MACOS_APIS_AVAILABLE if self.platform == "darwin" else False,
            'screen_analysis_enabled': self.screen_analysis_enabled,
            'current_context': {
                'active_window': self.current_context.active_window,
                'element_count': len(self.current_context.screen_elements),
                'available_actions': len(self.current_context.available_actions)
            }
        }
