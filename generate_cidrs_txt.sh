#!/bin/bash

# Generate cidrs.txt from cidrs.yaml
# This script converts a YAML file with grouped CIDRs into a simple newline-separated list

set -euo pipefail

YAML_FILE="${1:-cidrs.yaml}"
OUTPUT_FILE="${2:-cidrs.txt}"

# Check if input file exists
if [[ ! -f "$YAML_FILE" ]]; then
    echo "Error: YAML file '$YAML_FILE' not found" >&2
    exit 1
fi

# Check if yq is installed
if ! command -v yq &> /dev/null; then
    echo "Error: yq is required but not installed" >&2
    echo "Install with: brew install yq" >&2
    exit 1
fi

# Generate the cidrs.txt file
echo "Generating $OUTPUT_FILE from $YAML_FILE..."

# Create temporary file
TEMP_FILE=$(mktemp)
trap 'rm -f "$TEMP_FILE"' EXIT

# Extract user_devices CIDRs
yq eval '.user_devices[]' "$YAML_FILE" >> "$TEMP_FILE"

# Move to final location
mv "$TEMP_FILE" "$OUTPUT_FILE"

echo "Successfully generated $OUTPUT_FILE"
echo "Contents:"
cat "$OUTPUT_FILE"
