import os
import time
import streamlit as st
from st_audiorec import st_audiorec

def record_audio():
    wav_audio_data = st_audiorec()

    if wav_audio_data is not None:
        default_filename = f"file_{int(time.time())}"
        audio_filename = st.text_input("Enter filename:", default_filename)

        st.audio(wav_audio_data, format='audio/wav')
        st.success("Audio recorded successfully!")

        audio_file_path = f"temp_audio/{audio_filename}.wav"

        # Ensure temp directory exists
        os.makedirs(os.path.dirname(audio_file_path), exist_ok=True)

        # Save audio data
        with open(audio_file_path, "wb") as f:
            f.write(wav_audio_data)

        return audio_filename, audio_file_path
    return None, None
