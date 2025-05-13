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
#   - teton_utils.py
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
import fb_utils as tu
from tasks_lib import (
    copy_metadata_to_backup,
    extend_metadata_with_task_output,
    add_default_tasks_to_metadata,
)

# === Task Identifier ===
task = "perform_download"

# === Init Logging and Config ===
logger = tu.initialize_logging()
platform_config = tu.load_config()
app_config = {"default_tasks": platform_config.get("default_tasks", {})}
logger.info("🔴 Starting task: perform_download")


def main():
    try:
        # === Verify Download Path ===
        target_usb = platform_config["target_usb"]
        download_date = datetime.now().strftime("%Y-%m-%d")
        download_path = os.path.join(target_usb, download_date)

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
        params = {
            "download_path": download_path,
            "cookie_path": platform_config.get("cookie_path"),
            "url": url,
            "task": task,
        }

        if "facebook.com" in url:
            logger.info("➡️ Facebook video detected.")
            if not os.path.exists(params["cookie_path"]):
                logger.error(f"Missing cookie file: {params['cookie_path']}")
                sys.exit(1)

        # === Pre-Download Prep ===
        metadata = tu.mask_metadata(params)
        if metadata is None:
            logger.error("❌ No metadata returned. Aborting task.")
            return
        params.update(metadata)

        filename_info = tu.create_original_filename(params)
        params.update(filename_info)

        # === Perform Download ===
        download_result = tu.download_video(params)
        if not download_result:
            logger.warning(f"No video downloaded for URL: {url}")
            return
        params.update(download_result)

        json_result = tu.store_params_as_json(params)
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

