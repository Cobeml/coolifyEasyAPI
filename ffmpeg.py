import subprocess
import tempfile
import os
from uuid import uuid4
from google.cloud import storage
from google.oauth2.credentials import Credentials
from dotenv import load_dotenv
import base64

load_dotenv()

class GCSStorageManagerJWT:
    def __init__(self, bucket_name: str, token: str):
        self.bucket_name = bucket_name
        self.client = storage.Client(
            credentials=Credentials(token=token), 
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
        blob = self.bucket.blob(remote_path)
        blob.upload_from_filename(local_path)
        uri = f'gs://{self.bucket_name}/{remote_path}'
        print(f"File URL: {self.uri_to_url(uri)}")
        return uri

    def download(self, uri: str, local_path: str):
        blob = self.bucket.blob(uri.replace(f"gs://{self.bucket_name}/", ""))
        blob.download_to_filename(local_path)
        print(f"File downloaded to: {local_path}")

    def download_to_b64(self, uri: str) -> str:
        blob = self.bucket.blob(uri.replace(f"gs://{self.bucket_name}/", ""))
        data = blob.download_as_bytes()
        return base64.b64encode(data).decode('utf-8')
    
    def download_to_tempfile(self, uri: str):
        blob = self.bucket.blob(uri.replace(f"gs://{self.bucket_name}/", ""))
        temp_file = tempfile.NamedTemporaryFile(delete=False)
        blob.download_to_filename(temp_file.name)
        print(f"File downloaded to temporary file: {temp_file.name}")
        return temp_file

def execute_ffmpeg_on_gcs_video(video_uri: str, ffmpeg_command: str, bucket_name: str, token: str, output_extension: str = "mp4", return_raw_output: bool = False) -> dict:
    """
    Download video from GCS, execute ffmpeg command, upload result back to GCS
    
    Args:
        video_uri: GCS URI of input video (gs://bucket/path)
        ffmpeg_command: FFmpeg command string (without input/output files)
        bucket_name: GCS bucket name for output
        token: JWT token for GCS authentication
        output_extension: File extension for output file
        return_raw_output: If True, returns raw ffmpeg stdout/stderr
    
    Returns:
        dict with result_uri and optionally raw output
    """
    bucket_manager = GCSStorageManagerJWT(bucket_name, token)
    
    # Download video to temp file
    temp_video = bucket_manager.download_to_tempfile(video_uri)
    
    # Create temp output file
    temp_output = tempfile.NamedTemporaryFile(suffix=f'.{output_extension}', delete=False)
    temp_output.close()
    
    try:
        # Replace placeholders in ffmpeg command
        # Expected format: "ffmpeg -i INPUT_FILE [options] OUTPUT_FILE"
        command_parts = ffmpeg_command.split()
        
        # Find and replace INPUT_FILE and OUTPUT_FILE placeholders
        for i, part in enumerate(command_parts):
            if part == "INPUT_FILE":
                command_parts[i] = temp_video.name
            elif part == "OUTPUT_FILE":
                command_parts[i] = temp_output.name
        
        # If no placeholders found, assume standard format and insert files
        if "INPUT_FILE" not in ffmpeg_command and "OUTPUT_FILE" not in ffmpeg_command:
            # Find -i flag and insert input file after it
            if "-i" in command_parts:
                i_index = command_parts.index("-i") + 1
                command_parts.insert(i_index, temp_video.name)
            else:
                # Add -i and input file at the beginning
                command_parts.insert(1, "-i")
                command_parts.insert(2, temp_video.name)
            
            # Add output file at the end
            command_parts.append(temp_output.name)
        
        # Execute ffmpeg command
        result = subprocess.run(command_parts, check=True, capture_output=True, text=True)
        
        # Upload processed video to GCS
        output_path = f"ffmpeg_processed/{uuid4()}.{output_extension}"
        result_uri = bucket_manager.upload(temp_output.name, output_path)
        
        response = {"result_uri": result_uri}
        
        if return_raw_output:
            response.update({
                "stdout": result.stdout,
                "stderr": result.stderr,
                "command": " ".join(command_parts)
            })
        
        return response
        
    finally:
        # Cleanup temp files
        try:
            os.unlink(temp_video.name)
            os.unlink(temp_output.name)
        except OSError:
            pass

