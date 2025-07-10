#!/usr/bin/env python3
"""
Test the updated Gemini job resolver with improved KeyVault handling
"""

import sys
sys.path.append('.')

try:
    from gemini_job_resolver import GeminiJobResolver
    print("✅ Successfully imported GeminiJobResolver")
    
    # Test initialization
    print("Testing initialization...")
    resolver = GeminiJobResolver()
    print("✅ Successfully initialized GeminiJobResolver")
    print(f"Model: {resolver.model}")
    
    # Test that it works for the WEIDER case
    import pandas as pd
    comparison_df = pd.read_csv('comprehensive_comparison_dataframe.csv')
    
    book_id = 'digibok_2007031501007_0468'
    name_azure = 'WEIDER, Aasta'
    name_monkey = 'WEIDER, Aasta'
    
    azure_jobs, monkey_jobs = resolver.extract_job_titles_for_record(comparison_df, book_id, name_azure, name_monkey)
    print(f"✅ Job extraction working: Azure={azure_jobs}, Monkey={monkey_jobs}")
    
    print("\n🎉 All tests passed! The KeyVault integration is working correctly.")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
