"""EchoOS PySide6 - main.py
Entry point for the PySide6-based EchoOS prototype (Windows + macOS focus).
Enhanced with Resemblyzer authentication, comprehensive voice commands, and accessibility features.
Run: python main.py
"""
import sys
import pathlib
import json
import pickle
import logging
import threading
import time
from datetime import datetime

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QTimer

from modules.ui_pyside import EchoMainWindow
from modules.stt import VoskManager
from modules.tts import TTS
from modules.auth import Authenticator
from modules.app_discovery import AppDiscovery
from modules.parser import CommandParser
from modules.context_parser import ContextAwareParser
from modules.executor import Executor
from modules.accessibility import AccessibilityManager
from modules.ui_automation import UniversalUIAutomator
from modules.universal_config import UniversalConfig
from modules.universal_command_executor import UniversalCommandExecutor
from modules.enhanced_stt import EnhancedSTT
from modules.simple_screen_analyzer import SimpleScreenAnalyzer
from modules.advanced_screen_analyzer import AdvancedScreenAnalyzer
from modules.universal_executor_v2 import UniversalExecutorV2

# Initialize universal configuration
universal_config = UniversalConfig()
universal_config.create_directories()

CONFIG_DIR = pathlib.Path(universal_config.get("system.config_dir", "config"))
CONFIG_DIR.mkdir(exist_ok=True)

# Create legacy config files for backward compatibility
if not (CONFIG_DIR/"commands.json").exists():
    (CONFIG_DIR/"commands.json").write_text(json.dumps({
        "open": ["open","launch","start"],
        "open_website": ["open website","open site","go to"],
        "search_product": ["search product","find on amazon","search on amazon","search on swiggy","order on swiggy"],
        "send_whatsapp": ["send whatsapp","whatsapp"],
        "send_mail": ["send mail","send email","email"],
        "stop_listening": ["stop","sleep","go to sleep","stop listening","pause"],
        "wake_up": ["wake up","start listening","resume","start"],
    }, indent=2))

if not (CONFIG_DIR/"apps.json").exists():
    (CONFIG_DIR/"apps.json").write_text(json.dumps({"apps": []}, indent=2))

if not (CONFIG_DIR/"users.pkl").exists():
    with open(CONFIG_DIR/"users.pkl", "wb") as f:
        pickle.dump({}, f)

def main():
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('echoos.log'),
            logging.StreamHandler()
        ]
    )
    logger = logging.getLogger(__name__)
    
    logger.info("Starting EchoOS - Enhanced Voice-Controlled Operating System")
    
    # Initialize Qt application
    app = QApplication(sys.argv)
    app.setApplicationName("EchoOS")
    app.setApplicationVersion("2.0")
    
    try:
        # Initialize core components (fast startup)
        logger.info("Initializing TTS engine...")
        tts = TTS()
        
        logger.info("Initializing authentication system...")
        auth = Authenticator(tts=tts)
        
        logger.info("Initializing app discovery...")
        app_disc = AppDiscovery()
        
        logger.info("Initializing enhanced speech recognition...")
        stt_mgr = EnhancedSTT(tts=tts)
        
        logger.info("Initializing simple screen analyzer...")
        screen_analyzer = SimpleScreenAnalyzer(tts=tts)
        
        logger.info("Initializing advanced screen analyzer...")
        advanced_screen_analyzer = AdvancedScreenAnalyzer(tts=tts)
        
        logger.info("Initializing UI automation...")
        ui_automator = UniversalUIAutomator(tts=tts)
        
        logger.info("Initializing command parser...")
        parser = CommandParser(tts=tts)
        
        logger.info("Initializing context-aware parser...")
        context_parser = ContextAwareParser(tts=tts, ui_automator=ui_automator)
        
        logger.info("Initializing universal command executor...")
        universal_executor = UniversalCommandExecutor(tts=tts, auth=auth)
        
        logger.info("Initializing universal executor V2...")
        universal_executor_v2 = UniversalExecutorV2(tts=tts, screen_analyzer=advanced_screen_analyzer, app_discovery=app_disc, auth=auth)
        
        logger.info("Initializing legacy command executor...")
        executor = Executor(tts=tts, auth=auth, ui_automator=ui_automator)
        
        logger.info("Initializing accessibility manager...")
        accessibility = AccessibilityManager(tts=tts)
        
        # Clean up expired sessions
        auth.cleanup_expired_sessions()
        
        # Create main window (FAST STARTUP)
        logger.info("Creating main window...")
        win = EchoMainWindow(auth, stt_mgr, app_disc, context_parser, executor, tts, accessibility, universal_executor, screen_analyzer, advanced_screen_analyzer, universal_executor_v2)
        win.show()
        
        # Start app discovery in background (NON-BLOCKING)
        def background_discovery():
            try:
                logger.info("Starting background app discovery...")
                discovered_apps = app_disc.discover_and_save("config/apps.json")
                logger.info(f"Background discovery complete! Found {len(discovered_apps)} applications")
                win.apps_status.setText(f"✅ Discovery complete! Found {len(discovered_apps)} applications")
            except Exception as e:
                logger.error(f"Background discovery failed: {e}")
                win.apps_status.setText(f"❌ Discovery failed: {str(e)}")
        
        # Start background discovery thread
        discovery_thread = threading.Thread(target=background_discovery, daemon=True)
        discovery_thread.start()
        
        # Setup periodic cleanup
        cleanup_timer = QTimer()
        cleanup_timer.timeout.connect(auth.cleanup_expired_sessions)
        cleanup_timer.start(300000)  # Clean up every 5 minutes
        
        logger.info("EchoOS started successfully")
        logger.info("Voice commands available:")
        logger.info("- System control: shutdown, restart, sleep, lock screen")
        logger.info("- File operations: open file, create file, delete file, list files")
        logger.info("- App control: open app, close app, minimize, maximize")
        logger.info("- Web operations: open website, search google, search youtube")
        logger.info("- System info: system info, battery status, disk space, memory usage")
        logger.info("- Accessibility: read screen, navigate, click, scroll, zoom")
        
        # Start the application
        try:
            sys.exit(app.exec())
        finally:
            logger.info("EchoOS shutdown complete")
        
    except Exception as e:
        logger.error(f"Failed to start EchoOS: {e}")
        print(f"Error starting EchoOS: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
