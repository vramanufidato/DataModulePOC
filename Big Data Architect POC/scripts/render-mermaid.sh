#!/usr/bin/env bash
set -euo pipefail

DIAGRAMS_DIR="diagrams"
OUTPUT_DIR="diagrams/rendered"
VALIDATE_ONLY="${1:-}"

mkdir -p "$OUTPUT_DIR"

for mmd in "$DIAGRAMS_DIR"/*.mmd; do
  name=$(basename "$mmd" .mmd)
  if [[ "$VALIDATE_ONLY" == "--validate-only" ]]; then
    echo "Validating $name..."
    mmdc -i "$mmd" -o /dev/null --quiet
  else
    echo "Rendering $name..."
    mmdc -i "$mmd" -o "$OUTPUT_DIR/$name.svg" --quiet
    mmdc -i "$mmd" -o "$OUTPUT_DIR/$name.png" --quiet -b white
  fi
done
echo "Done."
