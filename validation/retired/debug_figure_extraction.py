"""
Test script to debug the figure extraction issue.
"""

import pandas as pd
import re
from figure_extraction import extract_figure_references

# Test with the problematic text
test_text = """AGDESTEEN, Ingrid, husmor, Hau- gesund, f. 1/8-12 sst., d. av grosserer Johannes Bøe Haga (1874-1917) og Gudrun Ingrid Beate Gautesen (1886-). Gift 1941 med kontorsjef Roy Agde-



**[FIGURE: 1.2]**



steen, f. 25/1-15 Bergen, s. av skipsfører Harald A. - Barn: Harald 10/7-44, Gudrun 22/2-47, Jorunn 23/12-49.

Hs/L - Sykepleierskeutdannelse. - Sykepleierske Ullevål sykehus, Oslo 1936 -40, Haukeland sykehus, Bergen 1942, Haugesund sykehus 1956, Haugesund revmatisme-sykehus, 1957. - Form. i Husmorlaget, Haugesund avd. - Int: Musikk og friluftsliv.

Høyt vurdert egenskap? Humoristisk sans.



**[FIGURE: 1.3]**"""

def test_current_pattern():
    """Test the current regex pattern"""
    print("Testing current pattern...")
    
    # Current pattern from the script
    current_pattern = r'\*\*\[Figure:\s*(\d+\.\d+)\]\*\*'
    
    matches = re.findall(current_pattern, test_text)
    print(f"Current pattern: {current_pattern}")
    print(f"Matches found: {matches}")
    print(f"Number of matches: {len(matches)}")
    
    # Test case-insensitive pattern
    print("\nTesting case-insensitive pattern...")
    case_insensitive_pattern = r'\*\*\[Figure:\s*(\d+\.\d+)\]\*\*'
    matches_ci = re.findall(case_insensitive_pattern, test_text, re.IGNORECASE)
    print(f"Case-insensitive matches: {matches_ci}")
    print(f"Number of matches: {len(matches_ci)}")
    
    # Test with FIGURE in caps
    print("\nTesting with FIGURE pattern...")
    caps_pattern = r'\*\*\[FIGURE:\s*(\d+\.\d+)\]\*\*'
    matches_caps = re.findall(caps_pattern, test_text)
    print(f"FIGURE pattern matches: {matches_caps}")
    print(f"Number of matches: {len(matches_caps)}")
    
    # Test with flexible case pattern
    print("\nTesting flexible case pattern...")
    flexible_pattern = r'\*\*\[(?:Figure|FIGURE):\s*(\d+\.\d+)\]\*\*'
    matches_flex = re.findall(flexible_pattern, test_text)
    print(f"Flexible pattern matches: {matches_flex}")
    print(f"Number of matches: {len(matches_flex)}")

def test_with_dataframe():
    """Test with actual DataFrame"""
    print("\n" + "="*50)
    print("Testing with DataFrame...")
    
    # Create test DataFrame
    df = pd.DataFrame({
        'markdown_chunk_azureocr': [test_text],
        'other_column': ['test']
    })
    
    # Test current function
    result = extract_figure_references(df)
    print("\nResult:")
    print(result[['markdown_chunk_azureocr', 'Figure1', 'Figure2']])

if __name__ == "__main__":
    test_current_pattern()
    test_with_dataframe()
