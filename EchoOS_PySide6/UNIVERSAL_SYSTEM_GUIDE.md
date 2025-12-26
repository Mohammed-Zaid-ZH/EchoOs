# EchoOS Universal Voice Control System

## Overview

EchoOS now features a truly universal voice control system that can understand and execute ANY command by analyzing screen context and user intent. This system eliminates hardcoded command limitations and provides intelligent, context-aware command execution.

## Key Features

### 🎯 Universal Command Recognition
- **Natural Language Processing**: Understands commands in natural language
- **Context-Aware Execution**: Analyzes current screen content to determine appropriate actions
- **Fuzzy Matching**: Corrects speech recognition errors and finds best matches
- **Intent Recognition**: Understands user intent even with imperfect speech

### 📺 Advanced Screen Analysis
- **Real-time Screen Understanding**: Analyzes what's currently on screen
- **UI Element Detection**: Identifies buttons, text fields, files, folders, and other elements
- **OCR Text Extraction**: Reads and understands text content on screen
- **Application Context**: Determines current application and available actions

### 🎤 Enhanced Speech Recognition
- **Multi-backend Support**: Uses Vosk, Google Speech Recognition, and Whisper
- **Error Correction**: Automatically corrects common speech recognition mistakes
- **Command Learning**: Learns from user patterns and improves over time
- **Confidence Scoring**: Only executes commands with sufficient confidence

### 🖥️ Complete System Control
- **OS-Level Operations**: Lock screen, shutdown, restart, sleep, volume control
- **File Operations**: Open, create, delete, copy, move, rename files and folders
- **Application Control**: Launch, close, minimize, maximize any application
- **Web Operations**: Search, navigate, bookmark, download from web
- **Media Control**: Play, pause, seek, volume control for any media player
- **Text Operations**: Type, copy, paste, select, find, replace in any text editor

## How It Works

### 1. Voice Input Processing
```
User says: "open not bad" (misrecognized "notepad")
↓
Enhanced STT corrects to: "open notepad"
↓
Universal Command Executor analyzes intent
↓
Screen Analyzer checks current context
↓
System executes appropriate action
```

### 2. Screen Context Analysis
The system continuously analyzes:
- **Active Application**: Determines what app is currently open
- **UI Elements**: Identifies clickable buttons, text fields, files, etc.
- **Text Content**: Extracts and understands text on screen
- **Available Actions**: Determines what actions are possible in current context

### 3. Intelligent Command Execution
Based on context, the system can:
- **Open files**: "open video" → finds and opens video file on screen
- **Navigate**: "go to documents" → navigates to documents folder
- **Control apps**: "play" → plays media if media player is open
- **Type text**: "type hello world" → types text at cursor position

## Supported Commands

### System Control
- `lock screen` / `lock computer`
- `shutdown` / `shut down` / `power off`
- `restart` / `reboot`
- `sleep` / `hibernate`
- `volume up` / `volume down` / `mute`
- `brightness up` / `brightness down`

### Application Control
- `open [app name]` - Opens any application
- `close [app name]` - Closes specific application
- `close all apps` - Closes all applications except EchoOS
- `minimize` / `maximize` - Window control
- `switch to [app]` - Switch between applications

### File Operations
- `open [filename]` - Opens file in current directory
- `create folder [name]` - Creates new folder
- `delete [filename]` - Deletes file or folder
- `copy [filename]` - Copies file
- `move [filename]` - Moves file
- `rename [oldname] to [newname]` - Renames file
- `go to [folder]` - Navigates to folder

### Web Operations
- `search [query]` - Searches Google
- `go to [website]` - Navigates to website
- `new tab` / `close tab` - Browser tab control
- `bookmark page` - Bookmarks current page
- `download` - Downloads current file

### Media Control
- `play` / `pause` / `stop` - Media playback control
- `next track` / `previous track` - Track navigation
- `volume up` / `volume down` - Volume control
- `fullscreen` - Toggle fullscreen mode

### Text Operations
- `type [text]` - Types text at cursor position
- `select all` - Selects all text
- `copy` / `paste` / `cut` - Text manipulation
- `find [text]` - Finds text in document
- `save` / `open file` - File operations

### Navigation
- `click [element]` - Clicks on screen element
- `double click [element]` - Double clicks element
- `right click [element]` - Right clicks element
- `scroll up` / `scroll down` - Scrolls page
- `zoom in` / `zoom out` - Zooms page

## Context-Aware Examples

### File Explorer Context
When file explorer is open:
- `open video` → Opens video file visible on screen
- `create folder test` → Creates "test" folder
- `delete document` → Deletes document file
- `go to desktop` → Navigates to desktop folder

### Browser Context
When browser is open:
- `search python tutorial` → Searches for "python tutorial"
- `bookmark page` → Bookmarks current page
- `new tab` → Opens new browser tab
- `go to youtube.com` → Navigates to YouTube

### Text Editor Context
When text editor is open:
- `type hello world` → Types "hello world"
- `save file` → Saves current document
- `find function` → Finds "function" in document
- `select all` → Selects all text

### Media Player Context
When media player is open:
- `play` → Starts playback
- `pause` → Pauses playback
- `next track` → Skips to next track
- `volume up` → Increases volume

## Installation and Setup

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Download Vosk Model (Optional)
```bash
python -c "from modules.stt import download_vosk_model; download_vosk_model()"
```

### 3. Install Tesseract OCR
- **Windows**: Download from https://github.com/UB-Mannheim/tesseract/wiki
- **macOS**: `brew install tesseract`
- **Linux**: `sudo apt-get install tesseract-ocr`

### 4. Run EchoOS
```bash
python main.py
```

## Configuration

### Voice Settings
- **Wake Words**: "hey echo", "echo os", "wake up"
- **Sleep Words**: "go to sleep", "sleep", "stop listening"
- **Confidence Threshold**: 0.7 (adjustable)
- **Timeout**: 30 seconds

### Screen Analysis Settings
- **Analysis Cache**: 1 second (for performance)
- **Element Detection**: Automatic UI element detection
- **OCR Confidence**: 0.6 threshold
- **Context Detection**: Automatic application identification

## Troubleshooting

### Speech Recognition Issues
- **Problem**: Commands not recognized
- **Solution**: Check microphone permissions and try different wake words
- **Alternative**: Use keyboard shortcut to activate listening

### Screen Analysis Issues
- **Problem**: Screen not analyzed properly
- **Solution**: Ensure Tesseract OCR is installed and accessible
- **Alternative**: System falls back to basic command recognition

### Command Execution Issues
- **Problem**: Commands not executing
- **Solution**: Check if target application is accessible
- **Alternative**: Try using more specific commands

## Advanced Usage

### Custom Commands
You can add custom command patterns:
```python
# Add to universal_command_executor.py
self.command_patterns['custom'] = {
    'my_action': ['my custom command', 'do something special']
}
```

### Command Aliases
Add command aliases for better recognition:
```python
# Add to enhanced_stt.py
self.correction_mappings['my alias'] = 'actual command'
```

### Context-Specific Actions
Add actions specific to certain applications:
```python
# Add to advanced_screen_analyzer.py
self.app_patterns['my_app'] = {
    'window_titles': ['my application'],
    'ui_elements': ['custom button', 'special field'],
    'keywords': ['custom', 'special']
}
```

## Performance Optimization

### For Better Performance
1. **Close unnecessary applications** before using EchoOS
2. **Use SSD storage** for faster file operations
3. **Ensure good lighting** for better screen analysis
4. **Use quality microphone** for better speech recognition

### For Better Accuracy
1. **Speak clearly** and at moderate pace
2. **Use specific commands** rather than vague requests
3. **Wait for confirmation** before giving next command
4. **Use context-appropriate commands** (e.g., "play" when media player is open)

## Future Enhancements

- **Machine Learning**: Learn from user patterns and improve over time
- **Multi-language Support**: Support for multiple languages
- **Gesture Recognition**: Combine voice with gesture control
- **Cloud Integration**: Sync settings and learnings across devices
- **Plugin System**: Allow third-party command extensions

## Support

For issues, feature requests, or questions:
1. Check this documentation first
2. Review the logs in `echoos.log`
3. Test with simple commands first
4. Ensure all dependencies are properly installed

The universal system is designed to be robust and handle edge cases gracefully. It will always try to execute your commands, even if it needs to make educated guesses based on context.
