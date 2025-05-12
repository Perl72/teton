# t/test_pipeline_direct.py

import os
import sys
import json
import time
from lib import teton_lib as tu
from lib import add_watermark
from bin import call_download, call_watermark


def ok(condition, number, description):
    if condition:
        print(f"ok {number} - ✅ {description}")
    else:
        print(f"not ok {number} - ❌ {description}")
        sys.exit(1)

def run():
    test_num = 1
    test_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"

    # Load configs
    platform_config = tu.load_config()
    app_config = tu.load_app_config()

    ok(platform_config is not None, test_num, "Loaded platform config")
    test_num += 1
    ok(app_config is not None, test_num, "Loaded app config")
    test_num += 1

    # Prepare params dict
    params = {
        "url": test_url,
        "download_path": platform_config["target_usb"],
        "video_download": {
            "cookie_path": platform_config["cookie_path"],
            "format": "bestvideo+bestaudio/best",
            "noplaylist": True
        },
        "app_config": app_config
    }

    # Download
    dl_result = call_download.download_video(params)
    ok(dl_result is not None, test_num, "Video downloaded")
    test_num += 1

    input_file = dl_result.get("to_process")
    ok(input_file and os.path.exists(input_file), test_num, "Downloaded file exists")
    test_num += 1

    # Watermark
    params["input_video_path"] = input_file
    params["original_filename"] = input_file
    wm_result = call_watermark.add_watermark(params)
    ok(wm_result is not None, test_num, "Watermark applied")
    test_num += 1

    output_file = wm_result.get("to_process")
    ok(output_file and os.path.exists(output_file), test_num, "Watermarked file exists")
    test_num += 1

    size = os.path.getsize(output_file)
    ok(size > 100_000, test_num, f"Watermarked file is large enough ({size} bytes)")
    test_num += 1

    print(f"1..{test_num - 1}")

if __name__ == "__main__":
    run()
