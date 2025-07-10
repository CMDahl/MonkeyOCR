"""
Simple Job Comparison Example

This script creates a clear, controlled example showing how job title matching works
with common Norwegian job titles and their variations.
"""

import pandas as pd
from thefuzz import fuzz
import numpy as np

def create_example_data():
    """Create a simple example dataset with Norwegian job titles"""
    
    # Example data showing different types of matches
    example_data = {
        'Person': [
            'Lars Hansen', 'Anna Olsen', 'Erik Nordahl', 'Kari Berg', 'Ole Svendsen',
            'Liv Andersen', 'Per Kristiansen', 'Astrid Haugen', 'Nils Johansen', 'Ingrid Larsen'
        ],
        'Book_ID': [f'book_{i+1:03d}' for i in range(10)],
        
        # Azure OCR job titles
        'job1_title_azure': [
            'Lærer', 'Sykepleier', 'Ingeniør', 'Advokat', 'Doktor',
            'Professor', 'Arkitekt', 'Forfatter', 'Bonde', 'Fisker'
        ],
        'job2_title_azure': [
            'Rektor', 'Overlege', 'Maskin-ingeniør', 'Dommer', 'Specialist',
            'Forskningssjef', 'Byggherre', 'Journalist', 'Gårdbruker', 'Kaptein'
        ],
        'job3_title_azure': [
            'Skolestyrer', 'Avdelingsleder', 'Civilingeniør', 'Jurist', 'Kirurg',
            'Universitetsprofessor', 'Planlegger', 'Redaktør', 'Småbruker', 'Skipsreder'
        ],
        
        # MonkeyOCR job titles (with variations)
        'job1_title_monkey': [
            'Teacher', 'Nurse', 'Engineer', 'Lawyer', 'Doctor',
            'Prof.', 'Architect', 'Writer', 'Farmer', 'Fisherman'
        ],
        'job2_title_monkey': [
            'Headmaster', 'Senior Doctor', 'Mechanical Engineer', 'Judge', 'Medical Specialist',
            'Research Director', 'Builder', 'Press Reporter', 'Agricultural Worker', 'Sea Captain'
        ],
        'job3_title_monkey': [
            'School Director', 'Department Manager', 'Civil Engineer', 'Legal Expert', 'Surgeon',
            'University Professor', 'Urban Planner', 'Editor', 'Small Farmer', 'Ship Owner'
        ]
    }
    
    return pd.DataFrame(example_data)

def extract_all_job_titles(df, suffix):
    """Extract all job titles from job columns"""
    job_titles = set()
    
    for col in ['job1_title', 'job2_title', 'job3_title']:
        full_col = f'{col}_{suffix}'
        if full_col in df.columns:
            titles = df[full_col].dropna()
            job_titles.update([str(title).strip() for title in titles if str(title).strip()])
    
    return job_titles

def show_detailed_comparison():
    """Show a detailed comparison of how job matching works"""
    
    print("SIMPLE JOB COMPARISON EXAMPLE")
    print("="*60)
    
    # Create example data
    df = create_example_data()
    
    print("\nEXAMPLE DATA:")
    print("-" * 40)
    print(f"{'Person':<15} {'Azure Job 1':<15} {'Monkey Job 1':<15} {'Similarity'}")
    print("-" * 40)
    
    # Show person-by-person comparison for job1
    for i, row in df.iterrows():
        azure_job = row['job1_title_azure']
        monkey_job = row['job1_title_monkey']
        similarity = fuzz.ratio(azure_job, monkey_job)
        
        print(f"{row['Person']:<15} {azure_job:<15} {monkey_job:<15} {similarity:>8.0f}%")
    
    # Extract all unique job titles
    azure_titles = extract_all_job_titles(df, 'azure')
    monkey_titles = extract_all_job_titles(df, 'monkey')
    
    print(f"\n\nUNIQUE JOB TITLES:")
    print("-" * 50)
    print(f"Azure titles ({len(azure_titles)}): {sorted(azure_titles)}")
    print(f"Monkey titles ({len(monkey_titles)}): {sorted(monkey_titles)}")
    
    # Perform fuzzy matching
    print(f"\n\nFUZZY MATCHING RESULTS (threshold ≥ 80%):")
    print("-" * 60)
    print(f"{'Azure Title':<20} {'Best Monkey Match':<20} {'Score':<8} {'Status'}")
    print("-" * 60)
    
    matched_pairs = []
    unmatched_azure = []
    threshold = 80
    
    for azure_title in sorted(azure_titles):
        best_score = 0
        best_match = None
        
        for monkey_title in monkey_titles:
            score = fuzz.ratio(azure_title, monkey_title)
            if score > best_score:
                best_score = score
                best_match = monkey_title
        
        if best_score >= threshold:
            matched_pairs.append((azure_title, best_match, best_score))
            status = "MATCHED"
        else:
            unmatched_azure.append(azure_title)
            status = "UNMATCHED"
        
        print(f"{azure_title:<20} {best_match or 'None':<20} {best_score:<8.0f} {status}")
    
    # Show summary statistics
    print(f"\n\nSUMMARY STATISTICS:")
    print("-" * 30)
    print(f"Total Azure titles: {len(azure_titles)}")
    print(f"Total Monkey titles: {len(monkey_titles)}")
    print(f"Matched pairs: {len(matched_pairs)}")
    print(f"Unmatched Azure: {len(unmatched_azure)}")
    print(f"Azure coverage: {(len(matched_pairs)/len(azure_titles))*100:.1f}%")
    
    # Calculate Jaccard similarity
    jaccard = len(matched_pairs) / (len(azure_titles) + len(monkey_titles) - len(matched_pairs))
    print(f"Jaccard similarity: {jaccard:.3f}")
    
    # Show examples of different match types
    print(f"\n\nMATCH TYPE EXAMPLES:")
    print("-" * 40)
    
    # Perfect matches
    perfect_matches = [(a, m, s) for a, m, s in matched_pairs if s == 100]
    if perfect_matches:
        print(f"Perfect matches (100%):")
        for azure, monkey, score in perfect_matches[:3]:
            print(f"  '{azure}' ↔ '{monkey}'")
    
    # High similarity matches
    high_matches = [(a, m, s) for a, m, s in matched_pairs if 90 <= s < 100]
    if high_matches:
        print(f"\nHigh similarity matches (90-99%):")
        for azure, monkey, score in high_matches[:3]:
            print(f"  '{azure}' ↔ '{monkey}' ({score:.0f}%)")
    
    # Medium similarity matches
    medium_matches = [(a, m, s) for a, m, s in matched_pairs if 80 <= s < 90]
    if medium_matches:
        print(f"\nMedium similarity matches (80-89%):")
        for azure, monkey, score in medium_matches[:3]:
            print(f"  '{azure}' ↔ '{monkey}' ({score:.0f}%)")
    
    # Unmatched examples
    if unmatched_azure:
        print(f"\nUnmatched Azure titles:")
        for title in unmatched_azure[:3]:
            print(f"  '{title}' (no good match found)")
    
    print(f"\n\nEXPLANATION:")
    print("-" * 30)
    print("• Perfect matches (100%): Identical titles")
    print("• High similarity (90-99%): Very similar, likely same job with minor differences")
    print("• Medium similarity (80-89%): Possibly same job, but with more variation")
    print("• Below 80%: Different jobs or too much variation to match reliably")
    print("\nThis same process is applied to the full Norwegian biography datasets!")

def show_threshold_comparison():
    """Show how different thresholds affect matching results"""
    
    print("\n\n" + "="*60)
    print("THRESHOLD COMPARISON EXAMPLE")
    print("="*60)
    
    df = create_example_data()
    azure_titles = extract_all_job_titles(df, 'azure')
    monkey_titles = extract_all_job_titles(df, 'monkey')
    
    thresholds = [60, 70, 80, 90, 95]
    
    print(f"\nHow different thresholds affect matching:")
    print(f"{'Threshold':<12} {'Matches':<8} {'Coverage':<10} {'Quality'}")
    print("-" * 40)
    
    for threshold in thresholds:
        matched_count = 0
        total_similarity = 0
        
        for azure_title in azure_titles:
            best_score = 0
            for monkey_title in monkey_titles:
                score = fuzz.ratio(azure_title, monkey_title)
                if score > best_score:
                    best_score = score
            
            if best_score >= threshold:
                matched_count += 1
                total_similarity += best_score
        
        coverage = (matched_count / len(azure_titles)) * 100
        avg_quality = total_similarity / matched_count if matched_count > 0 else 0
        
        print(f"{threshold}%{'':<8} {matched_count:<8} {coverage:<8.1f}% {avg_quality:<8.1f}%")
    
    print(f"\nThreshold selection trade-offs:")
    print("• Lower threshold → More matches, but lower quality")
    print("• Higher threshold → Fewer matches, but higher quality")
    print("• 80% is a good balance for most applications")

if __name__ == "__main__":
    show_detailed_comparison()
    show_threshold_comparison()
