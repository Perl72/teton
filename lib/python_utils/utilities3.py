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
def should_perform_task(task: str, app_config: dict) -> bool:
    val = app_config.get("default_tasks", {}).get(task)
    return val is True

def get_existing_task_output(task: str, app_config: dict) -> str | None:
    val = app_config.get("default_tasks", {}).get(task)
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
