import streamlit as st
import os
import time
from st_audiorec import st_audiorec

def record_audio():
    wav_audio_data = st_audiorec()

    if wav_audio_data is not None:
        default_filename = f"file_{int(time.time())}"  # Use current time as a random filename
        audio_filename = st.text_input("Enter filename:", default_filename)

        st.audio(wav_audio_data, format='audio/wav')
        st.write("Audio recorded successfully!")

        # Save the audio data to a file
        audio_file_path = f"{audio_filename}.wav"
        with open(audio_file_path, "wb") as f:
            f.write(wav_audio_data)

        return audio_filename, audio_file_path
    return None, None
