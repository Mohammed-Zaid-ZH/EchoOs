"""
Window Manager for EchoOS
Dynamically manages windows, apps, and tabs without hardcoding
"""

import os
import sys
import platform
import logging
import time
from typing import Optional, Dict, List, Any

# Window management imports
try:
    import pygetwindow as gw
    WINDOW_MANAGEMENT_AVAILABLE = True
except ImportError:
    WINDOW_MANAGEMENT_AVAILABLE = False

try:
    import pyautogui
    PYAUTOGUI_AVAILABLE = True
except ImportError:
    PYAUTOGUI_AVAILABLE = False

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

class WindowManager:
    """Dynamic window and application manager"""
    
    def __init__(self, tts=None):
        self.tts = tts
        self.logger = logging.getLogger(__name__)
        self.platform = platform.system().lower()
    
    def get_all_windows(self) -> List[Dict[str, Any]]:
        """Get all open windows dynamically"""
        windows = []
        
        try:
            if WINDOW_MANAGEMENT_AVAILABLE:
                all_windows = gw.getAllWindows()
                for win in all_windows:
                    if win.title and win.visible:  # Only visible windows
                        windows.append({
                            'title': win.title,
                            'app_name': self._extract_app_name(win.title),
                            'rect': (win.left, win.top, win.width, win.height),
                            'window': win
                        })
        except Exception as e:
            self.logger.error(f"Error getting windows: {e}")
        
        return windows
    
    def get_running_apps(self) -> List[Dict[str, Any]]:
        """Get all running applications dynamically"""
        apps = []
        
        try:
            if self.platform == "windows" and WINDOWS_APIS_AVAILABLE:
                # Get all processes
                for proc in psutil.process_iter(['pid', 'name', 'exe']):
                    try:
                        proc_info = proc.info
                        name = proc_info.get('name', '')
                        exe = proc_info.get('exe', '')
                        
                        # Filter system processes
                        if name and exe and not self._is_system_process(name):
                            apps.append({
                                'name': name.replace('.exe', ''),
                                'process_name': name,
                                'exe_path': exe,
                                'pid': proc_info.get('pid')
                            })
                    except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                        continue
            else:
                # Fallback: use window titles
                windows = self.get_all_windows()
                seen_apps = set()
                for win in windows:
                    app_name = win.get('app_name', '')
                    if app_name and app_name not in seen_apps:
                        seen_apps.add(app_name)
                        apps.append({
                            'name': app_name,
                            'process_name': app_name,
                            'exe_path': '',
                            'pid': None
                        })
        except Exception as e:
            self.logger.error(f"Error getting running apps: {e}")
        
        return apps
    
    def switch_to_app(self, app_name: str) -> bool:
        """Switch to a specific application by name"""
        try:
            windows = self.get_all_windows()
            
            # Find windows matching app name
            matching_windows = []
            app_name_lower = app_name.lower()
            
            for win in windows:
                win_title = win.get('title', '').lower()
                win_app = win.get('app_name', '').lower()
                
                if (app_name_lower in win_title or 
                    app_name_lower in win_app or
                    win_app in app_name_lower):
                    matching_windows.append(win)
            
            if matching_windows:
                # Activate the first matching window
                if WINDOW_MANAGEMENT_AVAILABLE:
                    matching_windows[0]['window'].activate()
                elif PYAUTOGUI_AVAILABLE:
                    # Use Alt+Tab to switch
                    pyautogui.hotkey('alt', 'tab')
                    time.sleep(0.3)
                
                if self.tts:
                    self.tts.say(f"Switched to {app_name}.")
                return True
            
            # Try using Alt+Tab to cycle
            if PYAUTOGUI_AVAILABLE:
                pyautogui.hotkey('alt', 'tab')
                if self.tts:
                    self.tts.say(f"Switching windows.")
                return True
            
            return False
        except Exception as e:
            self.logger.error(f"Error switching to app: {e}")
            return False
    
    def switch_to_next_app(self) -> bool:
        """Switch to next application"""
        try:
            if PYAUTOGUI_AVAILABLE:
                pyautogui.hotkey('alt', 'tab')
                if self.tts:
                    self.tts.say("Switched to next app.")
                return True
            return False
        except Exception as e:
            self.logger.error(f"Error switching to next app: {e}")
            return False
    
    def switch_to_previous_app(self) -> bool:
        """Switch to previous application"""
        try:
            if PYAUTOGUI_AVAILABLE:
                pyautogui.hotkey('alt', 'shift', 'tab')
                if self.tts:
                    self.tts.say("Switched to previous app.")
                return True
            return False
        except Exception as e:
            self.logger.error(f"Error switching to previous app: {e}")
            return False
    
    def switch_to_next_tab(self) -> bool:
        """Switch to next tab in browser"""
        try:
            if PYAUTOGUI_AVAILABLE:
                pyautogui.hotkey('ctrl', 'tab')
                if self.tts:
                    self.tts.say("Switched to next tab.")
                return True
            return False
        except Exception as e:
            self.logger.error(f"Error switching to next tab: {e}")
            return False
    
    def switch_to_previous_tab(self) -> bool:
        """Switch to previous tab in browser"""
        try:
            if PYAUTOGUI_AVAILABLE:
                pyautogui.hotkey('ctrl', 'shift', 'tab')
                if self.tts:
                    self.tts.say("Switched to previous tab.")
                return True
            return False
        except Exception as e:
            self.logger.error(f"Error switching to previous tab: {e}")
            return False
    
    def switch_to_tab_number(self, tab_number: int) -> bool:
        """Switch to specific tab number (1-9)"""
        try:
            if PYAUTOGUI_AVAILABLE and 1 <= tab_number <= 9:
                pyautogui.hotkey('ctrl', str(tab_number))
                if self.tts:
                    self.tts.say(f"Switched to tab {tab_number}.")
                return True
            return False
        except Exception as e:
            self.logger.error(f"Error switching to tab number: {e}")
            return False
    
    def list_open_apps(self) -> List[str]:
        """List all open applications"""
        apps = self.get_running_apps()
        app_names = [app['name'] for app in apps]
        return app_names
    
    def list_open_tabs(self) -> List[str]:
        """List open tabs (approximate - uses window titles)"""
        windows = self.get_all_windows()
        tabs = []
        
        # Browser windows often have tab info in title
        for win in windows:
            title = win.get('title', '')
            if title:
                tabs.append(title)
        
        return tabs
    
    def _extract_app_name(self, window_title: str) -> str:
        """Extract application name from window title"""
        # Common patterns
        if ' - ' in window_title:
            return window_title.split(' - ')[-1].strip()
        elif ' | ' in window_title:
            return window_title.split(' | ')[-1].strip()
        elif ' — ' in window_title:
            return window_title.split(' — ')[-1].strip()
        
        # Try to extract from common patterns
        parts = window_title.split()
        if len(parts) > 0:
            return parts[0].strip()
        
        return window_title.strip()
    
    def _is_system_process(self, process_name: str) -> bool:
        """Check if process is a system process"""
        system_processes = {
            'svchost', 'winlogon', 'csrss', 'lsass', 'smss', 'wininit',
            'dwm', 'explorer', 'conhost', 'audiodg', 'spoolsv', 'services',
            'system', 'dwm', 'winlogon', 'csrss', 'lsass'
        }
        return process_name.lower() in system_processes
    
    def get_active_window(self) -> Optional[Dict[str, Any]]:
        """Get currently active window"""
        try:
            if WINDOW_MANAGEMENT_AVAILABLE:
                active = gw.getActiveWindow()
                if active:
                    return {
                        'title': active.title,
                        'app_name': self._extract_app_name(active.title),
                        'rect': (active.left, active.top, active.width, active.height)
                    }
        except Exception as e:
            self.logger.error(f"Error getting active window: {e}")
        
        return None

