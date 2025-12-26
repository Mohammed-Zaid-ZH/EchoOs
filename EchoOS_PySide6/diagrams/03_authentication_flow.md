# EchoOS Authentication Flow

```mermaid
sequenceDiagram
    participant U as User
    participant UI as UI Interface
    participant AUTH as Auth System
    participant STT as Speech-to-Text
    participant TTS as Text-to-Speech
    
    U->>UI: Click "Wake/Authenticate"
    UI->>AUTH: Start Authentication
    AUTH->>STT: Start Voice Recording
    STT->>U: "Please speak for authentication"
    U->>STT: Speaks voice sample
    STT->>AUTH: Audio data (float32)
    AUTH->>AUTH: Extract Features (MFCC/Resemblyzer)
    AUTH->>AUTH: Compare with stored profiles
    AUTH->>AUTH: Calculate Similarity Score
    
    alt Authentication Successful (Score > Threshold)
        AUTH->>UI: Authentication Success
        UI->>TTS: "Access granted. Welcome back, [User]"
        TTS->>U: Voice confirmation
        UI->>UI: Enable voice commands
    else Authentication Failed (Score < Threshold)
        AUTH->>UI: Authentication Failed
        UI->>TTS: "Authentication failed"
        TTS->>U: Voice feedback
        UI->>UI: Request re-authentication
    end
```

## How to Use:
1. Copy the mermaid code above
2. Go to https://mermaid.live/
3. Paste the code
4. Click "Download PNG" or "Download SVG"

