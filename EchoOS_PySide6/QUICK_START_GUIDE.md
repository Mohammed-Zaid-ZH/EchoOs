# EchoOS Quick Start Guide

## 🚀 **Start the System**
```bash
cd EchoOS_PySide6
python main.py
```

## 🎤 **Voice Commands That Work Right Now**

### **Applications**
- `"open notepad"` → Opens Notepad
- `"open chrome"` → Opens Chrome browser  
- `"open calculator"` → Opens Calculator
- `"open file explorer"` → Opens File Explorer
- `"open paint"` → Opens Paint
- `"open cmd"` → Opens Command Prompt
- `"open powershell"` → Opens PowerShell

### **System Control**
- `"lock screen"` → Locks the screen
- `"shutdown"` → Shuts down (5 sec delay)
- `"restart"` → Restarts (5 sec delay)
- `"sleep"` → Puts system to sleep

### **Volume Control**
- `"volume up"` → Increases volume
- `"volume down"` → Decreases volume
- `"mute"` → Mutes/unmutes

### **Web & Search**
- `"search [anything]"` → Google search
- `"open youtube"` → Opens YouTube
- `"open google"` → Opens Google

### **Media Control**
- `"play"` → Play/pause media
- `"next"` → Next track
- `"previous"` → Previous track

## 🔧 **How It Works**

1. **Direct Executor** (Primary) - Actually executes commands
2. **Universal Executor** (Secondary) - Advanced features
3. **Legacy Executor** (Fallback) - Original system

## 📁 **Key Files**

- `modules/direct_executor.py` - **Main command executor**
- `modules/enhanced_stt.py` - Speech recognition
- `modules/ui_pyside.py` - Main interface
- `main.py` - System entry point

## 🐛 **If Something Doesn't Work**

1. Check the terminal for error messages
2. Try the command again (speech recognition might have failed)
3. Use simpler commands first to test
4. Check if the application exists on your system

## 🎯 **Tomorrow's Goals**

1. Test all commands thoroughly
2. Add more application mappings
3. Implement file operations (create, delete, copy)
4. Add system info commands (battery, disk space)
5. Consider installing Tesseract OCR for screen reading

## 💡 **Pro Tips**

- Speak clearly and pause between words
- Use simple, direct commands
- The system works best with common Windows applications
- If a command fails, try a different way of saying it

**The system is now working and ready to use!** 🎉
