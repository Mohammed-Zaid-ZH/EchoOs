# EchoOS System Diagrams

This folder contains Mermaid diagrams that illustrate the EchoOS system architecture and communication flow.

## 📁 Diagram Files

1. **01_complete_system_flow.md** - Overall system flow from startup to command execution
2. **02_component_architecture.md** - Component relationships and dependencies
3. **03_authentication_flow.md** - Detailed authentication process
4. **04_command_execution_flow.md** - Command processing and execution
5. **05_file_structure_flow.md** - File structure and data flow

## 🎨 How to Convert to Images

### Method 1: Online Mermaid Editor (Recommended)
1. Go to https://mermaid.live/
2. Copy the mermaid code from any .md file
3. Paste it into the editor
4. Click "Download PNG" or "Download SVG"

### Method 2: VS Code Extension
1. Install "Mermaid Preview" extension in VS Code
2. Open any .md file
3. Right-click and select "Export as PNG/SVG"

### Method 3: Command Line (if you have Node.js)
```bash
npm install -g @mermaid-js/mermaid-cli
mmdc -i diagram.md -o diagram.png
```

## 🔧 Alternative: Create Simple Text Diagrams

If you prefer simple text-based diagrams, I can create ASCII art versions instead!

## 📊 What Each Diagram Shows

- **System Flow**: Complete user journey from startup to command execution
- **Component Architecture**: How all modules interact with each other
- **Authentication Flow**: Step-by-step authentication process
- **Command Execution**: How commands are processed and executed
- **File Structure**: Data flow between configuration files and modules

Each diagram is self-contained and can be used independently for documentation or presentations.

