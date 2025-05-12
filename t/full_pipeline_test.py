import os
import subprocess
import sys
import json
import time

# === Path Setup ===
current_dir = os.path.dirname(os.path.abspath(__file__))
lib_path = os.path.join(current_dir, "../lib/python_utils")
sys.path.append(lib_path)


def ok(condition, number, description):
    if condition:
        print(f"ok {number} - ✅ {description}")
    else:
        print(f"not ok {number} - ❌ {description}")
        sys.exit(1)

def run():
    test_num = 1
    test_url = "https://www.facebook.com/share/v/1AHkKEThhd/"  # timmy Argentina
    metadata_dir = "metadata"

    # Step 1: Run dispatch.py with URL
    print("🚀 Running full pipeline test...")
    result = subprocess.run(
        ["python", "dispatch.py", test_url],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    ok(result.returncode == 0, test_num, "dispatch.py completed")
    test_num += 1

    # Step 2: Wait a moment for file sync if needed
    time.sleep(2)

    # Step 3: Find metadata file
    metadata_files = [f for f in os.listdir(metadata_dir) if f.endswith(".json")]
    matching_file = next((f for f in metadata_files if "RickAstley" in f or "dQw4w9WgXcQ" in f), None)
    ok(matching_file, test_num, "Found expected metadata file")
    test_num += 1

    with open(os.path.join(metadata_dir, matching_file)) as f:
        data = json.load(f)

    output_path = data.get("default_tasks", {}).get("apply_watermark")
    ok(output_path and os.path.exists(output_path), test_num, "Watermarked file created")
    test_num += 1

    size = os.path.getsize(output_path)
    ok(size > 100_000, test_num, f"Watermarked file is large enough ({size} bytes)")
    test_num += 1

    print(f"1..{test_num - 1}")  # Perl-style test plan

if __name__ == "__main__":
    run()
