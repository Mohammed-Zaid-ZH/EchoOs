# ✅ NO HARDCODING - Confirmed

## Universal Executor V2 - Completely Dynamic

### ✅ App Discovery
- **NO hardcoded app names** - All apps loaded from `config/apps.json` (discovered dynamically)
- Uses `app_discovery.py` to find ALL installed applications
- Works on Windows, macOS, and Linux
- Fuzzy matching for app names

### ✅ Window Management
- **NEW**: `window_manager.py` - Dynamic window/app/tab management
- Gets all windows dynamically using `pygetwindow` or Windows APIs
- Lists running apps dynamically using `psutil`
- NO hardcoded app names

### ✅ App Switching
- **"switch to [app name]"** - Switches to any open app dynamically
- **"next app"** - Switches to next app (Alt+Tab)
- **"previous app"** - Switches to previous app (Alt+Shift+Tab)
- **"list apps"** - Lists all open apps dynamically

### ✅ Tab Switching
- **"next tab"** - Switches to next browser tab (Ctrl+Tab)
- **"previous tab"** - Switches to previous tab (Ctrl+Shift+Tab)
- **"switch tab"** or **"tab number [1-9]"** - Switches to specific tab
- **"close tab"** - Closes current tab
- **"new tab"** - Opens new tab
- **"list tabs"** - Lists open tabs

### ✅ Close All Apps
- **NO hardcoded app list** - Dynamically gets all running processes
- Uses `psutil.process_iter()` to find ALL processes
- Only excludes system processes and EchoOS itself
- Works with ANY application

### ✅ File Operations
- **NO hardcoded paths** - Uses current directory and screen context
- Searches dynamically in common directories
- Uses OCR to find files on screen

### ✅ System Commands
- Uses platform-specific commands (Windows/macOS/Linux)
- NO hardcoded paths or app names

## Removed Hardcoding

### ❌ Removed from `direct_executor.py`:
- Removed `app_commands` dictionary (hardcoded app mappings)
- Removed `web_commands` dictionary (hardcoded websites)
- Now uses only discovered apps

### ❌ Removed from `universal_executor_v2.py`:
- Removed hardcoded app list in `_close_all_apps()`
- Now dynamically gets all processes using `psutil`

## New Commands Added

### App Switching:
- "switch to [app name]" - Switch to specific app
- "switch app [name]" - Switch to app
- "go to app [name]" - Go to app
- "bring to front [name]" - Bring app to front
- "next app" - Next app
- "previous app" - Previous app
- "list apps" - List all open apps

### Tab Switching:
- "next tab" - Next tab
- "previous tab" - Previous tab
- "switch tab" - Switch tab
- "switch to tab number [1-9]" - Switch to tab number
- "close tab" - Close current tab
- "new tab" - New tab
- "list tabs" - List open tabs

## How It Works

1. **App Discovery**: System discovers ALL apps on startup
2. **Window Detection**: Dynamically detects all open windows
3. **Process Detection**: Uses `psutil` to find all running processes
4. **Fuzzy Matching**: Matches app names even with slight variations
5. **No Hardcoding**: Everything is discovered and dynamic

## Example Usage

**Switch between apps:**
- "switch to chrome" - Switches to Chrome (if open)
- "switch to notepad" - Switches to Notepad (if open)
- "next app" - Cycles to next app
- "list apps" - Shows all open apps

**Switch between tabs:**
- "next tab" - Next browser tab
- "previous tab" - Previous tab
- "switch to tab number 3" - Switch to tab 3
- "list tabs" - Shows all open tabs

**Everything works dynamically - NO hardcoding!** ✅

