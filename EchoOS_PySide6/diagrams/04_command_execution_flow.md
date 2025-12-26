# EchoOS Command Execution Flow

```mermaid
sequenceDiagram
    participant U as User
    participant UI as UI Interface
    participant STT as Speech-to-Text
    participant AUTH as Auth System
    participant EXEC as Command Executor
    participant TTS as Text-to-Speech
    participant SYS as System
    
    U->>UI: Speaks command
    UI->>STT: Process voice input
    STT->>STT: Convert speech to text
    STT->>STT: Apply fuzzy matching corrections
    STT->>UI: Corrected text
    
    UI->>AUTH: Check authentication status
    AUTH->>UI: User authenticated
    
    UI->>EXEC: Execute command
    EXEC->>EXEC: Parse command type
    
    alt File Operation
        EXEC->>SYS: Open file with os.startfile()
        SYS->>EXEC: File opened
    else App Operation
        EXEC->>EXEC: Find app in discovered apps (2961 apps)
        EXEC->>SYS: Launch application
        SYS->>EXEC: App launched
    else System Command
        EXEC->>SYS: Execute system command
        SYS->>EXEC: Command executed
    else Web Navigation
        EXEC->>SYS: Send keyboard shortcuts
        SYS->>EXEC: Navigation completed
    end
    
    EXEC->>TTS: Provide feedback
    TTS->>U: Voice confirmation
    EXEC->>UI: Command result
    UI->>UI: Update status display
```

## How to Use:
1. Copy the mermaid code above
2. Go to https://mermaid.live/
3. Paste the code
4. Click "Download PNG" or "Download SVG"

