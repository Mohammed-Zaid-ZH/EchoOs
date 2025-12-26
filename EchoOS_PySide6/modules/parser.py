import random
import re
import os
from rapidfuzz import fuzz
from pathlib import Path

class CommandParser:
    def __init__(self, tts, commands_file="config/commands.json"):
        self.tts = tts
        self.commands_file = commands_file
        self.command_patterns = self.load_command_patterns()
        self.current_directory = os.getcwd()

    def load_command_patterns(self):
        """Load command patterns from configuration file"""
        try:
            import json
            if os.path.exists(self.commands_file):
                with open(self.commands_file, 'r') as f:
                    data = json.load(f)
                    # Check if it's the new format with system_control key
                    if "system_control" in data:
                        return data
                    else:
                        # It's the old format, ignore it and use defaults
                        print(f"Old format commands.json detected, using default patterns")
                        pass
        except Exception as e:
            print(f"Error loading command patterns: {e}")
        
        # Default command patterns
        return {
            "system_control": [
                "shutdown", "restart", "sleep", "hibernate", "lock screen", "log out",
                "go to sleep", "stop listening", "pause", "resume", "wake up", "start listening"
            ],
            "file_operations": [
                "open file", "create file", "delete file", "copy file", "move file", "rename file",
                "list files", "show files", "navigate to", "go to folder", "create folder", "delete folder",
                "open file explorer", "file explorer", "save file"
            ],
            "application_control": [
                "open app", "launch", "start", "go to", "switch to", "bring to front",
                "close app", "close all tabs", "close all windows", 
                "close browser tabs", "close chrome tabs", "close firefox tabs", "close edge tabs",
                "close paint", "close word", "close excel", "close powerpoint", "close notepad",
                "minimize", "maximize", "switch app", "new tab", "new window",
                "open chrome", "open firefox", "open edge", "open notepad", "open paint"
            ],
            "web_operations": [
                "open website", "search google", "search youtube", "search amazon", "search swiggy",
                "open gmail", "open facebook", "open twitter", "open instagram"
            ],
            "system_info": [
                "system info", "battery status", "disk space", "memory usage", "cpu usage",
                "network status", "wifi status", "bluetooth status", "volume up", "volume down", "mute"
            ],
            "accessibility": [
                "read screen", "describe screen", "navigate", "click", "double click", "right click",
                "scroll up", "scroll down", "zoom in", "zoom out", "high contrast", "large text"
            ]
        }

    def parse(self, text, apps=None):
        """Parse voice command and return action dictionary"""
        text = text.lower().strip()
        
        # System control commands
        if any(w in text for w in self.command_patterns["system_control"]):
            return self._parse_system_control(text)
        
        # File operation commands
        if any(w in text for w in self.command_patterns["file_operations"]):
            return self._parse_file_operations(text)
        
        # Application control commands
        if any(w in text for w in self.command_patterns["application_control"]):
            return self._parse_application_control(text, apps or [])
        
        # Web operation commands
        if any(w in text for w in self.command_patterns["web_operations"]):
            return self._parse_web_operations(text)
        
        # System information commands
        if any(w in text for w in self.command_patterns["system_info"]):
            return self._parse_system_info(text)
        
        # Accessibility commands
        if any(w in text for w in self.command_patterns["accessibility"]):
            return self._parse_accessibility(text)
        
        # Generic app matching
        if apps:
            app_match = self._match_application(text, apps)
            if app_match:
                return app_match
        
        # Unknown command
        return self._handle_unknown_command(text)

    def _parse_system_control(self, text):
        """Parse system control commands"""
        if any(w in text for w in ["shutdown", "shut down"]):
            return {"action": "shutdown", "confirm": True}
        elif any(w in text for w in ["restart", "reboot"]):
            return {"action": "restart", "confirm": True}
        elif any(w in text for w in ["sleep", "go to sleep", "hibernate"]):
            return {"action": "sleep"}
        elif any(w in text for w in ["lock screen", "lock"]):
            return {"action": "lock_screen"}
        elif any(w in text for w in ["log out", "logout"]):
            return {"action": "logout"}
        elif any(w in text for w in ["wake up", "start listening", "resume"]):
            return {"action": "wake"}
        elif any(w in text for w in ["stop listening", "pause"]):
            return {"action": "pause_listening"}
        return None

    def _parse_file_operations(self, text):
        """Parse file operation commands"""
        if "open file" in text:
            filename = self._extract_filename(text)
            return {"action": "open_file", "filename": filename}
        elif "create file" in text:
            filename = self._extract_filename(text)
            return {"action": "create_file", "filename": filename}
        elif "delete file" in text:
            filename = self._extract_filename(text)
            return {"action": "delete_file", "filename": filename, "confirm": True}
        elif "copy file" in text:
            files = self._extract_filenames(text)
            return {"action": "copy_file", "source": files[0] if files else None, "destination": files[1] if len(files) > 1 else None}
        elif "move file" in text:
            files = self._extract_filenames(text)
            return {"action": "move_file", "source": files[0] if files else None, "destination": files[1] if len(files) > 1 else None}
        elif "rename file" in text:
            files = self._extract_filenames(text)
            return {"action": "rename_file", "old_name": files[0] if files else None, "new_name": files[1] if len(files) > 1 else None}
        elif any(w in text for w in ["list files", "show files", "ls"]):
            return {"action": "list_files", "directory": self._extract_directory(text)}
        elif any(w in text for w in ["navigate to", "go to folder", "cd"]):
            directory = self._extract_directory(text)
            return {"action": "change_directory", "directory": directory}
        elif "create folder" in text:
            folder_name = self._extract_filename(text)
            return {"action": "create_folder", "folder_name": folder_name}
        elif "delete folder" in text:
            folder_name = self._extract_filename(text)
            return {"action": "delete_folder", "folder_name": folder_name, "confirm": True}
        elif "save file" in text:
            return {"action": "save_file"}
        elif any(w in text for w in ["open file explorer", "file explorer"]):
            return {"action": "open_file_explorer"}
        return None

    def _parse_application_control(self, text, apps):
        """Parse application control commands"""
        # Close all applications
        if any(w in text for w in ["close all tabs", "close all windows", "close everything"]):
            return {"action": "close_all_apps"}
        
        # Close specific browser tabs
        elif "close chrome tabs" in text:
            return {"action": "close_browser_tabs", "browser": "chrome"}
        elif "close firefox tabs" in text:
            return {"action": "close_browser_tabs", "browser": "firefox"}
        elif "close edge tabs" in text:
            return {"action": "close_browser_tabs", "browser": "edge"}
        elif "close browser tabs" in text:
            return {"action": "close_browser_tabs", "browser": "all"}
        
        # Close specific applications
        elif "close paint" in text:
            return {"action": "close_specific_app", "app": "mspaint"}
        elif "close word" in text:
            return {"action": "close_specific_app", "app": "winword"}
        elif "close excel" in text:
            return {"action": "close_specific_app", "app": "excel"}
        elif "close powerpoint" in text:
            return {"action": "close_specific_app", "app": "powerpnt"}
        elif "close notepad" in text:
            return {"action": "close_specific_app", "app": "notepad"}
        
        # Open specific applications
        elif "open chrome" in text:
            return {"action": "open_app", "app": {"name": "chrome", "exec": "chrome.exe"}}
        elif "open firefox" in text:
            return {"action": "open_app", "app": {"name": "firefox", "exec": "firefox.exe"}}
        elif "open edge" in text:
            return {"action": "open_app", "app": {"name": "edge", "exec": "msedge.exe"}}
        elif "open notepad" in text:
            return {"action": "open_app", "app": {"name": "notepad", "exec": "notepad.exe"}}
        elif "open paint" in text:
            return {"action": "open_app", "app": {"name": "paint", "exec": "mspaint.exe"}}
        
        # Generic close app
        elif "close app" in text:
            app_name = self._extract_app_name(text)
            return {"action": "close_app", "app_name": app_name}
        
        # New tab/window commands
        elif "new tab" in text:
            return {"action": "new_tab"}
        elif "new window" in text:
            return {"action": "new_window"}
        
        # App switching and bringing to front
        elif any(w in text for w in ["go to", "switch to", "bring to front"]):
            app_name = self._extract_app_name(text)
            return {"action": "switch_to_app", "app_name": app_name}
        
        # Other controls
        elif any(w in text for w in ["minimize", "minimize app"]):
            app_name = self._extract_app_name(text)
            return {"action": "minimize_app", "app_name": app_name}
        elif any(w in text for w in ["maximize", "maximize app"]):
            app_name = self._extract_app_name(text)
            return {"action": "maximize_app", "app_name": app_name}
        elif "switch app" in text:
            app_name = self._extract_app_name(text)
            return {"action": "switch_app", "app_name": app_name}
        else:
            # Generic app opening
            return self._match_application(text, apps)

    def _parse_web_operations(self, text):
        """Parse web operation commands"""
        if "open website" in text:
            url = self._extract_url(text)
            return {"action": "open_website", "url": url}
        elif "search google" in text:
            query = self._extract_search_query(text, "search google")
            return {"action": "search_google", "query": query}
        elif "search youtube" in text:
            query = self._extract_search_query(text, "search youtube")
            return {"action": "search_youtube", "query": query}
        elif "search amazon" in text:
            query = self._extract_search_query(text, "search amazon")
            return {"action": "search_amazon", "query": query}
        elif "search swiggy" in text:
            query = self._extract_search_query(text, "search swiggy")
            return {"action": "search_swiggy", "query": query}
        elif any(w in text for w in ["open gmail", "gmail"]):
            return {"action": "open_website", "url": "https://gmail.com"}
        elif any(w in text for w in ["open facebook", "facebook"]):
            return {"action": "open_website", "url": "https://facebook.com"}
        elif any(w in text for w in ["open twitter", "twitter"]):
            return {"action": "open_website", "url": "https://twitter.com"}
        elif any(w in text for w in ["open instagram", "instagram"]):
            return {"action": "open_website", "url": "https://instagram.com"}
        return None

    def _parse_system_info(self, text):
        """Parse system information commands"""
        if "system info" in text:
            return {"action": "system_info"}
        elif "battery status" in text:
            return {"action": "battery_status"}
        elif "disk space" in text:
            return {"action": "disk_space"}
        elif "memory usage" in text:
            return {"action": "memory_usage"}
        elif "cpu usage" in text:
            return {"action": "cpu_usage"}
        elif "network status" in text:
            return {"action": "network_status"}
        elif "wifi status" in text:
            return {"action": "wifi_status"}
        elif "bluetooth status" in text:
            return {"action": "bluetooth_status"}
        elif "volume up" in text:
            return {"action": "volume_up"}
        elif "volume down" in text:
            return {"action": "volume_down"}
        elif "mute" in text:
            return {"action": "mute"}
        return None

    def _parse_accessibility(self, text):
        """Parse accessibility commands"""
        if any(w in text for w in ["read screen", "describe screen"]):
            return {"action": "read_screen"}
        elif "navigate" in text:
            direction = self._extract_direction(text)
            return {"action": "navigate", "direction": direction}
        elif "click" in text:
            return {"action": "click"}
        elif "double click" in text:
            return {"action": "double_click"}
        elif "right click" in text:
            return {"action": "right_click"}
        elif "scroll up" in text:
            return {"action": "scroll", "direction": "up"}
        elif "scroll down" in text:
            return {"action": "scroll", "direction": "down"}
        elif "zoom in" in text:
            return {"action": "zoom", "direction": "in"}
        elif "zoom out" in text:
            return {"action": "zoom", "direction": "out"}
        elif "high contrast" in text:
            return {"action": "toggle_high_contrast"}
        elif "large text" in text:
            return {"action": "toggle_large_text"}
        return None

    def _match_application(self, text, apps):
        """Match text to an application using advanced fuzzy matching"""
        if not apps:
            return None
            
        best_match = None
        best_score = 0
        
        # Extract potential app name from text
        words = text.lower().split()
        app_candidates = []
        
        # Try different combinations of words
        for i in range(len(words)):
            for j in range(i + 1, len(words) + 1):
                candidate = " ".join(words[i:j])
                app_candidates.append(candidate)
        
        for app in apps:
            app_name = app.get("name", "").lower()
            aliases = app.get("aliases", [])
            
            # Strategy 1: Direct substring match
            for candidate in app_candidates:
                if candidate in app_name or app_name in candidate:
                    score = len(candidate) / len(app_name) if app_name else 0
                    if score > best_score:
                        best_score = score
                        best_match = app
                
                # Strategy 2: Alias matches
                for alias in aliases:
                    if candidate in alias or alias in candidate:
                        score = len(candidate) / len(alias) if alias else 0
                if score > best_score:
                    best_score = score
                    best_match = app

                # Strategy 3: Fuzzy matching with RapidFuzz
                for alias in aliases:
                    ratio = fuzz.ratio(candidate, alias)
                    if ratio > 60 and ratio > best_score * 100:  # Convert to percentage
                        best_score = ratio / 100
                        best_match = app
                
                # Strategy 4: Partial ratio for better matching
                for alias in aliases:
                    ratio = fuzz.partial_ratio(candidate, alias)
                    if ratio > 70 and ratio > best_score * 100:
                        best_score = ratio / 100
                        best_match = app

        # Lower threshold for better app discovery
        if best_match and best_score > 0.2:  # Reduced threshold for better matching
            return {"action": "open_app", "app": best_match}
        return None

    def _extract_filename(self, text):
        """Extract filename from text"""
        # Look for patterns like "file name.txt" or "filename"
        words = text.split()
        for i, word in enumerate(words):
            if word in ["file", "folder"] and i + 1 < len(words):
                return words[i + 1]
        return None

    def _extract_filenames(self, text):
        """Extract multiple filenames from text"""
        # Simple extraction - can be enhanced
        words = text.split()
        filenames = []
        for word in words:
            if "." in word or word.isalnum():
                filenames.append(word)
        return filenames[:2]  # Return first two

    def _extract_directory(self, text):
        """Extract directory path from text"""
        # Look for directory patterns
        if "navigate to" in text:
            return text.split("navigate to")[-1].strip()
        elif "go to folder" in text:
            return text.split("go to folder")[-1].strip()
        elif "cd" in text:
            return text.split("cd")[-1].strip()
        return None

    def _extract_url(self, text):
        """Extract URL from text"""
        if "open website" in text:
            url = text.split("open website")[-1].strip()
            if not url.startswith(("http://", "https://")):
                url = "https://" + url
            return url
        return None

    def _extract_search_query(self, text, search_engine):
        """Extract search query from text"""
        if search_engine in text:
            return text.split(search_engine)[-1].strip()
        return None

    def _extract_app_name(self, text):
        """Extract application name from text"""
        words = text.split()
        for i, word in enumerate(words):
            if word in ["app", "application"] and i + 1 < len(words):
                return words[i + 1]
        return None

    def _extract_direction(self, text):
        """Extract navigation direction from text"""
        directions = ["up", "down", "left", "right", "next", "previous", "back", "forward"]
        for direction in directions:
            if direction in text:
                return direction
        return "next"

    def _handle_unknown_command(self, text):
        """Handle unknown commands"""
        responses = [
            "I'm sorry, I didn't understand that command.",
            "Could you please repeat that?",
            "I'm not sure what you mean. Can you try a different command?",
            "Unknown command. Please try again.",
            "I didn't catch that. Could you speak more clearly?"
        ]
        self.tts.say(random.choice(responses))
        return None

    def get_available_commands(self):
        """Get list of available commands for help"""
        commands = []
        for category, patterns in self.command_patterns.items():
            commands.extend(patterns)
        return commands

    def update_current_directory(self, new_dir):
        """Update current directory for file operations"""
        self.current_directory = new_dir
