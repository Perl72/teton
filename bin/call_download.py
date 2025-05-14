# ==================================================
# call_download.py - Downloads video and saves metadata
# ==================================================
#
# Description:
# Downloads a video from a given URL, saves metadata,
# and updates the metadata JSON to track task completion.
#
# --------------------------------------------------
# USAGE:
#   python call_download.py <video_url>
#
# DEPENDENCIES:
#   - fb_utils.py
#   - task_lib.py
#
# TASK NAME:
#   perform_download
# ==================================================

import sys
import os
import logging
import traceback
from datetime import datetime

# === Path Setup ===
current_dir = os.path.dirname(os.path.abspath(__file__))
lib_path = os.path.join(current_dir, "../lib/")
sys.path.append(lib_path)

# === Imports ===
import fb_utils as fb
import re
from tasks_lib import (
    copy_metadata_to_backup,
    extend_metadata_with_task_output,
    add_default_tasks_to_metadata,
)

# === Task Identifier ===
task = "perform_download"

# === Init Logging and Config ===
logger = fb.initialize_logging()

# Ensure metadata directory exists
metadata_dir = fb.resolve_path("./metadata")
if not os.path.exists(metadata_dir):
    logger.info(f"📁 Creating metadata directory: {metadata_dir}")
    os.makedirs(metadata_dir, exist_ok=True)


platform_config = fb.load_config()
app_config = {"default_tasks": platform_config.get("default_tasks", {})}
logger.info("🔴 Starting task: perform_download")

def main():
    try:
        # === Verify Download Path ===
        target_usb = platform_config["target_usb"]
        download_date = datetime.now().strftime("%Y-%m-%d")
        download_path = fb.resolve_path(os.path.join(target_usb, download_date))

        if not os.path.exists(target_usb):
            logger.error(f"USB drive {target_usb} is not mounted.")
            sys.exit(1)

        if not os.path.exists(download_path):
            logger.warning(f"Creating download path: {download_path}")
            try:
                os.makedirs(download_path, exist_ok=True)
            except PermissionError:
                logger.error(f"Permission denied: {download_path}")
                sys.exit(1)

        elif not os.access(download_path, os.W_OK):
            logger.error(f"No write permission to: {download_path}")
            sys.exit(1)

        logger.info(f"✅ Download directory ready: {download_path}")

        # === Validate Input URL ===
        if len(sys.argv) < 2:
            logger.error("Missing required argument: <video_url>")
            sys.exit(1)

        url = sys.argv[1].strip()
        cookie_path = fb.resolve_path(platform_config.get("cookie_path"))

        params = {
            "download_path": download_path,
            "url": url,
            "task": task,
            "metadata_path": os.path.join(metadata_dir, "metadata.json"),
            "video_download": {
                "cookie_path": cookie_path
            },
            "url": url,
            "task": task,
        }

        if "facebook.com" in url:
            logger.info("➡️ Facebook video detected.")
            cookie_path_check = params.get("video_download", {}).get("cookie_path")
            if not os.path.exists(cookie_path_check):
                logger.warning(f"⚠️ Cookie file not found: {cookie_path_check}. Continuing anyway.")

        # === Pre-Download Prep ===
        metadata = fb.mask_metadata(params)
        if metadata is None:
            logger.error("❌ No metadata returned. Aborting task.")
            return
        params.update(metadata)

        # Sanitize video title for safe filenames
        if "video_title" in params:
            params["video_title"] = fb.safe_filename(params["video_title"])

        filename_info = fb.create_original_filename(params)
        params.update(filename_info)

        # === Perform Download ===
        download_result = fb.download_video(params)
        if not download_result:
            logger.warning(f"No video downloaded for URL: {url}")
            return
        params.update(download_result)

        json_result = fb.store_params_as_json(params)
        params.update(json_result)

        logger.info(f"✅ Download complete: {params.get('original_filename')}")
        print(params.get("original_filename"))

        # === Post-Download Metadata Update ===
        config_json = params.get("config_json")
        if config_json:
            add_default_tasks_to_metadata(config_json)
            backup_result = copy_metadata_to_backup(params)
            params["full_metadata_json"] = backup_result.get("full_metadata_json")
            params["perform_download_output_path"] = params.get("original_filename")
            params["app_config"] = app_config
            extend_metadata_with_task_output(params)
            logger.info("📦 Task metadata updated.")
            print(params.get("original_filename"))

    except Exception as e:
        logger.error(f"❌ Unhandled error in main(): {e}")
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

