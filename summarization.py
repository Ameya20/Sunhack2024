import os
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# OpenAI setup
openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def summarize_audio(audio_file_path):
    try:
        with open(audio_file_path, "rb") as audio_file:
            # Transcription step
            response = openai_client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file
            )
            transcription_text = response.text

        # Summarization step (IMPROVED: use chat model instead of older completion model)
        messages = [
            {"role": "system", "content": "You are a helpful assistant that summarizes lecture transcriptions."},
            {"role": "user", "content": f"Summarize the following lecture transcription:\n\n{transcription_text}"}
        ]

        summary_response = openai_client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=messages,
            max_tokens=250
        )
        summary_text = summary_response.choices[0].message.content.strip()

        return summary_text

    except Exception as e:
        raise Exception(f"An error occurred during summarization: {str(e)}")
