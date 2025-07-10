#!/usr/bin/env python3
"""
Gemini Analysis Results Summarizer

This script analyzes the Gemini job resolver results to provide insights
about the quality differences between Azure and Monkey OCR systems.
"""

import pandas as pd
import json
import numpy as np
from pathlib import Path
import matplotlib.pyplot as plt
import seaborn as sns

def load_all_analysis_results(base_dir="gemini_job_analysis_output"):
    """Load all Gemini analysis results from the output directory"""
    
    base_path = Path(base_dir)
    
    # Try to load the summary CSV
    summary_csv = base_path / "gemini_job_analysis_summary.csv"
    
    if summary_csv.exists():
        df = pd.read_csv(summary_csv)
        print(f"Loaded {len(df)} analysis results from {summary_csv}")
        return df
    else:
        print(f"Summary CSV not found at {summary_csv}")
        
        # Try to load individual JSON files
        json_files = list(base_path.glob("digibok_*_gemini_analysis.json"))
        
        if json_files:
            print(f"Found {len(json_files)} individual JSON analysis files")
            
            analyses = []
            for json_file in json_files:
                try:
                    with open(json_file, 'r', encoding='utf-8') as f:
                        analysis = json.load(f)
                        
                    # Convert to flat structure for DataFrame
                    flat_analysis = {
                        'book_id': analysis.get('book_id', ''),
                        'name_azure': analysis.get('name_azure', ''),
                        'name_monkey': analysis.get('name_monkey', ''),
                        'inspection_reason': analysis.get('inspection_reason', ''),
                        'correct_job_titles': '; '.join(analysis.get('correct_job_titles', [])),
                        'azure_accuracy_rating': analysis.get('azure_accuracy_rating', 0),
                        'monkey_accuracy_rating': analysis.get('monkey_accuracy_rating', 0),
                        'azure_analysis': analysis.get('azure_analysis', ''),
                        'monkey_analysis': analysis.get('monkey_analysis', ''),
                        'text_quality_issues': analysis.get('text_quality_issues', ''),
                        'recommendation': analysis.get('recommendation', ''),
                        'confidence_level': analysis.get('confidence_level', ''),
                        'original_azure_jobs': '; '.join(analysis.get('original_azure_jobs', [])),
                        'original_monkey_jobs': '; '.join(analysis.get('original_monkey_jobs', [])),
                        'analysis_timestamp': analysis.get('analysis_timestamp', '')
                    }
                    
                    analyses.append(flat_analysis)
                    
                except Exception as e:
                    print(f"Error loading {json_file}: {e}")
            
            if analyses:
                df = pd.DataFrame(analyses)
                print(f"Created DataFrame from {len(analyses)} individual analyses")
                return df
        
        print("No analysis results found")
        return pd.DataFrame()

def analyze_results(df):
    """Analyze the Gemini results to provide insights"""
    
    if df.empty:
        print("No data to analyze")
        return
    
    print("\n" + "="*80)
    print("GEMINI ANALYSIS RESULTS SUMMARY")
    print("="*80)
    
    # Basic statistics
    print(f"\nBASIC STATISTICS:")
    print("-" * 40)
    print(f"Total records analyzed: {len(df)}")
    print(f"Average Azure accuracy: {df['azure_accuracy_rating'].mean():.1f}/10")
    print(f"Average Monkey accuracy: {df['monkey_accuracy_rating'].mean():.1f}/10")
    print(f"Azure accuracy std dev: {df['azure_accuracy_rating'].std():.1f}")
    print(f"Monkey accuracy std dev: {df['monkey_accuracy_rating'].std():.1f}")
    
    # Compare Azure vs Monkey
    azure_better = len(df[df['azure_accuracy_rating'] > df['monkey_accuracy_rating']])
    monkey_better = len(df[df['monkey_accuracy_rating'] > df['azure_accuracy_rating']])
    equal = len(df[df['azure_accuracy_rating'] == df['monkey_accuracy_rating']])
    
    print(f"\nCOMPARATIVE PERFORMANCE:")
    print("-" * 40)
    print(f"Azure performed better: {azure_better} records ({azure_better/len(df)*100:.1f}%)")
    print(f"Monkey performed better: {monkey_better} records ({monkey_better/len(df)*100:.1f}%)")
    print(f"Equal performance: {equal} records ({equal/len(df)*100:.1f}%)")
    
    # Accuracy distribution
    print(f"\nACCURACY DISTRIBUTION:")
    print("-" * 40)
    print("Azure OCR:")
    for rating in range(1, 11):
        count = len(df[df['azure_accuracy_rating'] == rating])
        if count > 0:
            print(f"  Rating {rating}: {count} records ({count/len(df)*100:.1f}%)")
    
    print("Monkey OCR:")
    for rating in range(1, 11):
        count = len(df[df['monkey_accuracy_rating'] == rating])
        if count > 0:
            print(f"  Rating {rating}: {count} records ({count/len(df)*100:.1f}%)")
    
    # Confidence levels
    confidence_counts = df['confidence_level'].value_counts()
    print(f"\nCONFIDENCE LEVELS:")
    print("-" * 40)
    for level, count in confidence_counts.items():
        print(f"{level.capitalize()}: {count} records ({count/len(df)*100:.1f}%)")
    
    # Inspection reasons
    reason_counts = df['inspection_reason'].value_counts()
    print(f"\nINSPECTION REASONS:")
    print("-" * 40)
    for reason, count in reason_counts.items():
        print(f"{reason}: {count} records ({count/len(df)*100:.1f}%)")
    
    # Best and worst cases
    print(f"\nBEST AZURE CASES (Rating 8+):")
    print("-" * 40)
    best_azure = df[df['azure_accuracy_rating'] >= 8].sort_values('azure_accuracy_rating', ascending=False)
    for idx, row in best_azure.head(5).iterrows():
        print(f"  {row['name_azure']} (Book: {row['book_id']}) - Rating: {row['azure_accuracy_rating']}")
    
    print(f"\nBEST MONKEY CASES (Rating 8+):")
    print("-" * 40)
    best_monkey = df[df['monkey_accuracy_rating'] >= 8].sort_values('monkey_accuracy_rating', ascending=False)
    for idx, row in best_monkey.head(5).iterrows():
        print(f"  {row['name_monkey']} (Book: {row['book_id']}) - Rating: {row['monkey_accuracy_rating']}")
    
    print(f"\nWORST AZURE CASES (Rating 4 or below):")
    print("-" * 40)
    worst_azure = df[df['azure_accuracy_rating'] <= 4].sort_values('azure_accuracy_rating')
    for idx, row in worst_azure.head(5).iterrows():
        print(f"  {row['name_azure']} (Book: {row['book_id']}) - Rating: {row['azure_accuracy_rating']}")
    
    print(f"\nWORST MONKEY CASES (Rating 4 or below):")
    print("-" * 40)
    worst_monkey = df[df['monkey_accuracy_rating'] <= 4].sort_values('monkey_accuracy_rating')
    for idx, row in worst_monkey.head(5).iterrows():
        print(f"  {row['name_monkey']} (Book: {row['book_id']}) - Rating: {row['monkey_accuracy_rating']}")
    
    # Recommendations analysis
    print(f"\nRECOMMENDATION PATTERNS:")
    print("-" * 40)
    azure_recommended = len(df[df['recommendation'].str.contains('Azure', case=False, na=False)])
    monkey_recommended = len(df[df['recommendation'].str.contains('Monkey', case=False, na=False)])
    neither_recommended = len(df[df['recommendation'].str.contains('Neither', case=False, na=False)])
    
    print(f"Azure recommended: {azure_recommended} records ({azure_recommended/len(df)*100:.1f}%)")
    print(f"Monkey recommended: {monkey_recommended} records ({monkey_recommended/len(df)*100:.1f}%)")
    print(f"Neither recommended: {neither_recommended} records ({neither_recommended/len(df)*100:.1f}%)")
    
    return df

def create_visualization(df, output_dir="gemini_job_analysis_output"):
    """Create visualizations of the analysis results"""
    
    if df.empty:
        print("No data for visualization")
        return
    
    try:
        import matplotlib.pyplot as plt
        import seaborn as sns
        
        # Set style
        plt.style.use('default')
        sns.set_palette("husl")
        
        fig, axes = plt.subplots(2, 2, figsize=(15, 12))
        fig.suptitle('Gemini Analysis Results - Azure vs Monkey OCR', fontsize=16)
        
        # 1. Accuracy comparison
        axes[0, 0].scatter(df['azure_accuracy_rating'], df['monkey_accuracy_rating'], alpha=0.6)
        axes[0, 0].plot([0, 10], [0, 10], 'r--', alpha=0.5)  # Diagonal line
        axes[0, 0].set_xlabel('Azure Accuracy Rating')
        axes[0, 0].set_ylabel('Monkey Accuracy Rating')
        axes[0, 0].set_title('Accuracy Comparison')
        axes[0, 0].grid(True, alpha=0.3)
        
        # 2. Accuracy distributions
        axes[0, 1].hist(df['azure_accuracy_rating'], bins=10, alpha=0.7, label='Azure', color='blue')
        axes[0, 1].hist(df['monkey_accuracy_rating'], bins=10, alpha=0.7, label='Monkey', color='orange')
        axes[0, 1].set_xlabel('Accuracy Rating')
        axes[0, 1].set_ylabel('Count')
        axes[0, 1].set_title('Accuracy Distribution')
        axes[0, 1].legend()
        axes[0, 1].grid(True, alpha=0.3)
        
        # 3. Confidence levels
        confidence_counts = df['confidence_level'].value_counts()
        axes[1, 0].bar(confidence_counts.index, confidence_counts.values)
        axes[1, 0].set_xlabel('Confidence Level')
        axes[1, 0].set_ylabel('Count')
        axes[1, 0].set_title('Analysis Confidence Levels')
        axes[1, 0].grid(True, alpha=0.3)
        
        # 4. Inspection reasons
        reason_counts = df['inspection_reason'].value_counts()
        axes[1, 1].bar(range(len(reason_counts)), reason_counts.values)
        axes[1, 1].set_xticks(range(len(reason_counts)))
        axes[1, 1].set_xticklabels(reason_counts.index, rotation=45, ha='right')
        axes[1, 1].set_ylabel('Count')
        axes[1, 1].set_title('Inspection Reasons')
        axes[1, 1].grid(True, alpha=0.3)
        
        plt.tight_layout()
        
        # Save plot
        output_path = Path(output_dir)
        plot_file = output_path / "gemini_analysis_visualization.png"
        plt.savefig(plot_file, dpi=300, bbox_inches='tight')
        print(f"\nVisualization saved to: {plot_file}")
        
        plt.show()
        
    except ImportError:
        print("\nMatplotlib/Seaborn not available. Skipping visualization.")
    except Exception as e:
        print(f"\nError creating visualization: {e}")

def main():
    """Main function"""
    
    # Load results
    df = load_all_analysis_results()
    
    if not df.empty:
        # Analyze results
        analyzed_df = analyze_results(df)
        
        # Create visualization
        create_visualization(analyzed_df)
        
        # Save summary statistics
        output_path = Path("gemini_job_analysis_output")
        
        if not output_path.exists():
            output_path.mkdir(parents=True)
        
        # Save detailed statistics
        stats_file = output_path / "gemini_analysis_statistics.txt"
        
        with open(stats_file, 'w', encoding='utf-8') as f:
            f.write("GEMINI ANALYSIS STATISTICS\n")
            f.write("="*50 + "\n\n")
            f.write(f"Total records analyzed: {len(df)}\n")
            f.write(f"Average Azure accuracy: {df['azure_accuracy_rating'].mean():.2f}/10\n")
            f.write(f"Average Monkey accuracy: {df['monkey_accuracy_rating'].mean():.2f}/10\n")
            f.write(f"Azure wins: {len(df[df['azure_accuracy_rating'] > df['monkey_accuracy_rating']])}\n")
            f.write(f"Monkey wins: {len(df[df['monkey_accuracy_rating'] > df['azure_accuracy_rating']])}\n")
            f.write(f"Ties: {len(df[df['azure_accuracy_rating'] == df['monkey_accuracy_rating']])}\n")
        
        print(f"\nStatistics saved to: {stats_file}")
    
    else:
        print("No analysis results found. Please run gemini_job_resolver.py first.")

if __name__ == "__main__":
    main()
