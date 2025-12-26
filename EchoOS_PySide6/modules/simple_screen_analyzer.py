"""
Simple Screen Analyzer for EchoOS
Provides basic screen understanding without OCR dependencies
"""

import os
import sys
import time
import logging
import platform
from typing import Optional, Dict, List, Any, Tuple
from pathlib import Path

# Window management imports
try:
    import pygetwindow as gw
    WINDOW_MANAGEMENT_AVAILABLE = True
except ImportError:
    WINDOW_MANAGEMENT_AVAILABLE = False

# Platform-specific imports
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

class SimpleScreenAnalyzer:
    """Simple screen analyzer without OCR dependencies"""
    
    def __init__(self, tts=None):
        self.tts = tts
        self.logger = logging.getLogger(__name__)
        self.platform = platform.system().lower()
        
        # Analysis settings
        self.last_analysis = None
        self.analysis_cache_time = 2.0  # seconds
        
        # Application detection patterns
        self.app_patterns = self._build_app_patterns()
        
    def _build_app_patterns(self) -> Dict[str, Dict]:
        """Build patterns for detecting different applications"""
        return {
            'file_explorer': {
                'window_titles': ['explorer', 'file manager', 'files', 'this pc', 'computer'],
                'keywords': ['folder', 'file', 'directory', 'path', 'location']
            },
            'browser': {
                'window_titles': ['chrome', 'firefox', 'edge', 'safari', 'opera', 'browser'],
                'keywords': ['http', 'www', 'search', 'bookmark', 'tab']
            },
            'text_editor': {
                'window_titles': ['notepad', 'word', 'code', 'sublime', 'atom', 'vim'],
                'keywords': ['document', 'file', 'edit', 'format', 'save', 'open']
            },
            'media_player': {
                'window_titles': ['vlc', 'media player', 'quicktime', 'windows media'],
                'keywords': ['play', 'pause', 'stop', 'volume', 'time', 'track']
            },
            'terminal': {
                'window_titles': ['cmd', 'powershell', 'terminal', 'bash', 'command'],
                'keywords': ['c:\\', '>', '$', '#', 'command', 'prompt']
            }
        }
    
    def analyze_screen(self) -> Dict[str, Any]:
        """Perform basic screen analysis"""
        try:
            current_time = time.time()
            
            # Check cache
            if (self.last_analysis and 
                current_time - self.last_analysis.get('timestamp', 0) < self.analysis_cache_time):
                return self.last_analysis
            
            # Create new context
            context = {
                'timestamp': current_time,
                'active_window': self._get_active_window_info(),
                'current_app': None,
                'available_actions': [],
                'context_type': 'unknown'
            }
            
            # Determine current application
            if context['active_window']:
                context['current_app'] = self._identify_application(context['active_window'])
                context['context_type'] = context['current_app']
                context['available_actions'] = self._get_available_actions(context['current_app'])
            
            self.last_analysis = context
            return context
            
        except Exception as e:
            self.logger.error(f"Error analyzing screen: {e}")
            return {'timestamp': time.time(), 'active_window': None, 'current_app': None, 'available_actions': [], 'context_type': 'unknown'}
    
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
            self.logger.error(f"Error analyzing window: {e}")
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
    
    def _identify_application(self, window_info: Optional[Dict]) -> str:
        """Identify the current application"""
        if not window_info:
            return 'unknown'
        
        app_name = window_info.get('app_name', '').lower()
        title = window_info.get('title', '').lower()
        
        for app_type, patterns in self.app_patterns.items():
            # Check window titles
            for pattern in patterns['window_titles']:
                if pattern in app_name or pattern in title:
                    return app_type
        
        return 'unknown'
    
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
    
    def get_status(self) -> Dict[str, Any]:
        """Get analyzer status"""
        return {
            'window_management_available': WINDOW_MANAGEMENT_AVAILABLE,
            'windows_apis_available': WINDOWS_APIS_AVAILABLE,
            'last_analysis_time': self.last_analysis.get('timestamp', 0) if self.last_analysis else 0,
            'app_patterns_loaded': len(self.app_patterns)
        }
