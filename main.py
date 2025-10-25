import os
import subprocess
import tempfile
from typing import Union
from uuid import uuid4
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from google.cloud import storage
from google.oauth2.credentials import Credentials
from dotenv import load_dotenv
import base64

load_dotenv()

# Pydantic models for request/response
class ProcessVideoRequest(BaseModel):
    video_uri: str
    ffmpeg_command: str
    bucket_name: str = None  # Optional, will use GCP_BUCKET_NAME if not provided
    token: str
    output_extension: str = "mp4"
    return_raw_output: bool = False

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
        print(f"[GCS] Starting upload: {local_path} -> gs://{self.bucket_name}/{remote_path}")
        blob = self.bucket.blob(remote_path)
        blob.upload_from_filename(local_path)
        uri = f'gs://{self.bucket_name}/{remote_path}'
        print(f"[GCS] Upload completed. File URL: {self.uri_to_url(uri)}")
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
        print(f"[GCS] Starting download from: {uri}")
        blob = self.bucket.blob(uri.replace(f"gs://{self.bucket_name}/", ""))
        temp_file = tempfile.NamedTemporaryFile(delete=False)
        blob.download_to_filename(temp_file.name)
        print(f"[GCS] Download completed to temporary file: {temp_file.name}")
        return temp_file

def execute_ffmpeg_on_gcs_video(video_uri: str, ffmpeg_command: str, bucket_name: str, token: str, output_extension: str = "mp4", return_raw_output: bool = False) -> dict:
    """
    Download video from GCS, execute ffmpeg command, upload result back to GCS
    """
    print(f"[FFMPEG] Starting video processing pipeline")
    print(f"[FFMPEG] Input video URI: {video_uri}")
    print(f"[FFMPEG] Target bucket: {bucket_name}")
    
    bucket_manager = GCSStorageManagerJWT(bucket_name, token)
    
    # Download video to temp file
    print(f"[FFMPEG] Downloading video from GCS to temporary file...")
    temp_video = bucket_manager.download_to_tempfile(video_uri)
    print(f"[FFMPEG] Video downloaded to: {temp_video.name}")
    
    # Create temp output file
    temp_output = tempfile.NamedTemporaryFile(suffix=f'.{output_extension}', delete=False)
    temp_output.close()
    print(f"[FFMPEG] Created temporary output file: {temp_output.name}")
    
    try:
        # Replace placeholders in ffmpeg command
        command_parts = ffmpeg_command.split()
        print(f"[FFMPEG] Processing FFmpeg command: {ffmpeg_command}")
        
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
        
        final_command = " ".join(command_parts)
        print(f"[FFMPEG] Executing command: {final_command}")
        
        # Execute ffmpeg command
        result = subprocess.run(command_parts, check=True, capture_output=True, text=True)
        print(f"[FFMPEG] FFmpeg execution completed successfully")
        
        # Upload processed video to GCS
        output_path = f"ffmpeg_processed/{uuid4()}.{output_extension}"
        print(f"[FFMPEG] Uploading processed video to GCS path: {output_path}")
        result_uri = bucket_manager.upload(temp_output.name, output_path)
        print(f"[FFMPEG] Upload completed. Result URI: {result_uri}")
        
        response = {"result_uri": result_uri}
        
        if return_raw_output:
            print(f"[FFMPEG] Including raw output in response")
            response.update({
                "stdout": result.stdout,
                "stderr": result.stderr,
                "command": final_command
            })
        
        return response
        
    finally:
        # Cleanup temp files
        print(f"[FFMPEG] Cleaning up temporary files...")
        try:
            os.unlink(temp_video.name)
            os.unlink(temp_output.name)
            print(f"[FFMPEG] Temporary files cleaned up successfully")
        except OSError as e:
            print(f"[FFMPEG] Warning: Could not clean up temporary files: {e}")
            pass

app = FastAPI()

# Get the bearer key from environment variable
BEARER_KEY = os.getenv("BEARER_KEY")

# Security scheme for receiving the bearer token
security = HTTPBearer()

# Dependency to enforce Bearer token auth
def verify_bearer_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    if credentials.scheme.lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication scheme."
        )
    token = credentials.credentials
    if token != BEARER_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing token."
        )
    # Authorized
    return token

@app.get("/")
def read_root(token: str = Depends(verify_bearer_token)):
    return {"message": "Hello World"}

@app.get("/items/{item_id}")
def read_item(item_id: int, q: Union[str, None] = None, token: str = Depends(verify_bearer_token)):
    return {"item_id": item_id, "q": q}

@app.post("/process-video")
def process_video(request: ProcessVideoRequest, token: str = Depends(verify_bearer_token)):
    """
    POST endpoint to process video with ffmpeg
    """
    print(f"[API] Received video processing request for URI: {request.video_uri}")
    print(f"[API] FFmpeg command: {request.ffmpeg_command}")
    print(f"[API] Output extension: {request.output_extension}, Return raw output: {request.return_raw_output}")
    
    # Use default bucket if none provided
    bucket_name = request.bucket_name or os.getenv("GCP_BUCKET_NAME")
    if not bucket_name:
        print(f"[API] Error: No bucket name provided and GCP_BUCKET_NAME not set")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="bucket_name is required or set GCP_BUCKET_NAME environment variable"
        )
    
    print(f"[API] Using bucket: {bucket_name}")
    
    try:
        # Process video
        print(f"[API] Calling execute_ffmpeg_on_gcs_video function...")
        result = execute_ffmpeg_on_gcs_video(
            video_uri=request.video_uri,
            ffmpeg_command=request.ffmpeg_command,
            bucket_name=bucket_name,
            token=request.token,
            output_extension=request.output_extension,
            return_raw_output=request.return_raw_output
        )
        
        print(f"[API] Video processing completed successfully. Output URI: {result['result_uri']}")
        
        response = {
            'success': True,
            'output_uri': result["result_uri"],
            'message': 'Video processed successfully'
        }
        
        # Add raw output if requested
        if request.return_raw_output:
            response.update({
                'raw_output': {
                    'stdout': result.get("stdout"),
                    'stderr': result.get("stderr"),
                    'command': result.get("command")
                }
            })
            print(f"[API] Including raw FFmpeg output in response")
        
        return response
        
    except subprocess.CalledProcessError as e:
        print(f"[API] FFmpeg command failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                'error': 'FFmpeg command failed',
                'details': str(e),
                'stderr': e.stderr if hasattr(e, 'stderr') else None
            }
        )
        
    except Exception as e:
        print(f"[API] Video processing failed with error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                'error': 'Processing failed',
                'details': str(e)
            }
        )
