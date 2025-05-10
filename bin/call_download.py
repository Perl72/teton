
import sys
import os
import logging
import traceback
import platform
from datetime import datetime

# Add lib path to sys.path
current_dir = os.path.dirname(os.path.abspath(__file__))
lib_path = os.path.join(current_dir, "../lib/python_utils")
sys.path.append(lib_path)

# Unified import from utilities1 as ut1
import utilities1 as ut1

# ======================================
# Task Definition
# ======================================
task = "perform_download"

# ======================================
# Init & Config
# ======================================
logger = ut1.initialize_logging()
platform_config = ut1.load_config()

logger.info("🔴 Entering main routine... 🚀")
app_config = {"default_tasks": platform_config.get("default_tasks", {})}

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

        params = {
            "download_path": download_path,
            "cookie_path": platform_config.get("cookie_path"),
            "url": url,
            "task": task,
        }

        if "facebook.com" in url:
            logger.info("➡️ Facebook video detected — using cookie-authenticated download.")
            if not os.path.exists(params["cookie_path"]):
                logger.error(f"Missing Facebook cookie file: {params['cookie_path']}")
                sys.exit(1)

        # Pre-download: create filename and fetch metadata
        metadata = ut1.mask_metadata(params)
        if metadata:
            params.update(metadata)

        filename_info = ut1.create_original_filename(params)
        if filename_info:
            params.update(filename_info)

        # Download video
        downloader_result = ut1.download_video(params)
        if not downloader_result:
            logger.warning(f"No video to download for URL: {url}. Skipping.")
            return

        # Save metadata JSON
        result = ut1.store_params_as_json(params)
        if result:
            params.update(result)

        logger.info(f"✅ Downloaded and saved: {params.get('original_filename')}")
        print(params.get("original_filename"))

    except Exception as e:
        logger.error(f"Unexpected error in main(): {e}")
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
