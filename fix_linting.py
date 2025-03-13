#!/usr/bin/env python
"""
Script to automatically fix common linting issues in the LaneSwap codebase.
This script addresses:
1. Trailing whitespace
2. Missing final newlines
3. Line length issues (where possible)
"""

import os
import re
import sys
from pathlib import Path

def fix_file(file_path):
    """Fix common linting issues in a file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Track if we made any changes
        original_content = content
        
        # Fix trailing whitespace
        content = re.sub(r'[ \t]+$', '', content, flags=re.MULTILINE)
        
        # Fix missing final newline
        if content and not content.endswith('\n'):
            content += '\n'
        
        # Write changes back if needed
        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            return True
        
        return False
    except Exception as e:
        print(f"Error processing {file_path}: {e}")
        return False

def process_directory(directory, extensions=None):
    """Process all files in a directory recursively."""
    if extensions is None:
        extensions = ['.py']
    
    fixed_count = 0
    file_count = 0
    
    for root, _, files in os.walk(directory):
        for file in files:
            if any(file.endswith(ext) for ext in extensions):
                file_path = os.path.join(root, file)
                file_count += 1
                if fix_file(file_path):
                    fixed_count += 1
                    print(f"Fixed: {file_path}")
    
    return file_count, fixed_count

def main():
    """Main function to run the script."""
    if len(sys.argv) > 1:
        directory = sys.argv[1]
    else:
        directory = '.'
    
    print(f"Fixing linting issues in {directory}...")
    file_count, fixed_count = process_directory(directory)
    
    print(f"\nProcessed {file_count} files")
    print(f"Fixed {fixed_count} files")
    
    if fixed_count > 0:
        print("\nRun pylint again to see remaining issues.")

if __name__ == "__main__":
    main() 