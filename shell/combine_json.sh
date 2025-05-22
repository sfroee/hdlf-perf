#!/bin/bash

# Usage: ./combine_json.sh <input_directory> <output_file>
# Example: ./combine_json.sh . combined_results.json

# Check if parameters are provided
if [ $# -lt 2 ]; then
    echo "Usage: $0 <input_directory> <output_file>"
    exit 1
fi

INPUT_DIR="$1"
OUTPUT_FILE="$2"

# Check if input directory exists
if [ ! -d "$INPUT_DIR" ]; then
    echo "Error: Input directory does not exist"
    exit 1
fi

# Create the output file with opening bracket
echo "[" > "$OUTPUT_FILE"

# Find all JSON files and process them
first_file=true
for json_file in "$INPUT_DIR"/*.json; do
    # Skip if no files found
    [ -e "$json_file" ] || continue
    
    # Add comma separator if not the first file
    if [ "$first_file" = true ]; then
        first_file=false
    else
        # Add a comma to separate entries
        echo "," >> "$OUTPUT_FILE"
    fi
    
    # Preserve the file's indentation but remove the trailing newline
    cat "$json_file" | sed -e 's/^//' >> "$OUTPUT_FILE"
done

# Close the JSON array
echo "" >> "$OUTPUT_FILE"
echo "]" >> "$OUTPUT_FILE"

echo "Successfully combined JSON files from $INPUT_DIR into $OUTPUT_FILE"
