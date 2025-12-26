"""
Context-Aware Command Parser for EchoOS
Understands current screen state and provides intelligent command parsing
"""

import re
import logging
from typing import Optional, Dict, List, Any
from rapidfuzz import fuzz, process

from .ui_automation import UniversalUIAutomator, UIElement, ScreenContext

class ContextAwareParser:
    """Context-aware command parser that understands current screen state"""
    
    def __init__(self, tts, ui_automator: UniversalUIAutomator):
        self.tts = tts
        self.ui_automator = ui_automator
        self.logger = logging.getLogger(__name__)
        self.current_context = None
        
        # Command patterns for different contexts
        self.context_patterns = {
            'file_explorer': {
                'navigate': ['open', 'go to', 'enter', 'navigate to'],
                'create': ['create folder', 'new folder', 'make folder'],
                'delete': ['delete', 'remove', 'trash'],
                'rename': ['rename', 'change name'],
                'select': ['select', 'choose', 'pick'],
                'copy': ['copy', 'duplicate'],
                'paste': ['paste', 'paste here'],
                'cut': ['cut', 'move'],
                'view': ['view', 'show', 'display']
            },
            'browser': {
                'navigate': ['go to', 'open', 'visit', 'navigate to'],
                'search': ['search', 'find', 'look for'],
                'bookmark': ['bookmark', 'save', 'favorite'],
                'tab': ['new tab', 'close tab', 'switch tab', 'next tab', 'previous tab'],
                'refresh': ['refresh', 'reload', 'refresh page'],
                'back': ['go back', 'back', 'previous page'],
                'forward': ['go forward', 'forward', 'next page'],
                'scroll': ['scroll up', 'scroll down', 'scroll']
            },
            'text_editor': {
                'save': ['save', 'save file', 'save as'],
                'open': ['open', 'open file', 'open document'],
                'new': ['new', 'new file', 'new document'],
                'find': ['find', 'search', 'find text'],
                'replace': ['replace', 'find and replace'],
                'select': ['select all', 'select text', 'highlight'],
                'copy': ['copy', 'copy text'],
                'paste': ['paste', 'paste text'],
                'cut': ['cut', 'cut text'],
                'format': ['bold', 'italic', 'underline', 'format']
            },
            'system': {
                'control': ['shutdown', 'restart', 'sleep', 'hibernate'],
                'lock': ['lock screen', 'lock computer'],
                'logout': ['logout', 'sign out', 'log out'],
                'volume': ['volume up', 'volume down', 'mute', 'unmute'],
                'brightness': ['brightness up', 'brightness down'],
                'wifi': ['wifi', 'internet', 'network']
            }
        }
        
        # Generic patterns that work in any context
        self.generic_patterns = {
            'click': ['click', 'tap', 'press'],
            'double_click': ['double click', 'double tap'],
            'right_click': ['right click', 'context menu'],
            'type': ['type', 'enter', 'input', 'write'],
            'scroll': ['scroll up', 'scroll down', 'scroll'],
            'zoom': ['zoom in', 'zoom out'],
            'select': ['select', 'choose', 'pick'],
            'close': ['close', 'exit', 'quit'],
            'minimize': ['minimize', 'minimize window'],
            'maximize': ['maximize', 'maximize window'],
            'switch': ['switch', 'change', 'alt tab']
        }
    
    def parse_command(self, voice_text: str) -> Optional[Dict[str, Any]]:
        """Parse voice command with context awareness"""
        try:
            # Normalize input
            text = voice_text.lower().strip()
            
            # Try to analyze current screen context
            try:
                self.current_context = self.ui_automator.analyze_screen()
                context_type = self._determine_context_type()
                
                # Parse based on context
                if context_type == 'file_explorer':
                    return self._parse_file_explorer_command(text)
                elif context_type == 'browser':
                    return self._parse_browser_command(text)
                elif context_type == 'text_editor':
                    return self._parse_text_editor_command(text)
                elif context_type == 'system':
                    return self._parse_system_command(text)
                else:
                    return self._parse_generic_command(text)
                    
            except Exception as ui_error:
                # Silently fall back to original parser without logging
                return self._fallback_to_original_parser(text)
                
        except Exception as e:
            self.logger.error(f"Error parsing command: {e}")
            return None
    
    def _fallback_to_original_parser(self, text: str) -> Optional[Dict[str, Any]]:
        """Fallback to original parser when UI automation fails"""
        try:
            # Import and use the original parser
            from .parser import CommandParser
            original_parser = CommandParser(self.tts)
            return original_parser.parse(text, [])
        except Exception as e:
            self.logger.error(f"Fallback parser failed: {e}")
            return None
    
    def _determine_context_type(self) -> str:
        """Determine current context type based on active application"""
        if not self.current_context or not self.current_context.active_window:
            return 'generic'
        
        app_name = self.current_context.active_window.get('app_name', '').lower()
        window_title = self.current_context.active_window.get('title', '').lower()
        
        # File Explorer contexts - universal keywords
        file_explorer_keywords = ['explorer', 'finder', 'files', 'file manager', 'nautilus', 'dolphin', 'thunar']
        if any(keyword in app_name or keyword in window_title for keyword in file_explorer_keywords):
            return 'file_explorer'
        
        # Browser contexts - universal keywords
        browser_keywords = ['chrome', 'firefox', 'edge', 'safari', 'browser', 'opera', 'brave', 'vivaldi', 'chromium']
        if any(keyword in app_name or keyword in window_title for keyword in browser_keywords):
            return 'browser'
        
        # Text Editor contexts - universal keywords
        text_editor_keywords = ['notepad', 'textedit', 'vim', 'code', 'sublime', 'atom', 'gedit', 'kate', 'mousepad', 'word', 'libreoffice writer']
        if any(keyword in app_name or keyword in window_title for keyword in text_editor_keywords):
            return 'text_editor'
        
        # Spreadsheet contexts
        spreadsheet_keywords = ['excel', 'calc', 'numbers', 'libreoffice calc']
        if any(keyword in app_name or keyword in window_title for keyword in spreadsheet_keywords):
            return 'spreadsheet'
        
        # Presentation contexts
        presentation_keywords = ['powerpoint', 'impress', 'keynote', 'libreoffice impress']
        if any(keyword in app_name or keyword in window_title for keyword in presentation_keywords):
            return 'presentation'
        
        # System contexts (when no specific app is active)
        system_keywords = ['desktop', 'taskbar', 'dock', 'panel']
        if any(keyword in app_name or keyword in window_title for keyword in system_keywords):
            return 'system'
        
        return 'generic'
    
    def _parse_file_explorer_command(self, text: str) -> Optional[Dict[str, Any]]:
        """Parse file explorer specific commands"""
        patterns = self.context_patterns['file_explorer']
        
        # Navigation commands
        if any(pattern in text for pattern in patterns['navigate']):
            target = self._extract_target(text, patterns['navigate'])
            return {
                'action': 'navigate_folder',
                'target': target,
                'context': 'file_explorer'
            }
        
        # Create folder
        if any(pattern in text for pattern in patterns['create']):
            folder_name = self._extract_folder_name(text)
            return {
                'action': 'create_folder',
                'name': folder_name,
                'context': 'file_explorer'
            }
        
        # Delete
        if any(pattern in text for pattern in patterns['delete']):
            target = self._extract_target(text, patterns['delete'])
            return {
                'action': 'delete_item',
                'target': target,
                'context': 'file_explorer'
            }
        
        # Rename
        if any(pattern in text for pattern in patterns['rename']):
            new_name = self._extract_new_name(text)
            return {
                'action': 'rename_item',
                'new_name': new_name,
                'context': 'file_explorer'
            }
        
        # Select
        if any(pattern in text for pattern in patterns['select']):
            target = self._extract_target(text, patterns['select'])
            return {
                'action': 'select_item',
                'target': target,
                'context': 'file_explorer'
            }
        
        # Copy
        if any(pattern in text for pattern in patterns['copy']):
            target = self._extract_target(text, patterns['copy'])
            return {
                'action': 'copy_item',
                'target': target,
                'context': 'file_explorer'
            }
        
        # Paste
        if any(pattern in text for pattern in patterns['paste']):
            return {
                'action': 'paste_item',
                'context': 'file_explorer'
            }
        
        # Cut
        if any(pattern in text for pattern in patterns['cut']):
            target = self._extract_target(text, patterns['cut'])
            return {
                'action': 'cut_item',
                'target': target,
                'context': 'file_explorer'
            }
        
        return self._parse_generic_command(text)
    
    def _parse_browser_command(self, text: str) -> Optional[Dict[str, Any]]:
        """Parse browser specific commands"""
        patterns = self.context_patterns['browser']
        
        # Navigation
        if any(pattern in text for pattern in patterns['navigate']):
            url = self._extract_url(text)
            return {
                'action': 'navigate_url',
                'url': url,
                'context': 'browser'
            }
        
        # Search
        if any(pattern in text for pattern in patterns['search']):
            query = self._extract_search_query(text)
            return {
                'action': 'search_query',
                'query': query,
                'context': 'browser'
            }
        
        # Tab operations
        if any(pattern in text for pattern in patterns['tab']):
            if 'new tab' in text:
                return {'action': 'new_tab', 'context': 'browser'}
            elif 'close tab' in text:
                return {'action': 'close_tab', 'context': 'browser'}
            elif 'next tab' in text:
                return {'action': 'next_tab', 'context': 'browser'}
            elif 'previous tab' in text:
                return {'action': 'previous_tab', 'context': 'browser'}
        
        # Navigation
        if any(pattern in text for pattern in patterns['back']):
            return {'action': 'go_back', 'context': 'browser'}
        elif any(pattern in text for pattern in patterns['forward']):
            return {'action': 'go_forward', 'context': 'browser'}
        elif any(pattern in text for pattern in patterns['refresh']):
            return {'action': 'refresh_page', 'context': 'browser'}
        
        # Bookmark
        if any(pattern in text for pattern in patterns['bookmark']):
            return {'action': 'bookmark_page', 'context': 'browser'}
        
        return self._parse_generic_command(text)
    
    def _parse_text_editor_command(self, text: str) -> Optional[Dict[str, Any]]:
        """Parse text editor specific commands"""
        patterns = self.context_patterns['text_editor']
        
        # Save
        if any(pattern in text for pattern in patterns['save']):
            if 'save as' in text:
                filename = self._extract_filename(text)
                return {
                    'action': 'save_as',
                    'filename': filename,
                    'context': 'text_editor'
                }
            else:
                return {'action': 'save_file', 'context': 'text_editor'}
        
        # Open
        if any(pattern in text for pattern in patterns['open']):
            filename = self._extract_filename(text)
            return {
                'action': 'open_file',
                'filename': filename,
                'context': 'text_editor'
            }
        
        # New
        if any(pattern in text for pattern in patterns['new']):
            return {'action': 'new_file', 'context': 'text_editor'}
        
        # Find
        if any(pattern in text for pattern in patterns['find']):
            search_text = self._extract_search_text(text)
            return {
                'action': 'find_text',
                'search_text': search_text,
                'context': 'text_editor'
            }
        
        # Replace
        if any(pattern in text for pattern in patterns['replace']):
            return {'action': 'find_replace', 'context': 'text_editor'}
        
        # Select all
        if 'select all' in text:
            return {'action': 'select_all', 'context': 'text_editor'}
        
        # Copy/Cut/Paste
        if 'copy' in text:
            return {'action': 'copy_text', 'context': 'text_editor'}
        elif 'cut' in text:
            return {'action': 'cut_text', 'context': 'text_editor'}
        elif 'paste' in text:
            return {'action': 'paste_text', 'context': 'text_editor'}
        
        return self._parse_generic_command(text)
    
    def _parse_system_command(self, text: str) -> Optional[Dict[str, Any]]:
        """Parse system specific commands"""
        patterns = self.context_patterns['system']
        
        # System control
        if any(pattern in text for pattern in patterns['control']):
            if 'shutdown' in text:
                return {'action': 'shutdown', 'context': 'system'}
            elif 'restart' in text:
                return {'action': 'restart', 'context': 'system'}
            elif 'sleep' in text:
                return {'action': 'sleep', 'context': 'system'}
            elif 'hibernate' in text:
                return {'action': 'hibernate', 'context': 'system'}
        
        # Lock
        if any(pattern in text for pattern in patterns['lock']):
            return {'action': 'lock_screen', 'context': 'system'}
        
        # Logout
        if any(pattern in text for pattern in patterns['logout']):
            return {'action': 'logout', 'context': 'system'}
        
        # Volume
        if any(pattern in text for pattern in patterns['volume']):
            if 'volume up' in text:
                return {'action': 'volume_up', 'context': 'system'}
            elif 'volume down' in text:
                return {'action': 'volume_down', 'context': 'system'}
            elif 'mute' in text:
                return {'action': 'mute', 'context': 'system'}
            elif 'unmute' in text:
                return {'action': 'unmute', 'context': 'system'}
        
        return self._parse_generic_command(text)
    
    def _parse_generic_command(self, text: str) -> Optional[Dict[str, Any]]:
        """Parse generic commands that work in any context"""
        patterns = self.generic_patterns
        
        # Click operations
        if any(pattern in text for pattern in patterns['click']):
            target = self._extract_target(text, patterns['click'])
            return {
                'action': 'click_element',
                'target': target,
                'context': 'generic'
            }
        
        # Double click
        if any(pattern in text for pattern in patterns['double_click']):
            target = self._extract_target(text, patterns['double_click'])
            return {
                'action': 'double_click_element',
                'target': target,
                'context': 'generic'
            }
        
        # Right click
        if any(pattern in text for pattern in patterns['right_click']):
            target = self._extract_target(text, patterns['right_click'])
            return {
                'action': 'right_click_element',
                'target': target,
                'context': 'generic'
            }
        
        # Type
        if any(pattern in text for pattern in patterns['type']):
            text_to_type = self._extract_text_to_type(text)
            return {
                'action': 'type_text',
                'text': text_to_type,
                'context': 'generic'
            }
        
        # Scroll
        if any(pattern in text for pattern in patterns['scroll']):
            direction = 'down' if 'down' in text else 'up'
            return {
                'action': 'scroll',
                'direction': direction,
                'context': 'generic'
            }
        
        # Zoom
        if any(pattern in text for pattern in patterns['zoom']):
            direction = 'in' if 'in' in text else 'out'
            return {
                'action': 'zoom',
                'direction': direction,
                'context': 'generic'
            }
        
        # Close
        if any(pattern in text for pattern in patterns['close']):
            return {'action': 'close_window', 'context': 'generic'}
        
        # Minimize/Maximize
        if any(pattern in text for pattern in patterns['minimize']):
            return {'action': 'minimize_window', 'context': 'generic'}
        elif any(pattern in text for pattern in patterns['maximize']):
            return {'action': 'maximize_window', 'context': 'generic'}
        
        # Switch
        if any(pattern in text for pattern in patterns['switch']):
            return {'action': 'switch_window', 'context': 'generic'}
        
        return None
    
    def _extract_target(self, text: str, patterns: List[str]) -> str:
        """Extract target from command text"""
        for pattern in patterns:
            if pattern in text:
                # Remove the pattern and clean up
                target = text.replace(pattern, '').strip()
                # Remove common words
                target = re.sub(r'\b(the|a|an|this|that)\b', '', target).strip()
                return target
        return ""
    
    def _extract_folder_name(self, text: str) -> str:
        """Extract folder name from create folder command"""
        # Look for "called" or "named" patterns
        if 'called' in text:
            return text.split('called')[-1].strip()
        elif 'named' in text:
            return text.split('named')[-1].strip()
        else:
            # Extract after "folder" or "directory"
            parts = text.split()
            for i, part in enumerate(parts):
                if 'folder' in part or 'directory' in part:
                    if i + 1 < len(parts):
                        return ' '.join(parts[i+1:])
        return "New Folder"
    
    def _extract_new_name(self, text: str) -> str:
        """Extract new name from rename command"""
        if 'to' in text:
            return text.split('to')[-1].strip()
        elif 'as' in text:
            return text.split('as')[-1].strip()
        return ""
    
    def _extract_url(self, text: str) -> str:
        """Extract URL from navigation command"""
        # Look for common URL patterns
        url_pattern = r'https?://[^\s]+'
        match = re.search(url_pattern, text)
        if match:
            return match.group()
        
        # Extract after navigation words
        nav_words = ['to', 'visit', 'open', 'go to', 'navigate to']
        for word in nav_words:
            if word in text:
                url = text.split(word)[-1].strip()
                if url and not url.startswith('http'):
                    url = 'https://' + url
                return url
        
        return ""
    
    def _extract_search_query(self, text: str) -> str:
        """Extract search query from search command"""
        search_words = ['search', 'find', 'look for']
        for word in search_words:
            if word in text:
                query = text.split(word)[-1].strip()
                # Remove common words
                query = re.sub(r'\b(for|about|the|a|an)\b', '', query).strip()
                return query
        return ""
    
    def _extract_filename(self, text: str) -> str:
        """Extract filename from file operations"""
        if 'as' in text:
            return text.split('as')[-1].strip()
        elif 'to' in text:
            return text.split('to')[-1].strip()
        return ""
    
    def _extract_search_text(self, text: str) -> str:
        """Extract text to search for"""
        if 'for' in text:
            return text.split('for')[-1].strip()
        return ""
    
    def _extract_text_to_type(self, text: str) -> str:
        """Extract text to type from type command"""
        type_words = ['type', 'enter', 'input', 'write']
        for word in type_words:
            if word in text:
                text_to_type = text.split(word)[-1].strip()
                # Remove quotes if present
                text_to_type = text_to_type.strip('"\'')
                return text_to_type
        return ""
    
    def get_available_commands(self) -> List[str]:
        """Get list of available commands for current context"""
        if not self.current_context:
            return []
        
        context_type = self._determine_context_type()
        commands = []
        
        # Add context-specific commands
        if context_type in self.context_patterns:
            patterns = self.context_patterns[context_type]
            for category, pattern_list in patterns.items():
                commands.extend(pattern_list)
        
        # Add generic commands
        for category, pattern_list in self.generic_patterns.items():
            commands.extend(pattern_list)
        
        return list(set(commands))  # Remove duplicates
    
    def get_context_info(self) -> Dict[str, Any]:
        """Get current context information"""
        if not self.current_context:
            return {}
        
        return {
            'active_window': self.current_context.active_window,
            'context_type': self._determine_context_type(),
            'available_commands': len(self.get_available_commands()),
            'ui_elements': len(self.current_context.screen_elements),
            'has_text': bool(self.current_context.current_text.strip())
        }
    
    def parse(self, voice_text: str, apps=None) -> Optional[Dict[str, Any]]:
        """Compatibility method for legacy parser interface"""
        return self.parse_command(voice_text)