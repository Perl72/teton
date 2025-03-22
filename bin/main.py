import sys
import os
import json
import logging
import traceback
import platform
from datetime import datetime

def load_config(config_path):

    """Load configuration based on the operating system."""
    current_dir = os.path.dirname(os.path.abspath(__file__))
    config_path = os.path.join(current_dir, "../conf/config.json")

    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Configuration file not found at {config_path}")

    with open(config_path, "r") as file:
        config = json.load(file)

    os_name = platform.system()
    if os_name not in config:
        raise ValueError(f"Unsupported platform: {os_name}")

    return config[os_name]

def init_logging(logging_config):
    """Set up logging based on the configuration."""
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)

    if logging_config.get("log_to_file"):
        log_file = os.path.expanduser(logging_config["log_filename"])
        log_dir = os.path.dirname(log_file)

        if not os.path.exists(log_dir):
            os.makedirs(log_dir, exist_ok=True)

        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging_config.get("level", "DEBUG"))
        file_formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)

    if logging_config.get("log_to_console"):
        console_handler = logging.StreamHandler(stream=sys.stderr)
        console_handler.setLevel(logging_config.get("console_level", "INFO"))
        console_formatter = logging.Formatter("%(asctime)s - %(message)s")
        console_handler.setFormatter(console_formatter)
        logger.addHandler(console_handler)

    logger.info("Logging initialized.")
    return logger

def find_url_in_clips(url, clips_dir="./clips"):
    """
    Search for a JSON file in the clips directory that contains the given URL.
    :param url: The video URL to search for.
    :param clips_dir: The directory containing clip JSON files.
    :return: The full path to the JSON file if found, else None.
    """
    if not os.path.exists(clips_dir):
        logging.warning(f"Clips directory not found: {clips_dir}")
        return None

    for filename in os.listdir(clips_dir):
        if filename.endswith(".json"):
            json_path = os.path.join(clips_dir, filename)
            try:
                with open(json_path, "r", encoding="utf-8") as file:
                    data = json.load(file)
                    if isinstance(data, dict) and "url" in data and data["url"] == url:
                        logging.info(f"URL found in {filename}")
                        return json_path
            except (json.JSONDecodeError, IOError) as e:
                logging.error(f"Error reading {json_path}: {e}")

    logging.info("URL not found in any JSON file.")
    return None

def execute_tasks(task_config):
    """Execute tasks based on the provided task configuration."""
    task_mapping = {
        "perform_download": lambda: logging.info("Downloading video..."),
        "apply_watermark": lambda: logging.info("Applying watermark..."),
        "make_clips": lambda: logging.info("Making clips..."),
        "extract_audio": lambda: logging.info("Extracting audio..."),
        "generate_captions": lambda: logging.info("Generating captions..."),
    }
    
    for task, setting in task_config.items():
        if setting is True:
            logging.info(f"Executing {task}...")
            task_mapping[task]()
        elif isinstance(setting, str):
            logging.info(f"Executing {task} with output path: {setting}")
            task_mapping[task]()
        else:
            logging.info(f"Skipping {task}.")


def main():
    try:
        config_path = "./conf/template1.json"  # Lexical variable for config file
        platform_config = load_config(config_path)
        logger = init_logging(platform_config["logging"])

        current_dir = os.path.dirname(os.path.abspath(__file__))
        lib_path = os.path.join(current_dir, "../lib/python_utils")
        sys.path.append(lib_path)
        logger.debug(f"Current sys.path: {sys.path}")

        # Set up paths
        target_usb = platform_config["target_usb"]
        download_date = datetime.now().strftime("%Y-%m-%d")
        download_path = os.path.join(target_usb, download_date)

        # Check if the USB is mounted and writable
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

        # Validate URL input
        if len(sys.argv) < 2:
            logger.error("The URL is missing. Please provide a valid URL as a command-line argument.")
            sys.exit(1)

        url = sys.argv[1].strip()

        # Check if URL already exists in clips
        json_path = find_url_in_clips(url)
        if json_path:
            logger.info(f"Found URL in the following file: {json_path}")
            with open(json_path, "r") as file:
                task_config = json.load(file).get("default_tasks", {})
                execute_tasks(task_config)
    
    except Exception as e:
        logger.error("Error during execution: %s", traceback.format_exc())

if __name__ == "__main__":
    main()

