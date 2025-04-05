import sys
import os
import json
import logging
import traceback
import platform
from datetime import datetime

# Add lib path to sys.path
current_dir = os.path.dirname(os.path.abspath(__file__))
lib_path = os.path.join(current_dir, "../lib/python_utils")
sys.path.append(lib_path)

# Import modules
import downloader5
import utilities1
from utilities2 import initialize_logging, load_config
from utilities3 import set_imagemagick_env
from tasks_lib import (
    should_perform_task,
    get_existing_task_output,
    extend_metadata_with_task_output,
    find_url_json,
    copy_metadata_to_backup,
    load_default_tasks,
    add_default_tasks_to_metadata,
    update_task_output_path,
)

# ======================================
# Task Definition
# ======================================
task = "perform_download"

# ======================================
# Init & Config
# ======================================
logger = initialize_logging()
platform_config = load_config()
set_imagemagick_env(platform_config)

default_tasks = load_default_tasks()
logger.info("🔴 Entering main routine... 🚀")
logger.info(f"🧩 Loaded default_tasks from JSON: {default_tasks}")
app_config = {"default_tasks": default_tasks}

# ======================================
# Task Skipping Logic
# ======================================
logger.info(f"🧩 Checking if task '{task}' should be performed...")
logger.debug(f"Task '{task}' in config: {default_tasks.get('perform_download')}")

if should_perform_task(task, app_config):
    logger.info(f"✅ Task '{task}' is enabled and will be performed.")
else:
    existing = get_existing_task_output(task, app_config)
    if existing:
        logger.info(f"Task '{task}' already done. Output located at: {existing}")
    else:
        logger.info(f"❌ Task '{task}' is disabled in config. Exiting.")
    sys.exit(0)

# ======================================
# Main Download Logic
# ======================================
def main():
    try:
        logger.info("🔴 Entering main download logic... 🚀")

        target_usb = platform_config["target_usb"]
        download_date = datetime.now().strftime("%Y-%m-%d")
        download_path = os.path.join(target_usb, download_date)

        if not os.path.exists(target_usb):
            logger.error(f"Error: USB drive {target_usb} is not mounted.")
            sys.exit(1)

        if not os.path.exists(download_path):
            logger.warning(f"Download path {download_path} does not exist. Creating it now.")
            try:
                os.makedirs(download_path, exist_ok=True)
            except PermissionError:
                logger.error(f"Permission denied: Unable to create {download_path}")
                sys.exit(1)

        elif not os.access(download_path, os.W_OK):
            logger.error(f"Error: No write permission to {download_path}.")
            sys.exit(1)

        logger.info(f"Download directory confirmed: {download_path}")

        if len(sys.argv) < 2:
            logger.error("The URL is missing. Please provide a valid URL as a command-line argument.")
            sys.exit(1)

        url = sys.argv[1].strip()

        found_file, found_data = find_url_json(url, metadata_dir="./metadata")

        if found_file:
            logger.info(f"Metadata already exists for URL: {url}. Skipping download.")
            print(f"Metadata found in: {found_file}")
            return

        logger.warning("❌ No metadata found for URL. Proceeding with download...")

        params = {
            "download_path": download_path,
            "cookie_path": platform_config.get("cookie_path"),
            "url": url,
            **platform_config.get("watermark_config", {}),
            "task": task,
        }

        logger.debug(f"Initial params: {params}")

        try:
            downloader_result = downloader5.download_video(params)
            if not downloader_result:
                logger.warning(f"No video to download for URL: {url}. Skipping.")
                return
        except Exception as e:
            logger.error(f"Error downloading video for URL: {url}: {e}")
            return

        function_calls = [
            downloader5.mask_metadata,
            downloader5.create_original_filename,
            utilities1.store_params_as_json,
            copy_metadata_to_backup,
            extend_metadata_with_task_output,
        ]

        for func in function_calls:
            logger.info(f"➡️ Calling: {func.__name__}")
            try:
                logger.debug(f"Before {func.__name__}, params: {params}")
                result = func(params)
                if result:
                    params.update(result)
                    logger.debug(f"After {func.__name__}, updated params: {params}")
            except Exception as e:
                logger.error(f"Error in {func.__name__}: {e}")
                logger.debug(traceback.format_exc())

        original_filename = params.get("original_filename")
        if original_filename:
            logger.info(f"Downloaded file: {original_filename}")
            print(original_filename)  # ✅ <-- This is what Perl captures

            metadata_path = params.get("full_metadata_json")
            if metadata_path:
                add_default_tasks_to_metadata(metadata_path)
                update_task_output_path(metadata_path, task, original_filename)
            else:
                logger.warning("No metadata path found — skipping task injection.")
        else:
            logger.warning("No filename produced after download.")

    except Exception as e:
        logger.error(f"Unexpected error in main(): {e}")
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()

