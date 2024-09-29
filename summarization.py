import os
from openai import OpenAI
from dotenv import load_dotenv

# Load the .env file
load_dotenv()

# OpenAI setup
openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def summarize_audio(audio_file_path):
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

        return summary_text
    except Exception as e:
        raise Exception(f"An error occurred during summarization: {str(e)}")
