import os
import sys
import json
import logging
import tempfile
from datetime import datetime
from urllib.parse import urlparse
from moviepy.editor import VideoFileClip, TextClip, CompositeVideoClip

# === Path Setup ===
current_dir = os.path.dirname(os.path.abspath(__file__))
lib_path = os.path.join(current_dir, "../lib/python_utils")
sys.path.append(lib_path)

# === Imports from shared utils ===
from utilities2 import initialize_logging, load_config, create_output_directory, create_subdir
from utilities3 import extract_audio_from_video, transcribe_video_by_minute
from utilities4 import should_perform_task, update_task_output_path, load_default_tasks, generate_dynamic_clips_from_metadata

# === Task Info ===
task = "generate_captions"


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
# MAIN
# ==================================================
if len(sys.argv) < 2:
    print("Error: No input video provided.")
    sys.exit(1)

logger = initialize_logging()
video_path = sys.argv[1]
json_path = os.path.join("metadata", os.path.basename(video_path).replace(".mp4", ".json"))


if len(sys.argv) < 2:
    print("Error: No input video provided.")
    sys.exit(1)

logger = initialize()
video_path = sys.argv[1]
json_path = os.path.join("metadata", os.path.basename(video_path).replace(".mp4", ".json"))

# Load or generate clips
try:
    clip_result = generate_dynamic_clips_from_metadata(json_path)
    clips = clip_result["clips"]
    logger.info(f"🎞 Loaded {len(clips)} clips from metadata.")
except Exception as e:
    logger.error(f"Failed to prepare clips: {e}")
    sys.exit(1)
