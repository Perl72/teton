# ==================================================
# clips_audio
# ==================================================
#
# Contains higher-level versions of utilities that include config-based task control.
#
# Function List:
# 1. extract_audio(input_video: str, clips: dict, output_yaml_path: str, app_config: dict, task_name: str = "extract_audio") -> str | None
#    Task-aware wrapper that calls generate_clip_transcripts only if needed.
# ==================================================

from utilities2 import generate_clip_transcripts


def extract_audio(input_video, clips, output_yaml_path, app_config=None, task_name="extract_audio"):
    """
    Task-aware wrapper for audio extraction and transcription.
    Checks config to determine if the task should be performed.

    Args:
        input_video (str): Path to the source video
        clips (dict): Clip definitions (start/end)
        output_yaml_path (str): Output file path for YAML
        app_config (dict): Full app config
        task_name (str): Task key (default: 'extract_audio')

    Returns:
        str | None: Path to output YAML file, or None if skipped
    """
    if app_config:
        task_value = app_config.get("default_tasks", {}).get(task_name)
        if task_value is False:
            print(f"Task '{task_name}' is disabled in config. Skipping.")
            return None
        elif isinstance(task_value, str):
            print(f"Task '{task_name}' already done. Output at: {task_value}")
            return task_value

    return generate_clip_transcripts(input_video, clips, output_yaml_path)

import os
import tempfile
from moviepy.editor import VideoFileClip
import json
import platform

# === Utility Functions (new versions) ===

def extract_audio_from_video(video_path, start_time, end_time, output_path):
    """
    Extracts audio from a video segment and saves it to output_path
    Args:
        video_path (str): Path to the video file
        start_time (float): Start time in seconds
        end_time (float): End time in seconds
        output_path (str): Path to save the extracted audio
    Returns:
        str: Path to the extracted audio file
    """
    video_clip = VideoFileClip(video_path).subclip(start_time, end_time)
    audio = video_clip.audio
    audio.write_audiofile(output_path)
    return output_path

def transcribe_audio(audio_path):
    """
    Transcribes the audio file to text using speech recognition
    Args:
        audio_path (str): Path to the .wav audio file
    Returns:
        str: Transcribed text
    """
    import speech_recognition as sr
    recognizer = sr.Recognizer()
    with sr.AudioFile(audio_path) as source:
        audio_data = recognizer.record(source)
        try:
            return recognizer.recognize_google(audio_data)
        except sr.UnknownValueError:
            return ""
        except sr.RequestError as e:
            return f"ERROR: {e}"






def set_imagemagick_env(config_block):
    """
    Set ImageMagick binary path for MoviePy if specified in config.
    Args:
        config_block (dict): The platform-specific config loaded from config.json
    """
    binary = config_block.get("imagemagick_binary")
    if binary:
        os.environ["IMAGEMAGICK_BINARY"] = binary

