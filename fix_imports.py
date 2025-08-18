#!/usr/bin/env python3
"""Script to fix relative imports to absolute imports in the codebase."""

import os
import re
import sys

def fix_imports_in_file(file_path):
    """Fix imports in a single file."""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    original_content = content
    
    # Determine if this is an API or SMTP file
    if '/back/api/' in file_path:
        prefix = 'back.api'
    elif '/back/smtp/' in file_path:
        prefix = 'back.smtp'
    else:
        return False
    
    # Fix various import patterns
    patterns = [
        # from config import -> from back.api.config import
        (r'from config import', f'from {prefix}.config import'),
        # from database import -> from back.api.database import  
        (r'from database import', f'from {prefix}.database import'),
        # from database.models import -> from back.api.database.models import
        (r'from database\.([a-zA-Z_]+) import', f'from {prefix}.database.\\1 import'),
        # from utils import -> from back.api.utils import
        (r'from utils import', f'from {prefix}.utils import'),
        # from utils.xyz import -> from back.api.utils.xyz import
        (r'from utils\.([a-zA-Z_]+) import', f'from {prefix}.utils.\\1 import'),
        # from controllers import -> from back.api.controllers import
        (r'from controllers import', f'from {prefix}.controllers import'),
        # from controllers.xyz import -> from back.api.controllers.xyz import  
        (r'from controllers\.([a-zA-Z_]+) import', f'from {prefix}.controllers.\\1 import'),
        # from views import -> from back.api.views import
        (r'from views import', f'from {prefix}.views import'),
        # from views.xyz import -> from back.api.views.xyz import
        (r'from views\.([a-zA-Z_]+) import', f'from {prefix}.views.\\1 import'),
        # from forwarding import -> from back.smtp.forwarding import
        (r'from forwarding import', f'from {prefix}.forwarding import'),
        # from forwarding.xyz import -> from back.smtp.forwarding.xyz import
        (r'from forwarding\.([a-zA-Z_]+) import', f'from {prefix}.forwarding.\\1 import'),
        # import forwarding.xyz -> import back.smtp.forwarding.xyz
        (r'import forwarding\.([a-zA-Z_]+)', f'import {prefix}.forwarding.\\1'),
        # from smtp_server import -> from back.smtp.smtp_server import
        (r'from smtp_server import', f'from {prefix}.smtp_server import'),
        # from smtp_server.xyz import -> from back.smtp.smtp_server.xyz import
        (r'from smtp_server\.([a-zA-Z_]+) import', f'from {prefix}.smtp_server.\\1 import'),
    ]
    
    # Apply each pattern
    for pattern, replacement in patterns:
        content = re.sub(pattern, replacement, content)
    
    # Write back if changed
    if content != original_content:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Fixed imports in: {file_path}")
        return True
    return False

def main():
    """Main function to process all Python files."""
    back_dir = 'back'
    if not os.path.exists(back_dir):
        print("Error: 'back' directory not found!")
        sys.exit(1)
    
    files_changed = 0
    
    for root, dirs, files in os.walk(back_dir):
        for file in files:
            if file.endswith('.py'):
                file_path = os.path.join(root, file)
                if fix_imports_in_file(file_path):
                    files_changed += 1
    
    print(f"\nProcessed {files_changed} files with import fixes.")

if __name__ == "__main__":
    main()