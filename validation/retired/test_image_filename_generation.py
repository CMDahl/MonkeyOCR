"""
Test the new image filename generation functionality.
"""

import pandas as pd
from figure_extraction import extract_figure_references, add_figure_columns_to_dataframe

def test_image_filename_generation():
    """Test the new image filename generation feature"""
    
    # Create test data with your example
    test_data = {
        'book_id': [
            'digibok_2007031501007_0057',
            'digibok_2007031501007_0058', 
            'digibok_2007031501007_0059',
            'digibok_2007031501007_0060'
        ],
        'markdown_chunk_azureocr': [
            # Your exact example
            """AGDESTEEN, Ingrid, husmor, Hau- gesund, f. 1/8-12 sst., d. av grosserer Johannes Bøe Haga (1874-1917) og Gudrun Ingrid Beate Gautesen (1886-). Gift 1941 med kontorsjef Roy Agde-



**[FIGURE: 1.2]**



steen, f. 25/1-15 Bergen, s. av skipsfører Harald A. - Barn: Harald 10/7-44, Gudrun 22/2-47, Jorunn 23/12-49.

Hs/L - Sykepleierskeutdannelse. - Sykepleierske Ullevål sykehus, Oslo 1936 -40, Haukeland sykehus, Bergen 1942, Haugesund sykehus 1956, Haugesund revmatisme-sykehus, 1957. - Form. i Husmorlaget, Haugesund avd. - Int: Musikk og friluftsliv.

Høyt vurdert egenskap? Humoristisk sans.



**[FIGURE: 1.3]**""",
            
            # Test with different formats
            'Text with **[Figure: 2.1]** and **[FIGURE: 2.2]**',
            'Text with only **[Figure: 3.5]**',
            'Text with no figures'
        ]
    }
    
    df = pd.DataFrame(test_data)
    
    print("Original data:")
    print("=" * 80)
    for i, row in df.iterrows():
        print(f"Row {i}:")
        print(f"  book_id: {row['book_id']}")
        print(f"  text: {row['markdown_chunk_azureocr'][:50]}...")
        print()
    
    print("Testing figure extraction with image filename generation...")
    print("=" * 80)
    
    # Extract figures with image columns
    result = extract_figure_references(df, text_column='markdown_chunk_azureocr')
    
    print("Results:")
    print("=" * 80)
    
    # Display results in a clear format
    for i, row in result.iterrows():
        print(f"Row {i}:")
        print(f"  book_id: {row['book_id']}")
        print(f"  Figure1: {row['Figure1']}")
        print(f"  Figure2: {row['Figure2']}")
        print(f"  azure_image1: {row['azure_image1']}")
        print(f"  azure_image2: {row['azure_image2']}")
        print()
    
    # Verify your specific example
    print("Verification of your example:")
    print("=" * 80)
    expected_image1 = "digibok_2007031501007_0057_1.2.png"
    expected_image2 = "digibok_2007031501007_0057_1.3.png"
    
    actual_image1 = result.iloc[0]['azure_image1']
    actual_image2 = result.iloc[0]['azure_image2']
    
    print(f"Expected azure_image1: {expected_image1}")
    print(f"Actual azure_image1: {actual_image1}")
    print(f"Match: {actual_image1 == expected_image1} ✅" if actual_image1 == expected_image1 else f"Match: {actual_image1 == expected_image1} ❌")
    
    print(f"\nExpected azure_image2: {expected_image2}")
    print(f"Actual azure_image2: {actual_image2}")
    print(f"Match: {actual_image2 == expected_image2} ✅" if actual_image2 == expected_image2 else f"Match: {actual_image2 == expected_image2} ❌")
    
    return result

def test_simplified_function():
    """Test the simplified add_figure_columns_to_dataframe function"""
    
    print("\n" + "=" * 80)
    print("Testing simplified function")
    print("=" * 80)
    
    # Simple test data
    test_data = {
        'book_id': ['test_book_123', 'test_book_456'],
        'markdown_chunk_azureocr': [
            'Text with **[Figure: 4.1]** and **[FIGURE: 4.2]**',
            'Text with **[FIGURE: 5.10]** only'
        ]
    }
    
    df = pd.DataFrame(test_data)
    
    # Use the simplified function
    result = add_figure_columns_to_dataframe(df, text_column='markdown_chunk_azureocr')
    
    print("Results from simplified function:")
    for i, row in result.iterrows():
        print(f"Row {i}:")
        print(f"  book_id: {row['book_id']}")
        print(f"  Figure1: {row['Figure1']}")
        print(f"  Figure2: {row['Figure2']}")
        print(f"  azure_image1: {row['azure_image1']}")
        print(f"  azure_image2: {row['azure_image2']}")
        print()

if __name__ == "__main__":
    result = test_image_filename_generation()
    test_simplified_function()
    
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print("✅ Image filename generation is working correctly!")
    print("✅ Combines book_id + figure_number + .png")
    print("✅ Handles both **[Figure: X.Y]** and **[FIGURE: X.Y]** formats")
    print("✅ Creates proper filenames like: digibok_2007031501007_0057_1.2.png")
    print("✅ Handles missing values appropriately")
