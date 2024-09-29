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

# Tabs for Home and Existing Files
tab1, tab2 = st.tabs(["Home", "Existing Files"])

# Home Tab (Audio Recording & Summarization)
with tab1:
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

# Existing Files Tab (File Listing & Summary with Chat)
with tab2:
    st.write("Existing Files:")
    files = summaries_collection.find().sort("created_at", pymongo.DESCENDING)

    if "show_file" not in st.session_state:
        st.session_state.show_file = None

    # Reset the query input when a new file is selected
    if "user_query" not in st.session_state:
        st.session_state.user_query = ""

    for file in files:
        col1, col2 = st.columns([3, 1])

        with col1:
            # Display filename and summary in an expander
            if st.button(file['filename'], key=f"show_summary_{file['filename']}"):
                st.session_state.show_file = file  # Store the selected file in session state
                st.session_state.user_query = ""  # Reset the question input

        with col2:
            # Delete functionality
            if st.button("Delete", key=f"delete_{file['filename']}"):
                summaries_collection.delete_one({"filename": file['filename']})
                st.success(f"File {file['filename']} deleted successfully")

    # Display summary and chat when a file is selected
    if st.session_state.show_file:
        file = st.session_state.show_file
        
        # Always expand the expander when a file is selected
        with st.expander(f"Summary and Q&A for {file['filename']}", expanded=True):
            st.write(f"Summary: {file['summary']}")

            # Chat feature
            user_query = st.text_input("Ask a question:", value=st.session_state.user_query, key="user_query")
            if st.button("Ask", key="ask_button"):
                if user_query:
                    # Send query + summary to OpenAI
                    prompt = f"{file['summary']}\nUser question: {user_query}\nAnswer:"
                    answer_response = openai_client.completions.create(
                        model="gpt-3.5-turbo-instruct",
                        prompt=prompt,
                        max_tokens=150
                    )
                    answer_text = answer_response.choices[0].text.strip()

                    # Display the answer
                    st.write("Answer:", answer_text)
                else:
                    st.error("Please enter a question.")
