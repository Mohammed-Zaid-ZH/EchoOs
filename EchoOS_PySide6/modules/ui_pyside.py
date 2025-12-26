from PySide6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QLabel, QPushButton,
                               QListWidget, QHBoxLayout, QFileDialog, QMessageBox, QTabWidget,
                               QInputDialog, QTextEdit, QLineEdit, QFormLayout, QSlider, QFrame)
from PySide6.QtCore import Qt, Signal, QThread, QPropertyAnimation, QEasingCurve, QRect, QTimer
import json, os, webbrowser
from .direct_executor import DirectExecutor

class WorkerThread(QThread):
    def __init__(self, fn, *args, **kwargs):
        super().__init__()
        self.fn = fn; self.args = args; self.kwargs = kwargs
        self._result = None
    def run(self):
        try:
            self._result = self.fn(*self.args, **self.kwargs)
        except Exception as e:
            self._result = e
    def result(self):
        return self._result

class EchoMainWindow(QMainWindow):
    def __init__(self, auth, stt_mgr, app_disc, parser, executor, tts, accessibility=None, universal_executor=None, screen_analyzer=None, advanced_screen_analyzer=None, universal_executor_v2=None):
        super().__init__()
        self.setWindowTitle("EchoOS - Universal Voice-Controlled OS")
        self.resize(1200, 800)
        self.auth = auth
        self.stt_mgr = stt_mgr
        self.app_disc = app_disc
        self.parser = parser
        self.executor = executor
        self.universal_executor = universal_executor
        self.universal_executor_v2 = universal_executor_v2
        self.screen_analyzer = screen_analyzer
        self.advanced_screen_analyzer = advanced_screen_analyzer
        self.direct_executor = DirectExecutor(tts=tts, auth=auth)
        self.tts = tts
        self.accessibility = accessibility
        self.components_loaded = False
        # Typing mode state
        self.typing_mode = False
        self.typing_buffer = []
        self.typing_timer = None
        self._build_ui()

    def update_components(self, auth, stt_mgr, app_disc, parser, executor, accessibility):
        """Update components after background loading"""
        self.auth = auth
        self.stt_mgr = stt_mgr
        self.app_disc = app_disc
        self.parser = parser
        self.executor = executor
        self.accessibility = accessibility
        self.components_loaded = True
        print("✅ Components updated successfully!")

    def _styled_button(self, text, color="#4CAF50"):
        btn = QPushButton(text)
        btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {color};
                color: white;
                border-radius: 6px;
                padding: 16px 20px;
                font-weight: bold;
                font-size: 16px;
                border: none;
                min-height: 30px;
            }}
            QPushButton:hover {{
                background-color: #66bb6a;
            }}
            QPushButton:pressed {{
                background-color: #388e3c;
            }}
        """)
        return btn

    def _build_ui(self):
        # Tabs
        self.tabs = QTabWidget()
        self.tabs.addTab(self._dashboard_tab(), "Dashboard")
        self.tabs.addTab(self._users_tab(), "User Manager")
        self.tabs.addTab(self._apps_tab(), "App Catalog")
        self.tabs.addTab(self._accessibility_tab(), "Accessibility")
        self.tabs.addTab(self._settings_tab(), "Settings")
        self.setCentralWidget(self.tabs)

        # Apply hover animation for tabs and set background color
        self.tabs.setStyleSheet("""
            QTabWidget::pane {
                background-color: #f5f5f5;
                border: 1px solid #d0d0d0;
                border-radius: 8px;
            }
            QTabBar::tab {
                background: #e0e0e0;
                padding: 10px 20px;
                border-radius: 8px;
                margin: 2px;
            }
            QTabBar::tab:hover {
                background: #64b5f6;
                color: white;
                font-weight: bold;
            }
            QTabBar::tab:selected {
                background: #2196f3;
                color: white;
                font-weight: bold;
            }
        """)

        # Status bar
        self.status = self.statusBar()
        self.user_label = QLabel("User: -")
        self.state_label = QLabel("State: Sleeping")
        self.last_label = QLabel("Last: -")
        self.status.addPermanentWidget(self.user_label)
        self.status.addPermanentWidget(self.state_label)
        self.status.addPermanentWidget(self.last_label)

        # Connect tab change signal to show/hide floating dashboard
        self.tabs.currentChanged.connect(self._on_tab_changed)
        
        # Create floating dashboard (initially hidden)
        self._floating_dashboard()
        self.dashboard_frame.hide()  # Hide initially

    def _on_tab_changed(self, index):
        """Handle tab changes to show/hide floating dashboard"""
        if index == 0:  # Dashboard tab
            self.dashboard_frame.show()
        else:
            self.dashboard_frame.hide()

    def _floating_dashboard(self):
        self.dashboard_frame = QFrame(self)
        # Position below the tab bar (around y=120 to avoid overlap) - Significantly increased size
        self.dashboard_frame.setGeometry(20, 120, 350, 280)
        self.dashboard_frame.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                                            stop:0 #2196F3, stop:1 #21CBF3);
                border-radius: 12px;
                color: white;
            }
        """)
        layout = QVBoxLayout()
        layout.setSpacing(18)  # Increased spacing between buttons
        self.dashboard_frame.setLayout(layout)

        self.wake_btn = self._styled_button("Wake / Authenticate")
        self.wake_btn.clicked.connect(self.on_wake)
        self.sleep_btn = self._styled_button("Sleep EchoOS", "#f44336")
        self.sleep_btn.clicked.connect(self.on_sleep)
        self.listen_btn = self._styled_button("Start Listening", "#FF9800")
        self.listen_btn.setCheckable(True)
        self.listen_btn.clicked.connect(self.on_listen)

        layout.addWidget(self.wake_btn)
        layout.addWidget(self.sleep_btn)
        layout.addWidget(self.listen_btn)

        # Slide-in animation - Updated for new size
        self.anim = QPropertyAnimation(self.dashboard_frame, b"geometry")
        self.anim.setDuration(1000)
        self.anim.setStartValue(QRect(-370, 120, 350, 280))
        self.anim.setEndValue(QRect(20, 120, 350, 280))
        self.anim.setEasingCurve(QEasingCurve.OutBounce)
        self.anim.start()

    def _dashboard_tab(self):
        w = QWidget()
        w.setStyleSheet("background-color: #f8f9fa;")
        layout = QVBoxLayout()
        w.setLayout(layout)
        lbl = QLabel("Welcome to EchoOS Dashboard!")
        lbl.setAlignment(Qt.AlignCenter)
        lbl.setStyleSheet("font-size: 20px; font-weight: bold; margin-top: 50px; color: #333;")
        layout.addWidget(lbl)
        return w

    def _users_tab(self):
        w = QWidget()
        w.setStyleSheet("background-color: #f0f4f8;")
        layout = QHBoxLayout()
        w.setLayout(layout)
        self.users_list = QListWidget()
        self.users_list.setStyleSheet("""
            QListWidget {
                background-color: white;
                border: 1px solid #d0d0d0;
                border-radius: 8px;
                padding: 5px;
            }
            QListWidget::item {
                padding: 20px;
                border-bottom: 1px solid #e0e0e0;
                font-size: 48px;
                font-weight: bold;
                min-height: 50px;
            }
            QListWidget::item:selected {
                background-color: #2196f3;
                color: white;
            }
        """)
        left = QVBoxLayout()
        right = QVBoxLayout()
        left.addWidget(self.users_list)
        btn_reg = self._styled_button("Register User")
        btn_reg.clicked.connect(self.on_register)
        btn_rm = self._styled_button("Remove Selected", "#f44336")
        btn_rm.clicked.connect(self.on_remove)
        btn_refresh = self._styled_button("Refresh", "#2196F3")
        btn_refresh.clicked.connect(self.refresh_users)
        right.addWidget(btn_reg)
        right.addWidget(btn_rm)
        right.addWidget(btn_refresh)
        layout.addLayout(left, 3)
        layout.addLayout(right, 1)
        self.refresh_users()
        return w

    def _apps_tab(self):
        w = QWidget()
        w.setStyleSheet("background-color: #f8f5ff;")
        layout = QVBoxLayout()
        w.setLayout(layout)

        header = QLabel("📦 Comprehensive Application Discovery")
        header.setStyleSheet("font-size: 16px; font-weight: bold; margin: 10px; color: #333;")
        layout.addWidget(header)

        controls_layout = QHBoxLayout()
        self.btn_scan = self._styled_button("🔍 Discover All Apps", "#4CAF50")
        self.btn_scan.clicked.connect(self.on_scan)
        self.btn_refresh = self._styled_button("🔄 Refresh List", "#2196F3")
        self.btn_refresh.clicked.connect(self.load_apps)
        self.btn_open = self._styled_button("📁 Open apps.json", "#FF9800")
        self.btn_open.clicked.connect(lambda: webbrowser.open("file://"+os.path.abspath("config/apps.json")))
        
        controls_layout.addWidget(self.btn_scan)
        controls_layout.addWidget(self.btn_refresh)
        controls_layout.addWidget(self.btn_open)
        layout.addLayout(controls_layout)
        
        self.apps_status = QLabel("Ready to discover applications...")
        self.apps_status.setStyleSheet("color: #666; margin: 5px;")
        layout.addWidget(self.apps_status)

        # Modern QTextEdit style
        self.apps_text = QTextEdit()
        self.apps_text.setReadOnly(True)
        self.apps_text.setStyleSheet("""
            QTextEdit {
                font-family: 'Consolas', monospace;
                font-size: 11px;
                border: 2px solid qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #2196F3, stop:1 #21CBF3);
                border-radius: 10px;
                padding: 5px;
            }
            QScrollBar:vertical {
                background: #f0f0f0;
                width: 10px;
                margin: 0px 0px 0px 0px;
                border-radius: 5px;
            }
            QScrollBar::handle:vertical {
                background: #2196F3;
                min-height: 20px;
                border-radius: 5px;
            }
            QScrollBar::handle:vertical:hover {
                background: #64b5f6;
            }
        """)
        layout.addWidget(self.apps_text)
        
        # Load initial apps
        self.load_apps()
        return w

    def _accessibility_tab(self):
        w = QWidget()
        w.setStyleSheet("background-color: #fff8f0;")
        layout = QVBoxLayout()
        w.setLayout(layout)
        
        # Navigation controls
        nav_group = QWidget()
        nav_layout = QHBoxLayout()
        nav_group.setLayout(nav_layout)
        self.nav_mode_btn = self._styled_button("Enable Navigation Mode", "#4CAF50")
        self.nav_mode_btn.clicked.connect(self.toggle_navigation_mode)
        self.read_screen_btn = self._styled_button("Read Screen", "#2196F3")
        self.read_screen_btn.clicked.connect(self.read_screen)
        self.describe_btn = self._styled_button("Describe Screen", "#FF9800")
        self.describe_btn.clicked.connect(self.describe_screen)
        nav_layout.addWidget(self.nav_mode_btn)
        nav_layout.addWidget(self.read_screen_btn)
        nav_layout.addWidget(self.describe_btn)
        
        # Visual settings
        visual_group = QWidget()
        visual_layout = QHBoxLayout()
        visual_group.setLayout(visual_layout)
        self.high_contrast_btn = self._styled_button("Toggle High Contrast", "#9C27B0")
        self.high_contrast_btn.clicked.connect(self.toggle_high_contrast)
        self.large_text_btn = self._styled_button("Toggle Large Text", "#607D8B")
        self.large_text_btn.clicked.connect(self.toggle_large_text)
        visual_layout.addWidget(self.high_contrast_btn)
        visual_layout.addWidget(self.large_text_btn)
        
        # Voice settings
        voice_group = QWidget()
        voice_layout = QHBoxLayout()
        voice_group.setLayout(voice_layout)
        self.voice_speed_label = QLabel("Voice Speed:")
        self.voice_speed_slider = QSlider(Qt.Horizontal)
        self.voice_speed_slider.setRange(50, 200)
        self.voice_speed_slider.setValue(100)
        self.voice_speed_slider.valueChanged.connect(self.change_voice_speed)
        self.stop_tts_btn = self._styled_button("Stop TTS", "#f44336")
        self.stop_tts_btn.clicked.connect(self.stop_tts)
        voice_layout.addWidget(self.voice_speed_label)
        voice_layout.addWidget(self.voice_speed_slider)
        voice_layout.addWidget(self.stop_tts_btn)
        
        # Status display
        self.accessibility_status = QTextEdit()
        self.accessibility_status.setMaximumHeight(100)
        self.status_btn = self._styled_button("Check Status", "#2196F3")
        self.status_btn.clicked.connect(self.check_accessibility_status)
        self.help_btn = self._styled_button("Accessibility Help", "#FF9800")
        self.help_btn.clicked.connect(self.show_accessibility_help)
        
        layout.addWidget(nav_group)
        layout.addWidget(visual_group)
        layout.addWidget(voice_group)
        layout.addWidget(self.accessibility_status)
        layout.addWidget(self.status_btn)
        layout.addWidget(self.help_btn)
        return w

    def _settings_tab(self):
        w = QWidget()
        w.setStyleSheet("background-color: #f0f8ff;")
        layout = QFormLayout()
        w.setLayout(layout)
        self.model_path = QLineEdit("models/vosk-model-small-en-us-0.15")
        btn_dl = self._styled_button("Download Vosk Model", "#FF9800")
        btn_dl.clicked.connect(self.on_download)
        btn_open = self._styled_button("Open config folder", "#2196F3")
        btn_open.clicked.connect(lambda: webbrowser.open(os.path.abspath("config")))
        layout.addRow("Model:", self.model_path)
        layout.addRow(btn_dl, btn_open)
        return w

    def on_wake(self):
        if not self.auth:
            self.tts.say("Authentication system not loaded yet. Please wait for components to load.")
            return
            
        self.state_label.setText("State: Authenticating..."); self.tts.say("Please authenticate.")
        th = WorkerThread(self.auth.authenticate_interactive); th.start(); th.wait()
        res = th.result()
        if isinstance(res, Exception) or not res:
            QMessageBox.warning(self, "Auth", "Failed"); self.state_label.setText("State: Sleeping"); self.tts.say("Authentication failed")
        else:
            QMessageBox.information(self, "Auth", "Success"); self.state_label.setText("State: Active"); self.user_label.setText(f"User: {res}"); self.tts.say(f"Welcome {res}")

    def on_sleep(self):
        self.state_label.setText("State: Sleeping"); self.tts.say("Going to sleep")

    def on_listen(self, checked):
        if not self.stt_mgr or not self.parser or not self.executor:
            self.tts.say("System components not loaded yet. Please wait for initialization to complete.")
            self.listen_btn.setChecked(False)
            return
            
        if self.listen_btn.isChecked():
            self.listen_btn.setText("Stop Listening"); self.state_label.setText("State: Listening")
            self.stt_mgr.start_listening(self._stt_callback)
        else:
            self.listen_btn.setText("Start Listening"); self.state_label.setText("State: Active"); self.stt_mgr.stop_listening()

    def _is_valid_command(self, text: str) -> bool:
        """Check if the recognized text looks like a valid command"""
        if not text or len(text.strip()) < 3:
            return False
        
        text_lower = text.lower().strip()
        words = text_lower.split()
        
        # Filter out common false positives and noise
        noise_words = [
            'uh', 'um', 'ah', 'eh', 'oh', 'hmm', 'mm', 'hm',
            'hi', 'hey', 'hello', 'ok', 'okay', 'yeah', 'yep', 'nope',
            'right', 'left', 'up', 'down', 'one', 'two', 'three', 'four', 'five',
            'his', 'her', 'its', 'our', 'your', 'my', 'me', 'we', 'they', 'them',
            'best', 'good', 'bad', 'big', 'small', 'new', 'old', 'first', 'last',
            'you are', 'i am', 'he is', 'she is', 'it is', 'we are', 'they are',
            'and', 'or', 'but', 'so', 'if', 'as', 'be', 'do', 'go', 'no', 'yes',
            'op', 'it', 'is', 'at', 'in', 'on', 'to', 'of', 'for', 'the', 'a', 'an'
        ]
        
        # If it's just noise words, reject it
        if len(words) <= 2 and all(word in noise_words for word in words):
            return False
        
        # If it's a single noise word, reject it
        if len(words) == 1 and words[0] in noise_words:
            return False
        
        # Common command keywords that indicate a valid command
        command_keywords = [
            # System commands
            'open', 'close', 'start', 'stop', 'shutdown', 'restart', 'sleep', 'lock',
            # File operations
            'file', 'folder', 'create', 'delete', 'copy', 'paste', 'save', 'navigate', 'go to', 'list',
            # App control
            'app', 'application', 'switch', 'minimize', 'maximize', 'window',
            # Web operations
            'search', 'google', 'youtube', 'website', 'tab', 'browser',
            # Media control
            'play', 'pause', 'stop', 'next', 'previous', 'volume', 'mute',
            # Text operations
            'type', 'write', 'select', 'cut', 'undo', 'redo',
            # Navigation
            'click', 'scroll', 'zoom', 'back', 'forward',
            # System info
            'system', 'info', 'battery', 'disk', 'memory', 'cpu',
            # Accessibility
            'read', 'describe', 'screen'
        ]
        
        # Check if text contains any command keywords
        for keyword in command_keywords:
            if keyword in text_lower:
                return True
        
        # If it's a very short phrase (1-2 words) without command keywords, ignore it
        if len(words) <= 2 and not any(keyword in text_lower for keyword in command_keywords):
            return False
        
        # Require at least 3 words for commands without clear keywords (to reduce false positives)
        if len(words) < 3 and not any(keyword in text_lower for keyword in command_keywords):
            return False
        
        return False  # Default: ignore unrecognized text

    def _stt_callback(self, text):
        self.last_label.setText("Last: "+text)
        print(f"Voice command received: {text}")
        
        try:
            text_lower = text.lower().strip()
            
            # Handle typing mode
            if self.typing_mode:
                # Check for exit commands
                if any(exit_cmd in text_lower for exit_cmd in ['done typing', 'finish typing', 'stop typing', 'end typing', 'cancel typing', 'cancel']):
                    if 'cancel' in text_lower:
                        self._cancel_typing()
                    else:
                        self._finish_typing()
                    return
                
                # Check for new line command
                if 'new line' in text_lower or 'newline' in text_lower:
                    self.typing_buffer.append('\n')
                    if self.tts:
                        self.tts.say("New line")
                    # Reset timer
                    self._reset_typing_timer()
                    return
                
                # Add text to buffer
                self.typing_buffer.append(text)
                # Reset timer - will execute after 2.5 seconds of silence
                self._reset_typing_timer()
                return
            
            # Check if this is a type command that should enter typing mode
            if text_lower.startswith('type ') or text_lower.startswith('write '):
                # Extract initial text if any
                if text_lower.startswith('type '):
                    initial_text = text_lower.replace('type', '', 1).strip()
                else:
                    initial_text = text_lower.replace('write', '', 1).strip()
                
                # Enter typing mode
                self._start_typing_mode(initial_text)
                return
            
            # Validate if this looks like a valid command BEFORE authentication check
            if not self._is_valid_command(text):
                print(f"Ignoring invalid command: '{text}' (not a recognized command pattern)")
                return  # Silently ignore - don't execute, don't speak
            
            # Check if components are loaded
            if not self.executor:
                if self.tts:
                    self.tts.say("System components not ready yet. Please wait.")
                return
            
            # CRITICAL: Check authentication first - this is a main pillar of the project
            if not self.auth:
                print("Authentication system not available")
                if self.tts:
                    self.tts.say("Authentication system not available. Please restart EchoOS.")
                return
            
            if not self.auth.is_authenticated():
                print("User not authenticated, requesting authentication")
                if self.tts:
                    self.tts.say("Please authenticate first by clicking 'Wake / Authenticate'")
                return
            
            # Check session validity
            if not self.auth.is_session_valid():
                print("Session expired, requesting re-authentication")
                if self.tts:
                    self.tts.say("Session expired. Please authenticate again by clicking 'Wake / Authenticate'")
                return
            
            # Log authenticated user
            current_user = self.auth.get_current_user()
            print(f"User authenticated: {current_user} - Command authorized")
            # Execute command using simple universal executor
            result = self._execute_universal_command(text)
            
            if not result:
                print("Command execution failed")
                if self.tts:
                    self.tts.say("Command not understood. Please try again.")
            else:
                print("Command executed successfully")
                # Note: Individual commands should provide their own TTS feedback
            
        except Exception as e:
            print(f"STT callback error: {e}")
            import traceback
            traceback.print_exc()
            try:
                if self.tts:
                    self.tts.say("Sorry, I encountered an error processing that command")
            except Exception as tts_error:
                print(f"TTS error: {tts_error}")
    
    def _start_typing_mode(self, initial_text=""):
        """Enter typing mode - will listen for multiple phrases"""
        self.typing_mode = True
        self.typing_buffer = []
        if initial_text:
            self.typing_buffer.append(initial_text)
        if self.tts:
            self.tts.say("Typing mode. Speak what you want to type. Say 'done typing' when finished, or 'cancel' to cancel.")
        self._reset_typing_timer()
    
    def _cancel_typing(self):
        """Cancel typing mode without typing anything"""
        self.typing_mode = False
        if self.typing_timer:
            self.typing_timer.stop()
            self.typing_timer = None
        self.typing_buffer = []
        if self.tts:
            self.tts.say("Typing cancelled.")
    
    def _reset_typing_timer(self):
        """Reset the timer that will finish typing after silence"""
        if self.typing_timer:
            self.typing_timer.stop()
        # Wait 2.5 seconds of silence before typing
        self.typing_timer = QTimer()
        self.typing_timer.setSingleShot(True)
        self.typing_timer.timeout.connect(self._finish_typing)
        self.typing_timer.start(2500)  # 2.5 seconds
    
    def _finish_typing(self):
        """Finish typing mode and type all collected text"""
        if not self.typing_mode:
            return
        
        self.typing_mode = False
        if self.typing_timer:
            self.typing_timer.stop()
            self.typing_timer = None
        
        if not self.typing_buffer:
            if self.tts:
                self.tts.say("Nothing to type.")
            return
        
        # Combine all text with spaces, handle newlines
        full_text = self._process_typing_buffer(self.typing_buffer)
        
        # Execute typing
        result = self._execute_typing(full_text)
        
        # Clear buffer
        self.typing_buffer = []
        
        if result and self.tts:
            preview = full_text[:50] + "..." if len(full_text) > 50 else full_text
            self.tts.say(f"Typed: {preview}")
    
    def _process_typing_buffer(self, buffer):
        """Process typing buffer: add spaces between words, handle newlines"""
        if not buffer:
            return ""
        
        processed = []
        for i, item in enumerate(buffer):
            if item == '\n':
                processed.append('\n')
            else:
                # Add space before if not first item and previous wasn't newline
                if i > 0 and processed and processed[-1] != '\n':
                    processed.append(' ')
                processed.append(item)
        
        result = ''.join(processed).strip()
        # Replace multiple spaces with single space (except around newlines)
        import re
        # Replace multiple spaces with single space, but preserve newlines
        lines = result.split('\n')
        processed_lines = [re.sub(r' +', ' ', line).strip() for line in lines]
        result = '\n'.join(processed_lines)
        return result
    
    def _execute_typing(self, text):
        """Execute the actual typing"""
        try:
            # Try universal executor V2 first
            if hasattr(self, 'universal_executor_v2') and self.universal_executor_v2:
                return self.universal_executor_v2._type_text(text)
            
            # Try direct executor
            if hasattr(self, 'direct_executor') and self.direct_executor:
                return self.direct_executor._type_text(text)
            
            # Fallback to pyautogui directly
            try:
                import pyautogui
                pyautogui.typewrite(text, interval=0.05)
                return True
            except:
                return False
        except Exception as e:
            print(f"Error executing typing: {e}")
            return False
    
    def _execute_universal_command(self, voice_text):
        """Execute commands using universal executor V2 first (most advanced)"""
        try:
            # Try universal executor V2 first (most advanced, uses screen context)
            if hasattr(self, 'universal_executor_v2') and self.universal_executor_v2:
                result = self.universal_executor_v2.execute_command(voice_text)
                if result:
                    return True
            
            # Try direct executor second (reliable fallback)
            if hasattr(self, 'direct_executor') and self.direct_executor:
                result = self.direct_executor.execute_command(voice_text)
                if result:
                    return True
            
            # Try universal executor third
            if self.universal_executor:
                result = self.universal_executor.execute_command(voice_text)
                if result:
                    return True
            
            # Fallback to legacy executor
            if self.executor:
                # Parse command using context-aware parser
                if hasattr(self, 'parser') and self.parser:
                    command = self.parser.parse(voice_text)
                    if command:
                        return self.executor.execute(command)
                
                # Try direct execution
                return self.executor.execute({'action': 'unknown', 'text': voice_text})
            
            return False
            
        except Exception as e:
            print(f"Command execution error: {e}")
            if self.tts:
                self.tts.say(f"Error executing command: {str(e)}")
            return False
    

    def on_register(self):
        if not self.auth:
            QMessageBox.warning(self, "Register", "Authentication system not available")
            return
        name, ok = QInputDialog.getText(self, "Register", "Enter short username:")
        if not ok or not name: return
        self.tts.say("Recording samples now")
        th = WorkerThread(self.auth.register_user, name); th.start(); th.wait()
        res = th.result()
        if res: QMessageBox.information(self, "Register", "Registered"); self.refresh_users()
        else: QMessageBox.warning(self, "Register", "Failed")

    def on_remove(self):
        if not self.auth:
            QMessageBox.warning(self, "Remove", "Authentication system not available")
            return
        item = self.users_list.currentItem()
        if not item: return
        name = item.text()
        if QMessageBox.question(self, "Confirm", f"Remove {name}?") != QMessageBox.Yes: return
        th = WorkerThread(self.auth.remove_user, name); th.start(); th.wait(); self.refresh_users()

    def refresh_users(self):
        self.users_list.clear()
        if self.auth:
            for u in self.auth.load_users(): 
                self.users_list.addItem(u)

    def on_scan(self):
        if not self.components_loaded:
            self.tts.say("Please wait, components are still loading...")
            self.apps_status.setText("⏳ Components loading... Please wait...")
            return
            
        self.tts.say("Starting comprehensive application discovery. This may take a few minutes.")
        self.apps_status.setText("🔍 Discovering applications... Please wait...")
        self.btn_scan.setEnabled(False)
        self.btn_scan.setText("⏳ Discovering...")
        
        def scan_complete():
            try:
                discovered_apps = self.app_disc.discover_and_save("config/apps.json")
                self.load_apps()
                self.apps_status.setText(f"✅ Discovery complete! Found {len(discovered_apps)} applications")
                self.tts.say(f"Application discovery complete. Found {len(discovered_apps)} applications on your system.")
                QMessageBox.information(self, "Discovery Complete", f"Found {len(discovered_apps)} applications!\n\nYou can now say 'open [app name]' to launch any discovered application.")
            except Exception as e:
                self.apps_status.setText(f"❌ Discovery failed: {str(e)}")
                self.tts.say("Application discovery failed. Please try again.")
                QMessageBox.critical(self, "Discovery Failed", f"Error: {str(e)}")
            finally:
                self.btn_scan.setEnabled(True)
                self.btn_scan.setText("🔍 Discover All Apps")
        
        th = WorkerThread(scan_complete)
        th.start()

    def load_apps(self):
        try:
            with open("config/apps.json","r",encoding="utf-8") as f: self.apps_text.setPlainText(f.read())
        except: self.apps_text.setPlainText("{}")

    def on_save_apps(self):
        try:
            with open("config/apps.json","w",encoding="utf-8") as f: f.write(self.apps_text.toPlainText()); QMessageBox.information(self,"Saved","Saved")
        except Exception as e:
            QMessageBox.critical(self,"Error",str(e))

    def on_download(self):
        from modules.stt import download_vosk_model
        path = self.model_path.text().strip()
        ok = download_vosk_model(path)
        QMessageBox.information(self, "Download", "Completed" if ok else "Failed")

    # Accessibility methods
    def toggle_navigation_mode(self):
        if self.accessibility:
            if self.accessibility.navigation_mode:
                self.accessibility.disable_navigation_mode()
                self.nav_mode_btn.setText("Enable Navigation Mode")
            else:
                self.accessibility.enable_navigation_mode()
                self.nav_mode_btn.setText("Disable Navigation Mode")

    def read_screen(self):
        if self.accessibility:
            self.accessibility.read_screen()

    def describe_screen(self):
        if self.accessibility:
            self.accessibility.describe_screen()

    def toggle_high_contrast(self):
        if self.accessibility:
            self.accessibility.toggle_high_contrast()

    def toggle_large_text(self):
        if self.accessibility:
            self.accessibility.toggle_large_text()

    def change_voice_speed(self, value):
        if self.accessibility:
            speed = value / 100.0  # Convert slider value to speed
            self.accessibility.set_voice_speed(speed)

    def check_accessibility_status(self):
        if self.accessibility:
            status = self.accessibility.get_accessibility_status()
            status_text = f"Navigation Mode: {'On' if status['navigation_mode'] else 'Off'}\n"
            status_text += f"Screen Reading: {'On' if status['screen_reading'] else 'Off'}\n"
            status_text += f"High Contrast: {'On' if status['high_contrast'] else 'Off'}\n"
            status_text += f"Large Text: {'On' if status['large_text'] else 'Off'}\n"
            status_text += f"Voice Speed: {status['voice_speed']:.1f}x"
            self.accessibility_status.setPlainText(status_text)

    def show_accessibility_help(self):
        if self.accessibility:
            self.accessibility.help_accessibility()

    def stop_tts(self):
        """Stop current TTS speech"""
        if self.tts:
            self.tts.stop_speaking()
            print("[TTS] Speech stopped by user")
