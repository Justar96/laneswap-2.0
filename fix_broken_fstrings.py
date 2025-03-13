#!/usr/bin/env python
"""
Script to fix broken f-strings that were split across multiple lines.

This script finds and fixes f-strings that were incorrectly broken across
multiple lines during previous linting operations.
"""

import os
import re
import sys
from pathlib import Path


def fix_broken_fstrings(content):
    """Fix f-strings that were broken across multiple lines."""
    # Pattern to match broken f-strings
    pattern = r'(f"[^"]*?)(\n\s*?)([^"]*?")'
    
    # Replace broken f-strings with single-line versions
    fixed_content = re.sub(pattern, lambda m: f'{m.group(1)} {m.group(3)}', content)
    
    # Also fix for single quotes
    pattern = r"(f'[^']*?)(\n\s*?)([^']*?')"
    fixed_content = re.sub(pattern, lambda m: f"{m.group(1)} {m.group(3)}", fixed_content)
    
    return fixed_content


def process_file(file_path):
    """Process a single file to fix broken f-strings."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Apply fix
        fixed_content = fix_broken_fstrings(content)
        
        # Only write if changes were made
        if fixed_content != content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(fixed_content)
            print(f"Fixed broken f-strings in {file_path}")
            return True
        else:
            return False
    except Exception as e:
        print(f"Error processing {file_path}: {e}")
        return False


def process_directory(directory, extensions=None):
    """Process all files in a directory recursively."""
    if extensions is None:
        extensions = ['.py']
    
    fixed_files = 0
    total_files = 0
    
    for root, _, files in os.walk(directory):
        for file in files:
            if any(file.endswith(ext) for ext in extensions):
                file_path = os.path.join(root, file)
                total_files += 1
                if process_file(file_path):
                    fixed_files += 1
    
    print(f"Fixed broken f-strings in {fixed_files} out of {total_files} files.")
    return fixed_files, total_files


def main():
    """Main function to run the script."""
    if len(sys.argv) > 1:
        directory = sys.argv[1]
    else:
        directory = '.'
    
    print(f"Fixing broken f-strings in {directory}...")
    fixed_files, total_files = process_directory(directory)
    
    if fixed_files > 0:
        print(f"Successfully fixed broken f-strings in {fixed_files} files.")
    else:
        print("No broken f-strings found.")


if __name__ == "__main__":
    main() 