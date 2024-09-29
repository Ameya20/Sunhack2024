import streamlit as st
from database import get_existing_files, delete_file
from audio_processing import record_audio
from summarization import summarize_audio
from ui_components import display_existing_files
import time
from openai import OpenAI
import os
from dotenv import load_dotenv

# Load the .env file
load_dotenv()
openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Streamlit UI setup
st.title("EduSummarizer")

# Create tabs
tab_home, tab_existing_files = st.tabs(["Home", "Existing Files"])

# Home Tab
with tab_home:
    audio_filename, audio_file_path = record_audio()
    
    if audio_file_path and st.button("Summarize Audio"):
        try:
            summary_text = summarize_audio(audio_file_path)
            
            # Store summary in MongoDB
            from database import summaries_collection
            summaries_collection.update_one(
                {"filename": audio_filename},
                {"$set": {"summary": summary_text, "created_at": time.time()}},
                upsert=True  # Create if not exists
            )

            st.write("Summary: ", summary_text)
        except Exception as e:
            st.error(f"An error occurred while saving the summary: {str(e)}")

# Existing Files Tab
with tab_existing_files:
    files = get_existing_files()
    selected_file = st.selectbox("Select a file to view its summary:", [file['filename'] for file in files])
    summary_text = ""  # Initialize summary text

    if selected_file:
        # Retrieve the summary from the database
        file_data = next((file for file in files if file['filename'] == selected_file), None)
        if file_data:
            summary_text = file_data['summary']
            st.write(f"Summary of {selected_file}:")
            st.write(summary_text)

            # Reset the question input when a new file is selected
            user_question = st.text_input("Ask a question about this summary:", "", key=f"user_question_{selected_file}")  # Unique key using selected_file

            if st.button("Get Answer"):
                if user_question:
                    prompt = f"Summary: {summary_text}\nUser Question: {user_question}\nAnswer:"
                    try:
                        response = openai_client.completions.create(
                            model="gpt-3.5-turbo-instruct",
                            prompt=prompt,
                            max_tokens=150
                        )
                        answer = response.choices[0].text.strip()
                        st.write("Answer:", answer)
                    except Exception as e:
                        st.error(f"An error occurred while fetching the answer: {str(e)}")
        
    # Display existing files with delete functionality
    # display_existing_files(files, delete_file)
