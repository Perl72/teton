import sys
import os
import json
import traceback
from datetime import datetime
import logging 

# Add lib path to sys.path
current_dir = os.path.dirname(os.path.abspath(__file__))
lib_path = os.path.join(current_dir, "../lib/python_utils")
sys.path.append(lib_path)


# Import utilities
from utilities1 import store_params_as_json
from utilities2 import initialize_logging, load_config, load_app_config
from utilities3 import (
    should_perform_task,
    get_existing_task_output,
    prepare_usb_download_path,
    find_url_json,
    load_config,
    copy_and_extend_metadata
)
import chain_adapters

def main():
    try:
        config = load_config()  # platform config
        logger = initialize_logging()  # must come BEFORE any logger.debug

        # Load app_config and initialize logger
        app_config = load_app_config()
        logger.debug("App config loaded:")
        logger.debug(json.dumps(app_config, indent=2))
        print("App config:")
        print(json.dumps(app_config, indent=2))

        video_download_config = app_config.get("video_download", {})
        logger.debug("Video download config:")
        logger.debug(json.dumps(video_download_config, indent=2))
        print("Video download config:")
        print(json.dumps(video_download_config, indent=2))

        logger.info("=== Task-aware Download Pipeline Started ===")

        # Check if the task is enabled

        task = "perform_download"
        default_tasks = app_config.get("default_tasks", {})
        logger.debug("Default tasks config:")
        logger.debug(json.dumps(default_tasks, indent=2))
        print("Default tasks config:")
        print(json.dumps(default_tasks, indent=2))

        if not should_perform_task(task, default_tasks):
            existing = get_existing_task_output(task, default_tasks)
            if existing:
                logger.info(f"Task '{task}' already completed. Output at: {existing}")
                print(existing)
                return
            else:
                logger.info(f"Task '{task}' is disabled in default_tasks. Skipping.")
                return




        # Import downloader module
        try:
            import downloader5
        except ImportError as e:
            logger.error(f"Failed to import downloader5: {e}")
            sys.exit(1)

        # Validate input
        if len(sys.argv) < 2:
            logger.error("Missing URL. Please provide a URL.")
            sys.exit(1)
        url = sys.argv[1].strip()

        # Check if URL already exists in metadata
        found_file, found_data = find_url_json(url, metadata_dir="./metadata")
        if found_file:
            print(f"Found in: {found_file}")
            print(json.dumps(found_data, indent=2))
            return

        # Determine output path on USB
        download_path = prepare_usb_download_path(config, logger)

        # Build shared param dictionary
        params = {
            "download_path": download_path,
            "url": url,
            "config": config,
            "default_tasks": default_tasks,  # ✅ correct way
            **config.get("video_download", {}),
        }

        # Define pipeline
        function_calls = [
            downloader5.mask_metadata,
            downloader5.create_original_filename,
            downloader5.download_video,
            store_params_as_json,
            copy_and_extend_metadata

        ]

        # Execute pipeline
        for func in function_calls:
            logger.info(f"Calling: {func.__name__}")
            try:
                result = func(params)
                if result:
                    params.update(result)
            except Exception as e:
                logger.error(f"Error in {func.__name__}: {e}")
                logger.debug(traceback.format_exc())

        # Final output
        original_filename = params.get("original_filename")
        if original_filename:
            logger.info(f"Returning original filename: {original_filename}")
            print(original_filename)
        else:
            logger.warning("Download finished, but no filename was produced.")

    except Exception as e:
        print(f"Unexpected error: {e}")
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
