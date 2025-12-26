import os
import sys
import subprocess
import webbrowser
import random
import shutil
import psutil
import platform
import time
import logging
from pathlib import Path
from datetime import datetime

from .universal_keybindings import UniversalKeybindings
from .universal_filesystem import UniversalFileSystem

class Executor:
    def __init__(self, tts, auth=None, ui_automator=None):
        self.tts = tts
        self.auth = auth
        self.ui_automator = ui_automator
        
        # Initialize universal systems
        self.keybindings = UniversalKeybindings()
        self.filesystem = UniversalFileSystem()
        
        self.current_directory = self.filesystem.get_current_directory()
        self.logger = logging.getLogger(__name__)

    def execute(self, command):
        """Execute a command based on action dictionary"""
        if not command or 'action' not in command:
            return False
        
        # Check authentication before executing any command
        if self.auth and not self.auth.is_authenticated():
            self.tts.say("Please authenticate first by clicking 'Wake / Authenticate'")
            return False
        
        # Check session validity
        if self.auth and not self.auth.is_session_valid():
            self.tts.say("Session expired. Please authenticate again.")
            return False
        
        action = command['action']
        
        try:
            if action == "open_app":
                return self.open_app(command.get('app', {}).get('exec', ''), 
                                   command.get('app', {}).get('name', 'Unknown App'))
            elif action == "close_all_apps":
                return self.close_all_apps()
            elif action == "close_browser_tabs":
                return self.close_browser_tabs(command.get('browser', 'all'))
            elif action == "close_specific_app":
                return self.close_specific_app(command.get('app', ''))
            elif action == "new_tab":
                return self.new_tab()
            elif action == "new_window":
                return self.new_window()
            elif action == "switch_to_app":
                return self.switch_to_app(command.get('app_name', ''))
            elif action == "close_all_tabs":
                return self.close_all_tabs()
            elif action == "open_website":
                return self.open_website(command.get('url', ''))
            elif action == "search_google":
                return self.search_google(command.get('query', ''))
            elif action == "search_youtube":
                return self.search_youtube(command.get('query', ''))
            elif action == "search_amazon":
                return self.search_amazon(command.get('query', ''))
            elif action == "search_swiggy":
                return self.search_swiggy(command.get('query', ''))
            elif action == "open_file":
                return self.open_file(command.get('filename', ''))
            elif action == "create_file":
                return self.create_file(command.get('filename', ''))
            elif action == "delete_file":
                return self.delete_file(command.get('filename', ''), command.get('confirm', False))
            elif action == "list_files":
                return self.list_files(command.get('directory', ''))
            elif action == "change_directory":
                return self.change_directory(command.get('directory', ''))
            elif action == "system_info":
                return self.get_system_info()
            elif action == "battery_status":
                return self.get_battery_status()
            elif action == "disk_space":
                return self.get_disk_space()
            elif action == "memory_usage":
                return self.get_memory_usage()
            elif action == "cpu_usage":
                return self.get_cpu_usage()
            elif action == "volume_up":
                return self.volume_up()
            elif action == "volume_down":
                return self.volume_down()
            elif action == "mute":
                return self.mute()
            elif action == "shutdown":
                return self.shutdown(command.get('confirm', False))
            elif action == "restart":
                return self.restart(command.get('confirm', False))
            elif action == "sleep":
                return self.sleep()
            elif action == "lock_screen":
                return self.lock_screen()
            elif action == "logout":
                return self.logout()
            elif action == "wake":
                return self.wake()
            elif action == "pause_listening":
                return self.pause_listening()
            elif action == "open_file_explorer":
                return self.open_file_explorer()
            
            # Context-aware commands
            elif action == "navigate_folder":
                return self.navigate_folder(command.get('target', ''))
            elif action == "create_folder":
                return self.create_folder(command.get('folder_name', 'New Folder'))
            elif action == "delete_item":
                return self.delete_item(command.get('target', ''))
            elif action == "rename_item":
                return self.rename_item(command.get('new_name', ''))
            elif action == "select_item":
                return self.select_item(command.get('target', ''))
            elif action == "copy_item":
                return self.copy_item(command.get('target', ''))
            elif action == "paste_item":
                return self.paste_item()
            elif action == "cut_item":
                return self.cut_item(command.get('target', ''))
            
            # Browser commands
            elif action == "navigate_url":
                return self.navigate_url(command.get('url', ''))
            elif action == "search_query":
                return self.search_query(command.get('query', ''))
            elif action == "new_tab":
                return self.new_tab()
            elif action == "close_tab":
                return self.close_tab()
            elif action == "next_tab":
                return self.next_tab()
            elif action == "previous_tab":
                return self.previous_tab()
            elif action == "go_back":
                return self.go_back()
            elif action == "go_forward":
                return self.go_forward()
            elif action == "refresh_page":
                return self.refresh_page()
            elif action == "bookmark_page":
                return self.bookmark_page()
            
            # Text editor commands
            elif action == "save_file":
                return self.save_file()
            elif action == "save_as":
                return self.save_as(command.get('filename', ''))
            elif action == "open_file":
                return self.open_file(command.get('filename', ''))
            elif action == "new_file":
                return self.new_file()
            elif action == "find_text":
                return self.find_text(command.get('search_text', ''))
            elif action == "find_replace":
                return self.find_replace()
            elif action == "select_all":
                return self.select_all()
            elif action == "copy_text":
                return self.copy_text()
            elif action == "cut_text":
                return self.cut_text()
            elif action == "paste_text":
                return self.paste_text()
            
            # UI automation commands
            elif action == "click_element":
                return self.click_element(command.get('target', ''))
            elif action == "double_click_element":
                return self.double_click_element(command.get('target', ''))
            elif action == "right_click_element":
                return self.right_click_element(command.get('target', ''))
            elif action == "type_text":
                return self.type_text(command.get('text', ''))
            elif action == "scroll":
                return self.scroll(command.get('direction', 'down'))
            elif action == "zoom":
                return self.zoom(command.get('direction', 'in'))
            elif action == "close_window":
                return self.close_window()
            elif action == "minimize_window":
                return self.minimize_window()
            elif action == "maximize_window":
                return self.maximize_window()
            elif action == "switch_window":
                return self.switch_window()
            
            else:
                self.tts.say("I don't know how to handle that command.")
                return False
                
        except Exception as e:
            self.logger.error(f"Error executing command {action}: {e}")
            self.tts.say(f"Sorry, I encountered an error: {str(e)}")
            return False

    def open_app(self, app_path, app_name):
        # Check if application is already running
        if self._is_app_running(app_name, app_path):
            return self._handle_running_app(app_name, app_path)
        
        # Launch new instance
        responses = [
            f"Right away, sir. Launching {app_name}.",
            f"As you wish. Opening {app_name}.",
            f"Certainly. Starting {app_name} now."
        ]
        self.tts.say(random.choice(responses))

        try:
            if os.name == "nt":  # Windows
                os.startfile(app_path)
            elif sys.platform == "darwin":  # macOS
                subprocess.Popen(["open", app_path])
            else:  # Linux
                subprocess.Popen([app_path])
        except Exception as e:
            self.tts.say(f"Apologies, I could not start {app_name}. Error: {e}")

    def _is_app_running(self, app_name, app_path):
        """Check if an application is already running"""
        try:
            import psutil
            
            # Get the executable name from the path
            exe_name = os.path.basename(app_path).lower()
            
            # Check running processes
            for proc in psutil.process_iter(['pid', 'name', 'exe']):
                try:
                    proc_name = proc.info['name'].lower() if proc.info['name'] else ""
                    proc_exe = proc.info['exe'].lower() if proc.info['exe'] else ""
                    
                    # Check if process matches our app
                    if (exe_name in proc_name or 
                        exe_name in proc_exe or 
                        app_name.lower() in proc_name):
                        return True
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    continue
            
            return False
            
        except ImportError:
            # Fallback: try using tasklist on Windows
            if os.name == "nt":
                try:
                    result = subprocess.run(
                        ["tasklist", "/FI", f"IMAGENAME eq {exe_name}"],
                        capture_output=True, text=True
                    )
                    return exe_name in result.stdout.lower()
                except:
                    return False
            return False
        except Exception:
            return False

    def _handle_running_app(self, app_name, app_path):
        """Handle when application is already running"""
        # Special handling for browsers
        browser_apps = {
            'chrome': self._open_new_browser_tab,
            'firefox': self._open_new_browser_tab,
            'edge': self._open_new_browser_tab,
            'safari': self._open_new_browser_tab,
            'opera': self._open_new_browser_tab
        }
        
        app_lower = app_name.lower()
        for browser, handler in browser_apps.items():
            if browser in app_lower:
                return handler(app_name)
        
        # For other applications, try to bring to front or open new instance
        return self._bring_app_to_front(app_name, app_path)

    def _open_new_browser_tab(self, browser_name):
        """Open a new tab in the running browser"""
        try:
            import pyautogui
            
            self.tts.say(f"Opening a new tab in {browser_name}.")
            
            # Give user time to switch to browser if needed
            time.sleep(1)
            
            # Use Ctrl+T to open new tab
            pyautogui.hotkey('ctrl', 't')
            
            return True
            
        except ImportError:
            # Fallback: launch new instance
            self.tts.say(f"{browser_name} is already running. Opening a new window.")
            return False
        except Exception as e:
            self.tts.say(f"Could not open new tab in {browser_name}. Error: {e}")
            return False

    def _bring_app_to_front(self, app_name, app_path):
        """Try to bring the running application to the front"""
        try:
            import pyautogui
            
            self.tts.say(f"{app_name} is already running. Bringing it to the front.")
            
            # Try to find and click on the app window
            windows = pyautogui.getWindowsWithTitle(app_name)
            if windows:
                windows[0].activate()
                return True
            else:
                # Fallback: use Alt+Tab to cycle through windows
                pyautogui.hotkey('alt', 'tab')
                return True
                
        except ImportError:
            self.tts.say(f"{app_name} is already running. Please switch to it manually.")
            return False
        except Exception as e:
            self.tts.say(f"Could not bring {app_name} to front. Error: {e}")
            return False

    def open_website(self, url):
        responses = [
            f"Opening {url} for you, sir.",
            f"Certainly. Here is {url}.",
            f"As requested, launching {url}."
        ]
        self.tts.say(random.choice(responses))
        webbrowser.open(url)

    def search_amazon(self, query):
        import urllib.parse
        encoded_query = urllib.parse.quote_plus(query)
        url = f"https://www.amazon.in/s?k={encoded_query}"
        self.tts.say(f"Searching Amazon for {query}, sir.")
        webbrowser.open(url)

    def search_swiggy(self, query):
        import urllib.parse
        encoded_query = urllib.parse.quote_plus(query)
        url = f"https://www.swiggy.com/search?query={encoded_query}"
        self.tts.say(f"Searching Swiggy for {query}, sir.")
        webbrowser.open(url)

    def send_whatsapp(self):
        self.tts.say("Opening WhatsApp Web. Please wait.")
        webbrowser.open("https://web.whatsapp.com")

    def send_email(self):
        self.tts.say("Opening your email client, sir.")
        webbrowser.open("mailto:")

    def search_google(self, query):
        """Search Google"""
        if not query:
            self.tts.say("What would you like me to search for?")
            return False
        import urllib.parse
        encoded_query = urllib.parse.quote_plus(query)
        url = f"https://www.google.com/search?q={encoded_query}"
        self.tts.say(f"Searching Google for {query}.")
        webbrowser.open(url)
        return True

    def search_youtube(self, query):
        """Search YouTube"""
        if not query:
            self.tts.say("What would you like me to search for on YouTube?")
            return False
        import urllib.parse
        encoded_query = urllib.parse.quote_plus(query)
        url = f"https://www.youtube.com/results?search_query={encoded_query}"
        self.tts.say(f"Searching YouTube for {query}.")
        webbrowser.open(url)
        return True

    def open_file(self, filename):
        """Open a file with the default application"""
        if not filename:
            self.tts.say("I need a filename to open.")
            return False
            
        file_path = os.path.join(self.current_directory, filename)
        if not os.path.exists(file_path):
            self.tts.say(f"File {filename} not found.")
            return False
            
        try:
            if os.name == "nt":  # Windows
                os.startfile(file_path)
            elif sys.platform == "darwin":  # macOS
                subprocess.Popen(["open", file_path])
            else:  # Linux
                subprocess.Popen(["xdg-open", file_path])
            self.tts.say(f"Opening {filename}.")
            return True
        except Exception as e:
            self.tts.say(f"Could not open {filename}. Error: {e}")
            return False

    def create_file(self, filename):
        """Create a new file"""
        if not filename:
            self.tts.say("I need a filename to create.")
            return False
            
        file_path = os.path.join(self.current_directory, filename)
        try:
            with open(file_path, 'w') as f:
                f.write("")
            self.tts.say(f"Created file {filename}.")
            return True
        except Exception as e:
            self.tts.say(f"Could not create {filename}. Error: {e}")
            return False

    def delete_file(self, filename, confirm=False):
        """Delete a file"""
        if not filename:
            self.tts.say("I need a filename to delete.")
            return False
            
        file_path = os.path.join(self.current_directory, filename)
        if not os.path.exists(file_path):
            self.tts.say(f"File {filename} not found.")
            return False
            
        if confirm:
            self.tts.say(f"Are you sure you want to delete {filename}? Say yes to confirm.")
            
        try:
            os.remove(file_path)
            self.tts.say(f"Deleted {filename}.")
            return True
        except Exception as e:
            self.tts.say(f"Could not delete {filename}. Error: {e}")
            return False

    def list_files(self, directory=None):
        """List files in a directory"""
        target_dir = directory if directory else self.current_directory
        target_path = os.path.join(self.current_directory, target_dir) if directory else self.current_directory
        
        if not os.path.exists(target_path):
            self.tts.say(f"Directory {target_dir} not found.")
            return False
            
        try:
            files = os.listdir(target_path)
            if not files:
                self.tts.say("The directory is empty.")
                return True
                
            file_list = []
            for file in files[:10]:  # Limit to first 10 files
                file_path = os.path.join(target_path, file)
                if os.path.isdir(file_path):
                    file_list.append(f"{file} (folder)")
                else:
                    file_list.append(file)
            
            files_text = ", ".join(file_list)
            if len(files) > 10:
                files_text += f" and {len(files) - 10} more files"
                
            self.tts.say(f"Files in {target_dir}: {files_text}")
            return True
        except Exception as e:
            self.tts.say(f"Could not list files. Error: {e}")
            return False

    def change_directory(self, directory):
        """Change current directory"""
        if not directory:
            self.tts.say("I need a directory name.")
            return False
            
        target_path = os.path.join(self.current_directory, directory)
        if not os.path.exists(target_path):
            self.tts.say(f"Directory {directory} not found.")
            return False
            
        if not os.path.isdir(target_path):
            self.tts.say(f"{directory} is not a directory.")
            return False
            
        try:
            self.current_directory = target_path
            self.tts.say(f"Changed to directory {directory}.")
            return True
        except Exception as e:
            self.tts.say(f"Could not change directory. Error: {e}")
            return False

    def get_system_info(self):
        """Get system information"""
        try:
            info = {
                "Platform": platform.platform(),
                "System": platform.system(),
                "Release": platform.release(),
                "Version": platform.version(),
                "Machine": platform.machine(),
                "Processor": platform.processor(),
                "Python": platform.python_version()
            }
            
            info_text = f"System: {info['System']} {info['Release']}, "
            info_text += f"Architecture: {info['Machine']}, "
            info_text += f"Python: {info['Python']}"
            
            self.tts.say(info_text)
            return True
        except Exception as e:
            self.tts.say(f"Could not get system info. Error: {e}")
            return False

    def get_battery_status(self):
        """Get battery status"""
        try:
            battery = psutil.sensors_battery()
            if battery:
                percent = battery.percent
                plugged = "plugged in" if battery.power_plugged else "not plugged in"
                self.tts.say(f"Battery is at {percent}% and {plugged}.")
            else:
                self.tts.say("Battery information not available.")
            return True
        except Exception as e:
            self.tts.say(f"Could not get battery status. Error: {e}")
            return False

    def get_disk_space(self):
        """Get disk space information"""
        try:
            disk_usage = psutil.disk_usage('/')
            total = disk_usage.total // (1024**3)  # Convert to GB
            used = disk_usage.used // (1024**3)
            free = disk_usage.free // (1024**3)
            
            self.tts.say(f"Disk space: {used} GB used, {free} GB free out of {total} GB total.")
            return True
        except Exception as e:
            self.tts.say(f"Could not get disk space. Error: {e}")
            return False

    def get_memory_usage(self):
        """Get memory usage information"""
        try:
            memory = psutil.virtual_memory()
            total = memory.total // (1024**3)  # Convert to GB
            available = memory.available // (1024**3)
            percent = memory.percent
            
            self.tts.say(f"Memory usage: {percent}% used, {available} GB available out of {total} GB total.")
            return True
        except Exception as e:
            self.tts.say(f"Could not get memory usage. Error: {e}")
            return False

    def get_cpu_usage(self):
        """Get CPU usage information"""
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            cpu_count = psutil.cpu_count()
            
            self.tts.say(f"CPU usage: {cpu_percent}% across {cpu_count} cores.")
            return True
        except Exception as e:
            self.tts.say(f"Could not get CPU usage. Error: {e}")
            return False

    def volume_up(self):
        """Increase system volume"""
        try:
            if os.name == "nt":  # Windows
                subprocess.run(["powershell", "-c", "(New-Object -comObject WScript.Shell).SendKeys([char]175)"])
            elif sys.platform == "darwin":  # macOS
                subprocess.run(["osascript", "-e", "set volume output volume (output volume of (get volume settings) + 10)"])
            else:  # Linux
                subprocess.run(["amixer", "set", "Master", "10%+"])
            self.tts.say("Volume increased.")
            return True
        except Exception as e:
            self.tts.say(f"Could not increase volume. Error: {e}")
            return False

    def volume_down(self):
        """Decrease system volume"""
        try:
            if os.name == "nt":  # Windows
                subprocess.run(["powershell", "-c", "(New-Object -comObject WScript.Shell).SendKeys([char]174)"])
            elif sys.platform == "darwin":  # macOS
                subprocess.run(["osascript", "-e", "set volume output volume (output volume of (get volume settings) - 10)"])
            else:  # Linux
                subprocess.run(["amixer", "set", "Master", "10%-"])
            self.tts.say("Volume decreased.")
            return True
        except Exception as e:
            self.tts.say(f"Could not decrease volume. Error: {e}")
            return False

    def mute(self):
        """Mute system volume"""
        try:
            if os.name == "nt":  # Windows
                subprocess.run(["powershell", "-c", "(New-Object -comObject WScript.Shell).SendKeys([char]173)"])
            elif sys.platform == "darwin":  # macOS
                subprocess.run(["osascript", "-e", "set volume output volume 0"])
            else:  # Linux
                subprocess.run(["amixer", "set", "Master", "mute"])
            self.tts.say("Volume muted.")
            return True
        except Exception as e:
            self.tts.say(f"Could not mute volume. Error: {e}")
            return False

    def shutdown(self, confirm=False):
        """Shutdown the system"""
        if confirm:
            self.tts.say("Are you sure you want to shutdown? Say yes to confirm.")
            
        try:
            if os.name == "nt":  # Windows
                subprocess.run(["shutdown", "/s", "/t", "10"])
            elif sys.platform == "darwin":  # macOS
                subprocess.run(["sudo", "shutdown", "-h", "now"])
            else:  # Linux
                subprocess.run(["sudo", "shutdown", "-h", "now"])
            self.tts.say("System will shutdown in 10 seconds.")
            return True
        except Exception as e:
            self.tts.say(f"Could not shutdown system. Error: {e}")
            return False

    def restart(self, confirm=False):
        """Restart the system"""
        if confirm:
            self.tts.say("Are you sure you want to restart? Say yes to confirm.")
            
        try:
            if os.name == "nt":  # Windows
                subprocess.run(["shutdown", "/r", "/t", "10"])
            elif sys.platform == "darwin":  # macOS
                subprocess.run(["sudo", "shutdown", "-r", "now"])
            else:  # Linux
                subprocess.run(["sudo", "shutdown", "-r", "now"])
            self.tts.say("System will restart in 10 seconds.")
            return True
        except Exception as e:
            self.tts.say(f"Could not restart system. Error: {e}")
            return False

    def sleep(self):
        """Put system to sleep"""
        try:
            if os.name == "nt":  # Windows
                subprocess.run(["rundll32.exe", "powrprof.dll,SetSuspendState", "0,1,0"])
            elif sys.platform == "darwin":  # macOS
                subprocess.run(["pmset", "sleepnow"])
            else:  # Linux
                subprocess.run(["systemctl", "suspend"])
            self.tts.say("System going to sleep.")
            return True
        except Exception as e:
            self.tts.say(f"Could not put system to sleep. Error: {e}")
            return False

    def lock_screen(self):
        """Lock the screen"""
        try:
            if os.name == "nt":  # Windows
                subprocess.run(["rundll32.exe", "user32.dll,LockWorkStation"])
            elif sys.platform == "darwin":  # macOS
                subprocess.run(["pmset", "displaysleepnow"])
            else:  # Linux
                subprocess.run(["gnome-screensaver-command", "-l"])
            self.tts.say("Screen locked.")
            return True
        except Exception as e:
            self.tts.say(f"Could not lock screen. Error: {e}")
            return False

    def logout(self):
        """Logout current user"""
        if self.auth:
            self.auth.logout()
        else:
            self.tts.say("Logging out.")
        return True

    def wake(self):
        """Wake up the system"""
        self.tts.say("I am back online. At your service.")
        return True

    def pause_listening(self):
        """Pause voice listening"""
        self.tts.say("Going to sleep. Call me when you need me.")
        return True
    
    def open_file_explorer(self):
        """Open file explorer"""
        try:
            if os.name == "nt":  # Windows
                os.system("start explorer")
                self.tts.say("File explorer opened")
                return True
            elif os.name == "posix":  # macOS/Linux
                if sys.platform == "darwin":  # macOS
                    os.system("open .")
                else:  # Linux
                    os.system("xdg-open .")
                self.tts.say("File explorer opened")
                return True
            else:
                self.tts.say("File explorer not supported on this system")
                return False
        except Exception as e:
            self.logger.error(f"Error opening file explorer: {e}")
            self.tts.say("Sorry, I couldn't open file explorer")
            return False

    def close_all_apps(self):
        """Close all applications except EchoOS"""
        try:
            self.tts.say("Closing all applications except EchoOS. This will close Paint, Word, Excel, browsers, and other apps.")
            
            if os.name == "nt":  # Windows
                # Close common applications
                apps_to_close = [
                    "mspaint.exe", "winword.exe", "excel.exe", "powerpnt.exe", "notepad.exe",
                    "chrome.exe", "firefox.exe", "msedge.exe", "iexplore.exe",
                    "calc.exe", "explorer.exe"  # Note: explorer.exe will restart automatically
                ]
                
                for app in apps_to_close:
                    try:
                        subprocess.run(["taskkill", "/f", "/im", app], capture_output=True)
                    except:
                        pass
                
                self.tts.say("All applications have been closed. EchoOS remains active.")
                return True
                
            elif sys.platform == "darwin":  # macOS
                subprocess.run(["pkill", "-f", "Google Chrome"], capture_output=True)
                subprocess.run(["pkill", "-f", "Firefox"], capture_output=True)
                subprocess.run(["pkill", "-f", "Safari"], capture_output=True)
                subprocess.run(["pkill", "-f", "TextEdit"], capture_output=True)
                subprocess.run(["pkill", "-f", "Preview"], capture_output=True)
                
                self.tts.say("All applications have been closed. EchoOS remains active.")
                return True
                
            else:  # Linux
                subprocess.run(["pkill", "-f", "chrome"], capture_output=True)
                subprocess.run(["pkill", "-f", "firefox"], capture_output=True)
                subprocess.run(["pkill", "-f", "libreoffice"], capture_output=True)
                subprocess.run(["pkill", "-f", "gedit"], capture_output=True)
                
                self.tts.say("All applications have been closed. EchoOS remains active.")
                return True
                
        except Exception as e:
            self.tts.say(f"Could not close all applications. Error: {e}")
            return False

    def close_browser_tabs(self, browser="all"):
        """Close specific browser tabs"""
        try:
            if browser == "all":
                self.tts.say("Closing all browser tabs. Please switch to your browser window first.")
            else:
                self.tts.say(f"Closing {browser} tabs. Please switch to your {browser} window first.")
            
            # Use keyboard shortcuts to close tabs safely
            try:
                import pyautogui
                
                # Give user time to switch to browser
                time.sleep(2)
                
                # Close all tabs using Ctrl+W (close tab) repeatedly
                for i in range(10):  # Try up to 10 times
                    pyautogui.hotkey('ctrl', 'w')
                    time.sleep(0.2)
                
                # Alternative: Close all tabs at once with Ctrl+Shift+W (close all tabs)
                pyautogui.hotkey('ctrl', 'shift', 'w')
                
                self.tts.say(f"{browser.title()} tabs have been closed using keyboard shortcuts.")
                return True
                
            except ImportError:
                # Fallback: Use process killing for specific browser
                if browser == "chrome":
                    subprocess.run(["taskkill", "/f", "/im", "chrome.exe"], capture_output=True)
                elif browser == "firefox":
                    subprocess.run(["taskkill", "/f", "/im", "firefox.exe"], capture_output=True)
                elif browser == "edge":
                    subprocess.run(["taskkill", "/f", "/im", "msedge.exe"], capture_output=True)
                else:  # all browsers
                    subprocess.run(["taskkill", "/f", "/im", "chrome.exe"], capture_output=True)
                    subprocess.run(["taskkill", "/f", "/im", "firefox.exe"], capture_output=True)
                    subprocess.run(["taskkill", "/f", "/im", "msedge.exe"], capture_output=True)
                
                self.tts.say(f"{browser.title()} browser closed.")
                return True
                
        except Exception as e:
            self.tts.say(f"Could not close {browser} tabs. Error: {e}")
            return False

    def close_specific_app(self, app_name):
        """Close a specific application"""
        try:
            app_names = {
                "mspaint": "Paint",
                "winword": "Microsoft Word",
                "excel": "Microsoft Excel", 
                "powerpnt": "Microsoft PowerPoint",
                "notepad": "Notepad"
            }
            
            display_name = app_names.get(app_name, app_name)
            self.tts.say(f"Closing {display_name}.")
            
            if os.name == "nt":  # Windows
                subprocess.run(["taskkill", "/f", "/im", f"{app_name}.exe"], capture_output=True)
            elif sys.platform == "darwin":  # macOS
                if app_name == "notepad":
                    subprocess.run(["pkill", "-f", "TextEdit"], capture_output=True)
                else:
                    subprocess.run(["pkill", "-f", app_name], capture_output=True)
            else:  # Linux
                subprocess.run(["pkill", "-f", app_name], capture_output=True)
            
            self.tts.say(f"{display_name} has been closed.")
            return True
            
        except Exception as e:
            self.tts.say(f"Could not close {app_name}. Error: {e}")
            return False

    def new_tab(self):
        """Open a new tab in the current browser"""
        try:
            import pyautogui
            
            self.tts.say("Opening a new tab.")
            
            # Use Ctrl+T to open new tab
            pyautogui.hotkey('ctrl', 't')
            return True
            
        except ImportError:
            self.tts.say("Could not open new tab. Please install pyautogui for this feature.")
            return False
        except Exception as e:
            self.tts.say(f"Could not open new tab. Error: {e}")
            return False

    def new_window(self):
        """Open a new window in the current application"""
        try:
            import pyautogui
            
            self.tts.say("Opening a new window.")
            
            # Use Ctrl+N to open new window
            pyautogui.hotkey('ctrl', 'n')
            return True
            
        except ImportError:
            self.tts.say("Could not open new window. Please install pyautogui for this feature.")
            return False
        except Exception as e:
            self.tts.say(f"Could not open new window. Error: {e}")
            return False

    def switch_to_app(self, app_name):
        """Switch to a specific application"""
        try:
            import pyautogui
            
            self.tts.say(f"Switching to {app_name}.")
            
            # Try to find the app window
            windows = pyautogui.getWindowsWithTitle(app_name)
            if windows:
                windows[0].activate()
                return True
            else:
                # Fallback: use Alt+Tab to cycle through windows
                pyautogui.hotkey('alt', 'tab')
                return True
                
        except ImportError:
            self.tts.say(f"Could not switch to {app_name}. Please install pyautogui for this feature.")
            return False
        except Exception as e:
            self.tts.say(f"Could not switch to {app_name}. Error: {e}")
            return False

    def close_all_tabs(self):
        """Close all browser tabs and windows (safely, preserving EchoOS)"""
        try:
            self.tts.say("I'll help you close browser tabs safely. Please switch to your browser window first.")
            
            # Use keyboard shortcuts to close tabs safely
            try:
                import pyautogui
                
                # Give user time to switch to browser
                time.sleep(2)
                
                # Close all tabs using Ctrl+W (close tab) repeatedly
                for i in range(10):  # Try up to 10 times
                    pyautogui.hotkey('ctrl', 'w')
                    time.sleep(0.2)
                
                # Alternative: Close all tabs at once with Ctrl+Shift+W (close all tabs)
                pyautogui.hotkey('ctrl', 'shift', 'w')
                
                self.tts.say("Browser tabs have been closed using keyboard shortcuts. EchoOS remains safe.")
                return True
                
            except ImportError:
                # Fallback: Use process killing but with warning
                self.tts.say("Using alternative method to close browser windows.")
                
                if os.name == "nt":  # Windows
                    subprocess.run(["taskkill", "/f", "/im", "chrome.exe"], capture_output=True)
                    subprocess.run(["taskkill", "/f", "/im", "firefox.exe"], capture_output=True)
                    subprocess.run(["taskkill", "/f", "/im", "msedge.exe"], capture_output=True)
                elif sys.platform == "darwin":  # macOS
                    subprocess.run(["pkill", "-f", "Google Chrome"], capture_output=True)
                    subprocess.run(["pkill", "-f", "Firefox"], capture_output=True)
                else:  # Linux
                    subprocess.run(["pkill", "-f", "chrome"], capture_output=True)
                    subprocess.run(["pkill", "-f", "firefox"], capture_output=True)
                
                self.tts.say("Browser windows closed. EchoOS should remain active.")
                return True
                
        except Exception as e:
            self.tts.say(f"Could not close browser tabs. Error: {e}")
            return False
    
    # Context-aware File Explorer commands
    def navigate_folder(self, folder_name):
        """Navigate to a folder using universal filesystem"""
        try:
            success, result = self.filesystem.navigate_to_directory(folder_name)
            if success:
                self.current_directory = result
                self.tts.say(f"Navigated to {folder_name}")
                return True
            else:
                self.tts.say(f"Could not navigate to {folder_name}: {result}")
                return False
        except Exception as e:
            self.logger.error(f"Error navigating to folder: {e}")
            self.tts.say("Sorry, I couldn't navigate to that folder")
            return False
    
    def create_folder(self, folder_name):
        """Create a new folder using universal filesystem"""
        try:
            success, result = self.filesystem.create_directory(folder_name)
            if success:
                self.tts.say(f"Created folder {folder_name}")
                return True
            else:
                self.tts.say(f"Could not create folder {folder_name}: {result}")
                return False
        except Exception as e:
            self.logger.error(f"Error creating folder: {e}")
            self.tts.say("Sorry, I couldn't create that folder")
            return False
    
    def delete_item(self, item_name):
        """Delete an item"""
        if not self.ui_automator:
            self.tts.say("UI automation not available")
            return False
        
        try:
            # Find and select item
            item_element = self.ui_automator.find_element_by_text(item_name)
            if item_element:
                self.ui_automator.click_element(item_element)
                time.sleep(0.5)
                
                # Press delete key
                self.ui_automator.press_key('delete')
                self.tts.say(f"Deleted {item_name}")
                return True
            else:
                self.tts.say(f"Could not find {item_name}")
                return False
        except Exception as e:
            self.logger.error(f"Error deleting item: {e}")
            self.tts.say("Sorry, I couldn't delete that item")
            return False
    
    def rename_item(self, new_name):
        """Rename selected item"""
        if not self.ui_automator:
            self.tts.say("UI automation not available")
            return False
        
        try:
            # Press F2 to rename
            self.ui_automator.press_key('f2')
            time.sleep(0.5)
            
            # Type new name
            self.ui_automator.type_text(new_name)
            self.ui_automator.press_key('enter')
            
            self.tts.say(f"Renamed to {new_name}")
            return True
        except Exception as e:
            self.logger.error(f"Error renaming item: {e}")
            self.tts.say("Sorry, I couldn't rename that item")
            return False
    
    def select_item(self, item_name):
        """Select an item"""
        if not self.ui_automator:
            self.tts.say("UI automation not available")
            return False
        
        try:
            item_element = self.ui_automator.find_element_by_text(item_name)
            if item_element:
                self.ui_automator.click_element(item_element)
                self.tts.say(f"Selected {item_name}")
                return True
            else:
                self.tts.say(f"Could not find {item_name}")
                return False
        except Exception as e:
            self.logger.error(f"Error selecting item: {e}")
            return False
    
    def copy_item(self, item_name):
        """Copy an item"""
        if not self.ui_automator:
            self.tts.say("UI automation not available")
            return False
        
        try:
            # Select item first
            if item_name:
                self.select_item(item_name)
            
            # Copy (Ctrl+C)
            self.ui_automator.press_key('ctrl+c')
            self.tts.say("Copied")
            return True
        except Exception as e:
            self.logger.error(f"Error copying item: {e}")
            return False
    
    def paste_item(self):
        """Paste copied item"""
        if not self.ui_automator:
            self.tts.say("UI automation not available")
            return False
        
        try:
            # Paste (Ctrl+V)
            self.ui_automator.press_key('ctrl+v')
            self.tts.say("Pasted")
            return True
        except Exception as e:
            self.logger.error(f"Error pasting item: {e}")
            return False
    
    def cut_item(self, item_name):
        """Cut an item"""
        if not self.ui_automator:
            self.tts.say("UI automation not available")
            return False
        
        try:
            # Select item first
            if item_name:
                self.select_item(item_name)
            
            # Cut (Ctrl+X)
            self.ui_automator.press_key('ctrl+x')
            self.tts.say("Cut")
            return True
        except Exception as e:
            self.logger.error(f"Error cutting item: {e}")
            return False
    
    # Browser commands
    def navigate_url(self, url):
        """Navigate to URL in browser"""
        if not self.ui_automator:
            self.tts.say("UI automation not available")
            return False
        
        try:
            # Click address bar (Ctrl+L)
            self.ui_automator.press_key('ctrl+l')
            time.sleep(0.5)
            
            # Type URL
            self.ui_automator.type_text(url)
            self.ui_automator.press_key('enter')
            
            self.tts.say(f"Navigating to {url}")
            return True
        except Exception as e:
            self.logger.error(f"Error navigating to URL: {e}")
            return False
    
    def search_query(self, query):
        """Search in browser"""
        if not self.ui_automator:
            self.tts.say("UI automation not available")
            return False
        
        try:
            # Click search box or use Ctrl+K
            self.ui_automator.press_key('ctrl+k')
            time.sleep(0.5)
            
            # Type search query
            self.ui_automator.type_text(query)
            self.ui_automator.press_key('enter')
            
            self.tts.say(f"Searching for {query}")
            return True
        except Exception as e:
            self.logger.error(f"Error searching: {e}")
            return False
    
    def new_tab(self):
        """Open new tab in browser"""
        if not self.ui_automator:
            self.tts.say("UI automation not available")
            return False
        
        try:
            self.ui_automator.press_key('ctrl+t')
            self.tts.say("Opened new tab")
            return True
        except Exception as e:
            self.logger.error(f"Error opening new tab: {e}")
            return False
    
    def close_tab(self):
        """Close current tab"""
        if not self.ui_automator:
            self.tts.say("UI automation not available")
            return False
        
        try:
            self.ui_automator.press_key('ctrl+w')
            self.tts.say("Closed tab")
            return True
        except Exception as e:
            self.logger.error(f"Error closing tab: {e}")
            return False
    
    def next_tab(self):
        """Switch to next tab"""
        if not self.ui_automator:
            self.tts.say("UI automation not available")
            return False
        
        try:
            self.ui_automator.press_key('ctrl+tab')
            return True
        except Exception as e:
            self.logger.error(f"Error switching to next tab: {e}")
            return False
    
    def previous_tab(self):
        """Switch to previous tab"""
        if not self.ui_automator:
            self.tts.say("UI automation not available")
            return False
        
        try:
            self.ui_automator.press_key('ctrl+shift+tab')
            return True
        except Exception as e:
            self.logger.error(f"Error switching to previous tab: {e}")
            return False
    
    def go_back(self):
        """Go back in browser"""
        if not self.ui_automator:
            self.tts.say("UI automation not available")
            return False
        
        try:
            self.ui_automator.press_key('alt+left')
            return True
        except Exception as e:
            self.logger.error(f"Error going back: {e}")
            return False
    
    def go_forward(self):
        """Go forward in browser"""
        if not self.ui_automator:
            self.tts.say("UI automation not available")
            return False
        
        try:
            self.ui_automator.press_key('alt+right')
            return True
        except Exception as e:
            self.logger.error(f"Error going forward: {e}")
            return False
    
    def refresh_page(self):
        """Refresh current page"""
        if not self.ui_automator:
            self.tts.say("UI automation not available")
            return False
        
        try:
            self.ui_automator.press_key('f5')
            self.tts.say("Refreshed page")
            return True
        except Exception as e:
            self.logger.error(f"Error refreshing page: {e}")
            return False
    
    def bookmark_page(self):
        """Bookmark current page"""
        if not self.ui_automator:
            self.tts.say("UI automation not available")
            return False
        
        try:
            self.ui_automator.press_key('ctrl+d')
            self.tts.say("Bookmarked page")
            return True
        except Exception as e:
            self.logger.error(f"Error bookmarking page: {e}")
            return False
    
    # Text editor commands
    def save_file(self):
        """Save current file using universal keybindings"""
        if not self.ui_automator:
            self.tts.say("UI automation not available")
            return False
        
        try:
            shortcut = self.keybindings.get_shortcut("save")
            if shortcut:
                self.ui_automator.press_key(shortcut)
                self.tts.say("File saved")
                return True
            else:
                self.tts.say("Save shortcut not available")
                return False
        except Exception as e:
            self.logger.error(f"Error saving file: {e}")
            return False
    
    def save_as(self, filename):
        """Save file with new name"""
        if not self.ui_automator:
            self.tts.say("UI automation not available")
            return False
        
        try:
            # Open Save As dialog
            self.ui_automator.press_key('ctrl+shift+s')
            time.sleep(1)
            
            # Type filename
            self.ui_automator.type_text(filename)
            self.ui_automator.press_key('enter')
            
            self.tts.say(f"Saved as {filename}")
            return True
        except Exception as e:
            self.logger.error(f"Error saving file as: {e}")
            return False
    
    def open_file(self, filename):
        """Open file"""
        if not self.ui_automator:
            self.tts.say("UI automation not available")
            return False
        
        try:
            # Open file dialog
            self.ui_automator.press_key('ctrl+o')
            time.sleep(1)
            
            # Type filename
            self.ui_automator.type_text(filename)
            self.ui_automator.press_key('enter')
            
            self.tts.say(f"Opened {filename}")
            return True
        except Exception as e:
            self.logger.error(f"Error opening file: {e}")
            return False
    
    def new_file(self):
        """Create new file"""
        if not self.ui_automator:
            self.tts.say("UI automation not available")
            return False
        
        try:
            self.ui_automator.press_key('ctrl+n')
            self.tts.say("Created new file")
            return True
        except Exception as e:
            self.logger.error(f"Error creating new file: {e}")
            return False
    
    def find_text(self, search_text):
        """Find text in document"""
        if not self.ui_automator:
            self.tts.say("UI automation not available")
            return False
        
        try:
            # Open find dialog
            self.ui_automator.press_key('ctrl+f')
            time.sleep(0.5)
            
            # Type search text
            self.ui_automator.type_text(search_text)
            
            self.tts.say(f"Searching for {search_text}")
            return True
        except Exception as e:
            self.logger.error(f"Error finding text: {e}")
            return False
    
    def find_replace(self):
        """Open find and replace dialog"""
        if not self.ui_automator:
            self.tts.say("UI automation not available")
            return False
        
        try:
            self.ui_automator.press_key('ctrl+h')
            self.tts.say("Find and replace opened")
            return True
        except Exception as e:
            self.logger.error(f"Error opening find and replace: {e}")
            return False
    
    def select_all(self):
        """Select all text"""
        if not self.ui_automator:
            self.tts.say("UI automation not available")
            return False
        
        try:
            self.ui_automator.press_key('ctrl+a')
            self.tts.say("Selected all")
            return True
        except Exception as e:
            self.logger.error(f"Error selecting all: {e}")
            return False
    
    def copy_text(self):
        """Copy selected text"""
        if not self.ui_automator:
            self.tts.say("UI automation not available")
            return False
        
        try:
            self.ui_automator.press_key('ctrl+c')
            self.tts.say("Copied text")
            return True
        except Exception as e:
            self.logger.error(f"Error copying text: {e}")
            return False
    
    def cut_text(self):
        """Cut selected text"""
        if not self.ui_automator:
            self.tts.say("UI automation not available")
            return False
        
        try:
            self.ui_automator.press_key('ctrl+x')
            self.tts.say("Cut text")
            return True
        except Exception as e:
            self.logger.error(f"Error cutting text: {e}")
            return False
    
    def paste_text(self):
        """Paste text"""
        if not self.ui_automator:
            self.tts.say("UI automation not available")
            return False
        
        try:
            self.ui_automator.press_key('ctrl+v')
            self.tts.say("Pasted text")
            return True
        except Exception as e:
            self.logger.error(f"Error pasting text: {e}")
            return False
    
    # UI automation commands
    def click_element(self, target):
        """Click on an element"""
        if not self.ui_automator:
            self.tts.say("UI automation not available")
            return False
        
        try:
            # Find element by text
            element = self.ui_automator.find_element_by_text(target)
            if element:
                self.ui_automator.click_element(element)
                self.tts.say(f"Clicked {target}")
                return True
            else:
                self.tts.say(f"Could not find {target}")
                return False
        except Exception as e:
            self.logger.error(f"Error clicking element: {e}")
            return False
    
    def double_click_element(self, target):
        """Double click on an element"""
        if not self.ui_automator:
            self.tts.say("UI automation not available")
            return False
        
        try:
            element = self.ui_automator.find_element_by_text(target)
            if element:
                # Double click using pyautogui
                import pyautogui
                pyautogui.doubleClick(element.center_x, element.center_y)
                self.tts.say(f"Double clicked {target}")
                return True
            else:
                self.tts.say(f"Could not find {target}")
                return False
        except Exception as e:
            self.logger.error(f"Error double clicking element: {e}")
            return False
    
    def right_click_element(self, target):
        """Right click on an element"""
        if not self.ui_automator:
            self.tts.say("UI automation not available")
            return False
        
        try:
            element = self.ui_automator.find_element_by_text(target)
            if element:
                # Right click using pyautogui
                import pyautogui
                pyautogui.rightClick(element.center_x, element.center_y)
                self.tts.say(f"Right clicked {target}")
                return True
            else:
                self.tts.say(f"Could not find {target}")
                return False
        except Exception as e:
            self.logger.error(f"Error right clicking element: {e}")
            return False
    
    def type_text(self, text):
        """Type text at current cursor position"""
        if not self.ui_automator:
            self.tts.say("UI automation not available")
            return False
        
        try:
            self.ui_automator.type_text(text)
            self.tts.say(f"Typed: {text}")
            return True
        except Exception as e:
            self.logger.error(f"Error typing text: {e}")
            return False
    
    def scroll(self, direction):
        """Scroll in specified direction"""
        if not self.ui_automator:
            self.tts.say("UI automation not available")
            return False
        
        try:
            self.ui_automator.scroll(direction)
            self.tts.say(f"Scrolled {direction}")
            return True
        except Exception as e:
            self.logger.error(f"Error scrolling: {e}")
            return False
    
    def zoom(self, direction):
        """Zoom in or out"""
        if not self.ui_automator:
            self.tts.say("UI automation not available")
            return False
        
        try:
            if direction == "in":
                self.ui_automator.press_key('ctrl+plus')
            else:
                self.ui_automator.press_key('ctrl+minus')
            
            self.tts.say(f"Zoomed {direction}")
            return True
        except Exception as e:
            self.logger.error(f"Error zooming: {e}")
            return False
    
    def close_window(self):
        """Close current window"""
        if not self.ui_automator:
            self.tts.say("UI automation not available")
            return False
        
        try:
            self.ui_automator.press_key('alt+f4')
            self.tts.say("Closed window")
            return True
        except Exception as e:
            self.logger.error(f"Error closing window: {e}")
            return False
    
    def minimize_window(self):
        """Minimize current window"""
        if not self.ui_automator:
            self.tts.say("UI automation not available")
            return False
        
        try:
            self.ui_automator.press_key('alt+space')
            time.sleep(0.2)
            self.ui_automator.press_key('n')
            self.tts.say("Minimized window")
            return True
        except Exception as e:
            self.logger.error(f"Error minimizing window: {e}")
            return False
    
    def maximize_window(self):
        """Maximize current window"""
        if not self.ui_automator:
            self.tts.say("UI automation not available")
            return False
        
        try:
            self.ui_automator.press_key('alt+space')
            time.sleep(0.2)
            self.ui_automator.press_key('x')
            self.tts.say("Maximized window")
            return True
        except Exception as e:
            self.logger.error(f"Error maximizing window: {e}")
            return False
    
    def switch_window(self):
        """Switch between windows"""
        if not self.ui_automator:
            self.tts.say("UI automation not available")
            return False
        
        try:
            self.ui_automator.press_key('alt+tab')
            self.tts.say("Switched window")
            return True
        except Exception as e:
            self.logger.error(f"Error switching window: {e}")
            return False
