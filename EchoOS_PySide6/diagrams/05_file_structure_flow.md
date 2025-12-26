# EchoOS File Structure & Data Flow

```mermaid
graph TD
    subgraph "Configuration Files"
        A[config/apps.json - 2961 discovered apps]
        B[config/commands.json - Command patterns]
        C[config/users.pkl - User profiles]
        D[config/sessions.pkl - Active sessions]
    end
    
    subgraph "Core Modules"
        E[main.py - Application entry point]
        F[modules/auth.py - Voice authentication]
        G[modules/enhanced_stt.py - Speech processing]
        H[modules/direct_executor.py - Command execution]
        I[modules/ui_pyside.py - GUI interface]
        J[modules/tts.py - Text-to-speech]
    end
    
    subgraph "Data Flow"
        K[User Voice Input]
        L[Audio Processing]
        M[Feature Extraction]
        N[Authentication Check]
        O[Command Parsing]
        P[Execution]
        Q[Feedback]
    end
    
    A --> H
    B --> G
    C --> F
    D --> F
    
    E --> F
    E --> G
    E --> H
    E --> I
    E --> J
    
    K --> L
    L --> M
    M --> N
    N --> O
    O --> P
    P --> Q
```

## How to Use:
1. Copy the mermaid code above
2. Go to https://mermaid.live/
3. Paste the code
4. Click "Download PNG" or "Download SVG"

