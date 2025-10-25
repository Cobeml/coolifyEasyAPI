import os
import subprocess
import tempfile
import json
import requests
from uuid import uuid4
from google.cloud import speech, storage
from google.oauth2 import service_account
from google.oauth2.credentials import Credentials as OAuth2Credentials

from dotenv import load_dotenv

load_dotenv()


class GCSStorageManagerJWT:
    def __init__(self, bucket_name: str, token: str):
        self.bucket_name = bucket_name
        # Create OAuth2 credentials from access token
        credentials = OAuth2Credentials(token=token)
        
        self.client = storage.Client(
            credentials=credentials, 
            project=os.getenv("GCP_PROJECT_ID")
        )
        self.bucket = self.client.bucket(bucket_name)

    def uri_to_url(self, uri: str) -> str:
        if not uri.startswith("gs://"):
            raise ValueError("Invalid GCS URI")
        parts = uri[5:].split("/", 1)
        bucket_name = parts[0]
        blob_name = parts[1] if len(parts) > 1 else ""
        return f"https://storage.googleapis.com/{bucket_name}/{blob_name}"

    def upload(self, local_path: str, remote_path: str):
        print(f"[GCS] Starting upload: {local_path} -> gs://{self.bucket_name}/{remote_path}")
        blob = self.bucket.blob(remote_path)
        blob.upload_from_filename(local_path)
        uri = f'gs://{self.bucket_name}/{remote_path}'
        print(f"[GCS] Upload completed. File URL: {self.uri_to_url(uri)}")
        return uri

    def download_to_tempfile(self, uri: str):
        print(f"[GCS] Starting download from: {uri}")
        blob = self.bucket.blob(uri.replace(f"gs://{self.bucket_name}/", ""))
        temp_file = tempfile.NamedTemporaryFile(delete=False)
        blob.download_to_filename(temp_file.name)
        print(f"[GCS] Download completed to temporary file: {temp_file.name}")
        return temp_file


def get_speech_client():
    """
    Initializes the Google Cloud Speech-to-Text client using environment variables.
    """
    try:
        # Construct credentials info from environment variables
        creds_info = {
            "type": os.getenv("STT_TYPE"),
            "project_id": os.getenv("STT_PROJECT_ID"),
            "private_key_id": os.getenv("STT_PRIVATE_KEY_ID"),
            # Replace the literal '\\n' with actual newlines
            "private_key": os.getenv("STT_PRIVATE_KEY", "").replace('\\n', '\n'),
            "client_email": os.getenv("STT_CLIENT_EMAIL"),
            "client_id": os.getenv("STT_CLIENT_ID"),
            "auth_uri": os.getenv("STT_AUTH_URI"),
            "token_uri": os.getenv("STT_TOKEN_URI"),
            "auth_provider_x509_cert_url": os.getenv("STT_AUTH_PROVIDER_X509_CERT_URL"),
            "client_x509_cert_url": os.getenv("STT_CLIENT_X509_CERT_URL"),
        }
        
        # Check for missing required environment variables
        missing_vars = [key for key, value in creds_info.items() if not value]
        if missing_vars:
            raise Exception(f"Missing required environment variables: {', '.join([f'STT_{key.upper()}' for key in missing_vars])}")
        
        credentials = service_account.Credentials.from_service_account_info(creds_info)
        client = speech.SpeechClient(credentials=credentials)
        print("Successfully authenticated and initialized Speech-to-Text client.")
        return client
    except KeyError as e:
        print(f"Error: Environment variable {e} not set.")
        print("Please set all required STT_... environment variables.")
        raise Exception(f"Missing environment variable: {e}")
    except Exception as e:
        print(f"An error occurred during authentication: {e}")
        raise Exception(f"Speech-to-Text authentication failed: {e}")


def extract_audio(video_path, audio_path=None):
    """
    Extracts the audio from a video file using FFmpeg.
    Converts to mono (single channel) for Speech-to-Text compatibility.
    """
    if audio_path is None:
        audio_path = tempfile.NamedTemporaryFile(suffix=".wav", delete=False).name
    
    print(f"Extracting audio from '{video_path}'...")
    command = [
        "ffmpeg",
        "-i", video_path,
        "-ac", "1",           # Convert to mono (single channel)
        "-ar", "16000",       # Set sample rate to 16kHz (recommended for Speech-to-Text)
        "-q:a", "0",          # Preserve audio quality
        "-map", "a",          # Select only the audio stream
        "-y",                 # Overwrite output file if it exists
        audio_path
    ]
    try:
        result = subprocess.run(command, check=True, capture_output=True, text=True)
        print(f"Audio successfully extracted to '{audio_path}' (mono, 16kHz).")
        return audio_path
    except subprocess.CalledProcessError as e:
        print("Error during FFmpeg audio extraction:")
        print(e.stderr)
        raise Exception(f"Audio extraction failed: {e.stderr}")
    except FileNotFoundError:
        raise Exception("ffmpeg command not found. Is FFmpeg installed and in your PATH?")


def get_word_timestamps(audio_path, client):
    """
    Transcribes an audio file to get word-level timestamps.
    """
    print(f"Requesting transcription with word timestamps for '{audio_path}'...")
    with open(audio_path, "rb") as audio_file:
        content = audio_file.read()

    audio = speech.RecognitionAudio(content=content)
    config = speech.RecognitionConfig(
        language_code="en-US",
        enable_word_time_offsets=True,
    )

    try:
        operation = client.long_running_recognize(config=config, audio=audio)
        print("Waiting for transcription to complete...")
        response = operation.result(timeout=300)  # 5-minute timeout
        print("Transcription finished.")
        return response
    except Exception as e:
        print(f"An error occurred during transcription: {e}")
        raise Exception(f"Speech-to-text transcription failed: {e}")


def format_timestamps_to_srt(response, srt_path=None):
    """
    Converts the Speech-to-Text API response to an SRT subtitle file.
    """
    if srt_path is None:
        srt_path = tempfile.NamedTemporaryFile(suffix=".srt", delete=False).name
    
    print("Formatting timestamps into SRT format...")
    
    def format_time(seconds):
        """Converts seconds to SRT time format HH:MM:SS,ms"""
        delta = int(seconds * 1000)
        hours, delta = divmod(delta, 3600000)
        minutes, delta = divmod(delta, 60000)
        seconds, milliseconds = divmod(delta, 1000)
        return f"{hours:02}:{minutes:02}:{seconds:02},{milliseconds:03}"

    with open(srt_path, "w") as f:
        subtitle_index = 1
        for result in response.results:
            for word_info in result.alternatives[0].words:
                start_time_str = format_time(word_info.start_time.total_seconds())
                end_time_str = format_time(word_info.end_time.total_seconds())
                
                f.write(f"{subtitle_index}\n")
                f.write(f"{start_time_str} --> {end_time_str}\n")
                f.write(f"{word_info.word}\n\n")
                subtitle_index += 1
    
    print(f"SRT file saved to '{srt_path}'.")
    return srt_path


def translate_text(text: str, target_lang: str) -> str:
    """
    Translates text using DeepL API.
    """
    deepl_auth_key = os.getenv("DEEPL_AUTH_KEY")
    if not deepl_auth_key:
        raise Exception("DEEPL_AUTH_KEY environment variable not set")
    
    url = "https://api.deepl.com/v2/translate"
    headers = {
        "Authorization": f"DeepL-Auth-Key {deepl_auth_key}",
        "Content-Type": "application/json"
    }
    
    data = {
        "text": [text],
        "target_lang": target_lang.upper()
    }
    
    print(f"Translating text to {target_lang}...")
    try:
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()
        result = response.json()
        translated_text = result["translations"][0]["text"]
        print(f"Translation completed.")
        return translated_text
    except requests.exceptions.RequestException as e:
        raise Exception(f"Translation failed: {e}")
    except (KeyError, IndexError) as e:
        raise Exception(f"Invalid translation response: {e}")


def format_translated_timestamps_to_srt(response, translated_text: str, srt_path=None, chunk_size: int = 3):
    """
    Creates SRT captions using translated text split into chunks with original timing.
    """
    if srt_path is None:
        srt_path = tempfile.NamedTemporaryFile(suffix=".srt", delete=False).name
    
    print(f"Formatting translated text into {chunk_size}-word chunks for SRT...")
    
    def format_time(seconds):
        """Converts seconds to SRT time format HH:MM:SS,ms"""
        delta = int(seconds * 1000)
        hours, delta = divmod(delta, 3600000)
        minutes, delta = divmod(delta, 60000)
        seconds, milliseconds = divmod(delta, 1000)
        return f"{hours:02}:{minutes:02}:{seconds:02},{milliseconds:03}"
    
    # Extract all word timings from the original response
    word_timings = []
    for result in response.results:
        for word_info in result.alternatives[0].words:
            word_timings.append({
                'start': word_info.start_time.total_seconds(),
                'end': word_info.end_time.total_seconds()
            })
    
    if not word_timings:
        raise Exception("No word timings found in speech recognition response")
    
    # Split translated text into chunks
    translated_words = translated_text.split()
    chunks = [' '.join(translated_words[i:i+chunk_size]) for i in range(0, len(translated_words), chunk_size)]
    
    # Calculate timing for each chunk
    total_original_words = len(word_timings)
    chunk_duration = len(word_timings) / len(chunks) if chunks else 1
    
    with open(srt_path, "w", encoding='utf-8') as f:
        for i, chunk in enumerate(chunks):
            # Calculate start and end times for this chunk
            start_word_idx = int(i * chunk_duration)
            end_word_idx = min(int((i + 1) * chunk_duration) - 1, total_original_words - 1)
            
            # Ensure indices are within bounds
            start_word_idx = max(0, min(start_word_idx, total_original_words - 1))
            end_word_idx = max(start_word_idx, min(end_word_idx, total_original_words - 1))
            
            start_time = word_timings[start_word_idx]['start']
            end_time = word_timings[end_word_idx]['end']
            
            # Ensure end time is after start time
            if end_time <= start_time:
                end_time = start_time + 1.0  # Add 1 second minimum duration
            
            start_time_str = format_time(start_time)
            end_time_str = format_time(end_time)
            
            f.write(f"{i + 1}\n")
            f.write(f"{start_time_str} --> {end_time_str}\n")
            f.write(f"{chunk}\n\n")
    
    print(f"Translated SRT file saved to '{srt_path}' with {len(chunks)} chunks.")
    return srt_path


def add_captions_to_video(video_path, srt_path, output_path=None):
    """
    Burns the SRT captions into the video file using FFmpeg.
    """
    if output_path is None:
        output_path = tempfile.NamedTemporaryFile(suffix=".mp4", delete=False).name
    
    print(f"Adding captions from '{srt_path}' to '{video_path}'...")
    # Use a filter complex to overlay subtitles with a semi-transparent background for readability
    subtitle_style = "Fontname=Arial,Fontsize=16,PrimaryColour=&H00FFFFFF,BorderStyle=3,Outline=1,Shadow=1,BackColour=&H80000000"
    command = [
        "ffmpeg",
        "-i", video_path,
        "-vf", f"subtitles={srt_path}:force_style='{subtitle_style}'",
        "-c:a", "copy",       # Copy the audio stream without re-encoding
        "-y",                 # Overwrite output file if it exists
        output_path
    ]
    try:
        result = subprocess.run(command, check=True, capture_output=True, text=True)
        print(f"Video with burned-in captions saved to '{output_path}'.")
        return output_path
    except subprocess.CalledProcessError as e:
        print("Error during FFmpeg caption burning:")
        print(e.stderr)
        raise Exception(f"Caption burning failed: {e.stderr}")
    except FileNotFoundError:
        raise Exception("ffmpeg command not found. Is FFmpeg installed and in your PATH?")


def add_captions_to_video_from_uri(video_uri: str, bucket_name: str, token: str, output_extension: str = "mp4", target_lang: str = None) -> dict:
    """
    Main function to add captions to a video from GCS URI.
    Downloads video, extracts audio, gets transcription, creates captions, and uploads result.
    If target_lang is provided, translates the captions to that language.
    """
    print(f"[CAPTIONS] Starting caption addition pipeline")
    print(f"[CAPTIONS] Input video URI: {video_uri}")
    print(f"[CAPTIONS] Target bucket: {bucket_name}")
    if target_lang:
        print(f"[CAPTIONS] Target language: {target_lang}")
    
    bucket_manager = GCSStorageManagerJWT(bucket_name, token)
    
    # Initialize Speech-to-Text client
    speech_client = get_speech_client()
    
    # Download video to temp file
    print(f"[CAPTIONS] Downloading video from GCS to temporary file...")
    temp_video = bucket_manager.download_to_tempfile(video_uri)
    print(f"[CAPTIONS] Video downloaded to: {temp_video.name}")
    
    # Create temp files for processing
    temp_audio = None
    temp_srt = None
    temp_output = None
    
    try:
        # Extract audio from video
        print(f"[CAPTIONS] Extracting audio from video...")
        temp_audio = extract_audio(temp_video.name)
        
        # Get word timestamps from speech-to-text
        print(f"[CAPTIONS] Getting word timestamps from speech-to-text...")
        stt_response = get_word_timestamps(temp_audio, speech_client)
        
        # Format timestamps to SRT
        if target_lang:
            # Extract full transcript for translation
            full_transcript = ""
            for result in stt_response.results:
                full_transcript += result.alternatives[0].transcript + " "
            
            print(f"[CAPTIONS] Translating transcript to {target_lang}...")
            translated_text = translate_text(full_transcript.strip(), target_lang)
            
            print(f"[CAPTIONS] Formatting translated text into 3-word chunks...")
            temp_srt = format_translated_timestamps_to_srt(stt_response, translated_text)
        else:
            print(f"[CAPTIONS] Formatting timestamps to SRT...")
            temp_srt = format_timestamps_to_srt(stt_response)
        
        # Add captions to video
        print(f"[CAPTIONS] Adding captions to video...")
        temp_output = add_captions_to_video(temp_video.name, temp_srt)
        
        # Upload processed video to GCS
        lang_suffix = f"_{target_lang}" if target_lang else ""
        output_path = f"captioned_videos/{uuid4()}{lang_suffix}.{output_extension}"
        print(f"[CAPTIONS] Uploading captioned video to GCS path: {output_path}")
        result_uri = bucket_manager.upload(temp_output, output_path)
        print(f"[CAPTIONS] Upload completed. Result URI: {result_uri}")
        
        return {"result_uri": result_uri}
        
    except Exception as e:
        print(f"[CAPTIONS] Error during caption processing: {str(e)}")
        raise e
        
    finally:
        # Cleanup temp files
        print(f"[CAPTIONS] Cleaning up temporary files...")
        for temp_file in [temp_video.name, temp_audio, temp_srt, temp_output]:
            if temp_file:
                try:
                    os.unlink(temp_file)
                except OSError as e:
                    print(f"[CAPTIONS] Warning: Could not clean up {temp_file}: {e}")
        print(f"[CAPTIONS] Temporary files cleaned up successfully")