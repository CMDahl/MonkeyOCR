#!/usr/bin/env python3
"""
Test the updated Gemini job resolver with KeyVault integration
"""

import sys
sys.path.append('.')

try:
    from gemini_job_resolver import GeminiJobResolver
    print("✅ Successfully imported GeminiJobResolver")
    
    # Test initialization with KeyVault
    print("Testing KeyVault initialization...")
    resolver = GeminiJobResolver()
    print("✅ Successfully initialized GeminiJobResolver with KeyVault")
    print(f"Model: {resolver.model}")
    
except Exception as e:
    print(f"❌ Error during initialization: {e}")
    import traceback
    traceback.print_exc()
