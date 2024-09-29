import streamlit as st
import pymongo
from openai import OpenAI
from st_audiorec import st_audiorec
import os
from dotenv import load_dotenv
import time

# Load the .env file
load_dotenv()

# MongoDB setup
mongo_uri = os.getenv("MONGO_URI")
client = pymongo.MongoClient(mongo_uri)
db = client["edusummarize"]
summaries_collection = db["edusummarize"]

# OpenAI setup
openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Streamlit UI setup
st.title("EduSummarizer")

# Create tabs for Home and Existing Files
tabs = st.tabs(["Home", "Existing Files"])

# Home Tab: Audio recording and summarization
with tabs[0]:
    st.header("Home")

    # Audio recorder instance
    wav_audio_data = st_audiorec()

    # Default filename with a random number
    if wav_audio_data is not None:
        default_filename = f"file_{int(time.time())}"  # Use the current time as a random number
        st.write("Default Filename:", default_filename)
        audio_filename = st.text_input("Enter filename:", default_filename)

        st.audio(wav_audio_data, format='audio/wav')
        st.write("Audio recorded successfully!")

        # Save the audio data to a file
        audio_file_path = f"{audio_filename}.wav"
        with open(audio_file_path, "wb") as f:
            f.write(wav_audio_data)

        # Summarization logic using OpenAI Whisper
        if st.button("Summarize Audio"):
            try:
                with open(audio_file_path, "rb") as audio_file:
                    response = openai_client.audio.transcriptions.create(
                        model="whisper-1",
                        file=audio_file
                    )
                transcription_text = response.text

                # Summarization
                summary_response = openai_client.completions.create(
                    model="gpt-3.5-turbo-instruct",
                    prompt=f"Summarize the following transcription:\n{transcription_text}",
                    max_tokens=200
                )
                summary_text = summary_response.choices[0].text.strip()

                # Store summary in MongoDB
                summaries_collection.update_one(
                    {"filename": audio_filename},
                    {"$set": {"summary": summary_text, "pinecone_id": "", "created_at": time.time()}},
                    upsert=True  # Create if not exists
                )

                st.write("Summary: ", summary_text)

            except Exception as e:
                st.error(f"An error occurred during summarization: {str(e)}")

# Existing Files Tab: List all stored files and enable viewing and deleting files
with tabs[1]:
    st.header("Existing Files")

    # Display existing filenames sorted from recent to old
    st.write("Stored Summaries:")
    files = summaries_collection.find().sort("created_at", pymongo.DESCENDING)  # Sort by created_at field

    if summaries_collection.count_documents({}) == 0:
        st.write("No records found.")
    else:
        for file in files:
            col1, col2 = st.columns([3, 2])

            with col1:
                # Show summary on button click
                if st.button(file['filename'], key=f"show_summary_{file['filename']}"):
                    # Show existing summary
                    st.write(f"Filename: {file['filename']}")
                    st.write(f"Summary: {file['summary']}")

            with col2:
                # Delete functionality
                if st.button("Delete", key=f"delete_{file['filename']}"):
                    # Delete file from MongoDB
                    summaries_collection.delete_one({"filename": file['filename']})
                    st.success(f"File {file['filename']} deleted successfully")
