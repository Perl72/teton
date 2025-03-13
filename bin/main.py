def load_config(config_path):
    """Load configuration from a specified JSON file."""
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Configuration file not found at {config_path}")

    with open(config_path, "r") as file:
        config = json.load(file)

    return config

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

