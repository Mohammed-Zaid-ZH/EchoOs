#!/usr/bin/env python3
"""Re-register user with Resemblyzer features for better accuracy"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from modules.auth import Authenticator
from modules.tts import TTS

def reregister_user():
    print("🔄 Re-registering user with Resemblyzer features...")
    
    # Initialize components
    tts = TTS()
    auth = Authenticator(tts=tts)
    
    print("📝 This will re-register the user 'Zaid' with Resemblyzer features for better accuracy.")
    print("🎤 You will need to record 3 voice samples.")
    print("🎯 New thresholds: Resemblyzer=80%, MFCC=85%")
    
    try:
        # Remove existing user
        if 'Zaid' in auth.users:
            del auth.users['Zaid']
            print("✅ Removed existing user data")
        
        # Re-register with Resemblyzer
        result = auth.register_user('Zaid')
        
        if result:
            print("✅ User 'Zaid' re-registered successfully with Resemblyzer features!")
            print("🎯 Authentication should now work much better.")
        else:
            print("❌ Re-registration failed")
            
    except Exception as e:
        print(f"❌ Error during re-registration: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    reregister_user()
