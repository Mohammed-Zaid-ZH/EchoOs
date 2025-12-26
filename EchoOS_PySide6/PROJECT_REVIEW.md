# 📋 EchoOS Project Review - Getting Started Guide

## 🎯 Project Overview

**EchoOS** is a hands-free, voice-controlled operating system that works entirely offline. It uses voice commands to control your computer with no hardcoding - everything is discovered dynamically.

### Key Principles
- ✅ **No Hardcoding** - All apps discovered dynamically from the system
- ✅ **Offline Operation** - No internet connection required
- ✅ **Universal Compatibility** - Works on Windows, macOS, and Linux
- ✅ **Authentication Required** - Voice-based security is a main pillar
- ✅ **Screen-Aware** - Uses OCR to understand current context

---

## 🏗️ Project Structure

### Core Entry Point
- **`main.py`** - Main application entry point
  - Initializes all components
  - Sets up GUI
  - Manages background app discovery
  - Handles session cleanup

### Key Modules (`modules/`)

#### Authentication & Security
- **`auth.py`** - Voice-based authentication system (MAIN PILLAR)
  - Resemblyzer-based voice recognition
  - MFCC fallback
  - Session management (30-minute timeout)
  - Failed attempt tracking
  - Account lockout protection

#### Speech Processing
- **`enhanced_stt.py`** - Enhanced speech-to-text
  - Error correction
  - Fuzzy matching
  - Multiple backend support (Vosk, SpeechRecognition, Whisper)
  
- **`stt.py`** - Basic speech-to-text (Vosk-based)
- **`tts.py`** - Text-to-speech engine

#### Command Execution (3-tier system)
1. **`direct_executor.py`** - Primary executor (1432 lines)
   - Simple, reliable command execution
   - File operations
   - System control
   - App launching
   - **Currently open file - line 559**

2. **`universal_executor_v2.py`** - Advanced executor
   - Screen-aware execution
   - Context-based commands
   - Dynamic app discovery integration
   - File Explorer integration

3. **`executor.py`** - Legacy executor (fallback)

#### Screen Analysis
- **`advanced_screen_analyzer.py`** - OCR-based screen reading
  - Tesseract OCR integration
  - Context detection
  - File/folder detection on screen
  
- **`simple_screen_analyzer.py`** - Basic screen analysis

#### App Discovery
- **`app_discovery.py`** - Dynamic application discovery
  - Scans Start Menu, Registry, Program Files
  - Works on Windows, macOS, Linux
  - No hardcoding - discovers all apps

#### UI & Automation
- **`ui_pyside.py`** - Main GUI interface
  - PySide6-based interface
  - Dashboard, User Manager, App Catalog tabs
  - Authentication UI
  - Command listening controls

- **`ui_automation.py`** - UI automation utilities
- **`window_manager.py`** - Window/app/tab management

#### Parsing & Context
- **`parser.py`** - Command parsing
- **`context_parser.py`** - Context-aware parsing
- **`universal_config.py`** - Universal configuration management

#### Other Modules
- **`accessibility.py`** - Accessibility features
- **`universal_command_executor.py`** - Universal command handler
- **`universal_filesystem.py`** - File system operations
- **`universal_keybindings.py`** - Keyboard shortcuts

### Configuration Files (`config/`)
- **`apps.json`** - Discovered applications (dynamically generated)
- **`commands.json`** - Voice command patterns
- **`users.pkl`** - User voice profiles (pickle)
- **`sessions.pkl`** - Active user sessions
- **`universal_config.json`** - Universal configuration

### Models
- **`models/vosk-model-small-en-us-0.15/`** - Vosk speech recognition model

### Documentation
- **`README.md`** - Main project documentation
- **`QUICK_START_GUIDE.md`** - Quick start instructions
- **`AUTHENTICATION_GUIDE.md`** - Complete authentication guide
- **`PROJECT_COMPLETION_SUMMARY.md`** - Project status
- Multiple other documentation files

---

## 🚀 Getting Started

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

### 4. First-Time Setup

#### Step 1: Register a User
1. Go to "User Manager" tab
2. Click "Register User"
3. Enter username
4. Speak clearly for 3 samples (5 seconds each)

#### Step 2: Authenticate
1. Click "Wake / Authenticate" button
2. Speak clearly for 5 seconds
3. Wait for "Access granted" message

#### Step 3: Start Using Commands
1. Click "Start Listening"
2. Speak your commands
3. Commands will execute (if authenticated)

---

## 🎤 Available Voice Commands

### System Control
- `"lock screen"` - Locks the screen
- `"shutdown"` - Shuts down system (10 second delay)
- `"restart"` - Restarts system
- `"sleep"` - Puts system to sleep
- `"volume up"` / `"volume down"` / `"mute"` - Volume control
- `"system info"` - Shows system information
- `"battery status"` - Shows battery level

### File Operations
- `"open file [filename]"` - Opens file (checks screen first)
- `"create file [filename]"` - Creates new file
- `"delete file [filename]"` - Deletes file
- `"create folder [name]"` - Creates new folder
- `"navigate to [directory]"` - Changes directory
- `"list files"` - Lists files in current directory
- `"save file"` - Saves current file (Ctrl+S)

### Application Control
- `"open [app name]"` - Opens any discovered application
- `"close app"` or `"close [app name]"` - Closes application
- `"switch to [app name]"` - Switches to specific app
- `"next app"` - Switches to next app (Alt+Tab)
- `"list apps"` - Lists all open applications
- `"minimize"` / `"maximize"` - Window control

### Tab Switching (Browser)
- `"next tab"` - Switches to next browser tab
- `"previous tab"` - Switches to previous tab
- `"close tab"` - Closes current tab
- `"new tab"` - Opens new tab

### Media Control
- `"play"` / `"pause"` / `"stop"` - Media playback
- `"next"` / `"previous"` - Track navigation

### Text Operations
- `"type [text]"` - Types text at cursor position
- `"select all"` - Selects all text
- `"copy all"` - Copies all text
- `"paste all"` - Pastes text

### Navigation
- `"scroll up"` / `"scroll down"` - Scrolls page
- `"click"` - Clicks at cursor position
- `"zoom in"` / `"zoom out"` - Zooms page

### Web Operations
- `"search [query]"` - Searches Google
- `"search youtube [query]"` - Searches YouTube
- `"open website [url]"` - Opens website

### Command Prompt
- `"open command prompt"` or `"open cmd"` - Opens command prompt
- `"execute command [command]"` - Executes command in CMD

---

## 🔐 Authentication System

### Key Features
- **Voice-based authentication** using Resemblyzer (or MFCC fallback)
- **Session management** (30-minute timeout)
- **Security features** (failed attempt tracking, account lockout)
- **ALL commands require authentication** - no bypasses
- **Session validation** before every command execution

### Authentication Flow
1. User clicks "Wake / Authenticate"
2. System records 5 seconds of audio
3. Extracts voice features (Resemblyzer or MFCC)
4. Compares against registered users
5. If match > threshold (80% Resemblyzer, 85% MFCC):
   - ✅ Access granted
   - ✅ Session created (30 minutes)
   - ✅ Commands enabled

### Security Measures
- Max 3 failed attempts before lockout
- 5-minute lockout duration
- 30-minute session timeout
- No bypasses or workarounds

---

## 📊 Command Execution Flow

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

### Execution Priority
1. **Direct Executor** - Primary executor (simple, reliable)
2. **Universal Executor V2** - Advanced features (screen-aware)
3. **Legacy Executor** - Fallback

---

## 🔧 Key Features

### 1. No Hardcoding - Everything Dynamic
- ✅ All apps discovered automatically from system
- ✅ No hardcoded app names or paths
- ✅ Works on any Windows, macOS, or Linux system
- ✅ Adapts to any system configuration

### 2. Screen-Aware Execution
- ✅ Uses OCR to read screen content
- ✅ Detects files/folders visible on screen
- ✅ Understands current application context
- ✅ Executes commands based on screen state

### 3. Universal Compatibility
- ✅ Works on any laptop/system
- ✅ Cross-platform (Windows, macOS, Linux)
- ✅ Dynamic system discovery
- ✅ No configuration needed

### 4. Complete Command Coverage
- ✅ System control, file operations, app control
- ✅ Media control, text operations, navigation
- ✅ Web operations, command prompt

---

## 📁 Important Files Reference

### Currently Open
- **`modules/direct_executor.py`** (line 559)
  - Primary command executor
  - 1432 lines
  - Handles file operations, app launching, system control

### Core Files to Understand
1. **`main.py`** - Entry point, component initialization
2. **`modules/ui_pyside.py`** - GUI interface
3. **`modules/auth.py`** - Authentication system
4. **`modules/direct_executor.py`** - Command execution
5. **`modules/enhanced_stt.py`** - Speech recognition
6. **`modules/app_discovery.py`** - App discovery

### Configuration Files
- **`config/apps.json`** - Discovered apps (auto-generated)
- **`config/users.pkl`** - User profiles
- **`config/sessions.pkl`** - Active sessions
- **`config/commands.json`** - Command patterns

---

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

---

## 📚 Documentation Files

- **`README.md`** - Main documentation
- **`QUICK_START_GUIDE.md`** - Quick start
- **`AUTHENTICATION_GUIDE.md`** - Authentication details
- **`PROJECT_COMPLETION_SUMMARY.md`** - Project status
- **`AUTHENTICATION_VERIFIED.md`** - Auth verification
- **`NO_HARDCODING_CONFIRMED.md`** - No hardcoding confirmation
- **`IMPROVEMENTS_SUMMARY.md`** - Recent improvements
- **`UNIVERSAL_SYSTEM_GUIDE.md`** - Universal system guide

---

## ✅ Current Status

### Working Features
- ✅ Universal Command Execution
- ✅ App/Tab Switching
- ✅ Screen Understanding (OCR)
- ✅ Complete Command Coverage
- ✅ Enhanced Speech Recognition
- ✅ Authentication System (fully enforced)
- ✅ Dynamic App Discovery
- ✅ Cross-Platform Support

### System Status
- **Status**: ✅ Ready for use
- **Authentication**: ✅ Working perfectly
- **Commands**: ✅ All functional
- **No Hardcoding**: ✅ Confirmed
- **Cross-Platform**: ✅ Verified

---

## 🎯 Next Steps

1. **Run the application**: `python main.py`
2. **Register a user**: Use "User Manager" tab
3. **Authenticate**: Click "Wake / Authenticate"
4. **Test commands**: Start with simple commands like "lock screen"
5. **Explore features**: Try different voice commands
6. **Check logs**: Review `echoos.log` for any issues

---

## 💡 Pro Tips

- Speak clearly and pause between words
- Use simple, direct commands
- The system works best with common applications
- If a command fails, try a different way of saying it
- Check authentication status before using commands
- Session expires after 30 minutes - re-authenticate if needed

---

## 📞 Support

- Check logs in `echoos.log` for detailed error messages
- Review documentation files for specific guides
- Ensure all dependencies are installed
- Verify authentication is working

---

**EchoOS v2.0** - Universal Voice-Controlled Operating System
*Complete offline operation with comprehensive accessibility features and authentication*

**Last Updated**: Project Review - All systems operational
**Status**: ✅ Ready for use, authentication working perfectly, no hardcoding, all commands functional

