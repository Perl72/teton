# ==================================================
# utilities3.py - Task-aware Wrappers
# ==================================================
#
# Contains higher-level versions of utilities that include config-based task control.
#
# Function List:
# 1. extract_audio(...) -> str | None
#    Task-aware wrapper for audio transcript generation.
#
# 2. transcribe_full_video(...) -> str
#    Transcribes the entire video into one block of text.
#
# 3. transcribe_video_by_minute(...) -> dict
#    Breaks video into 1-minute chunks and transcribes each one separately.
# ==================================================

from utilities2 import generate_clip_transcripts
import os
import tempfile
from moviepy.editor import VideoFileClip
import json
import platform
import speech_recognition as sr
import logging
from datetime import datetime
from urllib.parse import urlparse


import shutil
import traceback




logger = logging.getLogger(__name__)

# === Audio Extraction + Transcription Helpers ===

def extract_audio(input_video, clips, output_yaml_path, app_config=None, task_name="extract_audio"):
    if app_config:
        task_value = app_config.get("default_tasks", {}).get(task_name)
        if task_value is False:
            print(f"Task '{task_name}' is disabled in config. Skipping.")
            return None
        elif isinstance(task_value, str):
            print(f"Task '{task_name}' already done. Output at: {task_value}")
            return task_value

    return generate_clip_transcripts(input_video, clips, output_yaml_path)


def extract_audio_from_video(video_path, start_time, end_time, output_path):
    video_clip = VideoFileClip(video_path).subclip(start_time, end_time)
    audio = video_clip.audio
    audio.write_audiofile(output_path)
    return output_path


def transcribe_audio(audio_path):
    recognizer = sr.Recognizer()
    with sr.AudioFile(audio_path) as source:
        audio_data = recognizer.record(source)
        try:
            return recognizer.recognize_google(audio_data)
        except sr.UnknownValueError:
            return ""
        except sr.RequestError as e:
            return f"ERROR: {e}"


# === New: Full and Chunked Video Transcription ===

def transcribe_full_video(video_path):
    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_audio_file:
        audio_path = extract_audio_from_video(video_path, 0, None, temp_audio_file.name)
        transcription = transcribe_audio(audio_path)
        os.remove(audio_path)
        return transcription


def transcribe_video_by_minute(video_path):
    video = VideoFileClip(video_path)
    duration = int(video.duration)
    transcript = {}

    for start in range(0, duration, 60):
        end = min(start + 60, duration)
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_audio_file:
            audio_path = extract_audio_from_video(video_path, start, end, temp_audio_file.name)
            text = transcribe_audio(audio_path)
            os.remove(audio_path)
            transcript[f"{start}-{end}s"] = text

    return transcript


# === Task Helpers ===
def should_perform_task(task: str, task_config: dict) -> bool:
    val = task_config.get(task)
    return val is True

def get_existing_task_output(task: str, task_config: dict) -> str | None:
    val = task_config.get(task)
    return val if isinstance(val, str) else None



def load_config():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    config_path = os.path.join(current_dir, "../../conf/config.json")
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Configuration file not found at {config_path}")
    with open(config_path, "r") as file:
        config = json.load(file)
    os_name = platform.system()
    if os_name not in config:
        raise ValueError(f"Unsupported platform: {os_name}")
    return config[os_name]


def set_imagemagick_env(config_block):
    binary = config_block.get("imagemagick_binary")
    if binary:
        os.environ["IMAGEMAGICK_BINARY"] = binary


        # --- Load Platform-Specific Configuration ---
def load_platform_config():

    # Go up two levels from lib/python_utils/utilities2.py
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    config_path = os.path.join(base_dir, "conf", "config.json")

    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Configuration file not found at {config_path}")

    with open(config_path, "r") as file:
        config = json.load(file)

    return config



def prepare_usb_download_path(config, logger=None):
    """
    Ensure USB target path exists and is writable.
    Returns full dated path like /Volumes/MyDrive/2025-03-23
    """
    target_usb = config["target_usb"]
    download_date = datetime.now().strftime("%Y-%m-%d")
    download_path = os.path.join(target_usb, download_date)

    if not os.path.exists(target_usb):
        msg = f"USB drive not mounted: {target_usb}"
        if logger: logger.error(msg)
        raise FileNotFoundError(msg)

    if not os.path.exists(download_path):
        if logger: logger.warning(f"Creating download path: {download_path}")
        try:
            os.makedirs(download_path, exist_ok=True)
        except PermissionError:
            msg = f"Permission denied: {download_path}"
            if logger: logger.error(msg)
            raise PermissionError(msg)
    elif not os.access(download_path, os.W_OK):
        msg = f"No write permission to: {download_path}"
        if logger: logger.error(msg)
        raise PermissionError(msg)

    if logger: logger.info(f"Download directory confirmed: {download_path}")
    return download_path




def find_url_json(url, metadata_dir="./metadata"):
    """
    Search for a JSON file in the metadata directory that contains the given URL.
    
    :param url: The video URL to search for.
    :param metadata_dir: The directory containing metadata JSON files.
    :return: A tuple (file_path, data) if found, else (None, None).
    """
    if not os.path.exists(metadata_dir):
        logging.warning(f"Metadata directory not found: {metadata_dir}")
        return None, None

    for filename in os.listdir(metadata_dir):
        if filename.endswith(".json"):
            json_path = os.path.join(metadata_dir, filename)
            try:
                with open(json_path, "r", encoding="utf-8") as file:
                    data = json.load(file)
                    if isinstance(data, dict) and "url" in data and data["url"] == url:
                        logging.info(f"URL found in: {json_path}")
                        return json_path, data
            except (json.JSONDecodeError, IOError) as e:
                logging.error(f"Error reading {json_path}: {e}")

    logging.info("URL not found in any metadata file.")
    return None, None




def copy_and_extend_metadata(params: dict) -> dict:
    """
    Copies the metadata JSON file from the USB location to metadata_backup_path,
    and updates 'perform_download' in default_tasks with the full original_filename path.

    Returns:
        dict: {'full_metadata_json': path_to_written_file}
    """
    try:
        original_json_path = params.get("config_json")
        original_filename = params.get("original_filename", "")
        default_tasks = params.get("default_tasks", {})
        app_config = params.get("app_config", {})
        task = "perform_download"

        if not original_json_path or not os.path.exists(original_json_path):
            logging.warning("Original config JSON not found. Skipping backup.")
            return {"full_metadata_json": None}

        # Determine target metadata path
        metadata_dir = app_config.get("video_download", {}).get("metadata_backup_path", "./metadata")
        os.makedirs(metadata_dir, exist_ok=True)

        base_name = os.path.basename(original_json_path)
        target_path = os.path.join(metadata_dir, base_name)

        # Copy the original JSON
        shutil.copy2(original_json_path, target_path)

        # Load it and patch default_tasks
        with open(target_path, "r") as f:
            data = json.load(f)

        if "default_tasks" in data and task in data["default_tasks"] and original_filename:
            data["default_tasks"][task] = original_filename
            logging.info(f"Updated '{task}' with completed path: {original_filename}")
        else:
            logging.warning("default_tasks not found in metadata JSON or task missing.")

        # Save it back
        with open(target_path, "w") as f:
            json.dump(data, f, indent=4)

        logging.info(f"Extended metadata saved to: {target_path}")
        return {"full_metadata_json": target_path}

    except Exception as e:
        logging.error(f"Error in copy_and_extend_metadata: {e}")
        logging.debug(traceback.format_exc())
        return {"full_metadata_json": None}
