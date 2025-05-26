# ==================================================
# Minimal Clip Extraction Utility (no captions, no transcription)
# ==================================================

import os
import sys
import logging
import json
import datetime
import yaml
from moviepy.editor import VideoFileClip
from typing import Dict


def initialize_logging():
    log_dir = "./logs"
    os.makedirs(log_dir, exist_ok=True)
    log_file = os.path.join(log_dir, "clipper.log")

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


def load_clips_from_file(file_path: str) -> Dict:
    if not os.path.exists(file_path):
        sys.exit(f"Error: Clip file '{file_path}' not found.")
    with open(file_path, 'r') as file:
        return yaml.safe_load(file) if file_path.endswith(('.yaml', '.yml')) else json.load(file)


def create_output_directory(base_dir="clips"):
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    input_video_name = os.path.splitext(os.path.basename(sys.argv[1]))[0]
    output_dir = os.path.join(base_dir, f"{input_video_name}_{timestamp}")
    os.makedirs(output_dir, exist_ok=True)
    return output_dir


def process_clips_basic(clips: Dict, logger, input_video: str, output_dir: str):
    video_clip = VideoFileClip(input_video)
    os.makedirs(output_dir, exist_ok=True)

    for clip_name, clip_list in clips.items():
        for clip in clip_list:
            start, end = clip["start"], clip["end"]
            output_file = os.path.join(output_dir, f"{clip_name}.mp4")

            logger.info(f"✂️ Processing Clip: {clip_name} ({start}-{end} sec)")

            clip_segment = video_clip.subclip(start, end)
            clip_segment.write_videofile(output_file, codec="libx264", audio_codec="aac")

            logger.info(f"✅ Saved: {output_file}")


# Optional: sample main()
if __name__ == "__main__":
    input_video = sys.argv[1]
    clips_file = sys.argv[2]

    logger = initialize_logging()
    clips = load_clips_from_file(clips_file)
    output_dir = create_output_directory("clips_output")

    process_clips_basic(clips, logger, input_video, output_dir)

