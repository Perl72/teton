# call_transcribe_all.py

import sys
import json
from lib.python_utils.utilities3 import (
    transcribe_full_video,
    transcribe_video_by_minute,
    load_config
)

if len(sys.argv) < 2:
    print("Usage: python call_transcribe_all.py <input_video>")
    sys.exit(1)

input_video = sys.argv[1]
config = load_config()

# === Full Video Transcription ===
print("\n=== Transcribing full video ===")
full_transcript = transcribe_full_video(input_video)
full_outfile = input_video.replace(".mp4", ".full.txt")
with open(full_outfile, "w") as f:
    f.write(full_transcript)
print(f"📝 Full transcript saved to {full_outfile}")

# === Minute-by-Minute Transcription ===
print("\n=== Transcribing by minute ===")
minute_transcript = transcribe_video_by_minute(input_video)
minute_outfile = input_video.replace(".mp4", ".minute.json")
with open(minute_outfile, "w") as f:
    json.dump(minute_transcript, f, indent=2)
print(f"📝 Minute transcript saved to {minute_outfile}")
