# EchoOS - Universal Voice-Controlled Operating System

## 🎯 Project Overview

EchoOS is a **hands-free PC automation system** that uses voice commands to control your computer. It works **entirely offline**, requires **no internet connection**, and is designed to work on **any laptop/system** without hardcoding.

**Key Principle**: Everything is discovered dynamically - no hardcoding. The system adapts to any Windows, macOS, or Linux system automatically.

## 🔐 Authentication - Main Pillar

**Authentication is a MAIN PILLAR of this project** and is fully enforced:

- ✅ **Voice-based authentication** using Resemblyzer (or MFCC fallback)
- ✅ **Session management** (30-minute timeout)
- ✅ **Security features** (failed attempt tracking, account lockout)
- ✅ **ALL commands require authentication** - no bypasses
- ✅ **Session validation** before every command execution

**You MUST authenticate before using any voice commands!**

## ✅ Current Status (Latest Updates)

### What's Working

1. **✅ Universal Command Execution**
   - Works on any system (Windows, macOS, Linux)
   - No hardcoding - all apps discovered dynamically
   - Screen-aware command execution using OCR
   - Complete command coverage

2. **✅ App/Tab Switching**
   - Switch between any open applications
   - Switch between browser tabs
   - List open apps and tabs
   - Dynamic window management

3. **✅ Screen Understanding**
   - OCR-based screen reading (Tesseract)
   - Detects files/folders visible on screen
   - Understands current application context
   - Context-aware command execution

4. **✅ Complete Command Coverage**
   - System control (shutdown, restart, lock, volume, system info, battery)
   - File operations (open, create, delete, navigate, list)
   - Application control (open/close any app, switch apps)
   - Media control (play, pause, stop, next, previous)
   - Text operations (type, copy all, paste all, select all)
   - Navigation (scroll, click, zoom)
   - Web operations (search, open websites, tab management)
   - Command prompt (open CMD, execute commands, type commands)

5. **✅ Enhanced Speech Recognition**
   - Better error correction
   - Fuzzy matching for commands
   - Improved accuracy

6. **✅ Authentication System**
   - Voice-based authentication
   - Session management
   - Security features
   - Fully enforced on all commands

## 🚀 Quick Start

### 1. Install Dependencies
```bash
cd EchoOS_PySide6
pip install -r requirements.txt
```

### 2. Install Tesseract OCR (Optional but Recommended)
- **Windows**: Download from https://github.com/UB-Mannheim/tesseract/wiki
- **macOS**: `brew install tesseract`
- **Linux**: `sudo apt-get install tesseract-ocr`

### 3. Run EchoOS
```bash
python main.py
```

### 4. Register User (First Time)
1. Go to "User Manager" tab
2. Click "Register User"
3. Enter username
4. Speak clearly for 3 samples (5 seconds each)

### 5. Authenticate
1. Click "Wake / Authenticate"
2. Speak clearly for 5 seconds
3. Wait for "Access granted" message

### 6. Start Using Voice Commands
1. Click "Start Listening"
2. Speak your commands
3. Commands will execute (if authenticated)

## 📋 Available Voice Commands

### System Control
- **"lock screen"** - Locks the screen
- **"shutdown"** - Shuts down system (10 second delay)
- **"restart"** - Restarts system
- **"sleep"** - Puts system to sleep
- **"volume up"** / **"volume down"** / **"mute"** - Volume control
- **"system info"** - Shows system information
- **"battery status"** - Shows battery level
- **"disk space"** - Shows disk usage
- **"memory usage"** - Shows memory usage
- **"cpu usage"** - Shows CPU usage

### File Operations
- **"open file [filename]"** - Opens file (checks screen first, then searches)
- **"create file [filename]"** - Creates new file
- **"delete file [filename]"** - Deletes file
- **"create folder [name]"** - Creates new folder
- **"navigate to [directory]"** or **"go to [directory]"** - Changes directory
- **"list files"** - Lists files in current directory
- **"save file"** - Saves current file (Ctrl+S)

### Application Control
- **"open [app name]"** - Opens any discovered application
- **"close app"** or **"close [app name]"** - Closes application
- **"close all apps"** - Closes all apps except EchoOS
- **"switch to [app name]"** - Switches to specific app
- **"switch app [name]"** - Switches to app
- **"next app"** - Switches to next app (Alt+Tab)
- **"previous app"** - Switches to previous app (Alt+Shift+Tab)
- **"list apps"** - Lists all open applications
- **"minimize"** - Minimizes current window
- **"maximize"** - Maximizes current window

### Tab Switching (Browser)
- **"next tab"** - Switches to next browser tab (Ctrl+Tab)
- **"previous tab"** - Switches to previous tab (Ctrl+Shift+Tab)
- **"switch tab"** or **"tab number [1-9]"** - Switches to specific tab
- **"close tab"** - Closes current tab
- **"new tab"** - Opens new tab
- **"list tabs"** - Lists open tabs

### Media Control
- **"play"** - Plays media
- **"pause"** - Pauses media
- **"stop"** - Stops media
- **"next"** - Next track
- **"previous"** - Previous track
- **"start from beginning"** - Restarts media from beginning

### Text Operations
- **"type [text]"** - Types text at cursor position
- **"select all"** - Selects all text
- **"copy all"** - Copies all text
- **"paste all"** - Pastes text
- **"cut"** - Cuts selected text
- **"undo"** - Undoes last action
- **"redo"** - Redoes last action

### Navigation
- **"scroll up"** / **"scroll down"** - Scrolls page
- **"click"** - Clicks at cursor position
- **"double click"** - Double clicks
- **"right click"** - Right clicks
- **"zoom in"** / **"zoom out"** - Zooms page

### Web Operations
- **"search [query]"** - Searches Google
- **"search youtube [query]"** - Searches YouTube
- **"search amazon [query]"** - Searches Amazon
- **"open website [url]"** - Opens website

### Command Prompt
- **"open command prompt"** or **"open cmd"** - Opens command prompt
- **"open powershell"** - Opens PowerShell
- **"execute command [command]"** - Executes command in CMD
- **"type command [command]"** - Types command in current terminal

## 🏗️ Project Structure

```
EchoOS_PySide6/
├── main.py                          # Main entry point
├── requirements.txt                 # Python dependencies
├── README.md                        # This file
├── AUTHENTICATION_GUIDE.md          # Authentication documentation
├── AUTHENTICATION_VERIFIED.md       # Authentication verification
├── NO_HARDCODING_CONFIRMED.md      # No hardcoding confirmation
├── IMPROVEMENTS_SUMMARY.md          # Recent improvements
├── config/                          # Configuration files
│   ├── apps.json                    # Discovered applications (dynamic)
│   ├── commands.json                # Voice command patterns
│   ├── users.pkl                    # User voice profiles
│   ├── sessions.pkl                 # Active user sessions
│   └── universal_config.json        # Universal configuration
├── models/                          # Speech recognition model
│   └── vosk-model-small-en-us-0.15/
└── modules/                         # Core modules
    ├── auth.py                      # Voice authentication (MAIN PILLAR)
    ├── enhanced_stt.py              # Enhanced speech recognition
    ├── advanced_screen_analyzer.py  # Screen analysis with OCR
    ├── universal_executor_v2.py      # Universal command executor (primary)
    ├── direct_executor.py           # Direct executor (fallback)
    ├── executor.py                  # Legacy executor
    ├── window_manager.py            # Dynamic window/app/tab management
    ├── app_discovery.py             # Dynamic app discovery
    ├── tts.py                       # Text-to-speech
    ├── stt.py                       # Speech-to-text
    ├── parser.py                    # Command parsing
    ├── context_parser.py            # Context-aware parsing
    ├── ui_pyside.py                 # GUI interface
    ├── accessibility.py             # Accessibility features
    └── ... (other modules)
```

## 🔧 Key Features

### 1. **No Hardcoding - Everything Dynamic**
- ✅ All apps discovered automatically from system
- ✅ No hardcoded app names or paths
- ✅ Works on any Windows, macOS, or Linux system
- ✅ Adapts to any system configuration

### 2. **Screen-Aware Execution**
- ✅ Uses OCR to read screen content
- ✅ Detects files/folders visible on screen
- ✅ Understands current application context
- ✅ Executes commands based on screen state

### 3. **Universal Compatibility**
- ✅ Works on any laptop/system
- ✅ Cross-platform (Windows, macOS, Linux)
- ✅ Dynamic system discovery
- ✅ No configuration needed

### 4. **Complete Command Coverage**
- ✅ Everything a user can do with keyboard/mouse
- ✅ System control, file operations, app control
- ✅ Media control, text operations, navigation
- ✅ Web operations, command prompt

### 5. **App/Tab Switching**
- ✅ Switch between any open applications
- ✅ Switch between browser tabs
- ✅ List open apps and tabs
- ✅ Dynamic window management

### 6. **Authentication (Main Pillar)**
- ✅ Voice-based authentication
- ✅ Session management (30-minute timeout)
- ✅ Security features (lockout, failed attempts)
- ✅ ALL commands require authentication

## 🔐 Authentication System

### Registration
1. Go to "User Manager" tab
2. Click "Register User"
3. Enter username
4. Provide 3 voice samples (5 seconds each)

### Authentication
1. Click "Wake / Authenticate"
2. Speak clearly for 5 seconds
3. System compares your voice to registered users
4. If match > threshold (80% Resemblyzer, 85% MFCC):
   - ✅ Access granted
   - ✅ Session created (30 minutes)
   - ✅ Commands enabled

### Security
- **Failed Attempts**: Max 3 attempts before lockout
- **Lockout Duration**: 5 minutes
- **Session Timeout**: 30 minutes
- **No Bypasses**: All commands require authentication

## 📝 How It Works

### Command Execution Flow
```
Voice Input → Enhanced STT (error correction)
    ↓
Screen Analysis → Advanced Screen Analyzer (OCR + context)
    ↓
Authentication Check → Verify user & session
    ↓
Command Execution → Universal Executor V2 (screen-aware)
    ↓
Fallback Chain → Direct Executor → Universal Executor → Legacy Executor
```

### App Discovery
1. System scans Start Menu, Registry, Program Files
2. Discovers ALL installed applications
3. Stores in `config/apps.json`
4. Uses fuzzy matching for app names
5. Works on any system

### Screen Analysis
1. Captures screen using OCR
2. Detects files/folders visible
3. Identifies current application
4. Provides context for commands
5. Enables screen-aware execution

## 🐛 Troubleshooting

### Authentication Issues
- **"No registered users found"**: Register a user first
- **"Authentication failed"**: Speak more clearly, use same voice as registration
- **"Session expired"**: Click "Wake / Authenticate" again
- **"Account locked"**: Wait 5 minutes, then try again

### Command Not Working
- **Check authentication**: Must be authenticated first
- **Check session**: Session must be valid (not expired)
- **Try simpler commands**: Start with "lock screen" or "volume up"
- **Check logs**: See `echoos.log` for details

### Speech Recognition Issues
- **Speak clearly**: Enunciate words clearly
- **Check microphone**: Ensure microphone is working
- **Try variations**: If "notepad" doesn't work, try "open notepad"
- **Reduce noise**: Minimize background noise

### Screen Reading Not Working
- **Install Tesseract**: Required for OCR features
- **Check permissions**: Ensure screen capture permissions
- **Fallback available**: System works without OCR, but screen-aware features limited

## 📚 Documentation

- **AUTHENTICATION_GUIDE.md** - Complete authentication guide
- **AUTHENTICATION_VERIFIED.md** - Authentication verification
- **NO_HARDCODING_CONFIRMED.md** - No hardcoding confirmation
- **IMPROVEMENTS_SUMMARY.md** - Recent improvements summary

## 🎯 Next Steps / TODO

### Potential Improvements
- [ ] Machine learning for better command recognition
- [ ] Multi-language support
- [ ] Gesture recognition integration
- [ ] Cloud sync for settings
- [ ] Plugin system for custom commands
- [ ] Better OCR accuracy
- [ ] More context-aware features
- [ ] Performance optimizations

### Known Areas to Enhance
- Screen reading accuracy (depends on Tesseract)
- Speech recognition in noisy environments
- Command execution speed
- Error recovery mechanisms

## 🎉 Summary

EchoOS is now a **truly universal voice control system** that:

✅ **Works on any laptop/system** (no hardcoding)
✅ **Understands screen context** (OCR-based)
✅ **Executes all commands** (complete coverage)
✅ **Dynamically discovers everything** (apps, files, system)
✅ **Enforces authentication** (main pillar, fully working)
✅ **Supports app/tab switching** (dynamic window management)
✅ **Provides better speech recognition** (error correction)

**The system is ready to use and will work on any Windows, macOS, or Linux system!**

## 📞 Support

- Check logs in `echoos.log` for detailed error messages
- Review documentation files for specific guides
- Ensure all dependencies are installed
- Verify authentication is working

---

**EchoOS v2.0** - Universal Voice-Controlled Operating System
*Complete offline operation with comprehensive accessibility features and authentication*

**Last Updated**: Today - All major improvements completed
**Status**: ✅ Ready for use, authentication working perfectly, no hardcoding, all commands functional
