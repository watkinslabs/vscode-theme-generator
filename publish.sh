#!/bin/bash

# Build and publish themes from directories

build_dir="build"
publisher_id="watkinslabs"
delay_between_publishes=5
themes_per_batch=5
delay_between_batches=60

# Options
build_only=false
publish_only=false

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --build-only)
            build_only=true
            shift
            ;;
        --publish-only)
            publish_only=true
            shift
            ;;
        *)
            shift
            ;;
    esac
done

# Find all theme directories in build folder
theme_dirs=($(find "$build_dir" -maxdepth 1 -type d -not -path "$build_dir" | sort))
total_themes=${#theme_dirs[@]}

echo "Found $total_themes theme directories"

# Build VSIX files
if [ "$publish_only" = false ]; then
    echo ""
    echo "=== Building VSIX files ==="
    built=0
    
    for theme_dir in "${theme_dirs[@]}"; do
        ((built++))
        theme_name=$(basename "$theme_dir")
        echo "[$built/$total_themes] Building: $theme_name"
        
        cd "$theme_dir"
        if vsce package; then
            echo "✓ Built: $theme_name"
            # Move VSIX to releases folder
            mkdir -p ../../releases
            mv *.vsix ../../releases/
        else
            echo "✗ Failed to build: $theme_name"
        fi
        cd ../..
    done
fi

# Publish themes
if [ "$build_only" = false ]; then
    echo ""
    echo "=== Publishing themes ==="
    published=0
    batch=0
    
    for theme_dir in "${theme_dirs[@]}"; do
        ((published++))
        theme_name=$(basename "$theme_dir")
        echo "[$published/$total_themes] Publishing: $theme_name"
        
        cd "$theme_dir"
        
        # Publish directly from the theme directory
        if vsce publish; then
            echo "✓ Published: $theme_name"
        else
            echo "✗ Failed to publish: $theme_name"
        fi
        
        cd ../..
        
        # Batch delay logic
        if (( published % themes_per_batch == 0 )) && (( published < total_themes )); then
            ((batch++))
            echo "Completed batch $batch. Waiting $delay_between_batches seconds..."
            sleep $delay_between_batches
        else
            sleep $delay_between_publishes
        fi
    done
fi

echo ""
echo "Complete!"