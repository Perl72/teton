#!/bin/bash

echo "Scanning dangling blobs for Python-like content..."
echo ""

# Create output folder
mkdir -p recovered_blobs

# Find all dangling blobs
git fsck --lost-found | grep 'dangling blob' | while read -r _ _ BLOB_HASH; do
    # Dump content temporarily
    CONTENT=$(git show "$BLOB_HASH" 2>/dev/null)

    # Heuristic: does it look like a Python file?
    if echo "$CONTENT" | grep -qE '^(def |class |import )'; then
        FILE="recovered_blobs/$BLOB_HASH.py"
        echo "$CONTENT" > "$FILE"
        echo "Recovered likely Python file: $FILE"
    fi
done

echo ""
echo "Done. Check the 'recovered_blobs/' folder."

