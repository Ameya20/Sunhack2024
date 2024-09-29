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
st.title("Audio Recording and Summarization")

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
                {"$set": {"summary": summary_text, "pinecone_id": ""}},
                upsert=True  # Create if not exists
            )

            st.write("Summary: ", summary_text)
            st.write("Summary stored in MongoDB!")

        except Exception as e:
            st.error(f"An error occurred during summarization: {str(e)}")

# Display existing filenames
st.write("Existing Files:")
files = summaries_collection.find()
for file in files:
    col1, col2 = st.columns([3, 2])

    with col1:
        # Show summary and summarize on click
        if st.button(file['filename'], key=f"show_summary_{file['filename']}"):
            # Retrieve the existing audio file from MongoDB (assuming you have a way to access the audio file)
            st.write(f"Filename: {file['filename']}")
            st.write(f"Summary: {file['summary']}")
            
            # Optionally, you can trigger the summarization again if you want to regenerate
            # The below code assumes you have the original audio file associated with the summary.
            # Uncomment if you want to summarize again when clicked.
            # audio_file_path = f"{file['filename']}.wav"  # Modify as necessary to locate the audio file
            # with open(audio_file_path, "rb") as audio_file:
            #     response = openai_client.audio.transcriptions.create(
            #         model="whisper-1",
            #         file=audio_file
            #     )
            # transcription_text = response.text
            # summary_response = openai_client.completions.create(
            #     model="gpt-3.5-turbo-instruct",
            #     prompt=f"Summarize the following transcription:\n{transcription_text}",
            #     max_tokens=200
            # )
            # summary_text = summary_response.choices[0].text.strip()
            # st.write("New Summary: ", summary_text)

    with col2:
        if st.button("Delete", key=f"delete_{file['filename']}"):
            # Delete file from MongoDB
            summaries_collection.delete_one({"filename": file['filename']})
            st.success(f"File {file['filename']} deleted successfully")
