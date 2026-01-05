import logging
import os
import soundfile as sf
from typing import List, Dict, Any
from pathlib import Path
from dataclasses import dataclass

# Try to import TTS, but handle the apex conflict gracefully
TTS = None
TTS_IMPORT_ERROR = None
GTTS_AVAILABLE = False
PYTTSX3_AVAILABLE = False

# Try to import gTTS (Google Text-to-Speech) - faster and async
try:
    from gtts import gTTS
    import io
    GTTS_AVAILABLE = True
except ImportError:
    GTTS_AVAILABLE = False

# Try to import pyttsx3 as fallback
try:
    import pyttsx3
    PYTTSX3_AVAILABLE = True
except ImportError:
    PYTTSX3_AVAILABLE = False

# Try to import Coqui TTS
try:
    # First check if we can import the base TTS module
    import TTS as tts_module
    # Then try to import the API
    from TTS.api import TTS
    TTS = TTS  # Success
except ImportError as e:
    import logging
    import traceback
    logger = logging.getLogger(__name__)
    error_msg = str(e).lower()
    error_traceback = traceback.format_exc().lower()
    TTS_IMPORT_ERROR = str(e)
    
    # Check both the error message and traceback for apex-related errors
    if "apex" in error_msg or "cannot import name 'amp'" in error_msg or "amp" in error_msg or "apex" in error_traceback:
        logger.warning(f"TTS package conflict detected: {str(e)}")
        logger.warning("TTS requires NVIDIA apex library, but apex-saas-framework is installed.")
        logger.warning("TTS audio generation will be disabled. To enable TTS, you may need to:")
        logger.warning("  1. Use a different TTS library (e.g., pyttsx3, gTTS)")
        logger.warning("  2. Install NVIDIA apex in a separate environment")
        logger.warning("  3. Or remove apex-saas-framework (not recommended if you need authentication)")
        TTS_IMPORT_ERROR = f"apex_conflict: {str(e)}"
    else:
        logger.warning(f"Coqui TTS not available: {str(e)}")
        logger.warning("Install with: pip install TTS>=0.22.0")
        # Log full traceback for debugging (use INFO level so it's visible)
        full_traceback = traceback.format_exc()
        logger.info(f"Full TTS import error traceback: {full_traceback}")
        # Check traceback for apex even if error message doesn't mention it
        if "apex" in full_traceback.lower() or "cannot import name 'amp'" in full_traceback.lower():
            logger.warning("Apex conflict detected in traceback!")
            TTS_IMPORT_ERROR = f"apex_conflict: {str(e)}"
    TTS = None
except Exception as e:
    import logging
    import traceback
    logger = logging.getLogger(__name__)
    error_msg = str(e).lower()
    error_traceback = traceback.format_exc().lower()
    TTS_IMPORT_ERROR = str(e)
    if "apex" in error_msg or "cannot import name 'amp'" in error_msg or "amp" in error_msg or "apex" in error_traceback:
        logger.error(f"TTS import failed due to apex conflict: {str(e)}")
        TTS_IMPORT_ERROR = f"apex_conflict: {str(e)}"
    else:
        logger.error(f"Unexpected error importing TTS: {str(e)}")
        logger.debug(f"Full TTS import error traceback: {traceback.format_exc()}")
    TTS = None

from src.podcast.script_generator import PodcastScript

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Log pyttsx3 availability after logger is set up
if PYTTSX3_AVAILABLE:
    logger.info("pyttsx3 is available as TTS fallback")


@dataclass
class AudioSegment:
    """Represents a single audio segment with metadata"""
    speaker: str
    text: str
    audio_data: Any
    duration: float
    file_path: str


class PodcastTTSGenerator:
    def __init__(self, model_name: str = "tts_models/en/ljspeech/tacotron2-DDC", sample_rate: int = 22050):
        self.sample_rate = sample_rate
        self.use_gtts = False
        self.use_pyttsx3 = False
        self.tts = None
        self.pyttsx3_engine = None
        
        # Try Coqui TTS first
        if TTS is not None:
            try:
                logger.info(f"Initializing Coqui TTS with model: {model_name}")
                self.tts = TTS(model_name=model_name, progress_bar=True)
                logger.info("Coqui TTS initialized successfully")
                return
            except Exception as e:
                logger.warning(f"Coqui TTS initialization failed: {e}, falling back to gTTS")
        
        # Fallback to gTTS (Google Text-to-Speech) - faster and async
        if GTTS_AVAILABLE:
            try:
                from gtts import gTTS
                self.use_gtts = True
                logger.info("gTTS (Google Text-to-Speech) initialized successfully")
                logger.info("Using gTTS for faster audio generation (requires internet connection)")
                return
            except Exception as e:
                logger.warning(f"gTTS initialization failed: {e}, falling back to pyttsx3")
        
        # Fallback to pyttsx3 if gTTS is not available
        if PYTTSX3_AVAILABLE:
            try:
                import pyttsx3
                self.pyttsx3_engine = pyttsx3.init()
                self.use_pyttsx3 = True
                
                # Configure pyttsx3 settings
                # Get available voices
                voices = self.pyttsx3_engine.getProperty('voices')
                if voices and len(voices) >= 2:
                    # Use different voices for different speakers
                    self.pyttsx3_engine.setProperty('voice', voices[0].id)  # Speaker 1
                    logger.info(f"pyttsx3 initialized with {len(voices)} voices available")
                else:
                    logger.info("pyttsx3 initialized with default voice")
                
                # Set speech rate (words per minute)
                self.pyttsx3_engine.setProperty('rate', 150)  # Normal speech rate
                # Set volume (0.0 to 1.0)
                self.pyttsx3_engine.setProperty('volume', 0.9)
                
                logger.info("pyttsx3 TTS initialized successfully as fallback")
                return
            except Exception as e:
                logger.error(f"Failed to initialize pyttsx3: {e}")
        
        # If all fail, raise an error
        if TTS is None and not GTTS_AVAILABLE and not PYTTSX3_AVAILABLE:
            error_msg = "No TTS library is available. "
            if TTS_IMPORT_ERROR and ("apex" in TTS_IMPORT_ERROR.lower() or "apex_conflict" in TTS_IMPORT_ERROR.lower()):
                error_msg += "Coqui TTS failed due to apex conflict. Please install gTTS: pip install gtts>=2.5.0 or pyttsx3: pip install pyttsx3>=2.90"
            else:
                error_msg += "Please install one of: TTS>=0.22.0, gtts>=2.5.0, or pyttsx3>=2.90"
            raise ImportError(error_msg)
        
        raise ImportError("Failed to initialize any TTS engine")
    
    def generate_podcast_audio(
        self, 
        podcast_script: PodcastScript,
        output_dir: str = None,
        combine_audio: bool = True,
        skip_individual_files: bool = True  # Skip individual files if we only need combined
    ) -> List[str]:

        Path(output_dir).mkdir(parents=True, exist_ok=True)
        
        total_segments = len(podcast_script.script)
        logger.info(f"Generating podcast audio for {total_segments} segments")
        logger.info(f"Output directory: {output_dir}")
        logger.info(f"Skip individual files: {skip_individual_files} (faster generation)")
        
        audio_segments = []
        output_files = []
        
        # Note: For pyttsx3, sequential generation is required due to voice switching
        # The main optimization is skipping individual file writes when combine_audio=True
        
        # Standard sequential generation
        for i, line_dict in enumerate(podcast_script.script):
            speaker, dialogue = next(iter(line_dict.items()))
            
            # Progress logging every 5 segments or at start/end
            if i == 0 or (i + 1) % 5 == 0 or (i + 1) == total_segments:
                logger.info(f"Processing segment {i+1}/{total_segments}: {speaker} ({len(dialogue)} chars)")
            
            try:
                segment_audio = self._generate_single_segment(speaker, dialogue)
                
                # Only save individual files if not skipping them
                if not skip_individual_files:
                    segment_filename = f"segment_{i+1:03d}_{speaker.replace(' ', '_').lower()}.wav"
                    segment_path = os.path.join(output_dir, segment_filename)
                    sf.write(segment_path, segment_audio, self.sample_rate)
                    output_files.append(segment_path)
                
                if combine_audio:
                    audio_segment = AudioSegment(
                        speaker=speaker,
                        text=dialogue,
                        audio_data=segment_audio,
                        duration=len(segment_audio) / self.sample_rate,
                        file_path=""  # No file path if skipping individual files
                    )
                    audio_segments.append(audio_segment)
                
                if (i + 1) % 5 == 0 or (i + 1) == total_segments:
                    logger.info(f"✓ Generated {i+1}/{total_segments} segments")
                
            except Exception as e:
                logger.error(f"✗ Failed to generate segment {i+1}: {str(e)}")
                continue
        
        if combine_audio and audio_segments:
            try:
                combined_path = self._combine_audio_segments(audio_segments, output_dir)
                output_files.append(combined_path)
                logger.info(f"✓ Combined audio file created: {combined_path}")
            except Exception as e:
                logger.error(f"✗ Failed to combine audio segments: {str(e)}", exc_info=True)
                # Continue even if combination fails - individual segments are still available
        
        logger.info(f"Podcast generation complete! Generated {len(output_files)} files")
        
        # Always return the combined file first if it exists (contains all speakers' content)
        if combine_audio and audio_segments:
            combined_file = next((f for f in output_files if 'complete_podcast.wav' in str(f)), None)
            if combined_file:
                # Return combined file first (all speakers in one file), then individual segments
                logger.info(f"Returning combined audio file first: {combined_file}")
                return [combined_file] + [f for f in output_files if f != combined_file]
        
        return output_files
    
    def _generate_single_segment(self, speaker: str, text: str) -> Any:
        """Generate audio for a single text segment"""
        clean_text = self._clean_text_for_tts(text)
        
        import tempfile
        import numpy as np
        
        if self.use_gtts:
            # Use gTTS (Google Text-to-Speech) - faster and async
            try:
                from gtts import gTTS
                from pydub import AudioSegment as PydubAudioSegment
                
                # Use different voices/languages for different speakers
                # Speaker 1: US English (male-like voice)
                # Speaker 2: UK English (different voice)
                if speaker == "Speaker 1":
                    lang = 'en'
                    tld = 'com'  # US English
                else:
                    lang = 'en'
                    tld = 'co.uk'  # UK English for variation
                
                # Create gTTS object
                tts = gTTS(text=clean_text, lang=lang, tld=tld, slow=False)
                
                # Save to temporary file
                with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as tmp_file:
                    temp_path = tmp_file.name
                
                # Generate speech to file
                tts.save(temp_path)
                
                # Convert MP3 to WAV and load as numpy array
                # gTTS outputs MP3, so we need to convert it
                audio_segment = PydubAudioSegment.from_mp3(temp_path)
                
                # Export as WAV to another temp file
                with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as wav_file:
                    wav_path = wav_file.name
                
                audio_segment.export(wav_path, format="wav")
                
                # Read the WAV file
                audio_data, sample_rate = sf.read(wav_path)
                
                # Resample if needed
                if sample_rate != self.sample_rate:
                    from scipy import signal
                    num_samples = int(len(audio_data) * self.sample_rate / sample_rate)
                    audio_data = signal.resample(audio_data, num_samples)
                
                # Clean up temp files
                os.unlink(temp_path)
                os.unlink(wav_path)
                
                # Ensure mono audio
                if len(audio_data.shape) > 1:
                    audio_data = np.mean(audio_data, axis=1)
                
                return audio_data.astype(np.float32)
                
            except Exception as e:
                logger.error(f"Error generating audio with gTTS: {e}")
                raise
        elif self.use_pyttsx3:
            # Use pyttsx3 for TTS
            try:
                import pyttsx3
                
                # Switch voice for different speakers if available
                if self.pyttsx3_engine:
                    voices = self.pyttsx3_engine.getProperty('voices')
                    if voices and len(voices) >= 2:
                        if speaker == "Speaker 1":
                            self.pyttsx3_engine.setProperty('voice', voices[0].id)
                        else:
                            self.pyttsx3_engine.setProperty('voice', voices[1].id if len(voices) > 1 else voices[0].id)
                
                # Save to temporary file
                with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp_file:
                    temp_path = tmp_file.name
                
                # Generate speech to file using pyttsx3
                self.pyttsx3_engine.save_to_file(clean_text, temp_path)
                self.pyttsx3_engine.runAndWait()
                
                # Read the generated audio file
                audio_data, sample_rate = sf.read(temp_path)
                
                # Resample if needed
                if sample_rate != self.sample_rate:
                    from scipy import signal
                    num_samples = int(len(audio_data) * self.sample_rate / sample_rate)
                    audio_data = signal.resample(audio_data, num_samples)
                
                # Clean up temp file
                os.unlink(temp_path)
                
                return audio_data.astype(np.float32)
                
            except Exception as e:
                logger.error(f"Error generating audio with pyttsx3: {e}")
                raise
        else:
            # Use Coqui TTS
            try:
                with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp_file:
                    temp_path = tmp_file.name
                
                # Generate speech to file
                self.tts.tts_to_file(
                    text=clean_text,
                    file_path=temp_path
                )
                
                # Read the generated audio file
                audio_data, sample_rate = sf.read(temp_path)
                
                # Resample if needed
                if sample_rate != self.sample_rate:
                    from scipy import signal
                    num_samples = int(len(audio_data) * self.sample_rate / sample_rate)
                    audio_data = signal.resample(audio_data, num_samples)
                
                # Clean up temp file
                os.unlink(temp_path)
                
                return audio_data.astype(np.float32)
                
            except Exception as e:
                logger.error(f"Error generating audio with Coqui TTS: {e}")
                raise
    
    def _clean_text_for_tts(self, text: str) -> str:
        """Clean and prepare text for TTS"""
        clean_text = text.strip()

        clean_text = clean_text.replace("...", ".")
        clean_text = clean_text.replace("!!", "!")
        clean_text = clean_text.replace("??", "?")

        if not clean_text.endswith(('.', '!', '?')):
            clean_text += '.'
        
        return clean_text
    
    def _combine_audio_segments(
        self, 
        segments: List[AudioSegment], 
        output_dir: str
    ) -> str:
        """Combine multiple audio segments from all speakers into one complete audio file"""
        logger.info(f"Combining {len(segments)} audio segments from all speakers into one file")
        
        try:
            import numpy as np
            
            if not segments:
                raise ValueError("No audio segments to combine")
            
            # Add a short pause between segments (0.5 seconds for better flow)
            pause_duration = 0.5  # seconds
            pause_samples = int(pause_duration * self.sample_rate)
            pause_audio = np.zeros(pause_samples, dtype=np.float32)
            
            combined_audio = []
            total_duration = 0.0
            
            for i, segment in enumerate(segments):
                # Add the segment audio
                segment_audio = segment.audio_data
                
                # Ensure audio is 1D (mono)
                if len(segment_audio.shape) > 1:
                    # Convert stereo to mono by taking the mean
                    segment_audio = np.mean(segment_audio, axis=1)
                
                combined_audio.append(segment_audio)
                total_duration += segment.duration
                
                logger.debug(f"Added segment {i+1}/{len(segments)}: {segment.speaker} ({segment.duration:.2f}s)")
                
                # Add pause between segments (except after the last one)
                if i < len(segments) - 1:
                    combined_audio.append(pause_audio)
                    total_duration += pause_duration
            
            # Concatenate all audio segments
            final_audio = np.concatenate(combined_audio)
            
            # Ensure audio is in the correct format (mono, float32)
            if len(final_audio.shape) > 1:
                # Convert stereo to mono by taking the mean
                final_audio = np.mean(final_audio, axis=1)
            
            # Normalize audio to prevent clipping
            max_val = np.max(np.abs(final_audio))
            if max_val > 1.0:
                final_audio = final_audio / max_val * 0.95  # Leave some headroom
            
            combined_filename = "complete_podcast.wav"
            combined_path = os.path.join(output_dir, combined_filename)
            
            # Write the combined audio file
            sf.write(combined_path, final_audio, self.sample_rate)
            
            actual_duration = len(final_audio) / self.sample_rate
            logger.info(f"✓ Combined podcast saved: {combined_path}")
            logger.info(f"  Total duration: {actual_duration:.2f}s ({actual_duration/60:.2f} minutes)")
            logger.info(f"  Contains {len(segments)} segments from all speakers")
            
            return combined_path
            
        except Exception as e:
            logger.error(f"✗ Failed to combine audio segments: {str(e)}", exc_info=True)
            raise


if __name__ == "__main__":
    try:
        tts_generator = PodcastTTSGenerator()
        
        sample_script_data = {
            "script": [
                {"Speaker 1": "Welcome everyone to our podcast! Today we're exploring the fascinating world of artificial intelligence."},
                {"Speaker 2": "Thanks for having me! AI is indeed one of the most exciting technological developments of our time."},
                {"Speaker 1": "Let's start with machine learning. Can you explain what makes it so revolutionary?"},
                {"Speaker 2": "Absolutely! Machine learning allows computers to learn from data without being explicitly programmed for every single task."},
            ]
        }
        
        from src.podcast.script_generator import PodcastScript
        test_script = PodcastScript(
            script=sample_script_data["script"],
            source_document="AI Overview Test",
            total_lines=len(sample_script_data["script"]),
            estimated_duration="2 minutes"
        )
        
        print("Generating podcast audio...")
        output_files = tts_generator.generate_podcast_audio(
            test_script,
            output_dir=None,  # Will default to backend/outputs/podcast_audio
            combine_audio=True
        )
        
        print(f"\nGenerated files:")
        for file_path in output_files:
            print(f"  - {file_path}")
        
        print("\nPodcast TTS test completed successfully!")
        
    except ImportError as e:
        print(f"Import error: {e}")
        print("Please install Coqui TTS: pip install TTS>=0.22.0")
    except Exception as e:
        print(f"Error: {e}")
