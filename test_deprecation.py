#!/usr/bin/env python3
"""Test script to reproduce the Pydantic deprecation warning."""

import sys
import os
import warnings

# Add the back directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'back'))

# Capture warnings to see the deprecation message
warnings.filterwarnings('default', category=DeprecationWarning)

print("Testing Pydantic deprecation warning...")
print("=" * 50)

try:
    # Import the Settings class that uses deprecated Field syntax
    from core.config import Settings
    
    print("Importing Settings class...")
    
    # Create an instance to trigger the deprecation warning
    settings = Settings()
    
    print("Settings instance created successfully")
    print(f"Environment: {settings.ENVIRONMENT}")
    print(f"Secret Key length: {len(settings.SECRET_KEY)}")
    
except Exception as e:
    print(f"Error occurred: {e}")
    import traceback
    traceback.print_exc()

print("=" * 50)
print("Test completed.")