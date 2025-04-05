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


def extract_audio(
    input_video, clips, output_yaml_path, app_config=None, task_name="extract_audio"
):
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


def transcribe_audio2(audio_path):
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


def transcribe_video_by_minute2(video_path):
    video = VideoFileClip(video_path)
    duration = int(video.duration)
    transcript = {}

    for start in range(0, duration, 60):
        end = min(start + 60, duration)
        with tempfile.NamedTemporaryFile(
            delete=False, suffix=".wav"
        ) as temp_audio_file:
            audio_path = extract_audio_from_video(
                video_path, start, end, temp_audio_file.name
            )
            text = transcribe_audio(audio_path)
            os.remove(audio_path)
            transcript[f"{start}-{end}s"] = text

    return transcript


import os
import time
import tempfile
from moviepy.editor import VideoFileClip
import speech_recognition as sr

# from whisper import load_model  # still commented out for now


def transcribe_video_by_minute(video_path, output_dir):
    video = VideoFileClip(video_path)
    duration = int(video.duration)

    os.makedirs(output_dir, exist_ok=True)

    recognizer = sr.Recognizer()
    stitched_transcript = []

    for start in range(0, duration, 60):
        end = min(start + 60, duration)
        base_name = f"min_{start // 60:02d}"
        wav_path = os.path.join(output_dir, f"{base_name}.wav")
        txt_path = os.path.join(output_dir, f"{base_name}.txt")

        # Export audio chunk
        if not os.path.exists(wav_path):
            try:
                print(f"🎧 Exporting audio {start}-{end} sec → {wav_path}")
                audio_clip = video.audio.subclip(start, end)
                audio_clip.write_audiofile(wav_path)
            except Exception as e:
                print(f"❌ Failed to export audio: {e}")
                continue

        # Transcribe audio
        if not os.path.exists(txt_path):
            print(f"🗣️ Transcribing {base_name}.wav...")
            text = None
            for attempt in range(3):
                try:
                    with sr.AudioFile(wav_path) as source:
                        audio_data = recognizer.record(source)
                        text = recognizer.recognize_google(audio_data)
                    break
                except sr.UnknownValueError:
                    text = "[Unintelligible]"
                    break
                except sr.RequestError as e:
                    print(f"⚠️ Google error on attempt {attempt+1}: {e}")
                    time.sleep(2**attempt)
                    text = None

            # Fallback would go here later

            if text is not None:
                with open(txt_path, "w") as f:
                    f.write(text)
            else:
                with open(txt_path, "w") as f:
                    f.write("[ERROR: No transcript]")
        else:
            with open(txt_path, "r") as f:
                text = f.read()

        stitched_transcript.append(f"[{start}-{end} sec]\n{text}\n")

    # Final transcript
    final_path = os.path.join(output_dir, "full_transcript.txt")
    with open(final_path, "w") as f:
        f.write("\n".join(stitched_transcript))

    print(f"\n✅ Full transcript saved to: {final_path}")
    return "\n".join(stitched_transcript)


import tempfile
from moviepy.editor import VideoFileClip
import speech_recognition as sr
import time


import os
import time

# import whisper
import tempfile
from moviepy.editor import VideoFileClip
import speech_recognition as sr


def run_whisper_fallback(audio_path):
    model = whisper.load_model("base")
    print(f"🤖 Falling back to Whisper for: {audio_path}")
    result = model.transcribe(audio_path)
    return result["text"]




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
        if logger:
            logger.error(msg)
        raise FileNotFoundError(msg)

    if not os.path.exists(download_path):
        if logger:
            logger.warning(f"Creating download path: {download_path}")
        try:
            os.makedirs(download_path, exist_ok=True)
        except PermissionError:
            msg = f"Permission denied: {download_path}"
            if logger:
                logger.error(msg)
            raise PermissionError(msg)
    elif not os.access(download_path, os.W_OK):
        msg = f"No write permission to: {download_path}"
        if logger:
            logger.error(msg)
        raise PermissionError(msg)

    if logger:
        logger.info(f"Download directory confirmed: {download_path}")
    return download_path


def find_url_json(url, metadata_dir="./metadata"):
    """
    Search for a JSON file in the metadata directory that contains the given URL.

    :param url: The video URL to search for.
    :param metadata_dir: The directory containing metadata JSON files.
    :return: A tuple (file_path, data) if found, else (None, None).
    """
    print(f"🔍 Looking in: {os.path.abspath(metadata_dir)} for metadata JSONs...")

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
                        print(f"✅ Match found: {json_path}")
                        return json_path, data
            except (json.JSONDecodeError, IOError) as e:
                logging.error(f"Error reading {json_path}: {e}")

    logging.info("URL not found in any metadata file.")
    print("⚠️ No metadata match found.")
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
        metadata_dir = app_config.get("video_download", {}).get(
            "metadata_backup_path", "./metadata"
        )
        os.makedirs(metadata_dir, exist_ok=True)

        base_name = os.path.basename(original_json_path)
        target_path = os.path.join(metadata_dir, base_name)

        # Copy the original JSON
        shutil.copy2(original_json_path, target_path)

        # Load it and patch default_tasks
        with open(target_path, "r") as f:
            data = json.load(f)

        if (
            "default_tasks" in data
            and task in data["default_tasks"]
            and original_filename
        ):
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


def copy_metadata_to_backup(params: dict) -> dict:
    """
    Copies the original JSON metadata file to the metadata_backup_path.

    Expects:
        - 'config_json': the source .json path
        - 'app_config': contains 'video_download.metadata_backup_path'

    Returns:
        dict: {'full_metadata_json': copied_file_path}
    """
    import os, shutil, logging

    config_json_path = params.get("config_json")
    app_config = params.get("app_config", {})
    metadata_dir = app_config.get("video_download", {}).get(
        "metadata_backup_path", "./metadata"
    )

    if not config_json_path or not os.path.exists(config_json_path):
        logging.warning("Original config JSON not found. Skipping copy.")
        return {"full_metadata_json": None}

    os.makedirs(metadata_dir, exist_ok=True)
    base_name = os.path.basename(config_json_path)
    target_path = os.path.join(metadata_dir, base_name)

    shutil.copy2(config_json_path, target_path)
    logging.info(f"Metadata copied to: {target_path}")

    return {"full_metadata_json": target_path}


def extend_metadata_with_task_output(params: dict) -> dict:
    """
    Updates the copied metadata JSON to mark a task as completed by replacing 'true' with an output path.

    Expects:
        - 'task': the task name (e.g., 'apply_watermark')
        - 'full_metadata_json': path to metadata JSON file
        - '[task]_output_path', 'original_filename', or 'to_process' for completion path

    Returns:
        dict: {'updated_metadata': path}
    """

    task = params.get("task")
    json_path = params.get("full_metadata_json")
    output_path = (
        params.get(f"{task}_output_path")
        or params.get("original_filename")
        or params.get("to_process")
    )

    if not json_path or not os.path.exists(json_path):
        logging.warning("Metadata file not found for extension.")
        return {"updated_metadata": None}

    try:
        with open(json_path, "r") as f:
            data = json.load(f)

        if "default_tasks" in data and task in data["default_tasks"] and output_path:
            data["default_tasks"][task] = output_path
            logging.info(f"Marked task '{task}' as completed: {output_path}")
        else:
            logging.warning(f"Task '{task}' not found or no output to record.")

        with open(json_path, "w") as f:
            json.dump(data, f, indent=4)

        return {"updated_metadata": json_path}
    except Exception as e:
        logging.error(f"Failed to extend metadata for task '{task}': {e}")
        logging.debug(traceback.format_exc())
        return {"updated_metadata": None}


def extract_full_audio(input_video, output_dir, logger):
    """
    Extracts the full audio from input_video and saves it as .mp3 and .txt in the same directory.

    Args:
        input_video (str): Path to the .mp4 file
        output_dir (str): Where to save output files
        logger (Logger): Logger for logging output
    """
    try:
        # Get video duration
        clip = VideoFileClip(input_video)
        duration = clip.duration
        clip.close()

        # Build paths
        base = os.path.splitext(os.path.basename(input_video))[0]
        mp3_path = os.path.join(output_dir, base + ".mp3")
        txt_path = os.path.join(output_dir, base + ".txt")

        # Extract full audio
        logger.info(f"Extracting full audio: 0 to {duration:.2f} seconds")
        extract_audio_from_video(input_video, 0, duration, mp3_path)

        # Create .txt marker file
        with open(txt_path, "w") as f:
            f.write(f"Extracted audio from {input_video} to {mp3_path}\n")
        logger.info(f"Audio saved to {mp3_path}")
        logger.info(f"Text marker saved to {txt_path}")

    except Exception as e:
        logger.error(f"Failed to extract audio: {e}")


def load_default_tasks(config_path="conf/default_tasks.json"):
    """
    Loads task control flags from a JSON config.

    Args:
        config_path (str): Path to the default_tasks JSON file.

    Returns:
        dict: A dictionary of task flags under 'default_tasks'.
    """
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Task config file not found: {config_path}")

    with open(config_path, "r") as f:
        config = json.load(f)

    return config.get("default_tasks", {})

    # === Task Helpers ===


def should_perform_task2(task: str, task_config: dict) -> bool:
    """
    Checks if a task should be performed based on config.

    Args:
        task (str): Task name (e.g., "extract_audio")
        task_config (dict): Should include 'default_tasks' key with task flags

    Returns:
        bool: True if task is enabled, False otherwise
    """
    val = task_config.get("default_tasks", {}).get(task)
    return val is True


def should_perform_task(task: str, task_config: dict) -> bool:
    """
    Checks if a task should be performed based on config.
    Args:
        task (str): Task name (e.g., "extract_audio")
        task_config (dict): dict of task flags
    Returns:
        bool: True if task is enabled, False otherwise
    """
    val = task_config.get(task)
    return val is True


import time
import speech_recognition as sr


def transcribe_audio(audio_path, retries=3):
    recognizer = sr.Recognizer()
    with sr.AudioFile(audio_path) as source:
        audio_data = recognizer.record(source)

    for attempt in range(retries):
        try:
            return recognizer.recognize_google(audio_data)
        except sr.RequestError as e:
            print(f"Attempt {attempt+1}/{retries} failed: {e}")
            time.sleep(1)
        except Exception as e:
            print(f"Other error: {e}")
            break
    return "[ERROR] Failed to transcribe audio."


import math
import json
import os
from datetime import datetime


def generate_dynamic_clips_from_metadata(metadata_path, interval_seconds=30):
    """
    Generates and stores basic clips in metadata if none exist.

    Args:
        metadata_path (str): Path to the metadata JSON file.
        interval_seconds (int): Length of each clip in seconds.

    Returns:
        dict: {
            "clips": [...],  # list of generated (or existing) clips
            "updated_metadata": metadata_path
        }
    """
    if not os.path.exists(metadata_path):
        raise FileNotFoundError(f"Metadata file not found: {metadata_path}")

    with open(metadata_path, "r") as f:
        metadata = json.load(f)

    if "clips" in metadata and metadata["clips"]:
        return {"clips": metadata["clips"], "updated_metadata": metadata_path}

    duration = metadata.get("duration")
    if duration is None:
        raise ValueError("Metadata is missing 'duration' — cannot generate clips.")

    num_clips = math.ceil(duration / interval_seconds)
    clips = []

    for i in range(num_clips):
        start = i * interval_seconds
        end = min((i + 1) * interval_seconds, duration)
        clips.append(
            {
                "start": start,
                "end": end,
                "text": f"Auto-generated clip {i + 1}",
                "name": f"clip_{i + 1}",
            }
        )

    metadata["clips"] = clips

    with open(metadata_path, "w") as f:
        json.dump(metadata, f, indent=4)

    return {"clips": clips, "updated_metadata": metadata_path}
