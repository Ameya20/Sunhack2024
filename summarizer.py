import streamlit as st
import pymongo
from openai import OpenAI
from st_audiorec import st_audiorec
import os
from dotenv import load_dotenv

# Load the .env file
load_dotenv()


# MongoDB setup
client = pymongo.MongoClient("mongodb://localhost:27017/")
db = client["audioTranscriptions"]
transcriptions_collection = db["transcriptions"]

# OpenAI setup
openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Streamlit UI setup
st.title("Audio Recording and Transcription")

# Audio recorder instance
wav_audio_data = st_audiorec()

# Check if audio data is recorded
if wav_audio_data is not None:
    st.audio(wav_audio_data, format='audio/wav')
    st.write("Audio recorded successfully!")

    # Save the audio data to a file
    audio_filename = "recorded_audio.wav"
    with open(audio_filename, "wb") as f:
        f.write(wav_audio_data)

    # Transcription logic using OpenAI Whisper
    if st.button("Transcribe Audio"):
        try:
            with open(audio_filename, "rb") as audio_file:
                response = openai_client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_file
                )
            transcription_text = response.text

            st.write("Transcription: ", transcription_text)

            # Store transcript in MongoDB
            transcriptions_collection.insert_one({
                audio_filename: {
                    "transcript": transcription_text
                }
            })

            st.write("Transcription stored in MongoDB!")
        except Exception as e:
            st.error(f"An error occurred during transcription: {str(e)}")

# Q&A Section (simplified for now)
st.write("Ask a Question: ")
question = st.text_input("Enter your question about the audio transcript")

if st.button("Ask"):
    # Retrieve the latest transcription from MongoDB
    latest_transcription = transcriptions_collection.find_one(sort=[('_id', -1)])

    if latest_transcription:
        transcription_text = latest_transcription[audio_filename]["transcript"]

        # Use OpenAI to answer the question
        prompt = f"""
        You are given the following transcription:
        {transcription_text}

        Answer the following question:
        {question}
        """

        try:
            response = openai_client.completions.create(
                model="gpt-3.5-turbo-instruct",
                prompt=prompt,
                max_tokens=200
            )
            answer = response.choices[0].text.strip()
            st.write("Answer: ", answer)
        except Exception as e:
            st.error(f"An error occurred while generating the answer: {str(e)}")
    else:
        st.write("No transcription found. Please transcribe an audio file first.")