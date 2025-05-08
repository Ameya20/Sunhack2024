import streamlit as st
import time
import os
from dotenv import load_dotenv
from openai import OpenAI
from database import get_existing_files, delete_file, summaries_collection
from audio_processing import record_audio
from summarization import summarize_audio

# Load environment variables
load_dotenv()
openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Streamlit UI setup
st.title("EduSummarizer")

# --- Cache heavy operations ---
@st.cache_data
def cached_get_existing_files():
    return get_existing_files()

@st.cache_data
def cached_summarize_audio(audio_path):
    return summarize_audio(audio_path)

# --- Session State initialization ---
if 'summary_text' not in st.session_state:
    st.session_state['summary_text'] = ""
if 'files' not in st.session_state:
    st.session_state['files'] = cached_get_existing_files()

# --- Create tabs ---
tab_home, tab_existing_files = st.tabs(["Home", "Existing Files"])

# --- Home Tab ---
with tab_home:
    audio_filename, audio_file_path = record_audio()

    if audio_file_path and st.button("Summarize Audio"):
        with st.spinner("Summarizing audio, please wait..."):
            try:
                summary_text = cached_summarize_audio(audio_file_path)
                st.session_state['summary_text'] = summary_text

                # Store summary in MongoDB
                summaries_collection.update_one(
                    {"filename": audio_filename},
                    {"$set": {"summary": summary_text, "created_at": time.time()}},
                    upsert=True
                )

                # Refresh the cached files
                st.session_state['files'] = cached_get_existing_files()

                st.success("Summary generated and saved successfully!")
                st.write("Summary:", summary_text)
            except Exception as e:
                st.error(f"An error occurred while summarizing or saving: {str(e)}")

    # If already summarized, show it
    if st.session_state['summary_text']:
        st.write("Summary:", st.session_state['summary_text'])

# --- Existing Files Tab ---
with tab_existing_files:
    files = st.session_state['files']
    filenames = [file['filename'] for file in files]

    if filenames:
        selected_file = st.selectbox("Select a file to view its summary:", filenames)

        if selected_file:
            file_data = next((file for file in files if file['filename'] == selected_file), None)
            if file_data:
                summary_text = file_data.get('summary', '')

                st.write(f"### Summary of {selected_file}")
                st.write(summary_text)

                # User can ask a question about the summary
                user_question = st.text_input(
                    "Ask a question about this summary:",
                    "",
                    key=f"user_question_{selected_file}"
                )

                if st.button("Get Answer", key=f"get_answer_{selected_file}"):
                    if user_question:
                        prompt = f"Summary:\n{summary_text}\n\nUser Question: {user_question}\nAnswer:"
                        with st.spinner("Fetching answer..."):
                            try:
                                response = openai_client.chat.completions.create(
                                    model="gpt-3.5-turbo",
                                    messages=[
                                        {"role": "system", "content": "You are a helpful assistant."},
                                        {"role": "user", "content": prompt}
                                    ],
                                    max_tokens=150
                                )
                                answer = response.choices[0].message.content.strip()
                                st.write("**Answer:**", answer)
                            except Exception as e:
                                st.error(f"An error occurred while fetching the answer: {str(e)}")
    else:
        st.info("No files found yet. Please record and summarize some audio first!")

# Optionally: display existing files with delete functionality
# display_existing_files(files, delete_file)
