"""
Universal Keybinding System for EchoOS
Provides cross-platform keyboard shortcuts that adapt to any OS and application
"""

import platform
import logging
from typing import Dict, List, Optional, Tuple
from enum import Enum

class KeyModifier(Enum):
    CTRL = "ctrl"
    ALT = "alt"
    SHIFT = "shift"
    CMD = "cmd"  # macOS Command key
    WIN = "win"  # Windows key
    META = "meta"  # Generic meta key

class UniversalKeybindings:
    """Universal keybinding system that adapts to any platform and application"""
    
    def __init__(self):
        self.system = platform.system().lower()
        self.logger = logging.getLogger(__name__)
        
        # Platform-specific key mappings
        self.platform_keys = self._initialize_platform_keys()
        
        # Application-specific keybinding overrides
        self.app_overrides = {}
        
        # Universal shortcuts that work across platforms
        self.universal_shortcuts = {
            # File operations
            "save": ["ctrl+s", "cmd+s"],
            "save_as": ["ctrl+shift+s", "cmd+shift+s"],
            "open": ["ctrl+o", "cmd+o"],
            "new": ["ctrl+n", "cmd+n"],
            "close": ["ctrl+w", "cmd+w"],
            "close_window": ["alt+f4", "cmd+q", "alt+f4"],
            
            # Edit operations
            "copy": ["ctrl+c", "cmd+c"],
            "paste": ["ctrl+v", "cmd+v"],
            "cut": ["ctrl+x", "cmd+x"],
            "undo": ["ctrl+z", "cmd+z"],
            "redo": ["ctrl+y", "cmd+shift+z"],
            "select_all": ["ctrl+a", "cmd+a"],
            
            # Find operations
            "find": ["ctrl+f", "cmd+f"],
            "find_replace": ["ctrl+h", "cmd+shift+f"],
            "find_next": ["f3", "cmd+g"],
            
            # Navigation
            "back": ["alt+left", "cmd+left"],
            "forward": ["alt+right", "cmd+right"],
            "refresh": ["f5", "cmd+r"],
            "home": ["ctrl+home", "cmd+up"],
            "end": ["ctrl+end", "cmd+down"],
            
            # Tab operations
            "new_tab": ["ctrl+t", "cmd+t"],
            "close_tab": ["ctrl+w", "cmd+w"],
            "next_tab": ["ctrl+tab", "cmd+shift+]"],
            "previous_tab": ["ctrl+shift+tab", "cmd+shift+["],
            
            # Window operations
            "minimize": ["alt+space+n", "cmd+m"],
            "maximize": ["alt+space+x", "cmd+ctrl+f"],
            "switch_window": ["alt+tab", "cmd+tab"],
            
            # Zoom operations
            "zoom_in": ["ctrl+plus", "cmd+plus", "ctrl+="],
            "zoom_out": ["ctrl+minus", "cmd+minus"],
            "zoom_reset": ["ctrl+0", "cmd+0"],
            
            # System operations
            "lock_screen": ["win+l", "ctrl+cmd+q"],
            "task_manager": ["ctrl+shift+esc", "cmd+option+esc"],
            "run_dialog": ["win+r", "cmd+space"],
            
            # Browser specific
            "address_bar": ["ctrl+l", "cmd+l"],
            "search": ["ctrl+k", "cmd+k"],
            "bookmark": ["ctrl+d", "cmd+d"],
            "bookmark_manager": ["ctrl+shift+o", "cmd+option+b"],
            
            # Text operations
            "bold": ["ctrl+b", "cmd+b"],
            "italic": ["ctrl+i", "cmd+i"],
            "underline": ["ctrl+u", "cmd+u"],
            
            # Accessibility
            "screen_reader": ["win+enter", "cmd+f5"],
            "magnifier": ["win+plus", "cmd+option+plus"],
        }
    
    def _initialize_platform_keys(self) -> Dict[str, str]:
        """Initialize platform-specific key mappings"""
        if self.system == "windows":
            return {
                "ctrl": "ctrl",
                "alt": "alt",
                "shift": "shift",
                "win": "win",
                "meta": "win"
            }
        elif self.system == "darwin":  # macOS
            return {
                "ctrl": "ctrl",
                "alt": "alt",
                "shift": "shift",
                "cmd": "cmd",
                "meta": "cmd"
            }
        else:  # Linux
            return {
                "ctrl": "ctrl",
                "alt": "alt",
                "shift": "shift",
                "meta": "alt"
            }
    
    def get_shortcut(self, action: str, app_name: str = None) -> Optional[str]:
        """Get the appropriate shortcut for an action, considering app and platform"""
        # Check for app-specific overrides first
        if app_name and app_name.lower() in self.app_overrides:
            app_shortcuts = self.app_overrides[app_name.lower()]
            if action in app_shortcuts:
                return self._adapt_to_platform(app_shortcuts[action])
        
        # Use universal shortcuts
        if action in self.universal_shortcuts:
            shortcuts = self.universal_shortcuts[action]
            return self._select_best_shortcut(shortcuts)
        
        # Return None if no shortcut found
        return None
    
    def _adapt_to_platform(self, shortcut: str) -> str:
        """Adapt a shortcut to the current platform"""
        if self.system == "windows":
            # Convert cmd to ctrl for Windows
            return shortcut.replace("cmd+", "ctrl+").replace("cmd", "ctrl")
        elif self.system == "darwin":
            # Convert ctrl to cmd for macOS where appropriate
            if shortcut.startswith("ctrl+") and not any(x in shortcut for x in ["ctrl+shift", "ctrl+alt"]):
                return shortcut.replace("ctrl+", "cmd+", 1)
            return shortcut
        else:  # Linux
            # Keep ctrl, convert cmd to ctrl
            return shortcut.replace("cmd+", "ctrl+").replace("cmd", "ctrl")
    
    def _select_best_shortcut(self, shortcuts: List[str]) -> str:
        """Select the best shortcut for the current platform"""
        if self.system == "windows":
            # Prefer Windows-specific shortcuts
            for shortcut in shortcuts:
                if "win+" in shortcut or ("ctrl+" in shortcut and "cmd+" not in shortcut):
                    return shortcut
        elif self.system == "darwin":
            # Prefer macOS-specific shortcuts
            for shortcut in shortcuts:
                if "cmd+" in shortcut:
                    return shortcut
        else:  # Linux
            # Prefer Linux-compatible shortcuts
            for shortcut in shortcuts:
                if "ctrl+" in shortcut and "cmd+" not in shortcut:
                    return shortcut
        
        # Fallback to first shortcut
        return shortcuts[0] if shortcuts else ""
    
    def register_app_shortcuts(self, app_name: str, shortcuts: Dict[str, str]):
        """Register app-specific shortcuts"""
        self.app_overrides[app_name.lower()] = shortcuts
        self.logger.info(f"Registered {len(shortcuts)} shortcuts for {app_name}")
    
    def get_app_specific_shortcut(self, app_name: str, action: str) -> Optional[str]:
        """Get app-specific shortcut if available"""
        app_name = app_name.lower()
        if app_name in self.app_overrides and action in self.app_overrides[app_name]:
            return self._adapt_to_platform(self.app_overrides[app_name][action])
        return None
    
    def discover_app_shortcuts(self, app_name: str) -> Dict[str, str]:
        """Attempt to discover shortcuts for a specific application"""
        app_name = app_name.lower()
        discovered = {}
        
        # Common application-specific shortcuts
        app_shortcuts = {
            "chrome": {
                "new_tab": "ctrl+t",
                "close_tab": "ctrl+w",
                "new_window": "ctrl+n",
                "incognito": "ctrl+shift+n",
                "history": "ctrl+h",
                "downloads": "ctrl+j",
                "bookmark_manager": "ctrl+shift+o",
                "developer_tools": "f12",
                "inspect": "ctrl+shift+i"
            },
            "firefox": {
                "new_tab": "ctrl+t",
                "close_tab": "ctrl+w",
                "new_window": "ctrl+n",
                "private_window": "ctrl+shift+p",
                "history": "ctrl+shift+h",
                "downloads": "ctrl+shift+y",
                "bookmark_manager": "ctrl+shift+o",
                "developer_tools": "f12",
                "inspect": "ctrl+shift+i"
            },
            "edge": {
                "new_tab": "ctrl+t",
                "close_tab": "ctrl+w",
                "new_window": "ctrl+n",
                "inprivate": "ctrl+shift+n",
                "history": "ctrl+h",
                "downloads": "ctrl+j",
                "favorites": "ctrl+shift+o",
                "developer_tools": "f12",
                "inspect": "ctrl+shift+i"
            },
            "notepad": {
                "find": "ctrl+f",
                "find_next": "f3",
                "replace": "ctrl+h",
                "go_to": "ctrl+g",
                "time_date": "f5",
                "word_wrap": "ctrl+w"
            },
            "word": {
                "bold": "ctrl+b",
                "italic": "ctrl+i",
                "underline": "ctrl+u",
                "font_dialog": "ctrl+d",
                "paragraph_dialog": "alt+o+p",
                "page_setup": "alt+f+u",
                "print_preview": "ctrl+f2",
                "spell_check": "f7"
            },
            "excel": {
                "new_workbook": "ctrl+n",
                "open_workbook": "ctrl+o",
                "save_workbook": "ctrl+s",
                "print": "ctrl+p",
                "cut": "ctrl+x",
                "copy": "ctrl+c",
                "paste": "ctrl+v",
                "undo": "ctrl+z",
                "redo": "ctrl+y",
                "find": "ctrl+f",
                "replace": "ctrl+h",
                "go_to": "ctrl+g",
                "spell_check": "f7"
            },
            "powerpoint": {
                "new_slide": "ctrl+m",
                "duplicate_slide": "ctrl+shift+d",
                "delete_slide": "delete",
                "slide_show": "f5",
                "slide_show_from_current": "shift+f5",
                "end_slide_show": "esc",
                "next_slide": "page down",
                "previous_slide": "page up"
            },
            "explorer": {
                "new_folder": "ctrl+shift+n",
                "rename": "f2",
                "delete": "delete",
                "permanent_delete": "shift+delete",
                "properties": "alt+enter",
                "refresh": "f5",
                "view_large_icons": "ctrl+shift+1",
                "view_details": "ctrl+shift+7",
                "view_list": "ctrl+shift+2",
                "view_tiles": "ctrl+shift+3"
            }
        }
        
        if app_name in app_shortcuts:
            discovered = app_shortcuts[app_name].copy()
            self.register_app_shortcuts(app_name, discovered)
        
        return discovered
    
    def get_all_shortcuts_for_app(self, app_name: str) -> Dict[str, str]:
        """Get all available shortcuts for an application"""
        app_name = app_name.lower()
        all_shortcuts = {}
        
        # Add universal shortcuts
        for action, shortcuts in self.universal_shortcuts.items():
            shortcut = self._select_best_shortcut(shortcuts)
            if shortcut:
                all_shortcuts[action] = shortcut
        
        # Add app-specific shortcuts
        app_shortcuts = self.discover_app_shortcuts(app_name)
        all_shortcuts.update(app_shortcuts)
        
        return all_shortcuts
    
    def is_shortcut_available(self, action: str, app_name: str = None) -> bool:
        """Check if a shortcut is available for an action"""
        return self.get_shortcut(action, app_name) is not None
    
    def get_alternative_shortcuts(self, action: str) -> List[str]:
        """Get all alternative shortcuts for an action"""
        if action in self.universal_shortcuts:
            return [self._adapt_to_platform(s) for s in self.universal_shortcuts[action]]
        return []
    
    def get_platform_info(self) -> Dict[str, str]:
        """Get information about the current platform's key system"""
        return {
            "platform": self.system,
            "primary_modifier": self.platform_keys.get("meta", "ctrl"),
            "secondary_modifier": self.platform_keys.get("ctrl", "ctrl"),
            "alt_key": self.platform_keys.get("alt", "alt"),
            "shift_key": self.platform_keys.get("shift", "shift")
        }
    
    def validate_shortcut(self, shortcut: str) -> bool:
        """Validate if a shortcut format is correct"""
        if not shortcut:
            return False
        
        # Basic validation - should contain at least one key
        parts = shortcut.split('+')
        if len(parts) < 1:
            return False
        
        # Check if modifiers are valid
        valid_modifiers = ['ctrl', 'alt', 'shift', 'cmd', 'win', 'meta']
        for part in parts[:-1]:  # All except the last should be modifiers
            if part.lower() not in valid_modifiers:
                return False
        
        return True
    
    def normalize_shortcut(self, shortcut: str) -> str:
        """Normalize a shortcut to standard format"""
        if not shortcut:
            return ""
        
        # Convert to lowercase and split
        parts = [part.strip().lower() for part in shortcut.split('+')]
        
        # Sort modifiers
        modifiers = []
        key = ""
        
        for part in parts:
            if part in ['ctrl', 'alt', 'shift', 'cmd', 'win', 'meta']:
                modifiers.append(part)
            else:
                key = part
        
        # Reconstruct shortcut
        if key:
            return '+'.join(sorted(modifiers) + [key])
        
        return shortcut
