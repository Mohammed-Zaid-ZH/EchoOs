import platform
import os
import json
import pathlib
import subprocess
import winreg
import logging
from typing import List, Dict, Set

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def resolve_lnk(path):
    """Resolve Windows shortcut (.lnk) files to their target paths"""
    try:
        import pythoncom
        import win32com.client
        shell = win32com.client.Dispatch("WScript.Shell")
        shortcut = shell.CreateShortCut(path)
        return shortcut.Targetpath
    except Exception as e:
        logger.debug(f"Could not resolve shortcut {path}: {e}")
        return None

class AppDiscovery:
    """Comprehensive application discovery system for all platforms"""
    
    def __init__(self):
        self.system = platform.system().lower()
        self.discovered_apps = []
        self.seen_names = set()
        
    def discover_and_save(self, out="config/apps.json"):
        """Discover all applications and save to JSON file"""
        logger.info("Starting comprehensive application discovery...")
        
        if self.system == "windows":
            apps = self._discover_windows()
        elif self.system == "darwin":
            apps = self._discover_mac()
        else:
            apps = self._discover_linux()
        
        # Save to file
        output_data = {
            "apps": apps,
            "total_count": len(apps),
            "discovery_date": str(pathlib.Path().cwd()),
            "system": self.system
        }
        
        pathlib.Path(out).write_text(json.dumps(output_data, indent=2))
        logger.info(f"Discovered {len(apps)} applications and saved to {out}")
        return apps
    
    def _discover_windows(self):
        """Comprehensive Windows application discovery"""
        logger.info("Discovering Windows applications...")
        apps = []
        
        try:
            # 1. Start Menu shortcuts (user and system)
            logger.info("Scanning Start Menu shortcuts...")
            apps.extend(self._discover_start_menu())
            logger.info(f"Found {len(apps)} apps from Start Menu")
        except Exception as e:
            logger.warning(f"Error scanning Start Menu: {e}")
        
        try:
            # 2. Registry-based discovery
            logger.info("Scanning Windows Registry...")
            registry_apps = self._discover_registry_apps()
            apps.extend(registry_apps)
            logger.info(f"Found {len(registry_apps)} apps from Registry")
        except Exception as e:
            logger.warning(f"Error scanning Registry: {e}")
        
        try:
            # 3. Program Files directories
            logger.info("Scanning Program Files...")
            program_apps = self._discover_program_files()
            apps.extend(program_apps)
            logger.info(f"Found {len(program_apps)} apps from Program Files")
        except Exception as e:
            logger.warning(f"Error scanning Program Files: {e}")
        
        try:
            # 4. System32 applications
            logger.info("Scanning System32...")
            system_apps = self._discover_system32_apps()
            apps.extend(system_apps)
            logger.info(f"Found {len(system_apps)} system apps")
        except Exception as e:
            logger.warning(f"Error scanning System32: {e}")
        
        try:
            # 5. Portable applications
            logger.info("Scanning portable applications...")
            portable_apps = self._discover_portable_apps()
            apps.extend(portable_apps)
            logger.info(f"Found {len(portable_apps)} portable apps")
        except Exception as e:
            logger.warning(f"Error scanning portable apps: {e}")
        
        try:
            # 6. Microsoft Store apps (may fail due to permissions)
            logger.info("Scanning Microsoft Store apps...")
            store_apps = self._discover_store_apps()
            apps.extend(store_apps)
            logger.info(f"Found {len(store_apps)} Store apps")
        except Exception as e:
            logger.warning(f"Error scanning Store apps: {e}")
        
        try:
            # 7. Environment PATH applications
            logger.info("Scanning PATH applications...")
            path_apps = self._discover_path_apps()
            apps.extend(path_apps)
            logger.info(f"Found {len(path_apps)} PATH apps")
        except Exception as e:
            logger.warning(f"Error scanning PATH apps: {e}")
        
        try:
            # 8. PowerShell-based discovery (fallback)
            logger.info("Using PowerShell for additional discovery...")
            ps_apps = self._discover_powershell_apps()
            apps.extend(ps_apps)
            logger.info(f"Found {len(ps_apps)} apps via PowerShell")
        except Exception as e:
            logger.warning(f"Error using PowerShell discovery: {e}")
        
        # Remove duplicates and clean up
        logger.info(f"Total apps found before deduplication: {len(apps)}")
        return self._clean_and_deduplicate(apps)
    
    def _discover_start_menu(self):
        """Discover applications from Start Menu shortcuts"""
        apps = []
        start_dirs = [
            os.path.join(os.environ.get("APPDATA", ""), "Microsoft", "Windows", "Start Menu", "Programs"),
            os.path.join(os.environ.get("PROGRAMDATA", ""), "Microsoft", "Windows", "Start Menu", "Programs"),
            os.path.join(os.environ.get("USERPROFILE", ""), "AppData", "Roaming", "Microsoft", "Windows", "Start Menu", "Programs")
        ]
        
        for start_dir in start_dirs:
            if not os.path.isdir(start_dir):
                continue
                
            for root, dirs, files in os.walk(start_dir):
                for file in files:
                    if file.lower().endswith(".lnk"):
                        name = os.path.splitext(file)[0]
                        full_path = os.path.join(root, file)
                        target = resolve_lnk(full_path)
                        
                        if target and os.path.exists(target):
                            # Create aliases from the name
                            aliases = [name.lower(), name.lower().replace(" ", ""), name.lower().replace(" ", "-")]
                            
                            apps.append({
                                "name": name,
                                "exec": target,
                                "aliases": aliases,
                                "category": "start_menu",
                                "icon": None
                            })
        
        return apps
    
    def _discover_registry_apps(self):
        """Discover applications from Windows Registry"""
        apps = []
        
        # Registry keys to check for installed applications
        registry_keys = [
            (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall"),
            (winreg.HKEY_CURRENT_USER, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall"),
            (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall"),
        ]
        
        for hkey, subkey in registry_keys:
            try:
                with winreg.OpenKey(hkey, subkey) as key:
                    for i in range(winreg.QueryInfoKey(key)[0]):
                        try:
                            subkey_name = winreg.EnumKey(key, i)
                            with winreg.OpenKey(key, subkey_name) as subkey_handle:
                                try:
                                    display_name = winreg.QueryValueEx(subkey_handle, "DisplayName")[0]
                                    install_location = winreg.QueryValueEx(subkey_handle, "InstallLocation")[0]
                                    display_icon = winreg.QueryValueEx(subkey_handle, "DisplayIcon")[0]
                                    
                                    # Find executable in install location
                                    if install_location and os.path.exists(install_location):
                                        exe_path = self._find_executable_in_dir(install_location)
                                        if exe_path:
                                            aliases = [
                                                display_name.lower(),
                                                display_name.lower().replace(" ", ""),
                                                display_name.lower().replace(" ", "-"),
                                                os.path.splitext(os.path.basename(exe_path))[0].lower()
                                            ]
                                            
                                            apps.append({
                                                "name": display_name,
                                                "exec": exe_path,
                                                "aliases": aliases,
                                                "category": "installed",
                                                "icon": display_icon if display_icon else None
                                            })
                                except FileNotFoundError:
                                    continue
                        except OSError:
                            continue
            except OSError:
                continue
        
        return apps
    
    def _discover_program_files(self):
        """Discover applications from Program Files directories"""
        apps = []
        program_dirs = [
            os.environ.get("PROGRAMFILES", "C:\\Program Files"),
            os.environ.get("PROGRAMFILES(X86)", "C:\\Program Files (x86)"),
            os.path.join(os.environ.get("USERPROFILE", ""), "AppData", "Local", "Programs")
        ]
        
        for program_dir in program_dirs:
            if not os.path.exists(program_dir):
                continue
                
            for root, dirs, files in os.walk(program_dir):
                for file in files:
                    if file.lower().endswith((".exe", ".bat", ".cmd")):
                        full_path = os.path.join(root, file)
                        name = os.path.splitext(file)[0]
                        
                        # Skip system files and common non-app executables
                        if self._is_system_file(name):
                            continue
                        
                        aliases = [
                            name.lower(),
                            name.lower().replace(" ", ""),
                            name.lower().replace(" ", "-")
                        ]
                        
                        apps.append({
                            "name": name,
                            "exec": full_path,
                            "aliases": aliases,
                            "category": "program_files",
                            "icon": None
                        })
        
        return apps
    
    def _discover_system32_apps(self):
        """Discover system applications from System32"""
        apps = []
        system32_path = os.path.join(os.environ.get("WINDIR", "C:\\Windows"), "System32")
        
        if not os.path.exists(system32_path):
            return apps
        
        # Common system applications that users might want to launch
        system_apps = [
            "calc.exe", "notepad.exe", "mspaint.exe", "mstsc.exe", "taskmgr.exe",
            "control.exe", "appwiz.cpl", "desk.cpl", "sysdm.cpl", "ncpa.cpl",
            "firewall.cpl", "powercfg.cpl", "timedate.cpl", "intl.cpl"
        ]
        
        for app in system_apps:
            app_path = os.path.join(system32_path, app)
            if os.path.exists(app_path):
                name = os.path.splitext(app)[0]
                aliases = [name.lower(), name.lower().replace(" ", "")]
                
                apps.append({
                    "name": name,
                    "exec": app_path,
                    "aliases": aliases,
                    "category": "system",
                    "icon": None
                })
        
        return apps
    
    def _discover_portable_apps(self):
        """Discover portable applications from common locations"""
        apps = []
        
        # Universal portable app directories
        portable_dirs = []
        
        # Get user directories dynamically
        home_dir = os.path.expanduser("~")
        portable_dirs.extend([
            os.path.join(home_dir, "Desktop"),
            os.path.join(home_dir, "Downloads"),
            os.path.join(home_dir, "PortableApps"),
            os.path.join(home_dir, "Apps"),
            os.path.join(home_dir, "Applications")
        ])
        
        # Platform-specific directories
        if self.system == "windows":
            # Windows drive letters
            for drive in "CDEFGHIJKLMNOPQRSTUVWXYZ":
                portable_dirs.extend([
                    f"{drive}:\\PortableApps",
                    f"{drive}:\\Apps",
                    f"{drive}:\\Applications"
                ])
        elif self.system == "darwin":
            # macOS directories
            portable_dirs.extend([
                "/Applications/Portable",
                "/usr/local/bin",
                "/opt"
            ])
        else:
            # Linux directories
            portable_dirs.extend([
                "/opt",
                "/usr/local/bin",
                "/usr/bin",
                "/snap/bin"
            ])
        
        for portable_dir in portable_dirs:
            if not os.path.exists(portable_dir):
                continue
                
            for root, dirs, files in os.walk(portable_dir):
                for file in files:
                    if file.lower().endswith(".exe") and not self._is_system_file(file):
                        full_path = os.path.join(root, file)
                        name = os.path.splitext(file)[0]
                        
                        aliases = [
                            name.lower(),
                            name.lower().replace(" ", ""),
                            name.lower().replace(" ", "-")
                        ]
                        
                        apps.append({
                            "name": name,
                            "exec": full_path,
                            "aliases": aliases,
                            "category": "portable",
                            "icon": None
                        })
        
        return apps
    
    def _discover_store_apps(self):
        """Discover Microsoft Store applications"""
        apps = []
        
        # Common Store app locations
        store_dirs = [
            os.path.join(os.environ.get("PROGRAMFILES", ""), "WindowsApps"),
            os.path.join(os.environ.get("LOCALAPPDATA", ""), "Microsoft", "WindowsApps")
        ]
        
        for store_dir in store_dirs:
            if not os.path.exists(store_dir):
                continue
                
            try:
                for item in os.listdir(store_dir):
                    if os.path.isdir(os.path.join(store_dir, item)):
                        # Look for executable in the app directory
                        exe_path = self._find_executable_in_dir(os.path.join(store_dir, item))
                        if exe_path:
                            # Extract app name (remove version numbers and publisher info)
                            name = self._clean_store_app_name(item)
                            aliases = [name.lower(), name.lower().replace(" ", "")]
                            
                            apps.append({
                                "name": name,
                                "exec": exe_path,
                                "aliases": aliases,
                                "category": "store",
                                "icon": None
                            })
            except (PermissionError, OSError) as e:
                logger.warning(f"Access denied to {store_dir}: {e}")
                continue
        
        return apps
    
    def _discover_path_apps(self):
        """Discover applications from PATH environment variable"""
        apps = []
        path_dirs = os.environ.get("PATH", "").split(os.pathsep)
        
        for path_dir in path_dirs:
            if not os.path.exists(path_dir):
                continue
                
            try:
                for file in os.listdir(path_dir):
                    if file.lower().endswith((".exe", ".bat", ".cmd")):
                        full_path = os.path.join(path_dir, file)
                        name = os.path.splitext(file)[0]
                        
                        if not self._is_system_file(name):
                            aliases = [name.lower(), name.lower().replace(" ", "")]
                            
                            apps.append({
                                "name": name,
                                "exec": full_path,
                                "aliases": aliases,
                                "category": "path",
                                "icon": None
                            })
            except (OSError, PermissionError):
                continue
        
        return apps
    
    def _discover_powershell_apps(self):
        """Discover applications using PowerShell (Windows fallback)"""
        apps = []
        
        try:
            # PowerShell command to get installed applications
            ps_command = """
            Get-WmiObject -Class Win32_Product | Select-Object Name, InstallLocation | 
            Where-Object { $_.Name -ne $null -and $_.InstallLocation -ne $null } |
            ForEach-Object { 
                $name = $_.Name
                $location = $_.InstallLocation
                $exe = Get-ChildItem -Path $location -Filter "*.exe" -Recurse -ErrorAction SilentlyContinue | 
                       Select-Object -First 1 -ExpandProperty FullName
                if ($exe) {
                    [PSCustomObject]@{
                        Name = $name
                        Executable = $exe
                    }
                }
            } | ConvertTo-Json
            """
            
            result = subprocess.run(
                ["powershell", "-Command", ps_command],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0 and result.stdout.strip():
                import json
                ps_apps = json.loads(result.stdout)
                
                if isinstance(ps_apps, list):
                    for app in ps_apps:
                        if app.get("Name") and app.get("Executable"):
                            name = app["Name"]
                            exec_path = app["Executable"]
                            
                            aliases = [
                                name.lower(),
                                name.lower().replace(" ", ""),
                                name.lower().replace(" ", "-"),
                                os.path.splitext(os.path.basename(exec_path))[0].lower()
                            ]
                            
                            apps.append({
                                "name": name,
                                "exec": exec_path,
                                "aliases": aliases,
                                "category": "powershell",
                                "icon": None
                            })
        
        except Exception as e:
            logger.debug(f"PowerShell discovery failed: {e}")
        
        return apps
    
    def _discover_mac(self):
        """Comprehensive macOS application discovery"""
        logger.info("Discovering macOS applications...")
        apps = []
        
        # System Applications
        system_apps_dir = "/Applications"
        user_apps_dir = os.path.expanduser("~/Applications")
        
        for apps_dir in [system_apps_dir, user_apps_dir]:
            if not os.path.exists(apps_dir):
                continue
                
            for item in os.listdir(apps_dir):
                if item.endswith(".app"):
                    app_path = os.path.join(apps_dir, item)
                    name = item.replace(".app", "")
                    
                    # Find executable
                    exec_path = os.path.join(app_path, "Contents", "MacOS")
                    exe = None
                    
                    if os.path.exists(exec_path):
                        for inner_file in os.listdir(exec_path):
                            exe = os.path.join(exec_path, inner_file)
                            break
                    
                    if exe:
                        aliases = [
                            name.lower(),
                            name.lower().replace(" ", ""),
                            name.lower().replace(" ", "-")
                        ]
                        
                        apps.append({
                            "name": name,
                            "exec": exe,
                            "aliases": aliases,
                            "category": "mac_app",
                            "icon": None
                        })
        
        return apps
    
    def _discover_linux(self):
        """Comprehensive Linux application discovery"""
        logger.info("Discovering Linux applications...")
        apps = []
        
        # Desktop files
        desktop_dirs = [
            "/usr/share/applications",
            "/usr/local/share/applications",
            os.path.expanduser("~/.local/share/applications"),
            "/var/lib/snapd/desktop/applications"
        ]
        
        for desktop_dir in desktop_dirs:
            if not os.path.exists(desktop_dir):
                continue
                
            for file in os.listdir(desktop_dir):
                if file.endswith(".desktop"):
                    desktop_path = os.path.join(desktop_dir, file)
                    
                    try:
                        with open(desktop_path, "r", encoding="utf-8", errors="ignore") as f:
                            content = f.read()
                        
                        name = None
                        exec_cmd = None
                        icon = None
                        categories = []
                        
                        for line in content.splitlines():
                            if line.startswith("Name="):
                                name = line.split("=", 1)[1].strip()
                            elif line.startswith("Exec="):
                                exec_cmd = line.split("=", 1)[1].strip().split("%")[0].strip()
                            elif line.startswith("Icon="):
                                icon = line.split("=", 1)[1].strip()
                            elif line.startswith("Categories="):
                                categories = line.split("=", 1)[1].strip().split(";")
                        
                        if name and exec_cmd:
                            aliases = [
                                name.lower(),
                                name.lower().replace(" ", ""),
                                name.lower().replace(" ", "-")
                            ]
                            
                            apps.append({
                                "name": name,
                                "exec": exec_cmd,
                                "aliases": aliases,
                                "category": "desktop",
                                "icon": icon
                            })
                    except Exception as e:
                        logger.debug(f"Error reading desktop file {desktop_path}: {e}")
                        continue
        
        return apps
    
    def _find_executable_in_dir(self, directory):
        """Find the first executable file in a directory"""
        if not os.path.exists(directory):
            return None
        
        for root, dirs, files in os.walk(directory):
            for file in files:
                if file.lower().endswith((".exe", ".bat", ".cmd")):
                    return os.path.join(root, file)
        return None
    
    def _is_system_file(self, filename):
        """Check if a file is a system file that shouldn't be launched directly"""
        system_files = {
            "svchost", "winlogon", "csrss", "lsass", "smss", "wininit",
            "dwm", "explorer", "conhost", "audiodg", "spoolsv", "services"
        }
        return filename.lower() in system_files
    
    def _clean_store_app_name(self, name):
        """Clean Microsoft Store app names by removing version and publisher info"""
        # Remove version numbers and publisher info
        parts = name.split("_")
        if len(parts) >= 2:
            return parts[0]
        return name
    
    def _clean_and_deduplicate(self, apps):
        """Remove duplicates and clean up the apps list"""
        seen = set()
        cleaned_apps = []
        
        for app in apps:
            # Create a unique key based on name and executable path
            key = (app.get("name", "").lower(), app.get("exec", ""))
            
            if key not in seen and app.get("exec") and os.path.exists(app.get("exec", "")):
                seen.add(key)
                cleaned_apps.append(app)
        
        # Sort by name for better organization
        cleaned_apps.sort(key=lambda x: x.get("name", "").lower())
        
        logger.info(f"Cleaned and deduplicated to {len(cleaned_apps)} unique applications")
        return cleaned_apps
