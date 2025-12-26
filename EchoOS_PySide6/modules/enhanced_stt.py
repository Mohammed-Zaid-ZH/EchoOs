"""
Enhanced Speech-to-Text System for EchoOS
Improves accuracy and handles common speech recognition errors
"""

import os
import sys
import threading
import time
import logging
import json
import re
from typing import Optional, Callable, Dict, List, Any
from rapidfuzz import fuzz, process

# NumPy for audio processing
try:
    import numpy as np
    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False
    print("NumPy not available - some audio processing features may be limited")

# Vosk imports
try:
    from vosk import Model, KaldiRecognizer
    import sounddevice as sd
    VOSK_AVAILABLE = True
except ImportError:
    VOSK_AVAILABLE = False
    print("Vosk not available - using fallback STT")

# Alternative STT imports
try:
    import speech_recognition as sr
    SPEECH_RECOGNITION_AVAILABLE = True
except ImportError:
    SPEECH_RECOGNITION_AVAILABLE = False

try:
    import whisper
    WHISPER_AVAILABLE = True
except ImportError:
    WHISPER_AVAILABLE = False

class EnhancedSTT:
    """Enhanced Speech-to-Text with error correction and multiple backends"""
    
    def __init__(self, tts=None, model_path="models/vosk-model-small-en-us-0.15"):
        self.tts = tts
        self.logger = logging.getLogger(__name__)
        self.model_path = model_path
        self.model = None
        self.recognizer = None
        self._listening = False
        self._current_callback = None
        
        # Speech recognition quality settings
        self.energy_threshold = 500  # Minimum audio energy to consider as speech (0-32767 for int16)
        self.silence_duration = 0.5  # Seconds of silence before stopping
        self.min_speech_duration = 0.3  # Minimum duration of speech to process
        self.min_text_length = 3  # Minimum number of characters in recognized text
        self.min_word_count = 2  # Minimum number of words for a valid command
        self.confidence_threshold = 0.3  # Minimum confidence (Vosk doesn't provide this directly, but we can infer)
        
        # Speech correction mappings
        self.correction_mappings = self._build_correction_mappings()
        
        # Common commands for better recognition
        self.common_commands = self._build_common_commands()
        
        # Initialize STT backend
        self._initialize_stt()
        
    def _build_correction_mappings(self) -> Dict[str, str]:
        """Build mappings for common speech recognition errors"""
        return {
            # Common misrecognitions
            'nor bad': 'notepad',
            'not bad': 'notepad',
            'knot bad': 'notepad',
            'not pad': 'notepad',
            'note pad': 'notepad',
            'notepad': 'notepad',
            
            # Hackathon and similar words
            'had a though': 'hackathon',
            'had a thought': 'hackathon',
            'hack a thon': 'hackathon',
            'hack a ton': 'hackathon',
            'hack a thong': 'hackathon',
            'hackathon': 'hackathon',
            'hackathon': 'hackathon',
            
            'whats up': 'whatsapp',
            'what\'s up': 'whatsapp',
            'what\'s app': 'whatsapp',
            'whats app': 'whatsapp',
            
            'chrome': 'chrome',
            'crow': 'chrome',
            'crown': 'chrome',
            
            'edge': 'edge',
            'edgy': 'edge',
            'ed': 'edge',
            
            'calculator': 'calculator',
            'calc': 'calculator',
            'calculate': 'calculator',
            
            'minimize': 'minimize',
            'minimise': 'minimize',
            'minimize app': 'minimize',
            'minimize window': 'minimize',
            
            'maximize': 'maximize',
            'maximise': 'maximize',
            'maximize app': 'maximize',
            'maximize window': 'maximize',
            
            'close': 'close',
            'close app': 'close',
            'close window': 'close',
            'close tab': 'close tab',
            'close all tabs': 'close all tabs',
            
            'lock': 'lock',
            'lock screen': 'lock screen',
            'lock computer': 'lock screen',
            
            'search': 'search',
            'search for': 'search for',
            'search about': 'search about',
            'search google': 'search google',
            
            'volume up': 'volume up',
            'volume down': 'volume down',
            'mute': 'mute',
            'unmute': 'unmute',
            
            'open': 'open',
            'launch': 'open',
            'start': 'open',
            'run': 'open',
            
            'type': 'type',
            'write': 'type',
            'enter': 'type',
            'input': 'type',
            
            'click': 'click',
            'tap': 'click',
            'press': 'click',
            
            'scroll up': 'scroll up',
            'scroll down': 'scroll down',
            'scroll': 'scroll',
            
            'documents': 'documents',
            'downloads': 'downloads',
            'desktop': 'desktop',
            'pictures': 'pictures',
            'videos': 'videos',
            'music': 'music',
            
            # File/fine confusion - CRITICAL FIX
            'create fine': 'create file',
            'delete fine': 'delete file',
            'open fine': 'open file',
            'copy fine': 'copy file',
            'move fine': 'move file',
            'rename fine': 'rename file',
            'fine': 'file',  # General correction when in file context
            'fines': 'files',
            
            # Additional common errors
            'open video': 'open video',
            'open videos': 'open video',
            'open file': 'open file',
            'open files': 'open file',
            'close app': 'close app',
            'close apps': 'close app',
            'close all': 'close all apps',
            'close all apps': 'close all apps',
            'close current': 'close app',
            'close current app': 'close app',
            'command prompt': 'command prompt',
            'cmd': 'command prompt',
            'execute': 'execute command',
            'run': 'run command',
            'type': 'type',
            'write': 'type',
            'enter': 'type',
            'copy all': 'copy all',
            'paste all': 'paste all',
            'select all': 'select all',
            'scroll down': 'scroll down',
            'scroll up': 'scroll up',
            'volume up': 'volume up',
            'volume down': 'volume down',
            'play': 'play',
            'pause': 'pause',
            'stop': 'stop',
            'next': 'next',
            'previous': 'previous',
            'start from beginning': 'start from beginning',
            'lock screen': 'lock screen',
            'lock': 'lock screen',
            'shutdown': 'shutdown',
            'restart': 'restart',
            'sleep': 'sleep',
            'system info': 'system info',
            'battery': 'battery status',
            'battery status': 'battery status'
        }
    
    def _build_common_commands(self) -> List[str]:
        """Build list of common commands for better recognition"""
        return [
            # App commands
            'open notepad', 'open chrome', 'open edge', 'open firefox',
            'open calculator', 'open paint', 'open word', 'open excel',
            'open powerpoint', 'open file explorer', 'open cmd',
            'open powershell', 'open task manager', 'open settings',
            
            # System commands
            'lock screen', 'shutdown', 'restart', 'sleep', 'hibernate',
            'volume up', 'volume down', 'mute', 'unmute',
            
            # Window commands
            'minimize', 'maximize', 'close', 'close all tabs',
            'new tab', 'close tab', 'next tab', 'previous tab',
            
            # Navigation commands
            'go to desktop', 'go to documents', 'go to downloads',
            'navigate to desktop', 'navigate to documents',
            
            # File commands
            'create file', 'create folder', 'delete file', 'copy file', 'move file',
            'rename file', 'save file', 'open file',
            
            # Search commands
            'search google', 'search youtube', 'search amazon',
            'search for', 'search about',
            
            # Media commands
            'play', 'pause', 'stop', 'next', 'previous',
            'volume up', 'volume down',
            
            # Text commands
            'type', 'write', 'enter', 'select all', 'copy', 'paste',
            'cut', 'undo', 'redo', 'find', 'replace',
            
            # Click commands
            'click', 'double click', 'right click', 'click on',
            
            # Scroll commands
            'scroll up', 'scroll down', 'scroll', 'page up', 'page down'
        ]
    
    def _initialize_stt(self):
        """Initialize STT backend"""
        if VOSK_AVAILABLE and os.path.exists(self.model_path):
            try:
                self.model = Model(self.model_path)
                self.recognizer = KaldiRecognizer(self.model, 16000)
                self.logger.info("Vosk STT initialized successfully")
            except Exception as e:
                self.logger.error(f"Failed to initialize Vosk: {e}")
                self._initialize_fallback_stt()
        else:
            self.logger.warning("Vosk not available, using fallback STT")
            self._initialize_fallback_stt()
    
    def _initialize_fallback_stt(self):
        """Initialize fallback STT system"""
        if SPEECH_RECOGNITION_AVAILABLE:
            try:
                self.recognizer = sr.Recognizer()
                self.microphone = sr.Microphone()
                # Adjust for ambient noise
                with self.microphone as source:
                    self.recognizer.adjust_for_ambient_noise(source)
                self.logger.info("Speech Recognition fallback initialized")
            except Exception as e:
                self.logger.error(f"Failed to initialize Speech Recognition: {e}")
        else:
            self.logger.error("No STT backend available")
    
    def start_listening(self, callback: Callable[[str], None], timeout: int = 4) -> bool:
        """Start listening for voice commands"""
        if self._listening:
            return False
        
        self._current_callback = callback
        self._listening = True
        
        # Calibrate energy threshold based on ambient noise if first time
        if not hasattr(self, '_energy_calibrated'):
            self._calibrate_energy_threshold()
            self._energy_calibrated = True
        
        if VOSK_AVAILABLE and self.model:
            self._thread = threading.Thread(
                target=self._vosk_listening_loop, 
                args=(callback, timeout), 
                daemon=True
            )
        else:
            self._thread = threading.Thread(
                target=self._fallback_listening_loop, 
                args=(callback, timeout), 
                daemon=True
            )
        
        self._thread.start()
        return True
    
    def _calibrate_energy_threshold(self):
        """Calibrate energy threshold based on ambient noise"""
        try:
            if not VOSK_AVAILABLE or not sd:
                return
            
            self.logger.info("Calibrating energy threshold...")
            # Record 1 second of ambient noise
            calibration_data = sd.rec(
                int(1.0 * 16000),
                samplerate=16000,
                channels=1,
                dtype='int16'
            )
            sd.wait()
            
            # Calculate baseline energy
            baseline_energy = self._calculate_audio_energy(calibration_data)
            
            # Set threshold to 1.5x baseline (speech should be louder than ambient)
            if baseline_energy > 0:
                self.energy_threshold = max(300, int(baseline_energy * 1.5 * 32767))
                self.logger.info(f"Energy threshold calibrated to: {self.energy_threshold} (baseline: {baseline_energy:.2f})")
            else:
                self.logger.info(f"Using default energy threshold: {self.energy_threshold}")
        except Exception as e:
            self.logger.warning(f"Energy calibration failed: {e}, using default threshold")
    
    def set_energy_threshold(self, threshold: int):
        """Manually set energy threshold (0-32767)"""
        self.energy_threshold = max(0, min(32767, threshold))
        self.logger.info(f"Energy threshold set to: {self.energy_threshold}")
    
    def set_min_word_count(self, count: int):
        """Set minimum word count for valid commands"""
        self.min_word_count = max(1, count)
        self.logger.info(f"Minimum word count set to: {self.min_word_count}")
    
    def stop_listening(self):
        """Stop listening for voice commands"""
        self._listening = False
        self._current_callback = None
    
    def _calculate_audio_energy(self, audio_data) -> float:
        """Calculate RMS energy of audio signal"""
        try:
            if not NUMPY_AVAILABLE:
                # Fallback: simple energy calculation without numpy
                if len(audio_data) == 0:
                    return 0.0
                energy_sum = sum(float(x) * float(x) for x in audio_data)
                rms = (energy_sum / len(audio_data)) ** 0.5
                return rms
            
            if len(audio_data) == 0:
                return 0.0
            # Calculate RMS (Root Mean Square) energy
            rms = np.sqrt(np.mean(audio_data.astype(np.float32) ** 2))
            return rms
        except Exception as e:
            self.logger.debug(f"Error calculating audio energy: {e}")
            return 0.0
    
    def _has_speech(self, audio_data) -> bool:
        """Check if audio contains speech based on energy threshold"""
        try:
            energy = self._calculate_audio_energy(audio_data)
            # Normalize energy threshold (int16 range is -32768 to 32767)
            # For int16, max value is 32767, so we normalize
            if NUMPY_AVAILABLE:
                max_val = 32767.0
            else:
                max_val = 32767.0
            normalized_threshold = self.energy_threshold / max_val
            return energy > normalized_threshold
        except Exception as e:
            self.logger.debug(f"Error checking for speech: {e}")
            return False
    
    def _vosk_listening_loop(self, callback: Callable[[str], None], timeout: int):
        """Vosk-based listening loop with improved filtering"""
        try:
            rec = KaldiRecognizer(self.model, 16000)
            
            while self._listening:
                try:
                    # Record audio
                    data = sd.rec(
                        int(timeout * 16000), 
                        samplerate=16000, 
                        channels=1, 
                        dtype='int16'
                    )
                    sd.wait()
                    
                    if not self._listening:
                        break
                    
                    # Check if audio has sufficient energy (not silence/background noise)
                    if not self._has_speech(data):
                        self.logger.debug("Audio energy too low, skipping...")
                        continue
                    
                    # Process audio
                    rec.AcceptWaveform(data.tobytes())
                    result = rec.Result()
                    result_dict = json.loads(result)
                    text = result_dict.get("text", "")
                    
                    # Additional filtering: check if result seems valid
                    if not text or len(text.strip()) < self.min_text_length:
                        continue
                    
                    # Check word count
                    words = text.strip().split()
                    if len(words) < self.min_word_count:
                        # Allow single-word commands only if they're common commands
                        if words and words[0].lower() not in ['open', 'close', 'minimize', 'maximize', 'lock', 'mute', 'unmute', 'play', 'pause', 'stop']:
                            self.logger.debug(f"Ignoring short text: '{text}' (only {len(words)} word(s))")
                            continue
                    
                    # Check for partial results (low confidence) - Vosk uses empty text for low confidence
                    # But we can also check if the text is too short or seems like noise
                    if self._is_likely_noise(text):
                        self.logger.debug(f"Filtered out likely noise: '{text}'")
                        continue
                    
                    # Correct and process the text
                    corrected_text = self._correct_speech_text(text.strip())
                    if corrected_text and len(corrected_text.strip()) >= self.min_text_length:
                        self.logger.info(f"Recognized: '{text}' -> '{corrected_text}'")
                        callback(corrected_text)
                    else:
                        self.logger.debug(f"Corrected text too short or empty: '{corrected_text}'")
                            
                except Exception as e:
                    self.logger.error(f"Vosk listening error: {e}")
                    # Continue listening instead of breaking - don't stop on single errors
                    import traceback
                    self.logger.debug(traceback.format_exc())
                    continue
                    
        except Exception as e:
            self.logger.error(f"Vosk listening loop error: {e}")
            import traceback
            self.logger.debug(traceback.format_exc())
            # Loop will exit naturally - user can restart listening manually
    
    def _is_likely_noise(self, text: str) -> bool:
        """Check if recognized text is likely background noise or false positive"""
        if not text:
            return True
        
        text_lower = text.lower().strip()
        
        # Very short text is likely noise
        if len(text_lower) < 2:
            return True
        
        # Common false positives from background noise
        noise_patterns = [
            'uh', 'um', 'ah', 'eh', 'oh', 'hmm', 'mm', 'hm',
            'a', 'an', 'the', 'is', 'it', 'at', 'in', 'on', 'to', 'of', 'for',
            'and', 'or', 'but', 'so', 'if', 'as', 'be', 'do', 'go', 'no', 'yes',
            'hi', 'hey', 'hello', 'ok', 'okay', 'yeah', 'yep', 'nope',
            'right', 'left', 'up', 'down', 'one', 'two', 'three', 'four', 'five',
            'his', 'her', 'its', 'our', 'your', 'my', 'me', 'we', 'they', 'them',
            'best', 'good', 'bad', 'big', 'small', 'new', 'old', 'first', 'last',
            'you are', 'i am', 'he is', 'she is', 'it is', 'we are', 'they are'
        ]
        
        # Check if text matches common noise patterns exactly
        if text_lower in noise_patterns:
            return True
        
        # Check if it's just filler words
        words = text_lower.split()
        if len(words) <= 2:
            # If all words are common noise words, it's likely noise
            if all(word in noise_patterns for word in words):
                return True
        
        # Check for very repetitive patterns (e.g., "ah ah ah")
        if len(set(words)) == 1 and len(words) > 1:
            return True
        
        return False
    
    def _fallback_listening_loop(self, callback: Callable[[str], None], timeout: int):
        """Fallback listening loop using speech_recognition"""
        if not SPEECH_RECOGNITION_AVAILABLE:
            return
        
        try:
            while self._listening:
                try:
                    with self.microphone as source:
                        # Listen for audio with timeout
                        audio = self.recognizer.listen(source, timeout=timeout, phrase_time_limit=5)
                    
                    if not self._listening:
                        break
                    
                    # Recognize speech
                    try:
                        text = self.recognizer.recognize_google(audio)
                        if text.strip():
                            # Correct and process the text
                            corrected_text = self._correct_speech_text(text.strip())
                            if corrected_text:
                                callback(corrected_text)
                    except sr.UnknownValueError:
                        # Speech not understood
                        pass
                    except sr.RequestError as e:
                        self.logger.error(f"Speech recognition service error: {e}")
                        
                except Exception as e:
                    self.logger.error(f"Fallback listening error: {e}")
                    # Continue listening instead of breaking - don't stop on single errors
                    import traceback
                    self.logger.debug(traceback.format_exc())
                    continue
                    
        except Exception as e:
            self.logger.error(f"Fallback listening loop error: {e}")
            import traceback
            self.logger.debug(traceback.format_exc())
            # Loop will exit naturally - user can restart listening manually
    
    def _correct_speech_text(self, text: str) -> Optional[str]:
        """Correct common speech recognition errors"""
        try:
            original_text = text.lower().strip()
            
            # First, clean up common issues
            original_text = self._clean_text(original_text)
            
            # Apply direct corrections - check for longer phrases first
            # Sort by length (longest first) to match longer phrases before shorter ones
            sorted_mappings = sorted(self.correction_mappings.items(), key=lambda x: len(x[0]), reverse=True)
            
            for incorrect, correct in sorted_mappings:
                # Use word boundary matching for better accuracy
                import re
                pattern = r'\b' + re.escape(incorrect) + r'\b'
                if re.search(pattern, original_text):
                    original_text = re.sub(pattern, correct, original_text)
                    self.logger.info(f"Applied correction: '{incorrect}' -> '{correct}'")
            
            # Special case: Fix "fine" -> "file" pattern (CRITICAL - common misrecognition)
            # "create file" is often misheard as "create fine"
            if 'fine' in original_text:
                # Check if it's in a file operation context
                file_operations = ['create', 'delete', 'open', 'copy', 'move', 'rename', 'save']
                if any(op in original_text for op in file_operations):
                    original_text = original_text.replace('fine', 'file')
                    original_text = original_text.replace('fines', 'files')
                    self.logger.info("Fixed pattern 'fine' -> 'file' (file operation context)")
            
            # Special case: Fix "had a though/thought" -> "hackathon" pattern (common misrecognition)
            # This is a critical fix - "open hackathon" is often misheard as "open had a though"
            if 'had' in original_text and ('though' in original_text or 'thought' in original_text):
                # Replace "had a though/thought" with "hackathon" regardless of context
                original_text = original_text.replace('had a though', 'hackathon')
                original_text = original_text.replace('had a thought', 'hackathon')
                original_text = original_text.replace('hadathought', 'hackathon')
                original_text = original_text.replace('hadathou', 'hackathon')
                original_text = original_text.replace('had a thou', 'hackathon')
                self.logger.info("Fixed pattern 'had a though/thought' -> 'hackathon'")
            
            # Also fix other hackathon variations
            patterns_to_fix = [
                ('hack a thon', 'hackathon'),
                ('hack a ton', 'hackathon'),
                ('hack a thong', 'hackathon'),
            ]
            
            for incorrect, correct in patterns_to_fix:
                if incorrect in original_text:
                    original_text = original_text.replace(incorrect, correct)
                    self.logger.info(f"Fixed pattern '{incorrect}' -> '{correct}'")
            
            # Use fuzzy matching for better command recognition
            corrected_text = self._fuzzy_match_commands(original_text)
            
            # Additional context-aware corrections
            corrected_text = self._context_aware_correction(corrected_text)
            
            # Final cleanup
            corrected_text = self._clean_text(corrected_text)
            
            # Remove duplicate words (e.g., "open open notepad" -> "open notepad")
            corrected_text = self._remove_duplicate_words(corrected_text)
            
            # Ensure we return the corrected text, or original if correction failed
            final_text = corrected_text if corrected_text else original_text
            
            if final_text and final_text != text.lower().strip():
                self.logger.info(f"Corrected '{text}' to '{final_text}'")
            
            # Always return something - don't return None
            return final_text if final_text else text
            
        except Exception as e:
            self.logger.error(f"Error correcting speech text: {e}")
            return text
    
    def _fuzzy_match_commands(self, text: str) -> str:
        """Use fuzzy matching to correct commands"""
        try:
            # First try to match the entire text against common commands
            result = process.extractOne(text, self.common_commands, scorer=fuzz.ratio)
            if result and len(result) == 2:
                best_match, best_ratio = result
                if best_ratio > 70:
                    return best_match
            
            # If no good match, try word-by-word correction
            words = text.split()
            
            # Special handling FIRST: If we have "fine" and it's in file operation context, correct to "file"
            # This must happen BEFORE fuzzy matching to ensure proper correction
            if 'fine' in words:
                file_ops = ['create', 'delete', 'open', 'copy', 'move', 'rename', 'save']
                if any(op in words for op in file_ops):
                    # Replace 'fine' with 'file' in the words list
                    words = ['file' if w == 'fine' else w for w in words]
                    self.logger.info("Corrected 'fine' to 'file' in file operation context (fuzzy match)")
            
            corrected_words = []
            
            # Common words that get misrecognized - expanded list
            common_words = [
                'notepad', 'calculator', 'chrome', 'edge', 'firefox', 'paint', 
                'word', 'excel', 'powerpoint', 'hackathon', 'java', 'python',
                'javascript', 'react', 'node', 'echo', 'open', 'close', 'copy',
                'paste', 'type', 'save', 'create', 'delete', 'folder', 'file',
                'document', 'document', 'documents', 'downloads', 'desktop',
                'vscode', 'code', 'visual studio', 'cursor', 'notepad++',
                'slack', 'discord', 'teams', 'zoom', 'outlook', 'gmail',
                'spotify', 'youtube', 'netflix', 'steam', 'git', 'github'
            ]
            
            for word in words:
                # Skip command words (open, close, etc.) - they're usually correct
                if word.lower() in ['open', 'close', 'copy', 'paste', 'type', 'save', 'create', 'delete', 'go', 'to', 'navigate']:
                    corrected_words.append(word)
                    continue
                
                # Try to match against common words with fuzzy matching
                try:
                    result = process.extractOne(word, common_words, scorer=fuzz.ratio)
                    if result and len(result) == 2:
                        best_word_match, best_word_ratio = result
                        # Lower threshold for better correction (50% similarity)
                        if best_word_ratio > 50:
                            corrected_words.append(best_word_match)
                            self.logger.info(f"Fuzzy matched '{word}' -> '{best_word_match}' (score: {best_word_ratio:.1f}%)")
                        else:
                            corrected_words.append(word)
                    else:
                        corrected_words.append(word)
                except Exception as e:
                    self.logger.debug(f"Fuzzy match error for word '{word}': {e}")
                    corrected_words.append(word)
            
            corrected_text = ' '.join(corrected_words)
            
            # Special case: Fix "had a though" pattern when it appears (post-fuzzy-match)
            if 'had' in corrected_text.lower() and ('though' in corrected_text.lower() or 'thought' in corrected_text.lower()):
                # Replace "had a though/thought" with "hackathon"
                corrected_text = corrected_text.replace('had a though', 'hackathon')
                corrected_text = corrected_text.replace('had a thought', 'hackathon')
                corrected_text = corrected_text.replace('hadathought', 'hackathon')
                self.logger.info(f"Fixed pattern 'had a though/thought' -> 'hackathon' (post-fuzzy)")
            
            return corrected_text
            
        except Exception as e:
            self.logger.error(f"Error in fuzzy matching: {e}")
            return text
    
    def _context_aware_correction(self, text: str) -> str:
        """Apply context-aware corrections"""
        try:
            # Handle common patterns
            patterns = [
                # "open [something]" patterns
                (r'open\s+(\w+)', lambda m: f"open {self._correct_app_name(m.group(1))}"),
                
                # "close [something]" patterns  
                (r'close\s+(\w+)', lambda m: f"close {self._correct_app_name(m.group(1))}"),
                
                # "search [something]" patterns
                (r'search\s+for\s+(.+)', r'search for \1'),
                (r'search\s+about\s+(.+)', r'search about \1'),
                
                # Volume patterns
                (r'turn\s+up\s+volume', 'volume up'),
                (r'turn\s+down\s+volume', 'volume down'),
                (r'increase\s+volume', 'volume up'),
                (r'decrease\s+volume', 'volume down'),
                
                # Window patterns
                (r'minimize\s+app', 'minimize'),
                (r'maximize\s+app', 'maximize'),
                (r'minimize\s+window', 'minimize'),
                (r'maximize\s+window', 'maximize'),
            ]
            
            for pattern, replacement in patterns:
                if callable(replacement):
                    text = re.sub(pattern, replacement, text)
                else:
                    text = re.sub(pattern, replacement, text)
            
            return text
            
        except Exception as e:
            self.logger.error(f"Error in context-aware correction: {e}")
            return text
    
    def _correct_app_name(self, app_name: str) -> str:
        """Correct application names"""
        app_corrections = {
            'notepad': 'notepad',
            'not bad': 'notepad',
            'nor bad': 'notepad',
            'knot bad': 'notepad',
            'chrome': 'chrome',
            'crow': 'chrome',
            'crown': 'chrome',
            'edge': 'edge',
            'edgy': 'edge',
            'calculator': 'calculator',
            'calc': 'calculator',
            'paint': 'paint',
            'word': 'word',
            'excel': 'excel',
            'powerpoint': 'powerpoint',
            'cmd': 'cmd',
            'command prompt': 'cmd',
            'powershell': 'powershell'
        }
        
        return app_corrections.get(app_name.lower(), app_name)
    
    def _clean_text(self, text: str) -> str:
        """Clean up the text"""
        try:
            # Remove extra whitespace
            text = re.sub(r'\s+', ' ', text).strip()
            
            # Remove common filler words at the beginning/end
            filler_words = ['um', 'uh', 'like', 'you know', 'actually', 'basically']
            words = text.split()
            
            # Remove leading filler words
            while words and words[0].lower() in filler_words:
                words.pop(0)
            
            # Remove trailing filler words
            while words and words[-1].lower() in filler_words:
                words.pop()
            
            return ' '.join(words)
            
        except Exception as e:
            self.logger.error(f"Error cleaning text: {e}")
            return text
    
    def _remove_duplicate_words(self, text: str) -> str:
        """Remove duplicate consecutive words"""
        try:
            words = text.split()
            if len(words) <= 1:
                return text
            
            cleaned_words = [words[0]]
            for i in range(1, len(words)):
                if words[i] != words[i-1]:
                    cleaned_words.append(words[i])
            
            return ' '.join(cleaned_words)
            
        except Exception as e:
            self.logger.error(f"Error removing duplicate words: {e}")
            return text
    
    def get_available_commands(self) -> List[str]:
        """Get list of available commands"""
        return self.common_commands.copy()
    
    def add_custom_correction(self, incorrect: str, correct: str):
        """Add custom speech correction mapping"""
        self.correction_mappings[incorrect.lower()] = correct.lower()
    
    def add_custom_command(self, command: str):
        """Add custom command to recognition list"""
        if command not in self.common_commands:
            self.common_commands.append(command)
    
    def get_status(self) -> Dict[str, Any]:
        """Get STT system status"""
        return {
            'vosk_available': VOSK_AVAILABLE,
            'speech_recognition_available': SPEECH_RECOGNITION_AVAILABLE,
            'whisper_available': WHISPER_AVAILABLE,
            'model_loaded': self.model is not None,
            'listening': self._listening,
            'correction_mappings': len(self.correction_mappings),
            'common_commands': len(self.common_commands)
        }
