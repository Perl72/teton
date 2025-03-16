import sys
import logging
import os
import json
from moviepy.editor import VideoFileClip, TextClip, CompositeVideoClip
import tempfile
import time
import speech_recognition as sr
from urllib.parse import urlparse

# ==================================================
# CLIPS CONFIGURATION 
# ==================================================
moviepy_config = {
    "clips_directory": "clips/",  # Directory where clips will be stored
    "width": 1280,  # Video width
    "height": 720,  # Video height
    "font": "Arial",  # Font file for text overlay
    "font_size": 64,  # Font size for overlay text
    "text_halign": "left",  # Horizontal alignment for overlay text
    "text_valign": "center",  # Vertical alignment for overlay text
    "output_format": "mp4",  # Output format
    "text_color": "white",  # Color of the text overlay
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

# ==================================================
# LOAD CLIPS FROM FILE
# ==================================================
import yaml

def load_clips_from_file(file_path):
    if not os.path.exists(file_path):
        print(f"Error: Clip file '{file_path}' not found.")
        sys.exit(1)

    try:
        with open(file_path, 'r') as file:
            if file_path.endswith((".yaml", ".yml")):
                clips = yaml.safe_load(file)  # Load YAML
            else:
                clips = json.load(file)  # Load JSON
            
            if not clips:
                print("Error: Clip file is empty or invalid.")
                sys.exit(1)

            return clips

    except (json.JSONDecodeError, yaml.YAMLError) as e:
        print(f"Error reading clips file: {e}")
        sys.exit(1)

# ==================================================
# PROCESS VIDEO CLIPS
# ==================================================
def process_clips_moviepy(moviepy_config, clips, logger, input_video):
    clips_directory = moviepy_config["clips_directory"]
    os.makedirs(clips_directory, exist_ok=True)

    video_clip = VideoFileClip(input_video)

    for clip_name, clip_list in clips.items():
        for clip in clip_list:
            start, end, text = clip["start"], clip["end"], clip["text"]
            output_file = os.path.join(clips_directory, f"{clip_name}.mp4")

            logger.info(f"Processing Clip: {clip_name} ({start}-{end} sec)")

            clip_segment = video_clip.subclip(start, end)

            if text.strip():  # Only create a TextClip if there is text
                txt_clip = TextClip(
                    text, fontsize=moviepy_config["font_size"], 
                    font=moviepy_config["font"], color=moviepy_config["text_color"]
                ).set_position((moviepy_config["text_halign"], moviepy_config["text_valign"])).set_duration(clip_segment.duration)
                
                video_with_text = CompositeVideoClip([clip_segment, txt_clip])
            else:
                video_with_text = clip_segment  # Just use the video clip with no text overlay

            video_with_text.write_videofile(output_file, codec="libx264", audio_codec="aac")

            logger.info(f"Clip {clip_name} processed successfully.")


# ==================================================
# MAIN EXECUTION
# ==================================================
if len(sys.argv) < 3:
    print("Usage: python script.py <input_video> <clips_json_file>")
    sys.exit(1)

input_video = sys.argv[1]
clips_file = sys.argv[2]

logger = initialize_logging()
logger.info(f"Processing video: {input_video}")

clips = load_clips_from_file(clips_file)
process_clips_moviepy(moviepy_config, clips, logger, input_video)
