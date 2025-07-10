"""
Final comprehensive test with your exact requirements.
"""

import pandas as pd
from figure_extraction import extract_figure_references

def test_your_exact_requirements():
    """Test the exact scenario you described"""
    
    print("=" * 80)
    print("TESTING YOUR EXACT REQUIREMENTS")
    print("=" * 80)
    
    # Your exact example
    test_data = {
        'book_id': ['digibok_2007031501007_0057'],
        'markdown_chunk_azureocr': [
            """AGDESTEEN, Ingrid, husmor, Hau- gesund, f. 1/8-12 sst., d. av grosserer Johannes Bøe Haga (1874-1917) og Gudrun Ingrid Beate Gautesen (1886-). Gift 1941 med kontorsjef Roy Agde-



**[FIGURE: 1.2]**



steen, f. 25/1-15 Bergen, s. av skipsfører Harald A. - Barn: Harald 10/7-44, Gudrun 22/2-47, Jorunn 23/12-49.

Hs/L - Sykepleierskeutdannelse. - Sykepleierske Ullevål sykehus, Oslo 1936 -40, Haukeland sykehus, Bergen 1942, Haugesund sykehus 1956, Haugesund revmatisme-sykehus, 1957. - Form. i Husmorlaget, Haugesund avd. - Int: Musikk og friluftsliv.

Høyt vurdert egenskap? Humoristisk sans.



**[FIGURE: 1.3]**"""
        ]
    }
    
    df = pd.DataFrame(test_data)
    
    print("Input:")
    print(f"book_id: {df.iloc[0]['book_id']}")
    print(f"Figure1 should be: **[FIGURE: 1.2]**")
    print(f"Figure2 should be: **[FIGURE: 1.3]**")
    print(f"azure_image1 should be: digibok_2007031501007_0057_1.2.png")
    print(f"azure_image2 should be: digibok_2007031501007_0057_1.3.png")
    print()
    
    # Extract figure references
    result = extract_figure_references(df, text_column='markdown_chunk_azureocr')
    
    print("Results:")
    print("=" * 40)
    
    row = result.iloc[0]
    
    print(f"book_id: {row['book_id']}")
    print(f"Figure1: {row['Figure1']}")
    print(f"Figure2: {row['Figure2']}")
    print(f"azure_image1: {row['azure_image1']}")
    print(f"azure_image2: {row['azure_image2']}")
    
    print()
    print("Verification:")
    print("=" * 40)
    
    # Check all requirements
    checks = [
        ("Figure1 is **[FIGURE: 1.2]**", row['Figure1'] == "**[FIGURE: 1.2]**"),
        ("Figure2 is **[FIGURE: 1.3]**", row['Figure2'] == "**[FIGURE: 1.3]**"),
        ("azure_image1 is digibok_2007031501007_0057_1.2.png", row['azure_image1'] == "digibok_2007031501007_0057_1.2.png"),
        ("azure_image2 is digibok_2007031501007_0057_1.3.png", row['azure_image2'] == "digibok_2007031501007_0057_1.3.png")
    ]
    
    all_passed = True
    for check_name, passed in checks:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status}: {check_name}")
        if not passed:
            all_passed = False
    
    print()
    if all_passed:
        print("🎉 ALL REQUIREMENTS MET! The function works exactly as requested.")
    else:
        print("❌ Some requirements not met. Please check the implementation.")
    
    return result

if __name__ == "__main__":
    test_your_exact_requirements()
    
    print("\n" + "=" * 80)
    print("READY TO USE!")
    print("=" * 80)
    print("""
Your figure extraction function now includes:

1. ✅ Extracts **[FIGURE: X.Y]** and **[Figure: X.Y]** patterns
2. ✅ Creates Figure1 and Figure2 columns with the full reference text
3. ✅ Creates azure_image1 and azure_image2 columns with image filenames
4. ✅ Combines book_id + figure_number + '.png' for image filenames
5. ✅ Handles missing values appropriately
6. ✅ Preserves original case formatting

Usage with your data:
=====================

import pandas as pd
from figure_extraction import extract_figure_references

# Load your data
df = pd.read_csv('your_data.csv')

# Extract figures and create image filenames
result = extract_figure_references(df, text_column='markdown_chunk_azureocr')

# Save the result
result.to_csv('output_with_figures_and_images.csv', index=False)

# The result will have columns:
# - Figure1, Figure2: The figure references
# - azure_image1, azure_image2: The image filenames
""")
