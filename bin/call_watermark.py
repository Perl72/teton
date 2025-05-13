# ==================================================
# call_watermark.py - Apply watermark to a video using metadata
# ==================================================
#
# Description:
# Applies a watermark to a downloaded video using metadata and app config,
# then updates the metadata JSON with output info.
#
# --------------------------------------------------
# USAGE:
#   python call_watermark.py <video_file_path>
#
# DEPENDENCIES:
#   - teton_utils.py
#   - watermark.py
#
# TASK NAME:
#   apply_watermark
# ==================================================

import os
import sys
import json
import traceback
from datetime import datetime

# === Path Setup ===
current_dir = os.path.dirname(os.path.abspath(__file__))
lib_path = os.path.join(current_dir, "../lib/")
sys.path.append(lib_path)

# === Imports ===
from teton_utils import initialize_logging
from add_watermark import (
    load_app_config,
    add_watermark,
    add_default_tasks_to_metadata,
    update_task_output_path,
)

# === Task Identifier ===
task = "apply_watermark"

# === Init Logging & Config ===
logger = initialize_logging()
app_config = load_app_config()
watermark_config = app_config.get("watermark_config", {})


def main():
    try:
        # === Validate input argument ===
        if len(sys.argv) < 2:
            logger.error("Usage: python call_watermark.py <video_file_path>")
            sys.exit(1)

        input_video_path = sys.argv[1]
        if not os.path.isfile(input_video_path):
            logger.error(f"Input video file does not exist: {input_video_path}")
            sys.exit(1)

        logger.info(f"🖼 Processing video file: {input_video_path}")

        # === Derive Metadata Path ===
        json_path = os.path.join(
            "metadata",
            os.path.basename(input_video_path).replace(".mp4", ".json")
        )

        if not os.path.isfile(json_path):
            logger.error(f"Metadata file not found: {json_path}")
            sys.exit(1)

        with open(json_path, "r") as file:
            data = json.load(file)

        logger.info(f"Loaded metadata from: {json_path}")
        username = data.get("uploader", "UnknownUploader")
        video_date = data.get("video_date", datetime.now().strftime("%Y-%m-%d"))

        # === Prepare Parameters ===
        params = {
            "input_video_path": input_video_path,
            "download_path": os.path.dirname(input_video_path),
            "username": username,
            "video_date": video_date,
            **watermark_config,
        }

        # === Perform Watermarking ===
        logger.info("Starting watermarking process...")
        result = add_watermark(params)

        if result and "to_process" in result:
            output_path = result["to_process"]
            logger.info(f"✅ Watermarked video created: {output_path}")
            print(output_path)
            

            add_default_tasks_to_metadata(json_path)
            update_result = update_task_output_path(json_path, task, output_path)
            logger.debug(f"default_tasks updated: {update_result}")
        else:
            logger.error("Watermarking failed or returned no output.")
            sys.exit(1)

    except Exception as e:
        logger.error(f"❌ Unhandled exception in watermarking: {e}")
        logger.debug(traceback.format_exc())
        sys.exit(1)


if __name__ == "__main__":
    main()
