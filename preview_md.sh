#!/bin/bash

# Script to generate a markdown gallery of all theme screenshots

output_file="THEME_GALLERY.md"
assets_dir="assets/builds"

# Start the markdown file
cat > "$output_file" << 'EOF'
# WL Theme Collection

A collection of 50 cool, stylish, and retro VS Code themes.

## Theme Gallery

EOF

# Find all images that don't contain "icon" in the filename
find "$assets_dir" -type f \( -name "*.png" -o -name "*.jpg" -o -name "*.jpeg" \) ! -name "*icon*" | sort | while read -r image_path; do
    # Get just the filename without path
    filename=$(basename "$image_path")
    
    # Get theme name (remove extension)
    theme_name="${filename%.*}"
    
    # Convert snake_case to Title Case for display
    display_name=$(echo "$theme_name" | sed 's/_/ /g' | sed 's/\b\(.\)/\u\1/g')
    
    # Add WL- prefix if not already there
    if [[ ! "$display_name" =~ ^WL- ]]; then
        display_name="WL-$display_name"
    fi
    
    # Write to markdown file
    echo "### $display_name" >> "$output_file"
    echo "" >> "$output_file"
    echo "![$display_name]($image_path)" >> "$output_file"
    echo "" >> "$output_file"
    echo "---" >> "$output_file"
    echo "" >> "$output_file"
done

# Add footer
cat >> "$output_file" << 'EOF'
## Installation

1. Open VS Code
2. Go to Extensions (Ctrl+Shift+X)
3. Search for the theme name
4. Click Install

## License

MIT License - See LICENSE file for details
EOF

echo "Theme gallery generated in $output_file"