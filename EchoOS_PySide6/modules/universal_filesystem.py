"""
Universal File System Adapter for EchoOS
Provides cross-platform file operations that work on any file system
"""

import os
import sys
import platform
import logging
import shutil
import pathlib
from typing import List, Dict, Optional, Tuple, Any
from pathlib import Path

class UniversalFileSystem:
    """Universal file system operations that work on any platform"""
    
    def __init__(self):
        self.system = platform.system().lower()
        self.logger = logging.getLogger(__name__)
        
        # Platform-specific paths and settings
        self.platform_config = self._initialize_platform_config()
        
        # Common directories that exist on most systems
        self.common_dirs = self._get_common_directories()
        
        # File type mappings
        self.file_types = self._get_file_type_mappings()
        
    def _initialize_platform_config(self) -> Dict[str, Any]:
        """Initialize platform-specific configuration"""
        config = {
            "separator": os.sep,
            "path_separator": os.pathsep,
            "home_dir": str(Path.home()),
            "temp_dir": str(Path.cwd() / "temp")  # Use current directory temp
        }
        
        if self.system == "windows":
            config.update({
                "program_files": os.environ.get("ProgramFiles", "C:\\Program Files"),
                "program_files_x86": os.environ.get("ProgramFiles(x86)", "C:\\Program Files (x86)"),
                "appdata": os.environ.get("APPDATA", ""),
                "localappdata": os.environ.get("LOCALAPPDATA", ""),
                "desktop": os.path.join(os.environ.get("USERPROFILE", ""), "Desktop"),
                "documents": os.path.join(os.environ.get("USERPROFILE", ""), "Documents"),
                "downloads": os.path.join(os.environ.get("USERPROFILE", ""), "Downloads"),
                "pictures": os.path.join(os.environ.get("USERPROFILE", ""), "Pictures"),
                "music": os.path.join(os.environ.get("USERPROFILE", ""), "Music"),
                "videos": os.path.join(os.environ.get("USERPROFILE", ""), "Videos")
            })
        elif self.system == "darwin":  # macOS
            config.update({
                "applications": "/Applications",
                "user_applications": os.path.join(os.path.expanduser("~"), "Applications"),
                "desktop": os.path.join(os.path.expanduser("~"), "Desktop"),
                "documents": os.path.join(os.path.expanduser("~"), "Documents"),
                "downloads": os.path.join(os.path.expanduser("~"), "Downloads"),
                "pictures": os.path.join(os.path.expanduser("~"), "Pictures"),
                "music": os.path.join(os.path.expanduser("~"), "Music"),
                "movies": os.path.join(os.path.expanduser("~"), "Movies"),
                "library": os.path.join(os.path.expanduser("~"), "Library")
            })
        else:  # Linux
            config.update({
                "applications": "/usr/share/applications",
                "user_applications": os.path.join(os.path.expanduser("~"), ".local", "share", "applications"),
                "desktop": os.path.join(os.path.expanduser("~"), "Desktop"),
                "documents": os.path.join(os.path.expanduser("~"), "Documents"),
                "downloads": os.path.join(os.path.expanduser("~"), "Downloads"),
                "pictures": os.path.join(os.path.expanduser("~"), "Pictures"),
                "music": os.path.join(os.path.expanduser("~"), "Music"),
                "videos": os.path.join(os.path.expanduser("~"), "Videos"),
                "bin": "/usr/bin",
                "local_bin": os.path.join(os.path.expanduser("~"), ".local", "bin")
            })
        
        return config
    
    def _get_common_directories(self) -> Dict[str, str]:
        """Get common directories that exist on most systems"""
        return {
            "home": self.platform_config["home_dir"],
            "desktop": self.platform_config.get("desktop", ""),
            "documents": self.platform_config.get("documents", ""),
            "downloads": self.platform_config.get("downloads", ""),
            "pictures": self.platform_config.get("pictures", ""),
            "music": self.platform_config.get("music", ""),
            "videos": self.platform_config.get("videos", ""),
            "temp": self.platform_config["temp_dir"]
        }
    
    def _get_file_type_mappings(self) -> Dict[str, List[str]]:
        """Get file type mappings for different categories"""
        return {
            "images": [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".tiff", ".svg", ".webp"],
            "documents": [".txt", ".doc", ".docx", ".pdf", ".rtf", ".odt", ".pages"],
            "spreadsheets": [".xls", ".xlsx", ".csv", ".ods", ".numbers"],
            "presentations": [".ppt", ".pptx", ".odp", ".key"],
            "videos": [".mp4", ".avi", ".mov", ".wmv", ".flv", ".webm", ".mkv"],
            "audio": [".mp3", ".wav", ".flac", ".aac", ".ogg", ".m4a"],
            "archives": [".zip", ".rar", ".7z", ".tar", ".gz", ".bz2"],
            "code": [".py", ".js", ".html", ".css", ".java", ".cpp", ".c", ".php", ".rb", ".go"],
            "executables": [".exe", ".app", ".deb", ".rpm", ".msi", ".dmg", ".pkg"]
        }
    
    def get_current_directory(self) -> str:
        """Get current working directory"""
        return str(Path.cwd())
    
    def list_directory(self, path: str = None) -> List[Dict[str, Any]]:
        """List contents of a directory with detailed information"""
        if path is None:
            path = self.get_current_directory()
        
        try:
            path_obj = Path(path)
            if not path_obj.exists():
                return []
            
            items = []
            for item in path_obj.iterdir():
                try:
                    stat = item.stat()
                    items.append({
                        "name": item.name,
                        "path": str(item),
                        "is_file": item.is_file(),
                        "is_dir": item.is_dir(),
                        "size": stat.st_size if item.is_file() else 0,
                        "modified": stat.st_mtime,
                        "extension": item.suffix.lower(),
                        "type": self._get_file_type(item.suffix.lower())
                    })
                except (OSError, PermissionError):
                    # Skip items we can't access
                    continue
            
            return sorted(items, key=lambda x: (not x["is_dir"], x["name"].lower()))
            
        except Exception as e:
            self.logger.error(f"Error listing directory {path}: {e}")
            return []
    
    def _get_file_type(self, extension: str) -> str:
        """Get file type category from extension"""
        for file_type, extensions in self.file_types.items():
            if extension in extensions:
                return file_type
        return "unknown"
    
    def navigate_to_directory(self, target: str) -> Tuple[bool, str]:
        """Navigate to a directory, handling various input formats"""
        target = target.strip()
        
        # Handle special directory names
        special_dirs = {
            "home": self.platform_config["home_dir"],
            "desktop": self.platform_config.get("desktop", ""),
            "documents": self.platform_config.get("documents", ""),
            "downloads": self.platform_config.get("downloads", ""),
            "pictures": self.platform_config.get("pictures", ""),
            "music": self.platform_config.get("music", ""),
            "videos": self.platform_config.get("videos", ""),
            "temp": self.platform_config["temp_dir"],
            "current": self.get_current_directory(),
            "parent": str(Path.cwd().parent),
            "root": str(Path.cwd().anchor)
        }
        
        if target.lower() in special_dirs:
            target_path = special_dirs[target.lower()]
        else:
            # Try to find directory by name in current location
            target_path = self._find_directory_by_name(target)
        
        if target_path and Path(target_path).exists():
            try:
                os.chdir(target_path)
                return True, target_path
            except Exception as e:
                self.logger.error(f"Error navigating to {target_path}: {e}")
                return False, str(e)
        
        return False, f"Directory '{target}' not found"
    
    def _find_directory_by_name(self, name: str) -> Optional[str]:
        """Find a directory by name in current and common locations"""
        # Search in current directory
        current_dir = Path.cwd()
        for item in current_dir.iterdir():
            if item.is_dir() and item.name.lower() == name.lower():
                return str(item)
        
        # Search in common directories
        for dir_path in self.common_dirs.values():
            if dir_path and Path(dir_path).exists():
                try:
                    for item in Path(dir_path).iterdir():
                        if item.is_dir() and item.name.lower() == name.lower():
                            return str(item)
                except (OSError, PermissionError):
                    continue
        
        return None
    
    def create_directory(self, name: str, parent_path: str = None) -> Tuple[bool, str]:
        """Create a new directory"""
        if parent_path is None:
            parent_path = self.get_current_directory()
        
        try:
            new_dir = Path(parent_path) / name
            new_dir.mkdir(parents=True, exist_ok=True)
            return True, str(new_dir)
        except Exception as e:
            self.logger.error(f"Error creating directory {name}: {e}")
            return False, str(e)
    
    def create_file(self, name: str, content: str = "", parent_path: str = None) -> Tuple[bool, str]:
        """Create a new file"""
        if parent_path is None:
            parent_path = self.get_current_directory()
        
        try:
            new_file = Path(parent_path) / name
            new_file.write_text(content, encoding='utf-8')
            return True, str(new_file)
        except Exception as e:
            self.logger.error(f"Error creating file {name}: {e}")
            return False, str(e)
    
    def delete_item(self, path: str) -> Tuple[bool, str]:
        """Delete a file or directory"""
        try:
            item_path = Path(path)
            if item_path.exists():
                if item_path.is_file():
                    item_path.unlink()
                elif item_path.is_dir():
                    shutil.rmtree(item_path)
                return True, f"Deleted {item_path.name}"
            else:
                return False, f"Item not found: {path}"
        except Exception as e:
            self.logger.error(f"Error deleting {path}: {e}")
            return False, str(e)
    
    def rename_item(self, old_path: str, new_name: str) -> Tuple[bool, str]:
        """Rename a file or directory"""
        try:
            old_item = Path(old_path)
            if old_item.exists():
                new_item = old_item.parent / new_name
                old_item.rename(new_item)
                return True, str(new_item)
            else:
                return False, f"Item not found: {old_path}"
        except Exception as e:
            self.logger.error(f"Error renaming {old_path}: {e}")
            return False, str(e)
    
    def copy_item(self, source: str, destination: str) -> Tuple[bool, str]:
        """Copy a file or directory"""
        try:
            source_path = Path(source)
            dest_path = Path(destination)
            
            if source_path.exists():
                if source_path.is_file():
                    shutil.copy2(source_path, dest_path)
                elif source_path.is_dir():
                    shutil.copytree(source_path, dest_path, dirs_exist_ok=True)
                return True, str(dest_path)
            else:
                return False, f"Source not found: {source}"
        except Exception as e:
            self.logger.error(f"Error copying {source} to {destination}: {e}")
            return False, str(e)
    
    def move_item(self, source: str, destination: str) -> Tuple[bool, str]:
        """Move a file or directory"""
        try:
            source_path = Path(source)
            dest_path = Path(destination)
            
            if source_path.exists():
                shutil.move(str(source_path), str(dest_path))
                return True, str(dest_path)
            else:
                return False, f"Source not found: {source}"
        except Exception as e:
            self.logger.error(f"Error moving {source} to {destination}: {e}")
            return False, str(e)
    
    def search_files(self, query: str, search_path: str = None, file_types: List[str] = None) -> List[Dict[str, Any]]:
        """Search for files matching query"""
        if search_path is None:
            search_path = self.get_current_directory()
        
        results = []
        search_path_obj = Path(search_path)
        
        if not search_path_obj.exists():
            return results
        
        try:
            for item in search_path_obj.rglob("*"):
                try:
                    if item.is_file():
                        # Check if filename matches query
                        if query.lower() in item.name.lower():
                            # Check file type filter
                            if file_types is None or item.suffix.lower() in file_types:
                                results.append({
                                    "name": item.name,
                                    "path": str(item),
                                    "size": item.stat().st_size,
                                    "modified": item.stat().st_mtime,
                                    "extension": item.suffix.lower(),
                                    "type": self._get_file_type(item.suffix.lower())
                                })
                except (OSError, PermissionError):
                    continue
        except Exception as e:
            self.logger.error(f"Error searching files: {e}")
        
        return sorted(results, key=lambda x: x["name"].lower())
    
    def get_directory_info(self, path: str = None) -> Dict[str, Any]:
        """Get information about a directory"""
        if path is None:
            path = self.get_current_directory()
        
        try:
            path_obj = Path(path)
            if not path_obj.exists():
                return {}
            
            contents = self.list_directory(path)
            file_count = sum(1 for item in contents if item["is_file"])
            dir_count = sum(1 for item in contents if item["is_dir"])
            total_size = sum(item["size"] for item in contents if item["is_file"])
            
            return {
                "path": str(path_obj),
                "name": path_obj.name,
                "exists": True,
                "file_count": file_count,
                "directory_count": dir_count,
                "total_size": total_size,
                "contents": contents,
                "parent": str(path_obj.parent) if path_obj.parent != path_obj else None,
                "is_root": str(path_obj.parent) == str(path_obj)
            }
        except Exception as e:
            self.logger.error(f"Error getting directory info for {path}: {e}")
            return {"path": path, "exists": False, "error": str(e)}
    
    def get_common_locations(self) -> Dict[str, str]:
        """Get common file system locations"""
        return {
            "current_directory": self.get_current_directory(),
            **self.common_dirs,
            "platform_config": self.platform_config
        }
    
    def validate_path(self, path: str) -> Tuple[bool, str]:
        """Validate if a path exists and is accessible"""
        try:
            path_obj = Path(path)
            if path_obj.exists():
                return True, "Path exists and is accessible"
            else:
                return False, "Path does not exist"
        except Exception as e:
            return False, f"Invalid path: {e}"
    
    def get_file_info(self, path: str) -> Dict[str, Any]:
        """Get detailed information about a file"""
        try:
            path_obj = Path(path)
            if not path_obj.exists():
                return {"exists": False, "path": path}
            
            stat = path_obj.stat()
            return {
                "exists": True,
                "name": path_obj.name,
                "path": str(path_obj),
                "size": stat.st_size,
                "modified": stat.st_mtime,
                "created": stat.st_ctime,
                "extension": path_obj.suffix.lower(),
                "type": self._get_file_type(path_obj.suffix.lower()),
                "is_file": path_obj.is_file(),
                "is_dir": path_obj.is_dir(),
                "is_symlink": path_obj.is_symlink(),
                "parent": str(path_obj.parent)
            }
        except Exception as e:
            self.logger.error(f"Error getting file info for {path}: {e}")
            return {"exists": False, "path": path, "error": str(e)}
