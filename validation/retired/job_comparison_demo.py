"""
Job Comparison Demonstration Script

This script illustrates how the job title overlap analysis works by:
1. Loading sample data from both AzureOCR and MonkeyOCR datasets
2. Extracting job titles (job1-job5) from both datasets
3. Performing fuzzy matching to identify matched and unmatched job titles
4. Displaying the results in a clear, organized format
"""

import pandas as pd
import numpy as np
from thefuzz import fuzz, process
from typing import Dict, List, Set, Tuple
import json

def load_sample_data(max_records: int = 20) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Load sample data from both datasets"""
    
    print("Loading sample data from both datasets...")
    
    try:
        # Load the actual datasets
        azure_df = pd.read_csv(r'd:\data\HCNC\norway\biographies\storage\AzureOCR\output_csv\extracted_all_names_portraits_biographies_final.csv')
        monkey_df = pd.read_csv(r'd:\data\HCNC\norway\biographies\storage\MonkeyOCR\output_csv\extracted_all_names_portraits_biographies_final.csv')
        
        # Take a sample for demonstration
        azure_sample = azure_df.head(max_records)
        monkey_sample = monkey_df.head(max_records)
        
        print(f"Azure sample: {len(azure_sample)} records")
        print(f"Monkey sample: {len(monkey_sample)} records")
        
        return azure_sample, monkey_sample
        
    except FileNotFoundError:
        print("Could not find the actual data files. Creating synthetic demo data...")
        return create_demo_data(max_records)

def create_demo_data(num_records: int = 20) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Create synthetic demo data if actual files are not available"""
    
    # Sample Norwegian job titles with variations
    job_variations = [
        # Exact matches
        ("Lærer", "Lærer"),
        ("Ingeniør", "Ingeniør"),
        ("Lege", "Lege"),
        ("Advokat", "Advokat"),
        ("Sykepleier", "Sykepleier"),
        
        # Similar matches (should match with fuzzy logic)
        ("Doktor", "Dr."),
        ("Professor", "Prof."),
        ("Arkitekt", "Architect"),
        ("Forfatter", "Skribent"),
        ("Journalist", "Pressemann"),
        
        # Different jobs (should not match)
        ("Bonde", "Kjøpmann"),
        ("Smed", "Snekker"),
        ("Baker", "Slakter"),
        ("Fisker", "Jeger"),
        ("Maler", "Musiker"),
    ]
    
    # Create sample biography JSON data
    azure_data = []
    monkey_data = []
    
    for i in range(num_records):
        book_id = f"book_{i+1:03d}"
        name = f"Person {i+1}"
        
        # Select random job variations for this person
        selected_jobs = np.random.choice(len(job_variations), size=min(5, len(job_variations)), replace=False)
        
        # Create Azure jobs
        azure_jobs = []
        for j, job_idx in enumerate(selected_jobs):
            if j < 5:  # Max 5 jobs
                azure_job = job_variations[job_idx][0]  # Azure version
                azure_jobs.append({
                    "title": azure_job,
                    "location": f"Oslo {j+1}",
                    "years": f"{1900 + j*10}-{1910 + j*10}"
                })
        
        # Create Monkey jobs (with variations)
        monkey_jobs = []
        for j, job_idx in enumerate(selected_jobs):
            if j < 5:  # Max 5 jobs
                monkey_job = job_variations[job_idx][1]  # Monkey version
                monkey_jobs.append({
                    "title": monkey_job,
                    "location": f"Bergen {j+1}",
                    "years": f"{1905 + j*10}-{1915 + j*10}"
                })
        
        # Create biography JSON
        azure_bio = {
            "title": f"Herr/Fru",
            "jobs": azure_jobs,
            "birth_date": f"{1880 + i}",
            "birth_place": "Norge"
        }
        
        monkey_bio = {
            "title": f"Mr./Mrs.",
            "jobs": monkey_jobs,
            "birth_date": f"{1880 + i}",
            "birth_place": "Norway"
        }
        
        azure_data.append({
            'book_id': book_id,
            'name': name,
            'biography_json': json.dumps(azure_bio)
        })
        
        monkey_data.append({
            'book_id': book_id,
            'name': name,
            'biography_json': json.dumps(monkey_bio)
        })
    
    return pd.DataFrame(azure_data), pd.DataFrame(monkey_data)

def extract_job_titles_from_json(df: pd.DataFrame, json_col: str = 'biography_json', max_jobs: int = 5) -> pd.DataFrame:
    """Extract job titles from JSON biography data"""
    
    result_df = df.copy()
    
    # Initialize job title columns
    for i in range(1, max_jobs + 1):
        result_df[f'job{i}_title'] = 'Missing'
    
    # Extract job titles
    for index, row in result_df.iterrows():
        try:
            if pd.notna(row[json_col]) and row[json_col] != '':
                bio_data = json.loads(row[json_col])
                jobs = bio_data.get('jobs', [])
                
                for i, job in enumerate(jobs[:max_jobs]):
                    if isinstance(job, dict) and 'title' in job:
                        result_df.at[index, f'job{i+1}_title'] = job['title']
        except (json.JSONDecodeError, TypeError):
            continue
    
    return result_df

def collect_unique_job_titles(df: pd.DataFrame, source_name: str, max_jobs: int = 5) -> Set[str]:
    """Collect all unique job titles from a dataframe"""
    
    job_titles = set()
    
    for i in range(1, max_jobs + 1):
        col_name = f'job{i}_title'
        if col_name in df.columns:
            titles = df[col_name].dropna()
            titles = titles[titles != 'Missing']
            job_titles.update([str(title).strip() for title in titles if str(title).strip()])
    
    print(f"{source_name} unique job titles: {len(job_titles)}")
    return job_titles

def perform_fuzzy_matching(azure_titles: Set[str], monkey_titles: Set[str], threshold: int = 80) -> Dict:
    """Perform fuzzy matching between job title sets"""
    
    print(f"\nPerforming fuzzy matching with threshold {threshold}...")
    
    matched_pairs = []
    unmatched_azure = []
    unmatched_monkey = list(monkey_titles)
    
    for azure_title in azure_titles:
        # Find best match in monkey titles
        best_match = process.extractOne(azure_title, monkey_titles, scorer=fuzz.ratio)
        
        if best_match and best_match[1] >= threshold:
            matched_pairs.append({
                'azure_title': azure_title,
                'monkey_title': best_match[0],
                'similarity_score': best_match[1]
            })
            # Remove from unmatched monkey titles
            if best_match[0] in unmatched_monkey:
                unmatched_monkey.remove(best_match[0])
        else:
            unmatched_azure.append(azure_title)
    
    return {
        'matched_pairs': matched_pairs,
        'unmatched_azure': unmatched_azure,
        'unmatched_monkey': unmatched_monkey
    }

def display_job_comparison_results(azure_df: pd.DataFrame, monkey_df: pd.DataFrame, 
                                   matching_results: Dict, max_jobs: int = 5):
    """Display comprehensive job comparison results"""
    
    print("\n" + "="*100)
    print("JOB COMPARISON DEMONSTRATION")
    print("="*100)
    
    # Show sample records with their job titles
    print("\nSAMPLE RECORDS AND JOB TITLES:")
    print("-" * 80)
    
    for i in range(min(5, len(azure_df))):  # Show first 5 records
        azure_row = azure_df.iloc[i]
        monkey_row = monkey_df.iloc[i]
        
        print(f"\nRecord {i+1}: {azure_row['name']} (Book: {azure_row['book_id']})")
        print("  Azure jobs:", end=" ")
        azure_jobs = [azure_row.get(f'job{j}_title', 'Missing') for j in range(1, max_jobs+1)]
        azure_jobs = [job for job in azure_jobs if job != 'Missing']
        print(", ".join(azure_jobs) if azure_jobs else "None")
        
        print("  Monkey jobs:", end=" ")
        monkey_jobs = [monkey_row.get(f'job{j}_title', 'Missing') for j in range(1, max_jobs+1)]
        monkey_jobs = [job for job in monkey_jobs if job != 'Missing']
        print(", ".join(monkey_jobs) if monkey_jobs else "None")
    
    # Show matching results
    print(f"\n\nMATCHING RESULTS:")
    print("-" * 50)
    
    matched_pairs = matching_results['matched_pairs']
    unmatched_azure = matching_results['unmatched_azure']
    unmatched_monkey = matching_results['unmatched_monkey']
    
    print(f"Total matched pairs: {len(matched_pairs)}")
    print(f"Unmatched Azure titles: {len(unmatched_azure)}")
    print(f"Unmatched Monkey titles: {len(unmatched_monkey)}")
    
    # Show matched pairs
    if matched_pairs:
        print(f"\nMATCHED JOB TITLES:")
        print("-" * 60)
        print(f"{'Azure Title':<25} {'Monkey Title':<25} {'Similarity'}")
        print("-" * 60)
        
        # Sort by similarity score (highest first)
        sorted_matches = sorted(matched_pairs, key=lambda x: x['similarity_score'], reverse=True)
        for pair in sorted_matches:
            print(f"{pair['azure_title']:<25} {pair['monkey_title']:<25} {pair['similarity_score']:>7.0f}%")
    
    # Show unmatched titles
    if unmatched_azure:
        print(f"\nUNMATCHED AZURE TITLES:")
        print("-" * 30)
        for i, title in enumerate(unmatched_azure, 1):
            print(f"{i:2d}. {title}")
    
    if unmatched_monkey:
        print(f"\nUNMATCHED MONKEY TITLES:")
        print("-" * 30)
        for i, title in enumerate(unmatched_monkey, 1):
            print(f"{i:2d}. {title}")
    
    # Calculate and show statistics
    total_azure = len(matching_results['unmatched_azure']) + len(matched_pairs)
    total_monkey = len(matching_results['unmatched_monkey']) + len(matched_pairs)
    
    azure_coverage = (len(matched_pairs) / total_azure) * 100 if total_azure > 0 else 0
    monkey_coverage = (len(matched_pairs) / total_monkey) * 100 if total_monkey > 0 else 0
    
    # Jaccard similarity
    jaccard = len(matched_pairs) / (total_azure + total_monkey - len(matched_pairs)) if (total_azure + total_monkey - len(matched_pairs)) > 0 else 0
    
    print(f"\nSTATISTICS:")
    print("-" * 30)
    print(f"Azure coverage: {azure_coverage:.1f}%")
    print(f"Monkey coverage: {monkey_coverage:.1f}%")
    print(f"Jaccard similarity: {jaccard:.3f}")
    
    if matched_pairs:
        similarity_scores = [pair['similarity_score'] for pair in matched_pairs]
        print(f"Average similarity: {np.mean(similarity_scores):.1f}%")
        print(f"Similarity range: {np.min(similarity_scores):.0f}% - {np.max(similarity_scores):.0f}%")

def main():
    """Main demonstration function"""
    
    print("JOB TITLE COMPARISON DEMONSTRATION")
    print("="*50)
    
    # Step 1: Load sample data
    azure_df, monkey_df = load_sample_data(max_records=15)
    
    # Step 2: Extract job titles from JSON
    print("\nExtracting job titles from biography JSON...")
    azure_with_jobs = extract_job_titles_from_json(azure_df, 'biography_json', max_jobs=5)
    monkey_with_jobs = extract_job_titles_from_json(monkey_df, 'biography_json', max_jobs=5)
    
    # Step 3: Collect unique job titles
    print("\nCollecting unique job titles...")
    azure_titles = collect_unique_job_titles(azure_with_jobs, "Azure", max_jobs=5)
    monkey_titles = collect_unique_job_titles(monkey_with_jobs, "Monkey", max_jobs=5)
    
    print(f"\nAll Azure job titles: {sorted(azure_titles)}")
    print(f"All Monkey job titles: {sorted(monkey_titles)}")
    
    # Step 4: Perform fuzzy matching
    matching_results = perform_fuzzy_matching(azure_titles, monkey_titles, threshold=80)
    
    # Step 5: Display comprehensive results
    display_job_comparison_results(azure_with_jobs, monkey_with_jobs, matching_results, max_jobs=5)
    
    # Step 6: Show how to analyze specific cases
    print(f"\n\nDETAILED ANALYSIS EXAMPLES:")
    print("-" * 50)
    
    # Show examples of different similarity scores
    if matching_results['matched_pairs']:
        print("\nExamples of different matching quality:")
        sorted_matches = sorted(matching_results['matched_pairs'], key=lambda x: x['similarity_score'], reverse=True)
        
        # Perfect matches
        perfect_matches = [m for m in sorted_matches if m['similarity_score'] == 100]
        if perfect_matches:
            print(f"\nPerfect matches (100% similarity):")
            for match in perfect_matches[:3]:
                print(f"  '{match['azure_title']}' ↔ '{match['monkey_title']}'")
        
        # Good matches
        good_matches = [m for m in sorted_matches if 90 <= m['similarity_score'] < 100]
        if good_matches:
            print(f"\nGood matches (90-99% similarity):")
            for match in good_matches[:3]:
                print(f"  '{match['azure_title']}' ↔ '{match['monkey_title']}' ({match['similarity_score']:.0f}%)")
        
        # Moderate matches
        moderate_matches = [m for m in sorted_matches if 80 <= m['similarity_score'] < 90]
        if moderate_matches:
            print(f"\nModerate matches (80-89% similarity):")
            for match in moderate_matches[:3]:
                print(f"  '{match['azure_title']}' ↔ '{match['monkey_title']}' ({match['similarity_score']:.0f}%)")
    
    print(f"\n\nThis demonstration shows how the job title overlap analysis:")
    print("1. Extracts job titles from both Azure and Monkey OCR results")
    print("2. Uses fuzzy matching to find similar job titles across datasets")
    print("3. Categorizes titles as matched or unmatched")
    print("4. Provides detailed statistics and quality metrics")
    print("\nThe actual analysis works the same way but with the full datasets!")

if __name__ == "__main__":
    main()
