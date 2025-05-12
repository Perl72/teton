# t/watermark_harness.py

import os
import subprocess
import sys

def ok(condition, number, description):
    if condition:
        print(f"ok {number} - ✅ {description}")
    else:
        print(f"not ok {number} - ❌ {description}")
        sys.exit(1)

def run():
    test_num = 1

    input_path = "test_assets/sample_input.mp4"
    script_path = "bin/call_watermark.py"
    output_path = input_path.replace(".mp4", "_watermarked.mp4")

    ok(os.path.exists(input_path), test_num, "Input video exists")
    test_num += 1

    result = subprocess.run(
        ["python", script_path, input_path],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
    )
    ok(result.returncode == 0, test_num, "Watermarking script completed")
    test_num += 1

    ok(os.path.exists(output_path), test_num, "Watermarked file created")
    test_num += 1

    size = os.path.getsize(output_path)
    ok(size > 100_000, test_num, f"Watermarked file is large enough ({size} bytes)")
    test_num += 1

    print(f"1..{test_num - 1}")

if __name__ == "__main__":
    run()
