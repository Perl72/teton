# ==================================================
# utilities2.py - Video Processing Utility
# ==================================================
#
# Function List:
# 1. initialize_logging() -> logging.Logger
#    Initializes logging for the script.
#
# 2. extract_audio_from_video(video_path: str, start_time: float, end_time: float, temp_audio_path: str) -> str
#    Extracts audio from a video between the specified time range.
#
# 3. transcribe_audio(audio_path: str) -> str
#    Converts an audio file to text using speech recognition.
#
# 4. process_clip(video_path: str, start_time: float, end_time: float) -> str
#    Extracts, transcribes, and allows confirmation of the text before adding captions.
#
# 5. process_clips_moviepy(config: dict, clips: dict, logger: logging.Logger, input_video: str, output_dir: str, captions_config)
#    Processes video clips by adding captions and saving them.
#
# 6. create_output_directory(base_dir: str = "clips") -> str
#    Creates an output directory named based on a timestamp and video filename.
#
# 7. load_clips_from_file(file_path: str) -> dict
#    Loads clips data from a JSON or YAML file.
#
# 8. stitch_clips(clip_files: list, output_file: str)
#    Stitches multiple video clips into one output file.
#
# 9. generate_clip_transcripts(input_video: str, clips: dict, output_yaml_path: str) -> str
#    Generates transcription for each clip and saves the results to a YAML file.
#
# 10. load_app_config() -> dict
#     Loads the application configuration from a JSON or YAML file.
# ==================================================

import os
import sys
import logging
import json
import datetime
import yaml
import tempfile
import time
import speech_recognition as sr
from moviepy.editor import VideoFileClip, TextClip, CompositeVideoClip, ColorClip, concatenate_videoclips



# ==================================================

# ==================================================
# CLIPS CONFIGURATION
# ==================================================
moviepy_config = {
    "clips_directory": "clips/",
    "width": 1280,
    "height": 720,
    "font": "Arial",
    "font_size": 64,
    "text_halign": "left",
    "text_valign": "center",
    "output_format": "mp4",
    "text_color": "white",
}

# ==================================================
# LOGGING INITIALIZATION
# ==================================================
def initialize_logging():
    log_dir = "./logs"
    os.makedirs(log_dir, exist_ok=True)
    log_file = os.path.join(log_dir, "moviepy_clips.log")

    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)

    if not logger.handlers:
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.DEBUG)
        file_formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)

        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_formatter = logging.Formatter("%(asctime)s - %(message)s")
        console_handler.setFormatter(console_formatter)
        logger.addHandler(console_handler)

    logger.info("Logging initialized.")
    return logger


def load_app_config():
    """Load the application configuration from a JSON file."""
    current_dir = os.path.dirname(os.path.abspath(__file__))
    base_dir = os.path.join(current_dir, "../../")
    
    if not os.path.exists(base_dir):
        raise FileNotFoundError(f"Base directory not found at {base_dir}")
    
    config_path = os.path.join(base_dir, "conf/app_config.json")

    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Configuration file not found at {config_path}")
    
    try:
        with open(config_path, "r") as file:
            app_config = json.load(file)
        return app_config
    except json.JSONDecodeError as e:
        raise ValueError(f"Failed to parse JSON configuration at {config_path}: {e}")

if len(sys.argv) < 3:
    print("Usage: python script.py <input_video> <clips_json_file>")
    sys.exit(1)

# ==================================================
# AUDIO EXTRACTION AND CAPTIONING
# ==================================================
def extract_audio_from_video(video_path, start_time, end_time, temp_audio_path):
    video = VideoFileClip(video_path).subclip(start_time, end_time)
    video.audio.write_audiofile(temp_audio_path)
    return temp_audio_path

def transcribe_audio(audio_path):
    recognizer = sr.Recognizer()
    with sr.AudioFile(audio_path) as source:
        audio_data = recognizer.record(source)
    try:
        return recognizer.recognize_google(audio_data)
    except (sr.UnknownValueError, sr.RequestError):
        return ""

def process_clip(video_path, start_time, end_time):
    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_audio_file:
        audio_path = extract_audio_from_video(video_path, start_time, end_time, temp_audio_file.name)
        transcription = transcribe_audio(audio_path)
        os.remove(audio_path)
        user_input = input(f"Transcribed text: '{transcription}'\nPress Enter to keep or type a new caption: ")
        return user_input.strip() if user_input else transcription

# ==================================================
# NEW: Generate Transcripts from Clip Set
# ==================================================
def generate_clip_transcripts(input_video, clips, output_yaml_path):
    for clip_name, clip_list in clips.items():
        for clip in clip_list:
            start, end = clip["start"], clip["end"]
            with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_audio_file:
                audio_path = extract_audio_from_video(input_video, start, end, temp_audio_file.name)
                transcription = transcribe_audio(audio_path)
                os.remove(audio_path)
            clip["text"] = transcription
    with open(output_yaml_path, "w") as f:
        yaml.dump(clips, f)
    return output_yaml_path

# ==================================================
# PROCESS CLIPS
# ==================================================
def process_clips_moviepy(config, clips, logger, input_video, output_dir, captions_config=None):
    video_clip = VideoFileClip(input_video)
    clips_directory = os.path.join(output_dir, "clips")
    os.makedirs(clips_directory, exist_ok=True)

    # Prefer captions config if provided
    font = (captions_config or config).get("font", "Arial")
    font_size = (captions_config or config).get("font_size", 48)
    text_color = (captions_config or config).get("text_color", "white")
    text_halign = (captions_config or config).get("text_halign", "center")
    text_valign = (captions_config or config).get("text_valign", "bottom")

    for clip_name, clip_list in clips.items():
        for clip in clip_list:
            start, end = clip["start"], clip["end"]
            text = process_clip(input_video, start, end)
            clip["text"] = text
            output_file = os.path.join(clips_directory, f"{clip_name}.mp4")
            logger.info(f"Processing Clip: {clip_name} ({start}-{end} sec)")

            clip_segment = video_clip.subclip(start, end)

            if text.strip():
                txt_clip = TextClip(
                    text,
                    fontsize=font_size,
                    font=font,
                    color=text_color
                ).set_position((text_halign, text_valign)).set_duration(clip_segment.duration)
                video_with_text = CompositeVideoClip([clip_segment, txt_clip])
            else:
                video_with_text = clip_segment

            video_with_text.write_videofile(output_file, codec="libx264", audio_codec="aac")
            logger.info(f"Clip {clip_name} processed successfully.")


def create_output_directory(base_dir="clips"):
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    input_video_name = os.path.splitext(os.path.basename(sys.argv[1]))[0]
    output_dir = os.path.join(base_dir, f"{input_video_name}_{timestamp}")
    os.makedirs(output_dir, exist_ok=True)
    return output_dir

def load_clips_from_file(file_path):
    if not os.path.exists(file_path):
        sys.exit(f"Error: Clip file '{file_path}' not found.")
    with open(file_path, 'r') as file:
        return yaml.safe_load(file) if file_path.endswith(('.yaml', '.yml')) else json.load(file)

def stitch_clips(clip_files, output_file):
    final_clips = [VideoFileClip(clip) for clip in clip_files]
    final_video = concatenate_videoclips(final_clips, method="compose")
    final_video.write_videofile(output_file, codec="libx264", fps=24, audio_codec="aac")
    print(f"Final stitched video saved as {output_file}")
