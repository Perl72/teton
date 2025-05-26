import sys
import os
import json
import logging
import traceback
import subprocess
from datetime import datetime
import math
import yaml
from moviepy.editor import VideoFileClip

# Add lib path to sys.path
current_dir = os.path.dirname(os.path.abspath(__file__))
lib_path = os.path.join(current_dir, "../lib")
sys.path.append(lib_path)

# Import utilities
from teton_lib import initialize_logging, load_config, load_app_config
from tasks_lib import find_url_json
# Map tasks to their respective scripts
TASK_DISPATCH = {
    "perform_download": "bin/call_download.py",
    "apply_watermark": "bin/call_watermark.py",
    "make_clips": "bin/call_clips.py",
    "extract_audio": "bin/call_extract_audio.py",
    "generate_captions": "bin/call_captions.py",
    "post_process": "bin/call_screenshots.py"
}

def find_clips_file(to_process_path, clip_file_path, logger):
    """
    Use the specified clip_file_path:
    - If it exists, return it.
    - If not, generate default 1-minute segments at that path.
    """
    if os.path.exists(clip_file_path):
        logger.info(f"✅ Using existing clips file: {clip_file_path}")
        return clip_file_path

    logger.warning(f"⚠️ Clips file not found: {clip_file_path}")
    logger.info(f"🛠 Generating default 1-minute chunks to: {clip_file_path}")
    generate_default_clips_yaml(to_process_path, clip_file_path)
    return clip_file_path


def generate_default_clips_yaml(video_path, output_yaml_path, chunk_duration=60):
    """
    Creates a default clips YAML file that divides the video into fixed-length chunks.
    """
    video = VideoFileClip(video_path)
    total_duration = math.floor(video.duration)
    chunks = []

    for i in range(0, total_duration, chunk_duration):
        end = min(i + chunk_duration, total_duration)
        chunks.append({"start": i, "end": end})

    default_clips = {"auto_chunks": chunks}

    with open(output_yaml_path, "w") as f:
        yaml.dump(default_clips, f)

    return output_yaml_path

def add_clip_data_to_metadata(metadata_path, clips_file_path):
    """
    Updates the metadata JSON with a reference to the clips YAML used.
    Adds a 'clips_metadata' section if not already present.
    """
    if not os.path.exists(metadata_path):
        logging.error(f"Cannot update metadata. File not found: {metadata_path}")
        return False

    try:
        with open(metadata_path, "r") as f:
            data = json.load(f)

        data.setdefault("clips_metadata", {})
        data["clips_metadata"]["clips_file"] = clips_file_path
        data["clips_metadata"]["updated_at"] = datetime.now().isoformat()

        with open(metadata_path, "w") as f:
            json.dump(data, f, indent=2)

        logging.info(f"📝 Metadata updated with clips_file: {clips_file_path}")
        return True

    except Exception as e:
        logging.error(f"Failed to update metadata: {e}")
        return False

def execute_tasks(task_config, url, to_process, dry_run=False, clips_file=None):
    """Run appropriate script for each task based on its config."""
    for task, status in task_config.items():
        script = TASK_DISPATCH.get(task)

        if not script:
            logging.warning(f"No script defined for task: {task}")
            continue

        if task == "perform_download":
            args = [url]
        elif task == "make_clips" and clips_file:
            args = [to_process, clips_file]
        else:
            args = [to_process]

        if status is True:
            logging.info(f"🚀 Running task: {task} -> {script}")
            if dry_run:
                logging.info(f"[Dry Run] Would run: python {script} {' '.join(args)}")
            else:
                subprocess.run(["python", script] + args)
        elif isinstance(status, str):
            logging.info(f"✅ Task already completed: {task} @ {status}")
        else:
            logging.info(f"⏭️  Skipping task: {task}")

def run_my_existing_downloader(url, logger):
    logger.info(f"📥 Initiating download for: {url}")
    result = subprocess.run(
        ["python", "bin/call_download.py", url],
        capture_output=True,
        text=True
    )
    if result.returncode != 0:
        logger.error(f"Download script failed:\n{result.stderr}")
    else:
        logger.info(f"Download stdout:\n{result.stdout}")

def main():
    try:
        dry_run = "--dry-run" in sys.argv
        url_args = [arg for arg in sys.argv[1:] if not arg.startswith("--")]

        if len(url_args) < 1:
            print("Usage: python call_router.py <url> [--dry-run]")
            sys.exit(1)

        url = url_args[0].strip()

        # Load logger and app config early
        logger = initialize_logging()
        app_config = load_app_config()

        config = load_config()
        logger.info("🔁 Task Router Started")

        # Look for metadata
        found_file, found_data = find_url_json(url, metadata_dir="./metadata")
        perform_download_done = (
            found_data.get("default_tasks", {}).get("perform_download")
            if found_data else None
        )

        if not found_file or not perform_download_done:
            logger.info("📥 No completed download or metadata found — running downloader...")
            run_my_existing_downloader(url, logger)
            found_file, found_data = find_url_json(url, metadata_dir="./metadata")
            perform_download_done = (
                found_data.get("default_tasks", {}).get("perform_download")
                if found_data else None
            )

        if not found_data:
            logger.error("❌ No metadata found after attempted download.")
            return

        print(f"Found in: {found_file}")
        print(json.dumps(found_data, indent=2))

        if isinstance(perform_download_done, str):
            to_process = perform_download_done
        else:
            logger.error("Download task not completed and no output path recorded.")
            return

        if not os.path.exists(to_process):
            logger.error(f"Input file does not exist: {to_process}")
            return

        default_tasks = found_data.get("default_tasks", {})
        if not default_tasks:
            logger.warning("No 'default_tasks' section found in metadata.")
            return

        clip_file_path = app_config.get("clips", {}).get("default_path")

        if not clip_file_path:
            logger.error("❌ No clips file path configured in app_config['clips']['default_path'].")
            return

        clips_file = find_clips_file(to_process, clip_file_path, logger)

        metadata_path = found_data.get("metadata_path") or found_file
        if metadata_path:
            add_clip_data_to_metadata(metadata_path, clips_file)

        logger.info(f"🛠 Tasks to evaluate: {list(default_tasks.keys())}")
        execute_tasks(default_tasks, url, to_process, dry_run, clips_file)

    except Exception as e:
        logging.error(f"Unexpected error in main(): {e}")
        traceback.print_exc()

if __name__ == "__main__":
    main()

