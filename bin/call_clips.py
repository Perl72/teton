import sys
import logging
import os
import json
import yaml
from moviepy.editor import VideoFileClip

# Set IM path for MoviePy
os.environ["IMAGEMAGICK_BINARY"] = os.getenv("IMAGEMAGICK_BINARY", "magick")

# Import external utility functions
current_dir = os.path.dirname(os.path.abspath(__file__))
lib_path = os.path.join(current_dir, "../lib/python_utils")
sys.path.append(lib_path)

from utilities3 import (
    should_perform_task,
    get_existing_task_output,
    process_clips_with_captions,
    load_config,
    set_imagemagick_env
)

from utilities2 import (
    initialize_logging,
    load_app_config,
    load_clips_from_file,
    create_output_directory
)

# ======================================
# Task Definition
# ======================================
task = "generate_captions"

# ======================================
# CLI Argument Handling
# ======================================
if len(sys.argv) < 3:
    print("Usage: python call_clips.py <input_video> <clips_json_file>")
    sys.exit(1)

input_video = sys.argv[1]
clips_file = sys.argv[2]

# ======================================
# Init & Config
# ======================================
logger = initialize_logging()
platform_config = load_config()
set_imagemagick_env(platform_config)
app_config = load_app_config()


# ======================================
# Task Skipping Logic
# ======================================
if not should_perform_task(task, app_config):
    existing = get_existing_task_output(task, app_config)
    if existing:
        logger.info(f"Task '{task}' already done. Output located at: {existing}")
    else:
        logger.info(f"Task '{task}' is disabled in config. Exiting.")
    sys.exit(0)

# ======================================
# Pre-checks
# ======================================
if not os.path.exists(input_video):
    logger.error(f"Error: Video file '{input_video}' not found.")
    sys.exit(1)

logger.info(f"Processing video: {input_video}")

# ======================================
# Load & Process Clips
# ======================================
clips = load_clips_from_file(clips_file)
output_dir = create_output_directory()

process_clips_with_captions(app_config, clips, logger, input_video, output_dir)
