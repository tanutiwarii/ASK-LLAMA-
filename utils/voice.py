import streamlit as st
import speech_recognition as sr
import subprocess



# --- Voice input function ---
def listen(recognizer):
    try:
        with sr.Microphone() as source:
            # Adjust for ambient noise with longer duration for better detection
            recognizer.adjust_for_ambient_noise(source, duration=1.0)
            # Set microphone sensitivity
            recognizer.energy_threshold = 300  # Lower threshold for better sensitivity
            recognizer.dynamic_energy_threshold = True
            st.toast("🎙 Listening... Speak now!")
            
            # Listen with longer timeout and phrase time limit
            audio = recognizer.listen(
                source, 
                timeout=5,  # Wait 5 seconds for speech to start
                phrase_time_limit=15  # Allow up to 15 seconds of speech
            )
            
        # Try to recognize the speech
        try:
            text = recognizer.recognize_google(audio)
            if text and text.strip():
                return text.strip()
            else:
                return "Sorry, I couldn't understand the audio."
        except Exception as e:
            return f"Speech recognition error: {str(e)}"
            
    except sr.WaitTimeoutError:
        st.toast("⏰ No speech detected. Please try again.")
        return "No speech detected within timeout period. Please try again."
    except sr.UnknownValueError:
        st.toast("❓ Could not understand speech. Please try again.")
        return "Sorry, I couldn't understand the audio. Please try again."
    except sr.RequestError as e:
        st.toast("🌐 Speech recognition service error.")
        return f"Speech recognition service error: {str(e)}"
    except Exception as e:
        st.toast("❌ Microphone error occurred.")
        return f"Microphone error: {str(e)}"

# --- Voice output using macOS 'say' command ---
def speak(text):
    if not st.session_state.voice_output_enabled:
        st.info("🔇 Voice output is disabled")
        return
    if not st.session_state.tts_working:
        st.warning("🔇 TTS system not working. Voice output disabled.")
        return
    if st.session_state.is_speaking:
        st.warning("🔁 Already speaking. Please wait.")
        return
    
    # Clean and truncate text for speech
    speech_text = text.strip()
    
    # Remove markdown formatting and code blocks for better speech
    import re
    speech_text = re.sub(r'```[\s\S]*?```', '[Code block]', speech_text)  # Replace code blocks
    speech_text = re.sub(r'`([^`]+)`', r'\1', speech_text)  # Remove inline code
    speech_text = re.sub(r'\*\*([^*]+)\*\*', r'\1', speech_text)  # Remove bold
    speech_text = re.sub(r'\*([^*]+)\*', r'\1', speech_text)  # Remove italic
    speech_text = re.sub(r'#{1,6}\s+', '', speech_text)  # Remove headers
    speech_text = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', speech_text)  # Remove links
    
    # Truncate very long responses to avoid long speech
    if len(speech_text) > 500:
        # Find a good breaking point (end of sentence)
        truncated = speech_text[:500]
        last_period = truncated.rfind('.')
        last_exclamation = truncated.rfind('!')
        last_question = truncated.rfind('?')
        
        break_point = max(last_period, last_exclamation, last_question)
        if break_point > 300:  # Only break if we have a reasonable sentence ending
            speech_text = speech_text[:break_point + 1] + " [Response continues in chat]"
        else:
            speech_text = speech_text[:500] + " [Response continues in chat]"
    
    try:
        st.session_state.is_speaking = True
        st.toast("🔊 Speaking AI response...")
        subprocess.run(['say', speech_text], check=True)
        st.toast("✅ Voice output completed!")
    except subprocess.CalledProcessError as e:
        st.error(f"TTS command failed: {e}")
        st.session_state.tts_working = False
    except Exception as e:
        st.error(f"Voice output error: {e}")
        st.session_state.tts_working = False
    finally:
        st.session_state.is_speaking = False

# --- Stop speaking function for macOS ---
def stop_speaking():
    try:
        subprocess.run(['pkill', 'say'], check=False)
        st.session_state.is_speaking = False
        st.toast("🔇 Voice stopped!")
    except Exception as e:
        st.error(f"Error stopping voice: {e}")