#!/usr/bin/env python3
"""
Gemini Job Overlap Resolver

This script uses Google Gemini-2.5-Flash to analyze flagged job overlap records
by examining the original markdown content from both Azure and Monkey OCR to
resolve discrepancies in job title extraction.
"""

import os
import json
import pandas as pd
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import logging
import time
import argparse
from google import genai
from google.genai import types
import shutil  # For file operations

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Add parent directory to path for key vault access
import sys
sys.path.append(str(Path(__file__).parent.parent))

# Try to import KeyVault with better error handling
try:
    from agents.key_vault import KeyVault
    KEYVAULT_AVAILABLE = True
    logger.info("KeyVault successfully imported")
except ImportError as e:
    logger.warning(f"Could not import KeyVault: {e}")
    KEYVAULT_AVAILABLE = False
    KeyVault = None

class GeminiJobResolver:
    def __init__(self, api_key: str = None):
        """Initialize Gemini client"""
        # Try to get API key from KeyVault first, then environment variable, then parameter
        if api_key:
            self.api_key = api_key
        else:
            try:
                if KEYVAULT_AVAILABLE and KeyVault is not None:
                    vault = KeyVault()
                    self.api_key = vault.get_key("SDUGeminiAPI")
                    #self.api_key = vault.get_key("AMDGeminiFlashKey")
                    logger.info("API key retrieved from KeyVault")
                else:
                    logger.info("KeyVault not available, trying environment variable")
                    self.api_key = os.getenv("AMDGeminiFlashKey")
                    if self.api_key:
                        logger.info("API key retrieved from environment variable")
            except Exception as e:
                logger.warning(f"Could not get API key from KeyVault: {e}")
                self.api_key = os.getenv("AMDGeminiFlashKey")
                if self.api_key:
                    logger.info("API key retrieved from environment variable")
        
        if not self.api_key:
            raise ValueError("Gemini API key is required. Set AMDGeminiFlashKey environment variable, configure KeyVault, or pass as parameter.")
        
        # Initialize Gemini client
        self.client = genai.Client(api_key=self.api_key)
        self.model = "gemini-2.5-flash"
        
        logger.info(f"Initialized Gemini client with model: {self.model}")
    
    def load_flagged_records(self, flagged_csv_path: str) -> pd.DataFrame:
        """Load flagged records from CSV file"""
        try:
            df = pd.read_csv(flagged_csv_path)
            logger.info(f"Loaded {len(df)} flagged records from {flagged_csv_path}")
            return df
        except Exception as e:
            logger.error(f"Error loading flagged records: {e}")
            raise
    
    def load_comparison_dataframe(self, comparison_csv_path: str) -> pd.DataFrame:
        """Load comprehensive comparison dataframe"""
        try:
            df = pd.read_csv(comparison_csv_path)
            logger.info(f"Loaded comparison dataframe with {len(df)} records")
            return df
        except Exception as e:
            logger.error(f"Error loading comparison dataframe: {e}")
            raise
    
    def extract_job_data_for_record(self, comparison_df: pd.DataFrame, book_id: str, name_azure: str, name_monkey: str) -> Tuple[Dict, Dict]:
        """Extract all job data (titles, locations, years) for a specific record"""
        # First try to match by book_id and name
        record = comparison_df[
            (comparison_df['book_id'] == book_id) & 
            (comparison_df['name_azure'] == name_azure) & 
            (comparison_df['name_monkey'] == name_monkey)
        ]
        
        if record.empty:
            logger.warning(f"No record found for book_id: {book_id}, name_azure: {name_azure}, name_monkey: {name_monkey}")
            return {}, {}
        
        record = record.iloc[0]  # Take first match
        
        # Extract Azure job data
        azure_data = {}
        for i in range(1, 6):  # job1 to job5
            job_title = record.get(f'job{i}_title_azure', 'Missing')
            job_location = record.get(f'job{i}_location_azure', 'Missing')
            job_years = record.get(f'job{i}_years_azure', 'Missing')
            
            if pd.notna(job_title) and job_title != 'Missing':
                azure_data[f'job{i}'] = {
                    'title': str(job_title),
                    'location': str(job_location) if pd.notna(job_location) and job_location != 'Missing' else '',
                    'years': str(job_years) if pd.notna(job_years) and job_years != 'Missing' else ''
                }
        
        # Extract Monkey job data
        monkey_data = {}
        for i in range(1, 6):  # job1 to job5
            job_title = record.get(f'job{i}_title_monkey', 'Missing')
            job_location = record.get(f'job{i}_location_monkey', 'Missing')
            job_years = record.get(f'job{i}_years_monkey', 'Missing')
            
            if pd.notna(job_title) and job_title != 'Missing':
                monkey_data[f'job{i}'] = {
                    'title': str(job_title),
                    'location': str(job_location) if pd.notna(job_location) and job_location != 'Missing' else '',
                    'years': str(job_years) if pd.notna(job_years) and job_years != 'Missing' else ''
                }
        
        return azure_data, monkey_data

    def extract_job_titles_for_record(self, comparison_df: pd.DataFrame, book_id: str, name_azure: str, name_monkey: str) -> Tuple[List[str], List[str]]:
        """Extract all job titles for a specific record"""
        # First try to match by book_id and name
        record = comparison_df[
            (comparison_df['book_id'] == book_id) & 
            (comparison_df['name_azure'] == name_azure) & 
            (comparison_df['name_monkey'] == name_monkey)
        ]
        
        if record.empty:
            logger.warning(f"No record found for book_id: {book_id}, name_azure: {name_azure}, name_monkey: {name_monkey}")
            return [], []
        
        record = record.iloc[0]  # Take first match
        
        # Extract Azure job titles
        azure_jobs = []
        for i in range(1, 6):  # job1 to job5
            job_col = f'job{i}_title_azure'
            if job_col in record and pd.notna(record[job_col]) and record[job_col] != 'Missing':
                azure_jobs.append(str(record[job_col]))
        
        # Extract Monkey job titles
        monkey_jobs = []
        for i in range(1, 6):  # job1 to job5
            job_col = f'job{i}_title_monkey'
            if job_col in record and pd.notna(record[job_col]) and record[job_col] != 'Missing':
                monkey_jobs.append(str(record[job_col]))
        
        return azure_jobs, monkey_jobs
    
    def get_markdown_content(self, comparison_df: pd.DataFrame, book_id: str, name_azure: str, name_monkey: str) -> Tuple[str, str]:
        """Get markdown content for Azure and Monkey OCR"""
        # First try to match by book_id and name
        record = comparison_df[
            (comparison_df['book_id'] == book_id) & 
            (comparison_df['name_azure'] == name_azure) & 
            (comparison_df['name_monkey'] == name_monkey)
        ]
        
        if record.empty:
            logger.warning(f"No record found for book_id: {book_id}, name_azure: {name_azure}, name_monkey: {name_monkey}")
            return "", ""
        
        record = record.iloc[0]  # Take first match
        
        azure_content = record.get('markdown_chunk_azure', '')
        monkey_content = record.get('markdown_chunk_monkey', '')
        
        # Handle NaN values
        if pd.isna(azure_content):
            azure_content = ""
        if pd.isna(monkey_content):
            monkey_content = ""
        
        return str(azure_content), str(monkey_content)
    
    def create_job_analysis_prompt(self, name_azure: str, name_monkey: str, book_id: str,
                                  azure_data: Dict, monkey_data: Dict,
                                  azure_content: str, monkey_content: str,
                                  inspection_reason: str) -> str:
        """Create a detailed prompt for Gemini to analyze job discrepancies"""
        
        # Format job data for display
        def format_job_data(data, source_name):
            if not data:
                return f"{source_name} OCR extracted: No jobs found"
            
            formatted = f"{source_name} OCR extracted:\n"
            for job_key, job_info in data.items():
                formatted += f"  {job_key}: {job_info['title']}"
                if job_info['location']:
                    formatted += f" (Location: {job_info['location']})"
                if job_info['years']:
                    formatted += f" (Years: {job_info['years']})"
                formatted += "\n"
            return formatted.strip()
        
        azure_jobs_display = format_job_data(azure_data, "Azure")
        monkey_jobs_display = format_job_data(monkey_data, "Monkey")
        
        prompt = f"""You are an expert at analyzing Norwegian biographical text and job title extraction. 

I have a biographical record where two different OCR systems (Azure and Monkey) have extracted different job titles from the same person's biography. I need you to analyze the original text content and provide the most accurate job title extraction with corresponding locations and years.

**PERSON INFORMATION:**
- Name (Azure): {name_azure}
- Name (Monkey): {name_monkey}
- Book ID: {book_id}
- Issue: {inspection_reason}

**EXTRACTED JOB DATA:**
{azure_jobs_display}

{monkey_jobs_display}

**ORIGINAL TEXT CONTENT:**

**Azure OCR Text:**
```
{azure_content}
```

**Monkey OCR Text:**
```
{monkey_content}
```

**ANALYSIS TASK:**
Please analyze both text sources and provide:

1. **Correct Job Data**: Based on the original text, extract the actual job titles, locations, and years mentioned for this person. You MUST provide exactly 5 entries in chronological order to match the job1-job5 structure. If fewer than 5 job titles exist, use null for the remaining slots.

2. **Quality Assessment**: 
   - Rate Azure OCR extraction accuracy (1-10)
   - Rate Monkey OCR extraction accuracy (1-10)
   - Explain the main differences

3. **Text Quality Issues**: Are there any OCR errors or text quality issues that might explain the discrepancies?

4. **Recommendations**: Which OCR system performed better for this specific record and why?

**CRITICAL REQUIREMENTS:**
- You MUST provide exactly 5 job entries in the correct_job_titles, correct_job_locations, and correct_job_years arrays
- Use null for empty slots if fewer than 5 jobs exist
- Order jobs chronologically when possible (job1 = earliest, job5 = latest)
- **ALIGNMENT IS CRITICAL**: The locations and years MUST correspond to the order of your corrected job titles
- If you reorder job titles from their original extraction, you MUST also reorder the corresponding locations and years
- Example: If job title 1 in your corrected list corresponds to what was originally job title 3, then the location and year for position 1 must also come from the original job title 3's data
- This maintains perfect alignment between titles, locations, and years across all 5 positions
- Extract locations and years from the biographical text when available
- Look for Norwegian job titles, occupations, and professional roles
- Consider spelling variations and Norwegian language conventions
- Focus on job titles that are clearly stated in the biographical text
- Ignore honorary titles or family relationships unless they represent actual occupations
- Do not include abbreviations like Pr./R or HV as they are not job titles
- Do not include educational titles or degrees, only actual job titles
- Do not include educational activities like "elev" or "student" as they are not actual job titles

Please provide your analysis in the following JSON format:
```json
{{
  "correct_job_titles": [
  "correct_job_titles": [
    "job title 1 (earliest chronologically)",
    "job title 2", 
    "job title 3",
    "job title 4",
    "job title 5 (latest chronologically or null if no 5th job)"
  ],
  "correct_job_locations": [
    "location 1 (corresponding to job title 1)",
    "location 2 (corresponding to job title 2)",
    "location 3 (corresponding to job title 3)", 
    "location 4 (corresponding to job title 4)",
    "location 5 (corresponding to job title 5, or null if no 5th job)"
  ],
  "correct_job_years": [
    "years 1 (corresponding to job title 1)",
    "years 2 (corresponding to job title 2)",
    "years 3 (corresponding to job title 3)",
    "years 4 (corresponding to job title 4)", 
    "years 5 (corresponding to job title 5, or null if no 5th job)"
  ],
  "azure_accuracy_rating": 8,
  "monkey_accuracy_rating": 6,
  "azure_analysis": "Explanation of Azure OCR performance",
  "monkey_analysis": "Explanation of Monkey OCR performance",
  "text_quality_issues": "Description of any OCR errors or quality issues",
  "recommendation": "Which system performed better and why",
  "confidence_level": "high/medium/low"
}}
```

**ALIGNMENT EXAMPLE:**
If the original extractions were:
- Azure: job1="Teacher", job2="Principal" 
- Monkey: job1="Principal", job2="Teacher"

And you determine the chronological order should be "Teacher" (1920-1930) then "Principal" (1931-1940), your output should be:
```json
{{
  "correct_job_titles": ["Teacher", "Principal", null, null, null],
  "correct_job_locations": ["Oslo", "Bergen", null, null, null],
  "correct_job_years": ["1920-1930", "1931-1940", null, null, null]
}}
```
This ensures perfect alignment across all three arrays.
"""
        return prompt
    
    def analyze_job_discrepancy(self, name_azure: str, name_monkey: str, book_id: str,
                               azure_data: Dict, monkey_data: Dict,
                               azure_content: str, monkey_content: str,
                               inspection_reason: str) -> Dict:
        """Use Gemini to analyze job title discrepancies"""
        
        # Extract job titles for metadata storage
        azure_jobs = [job_info['title'] for job_info in azure_data.values()]
        monkey_jobs = [job_info['title'] for job_info in monkey_data.values()]
        
        prompt = self.create_job_analysis_prompt(
            name_azure, name_monkey, book_id,
            azure_data, monkey_data,
            azure_content, monkey_content,
            inspection_reason
        )
        
        # Temperature options for retry attempts
        temperature_options = [0.01, 0.02, 0.1, 0.2]
        
        # Retry up to 4 times with increasing temperature
        for attempt in range(4):
            temperature = temperature_options[attempt]
            
            try:
                logger.info(f"Analyzing {book_id} - Attempt {attempt + 1} with temperature {temperature}")
                
                # Prepare content for Gemini
                contents = [
                    types.Content(
                        role="user",
                        parts=[
                            types.Part.from_text(text=prompt),
                        ],
                    ),
                ]
                
                # Configure generation
                generate_content_config = types.GenerateContentConfig(
                    thinking_config=types.ThinkingConfig(
                        thinking_budget=500,  # More thinking for complex analysis
                    ),
                    response_mime_type="application/json",
                    temperature=temperature,
                    max_output_tokens=2000
                )
                
                # Generate response
                response = self.client.models.generate_content(
                    model=self.model,
                    contents=contents,
                    config=generate_content_config,
                )
                
                # Parse JSON response
                try:
                    analysis = json.loads(response.text)
                    
                    # Add metadata
                    analysis['book_id'] = book_id
                    analysis['name_azure'] = name_azure
                    analysis['name_monkey'] = name_monkey
                    analysis['original_azure_jobs'] = azure_jobs
                    analysis['original_monkey_jobs'] = monkey_jobs
                    analysis['inspection_reason'] = inspection_reason
                    analysis['analysis_timestamp'] = time.strftime("%Y-%m-%d %H:%M:%S")
                    analysis['gemini_attempt'] = attempt + 1
                    analysis['gemini_temperature'] = temperature
                    
                    logger.info(f"Successfully analyzed {book_id} on attempt {attempt + 1}")
                    return analysis
                    
                except json.JSONDecodeError as e:
                    logger.warning(f"Attempt {attempt + 1}: JSON decode error for {book_id}: {e}")
                    
                    # Try to extract JSON from response
                    try:
                        json_match = json.loads(response.text.strip())
                        if json_match:
                            analysis = json_match
                            analysis['book_id'] = book_id
                            analysis['name_azure'] = name_azure
                            analysis['name_monkey'] = name_monkey
                            analysis['original_azure_jobs'] = azure_jobs
                            analysis['original_monkey_jobs'] = monkey_jobs
                            analysis['inspection_reason'] = inspection_reason
                            analysis['analysis_timestamp'] = time.strftime("%Y-%m-%d %H:%M:%S")
                            analysis['gemini_attempt'] = attempt + 1
                            analysis['gemini_temperature'] = temperature
                            
                            logger.info(f"Recovered analysis for {book_id} using fallback method")
                            return analysis
                    except Exception as fallback_error:
                        logger.warning(f"Fallback extraction also failed: {fallback_error}")
                    
                    # If this is the last attempt, log the response
                    if attempt == 3:
                        logger.error(f"Raw response causing JSON error: {response.text[:1000]}...")
                        
            except Exception as e:
                logger.warning(f"Attempt {attempt + 1}: General error for {book_id}: {e}")
                
                # If this is the last attempt, log the full error
                if attempt == 3:
                    logger.error(f"All attempts failed for {book_id}: {e}")
        
        # All attempts failed - return error analysis
        return {
            "book_id": book_id,
            "name_azure": name_azure,
            "name_monkey": name_monkey,
            "original_azure_jobs": azure_jobs,
            "original_monkey_jobs": monkey_jobs,
            "inspection_reason": inspection_reason,
            "error": "Failed to analyze after 4 attempts",
            "analysis_timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        }
    
    def process_flagged_records(self, flagged_csv_path: str, comparison_csv_path: str, 
                               output_dir: str, max_records: Optional[int] = None) -> Dict:
        """Process all flagged records and generate Gemini analysis"""
        
        # Load data
        flagged_df = self.load_flagged_records(flagged_csv_path)
        comparison_df = self.load_comparison_dataframe(comparison_csv_path)
        
        # Create output directory
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        # Limit records if specified
        if max_records:
            flagged_df = flagged_df.head(max_records)
            logger.info(f"Processing limited to {max_records} records")
        
        analyses = []
        successful_analyses = 0
        failed_analyses = 0
        
        # Process each flagged record
        for idx, record in flagged_df.iterrows():
            try:
                book_id = record['book_id']
                name_azure = record['name_azure']
                name_monkey = record['name_monkey']
                inspection_reason = record['inspection_reason']
                
                logger.info(f"Processing {idx + 1}/{len(flagged_df)}: {book_id} - {name_azure}")
                
                # Get job data for this record (including titles, locations, years)
                azure_job_data, monkey_job_data = self.extract_job_data_for_record(comparison_df, book_id, name_azure, name_monkey)
                
                # Get markdown content
                azure_content, monkey_content = self.get_markdown_content(comparison_df, book_id, name_azure, name_monkey)
                
                # Check if we have content to analyze
                if not azure_content and not monkey_content:
                    logger.warning(f"No markdown content found for {book_id}")
                    continue
                
                # Analyze with Gemini
                analysis = self.analyze_job_discrepancy(
                    name_azure, name_monkey, book_id,
                    azure_job_data, monkey_job_data,
                    azure_content, monkey_content,
                    inspection_reason
                )
                
                analyses.append(analysis)
                
                if 'error' in analysis:
                    failed_analyses += 1
                else:
                    successful_analyses += 1
                
                # Save individual analysis
                individual_output = output_path / f"{book_id}_gemini_analysis.json"
                with open(individual_output, 'w', encoding='utf-8') as f:
                    json.dump(analysis, f, indent=2, ensure_ascii=False)
                
                # Add small delay to avoid rate limiting
                time.sleep(0.5)
                
            except Exception as e:
                logger.error(f"Error processing record {idx}: {e}")
                failed_analyses += 1
        
        # Create summary results
        results = {
            "input_flagged_csv": flagged_csv_path,
            "input_comparison_csv": comparison_csv_path,
            "output_directory": str(output_path),
            "total_flagged_records": len(flagged_df),
            "successful_analyses": successful_analyses,
            "failed_analyses": failed_analyses,
            "processing_timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "gemini_model": self.model,
            "analyses": analyses
        }
        
        # Save combined results
        combined_output = output_path / "gemini_job_analysis_results.json"
        with open(combined_output, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        
        # Create analysis summary CSV
        summary_data = []
        for analysis in analyses:
            if 'error' not in analysis:
                summary_data.append({
                    'book_id': analysis['book_id'],
                    'name_azure': analysis['name_azure'],
                    'name_monkey': analysis['name_monkey'],
                    'inspection_reason': analysis['inspection_reason'],
                    'correct_job_titles': '; '.join([str(x) for x in analysis.get('correct_job_titles', []) if x is not None]),
                    'correct_job_locations': '; '.join([str(x) for x in analysis.get('correct_job_locations', []) if x is not None]),
                    'correct_job_years': '; '.join([str(x) for x in analysis.get('correct_job_years', []) if x is not None]),
                    'azure_accuracy_rating': analysis.get('azure_accuracy_rating', 0),
                    'monkey_accuracy_rating': analysis.get('monkey_accuracy_rating', 0),
                    'azure_analysis': analysis.get('azure_analysis', ''),
                    'monkey_analysis': analysis.get('monkey_analysis', ''),
                    'text_quality_issues': analysis.get('text_quality_issues', ''),
                    'recommendation': analysis.get('recommendation', ''),
                    'confidence_level': analysis.get('confidence_level', 'unknown'),
                    'original_azure_jobs': '; '.join([str(x) for x in analysis.get('original_azure_jobs', []) if x is not None]),
                    'original_monkey_jobs': '; '.join([str(x) for x in analysis.get('original_monkey_jobs', []) if x is not None]),
                    'analysis_timestamp': analysis.get('analysis_timestamp', '')
                })
        
        if summary_data:
            summary_df = pd.DataFrame(summary_data)
            summary_csv = output_path / "gemini_job_analysis_summary.csv"
            summary_df.to_csv(summary_csv, index=False)
            logger.info(f"Saved analysis summary to: {summary_csv}")
        
        logger.info(f"Processing complete. Results saved to: {output_path}")
        
        # Create corrected CSV files if we have successful analyses
        if successful_analyses > 0:
            logger.info("Creating corrected CSV files...")
            try:
                correction_files = self.create_corrected_csv_files(results, output_dir=str(output_path / "corrected_csv"))
                results['corrected_files'] = correction_files
                
                if 'error' not in correction_files and 'warning' not in correction_files:
                    logger.info(f"Successfully created {len(correction_files)} corrected files")
                else:
                    logger.warning(f"Correction file creation completed with issues: {correction_files}")
                    
            except Exception as e:
                logger.error(f"Failed to create corrected CSV files: {e}")
                results['correction_error'] = str(e)
        
        return results

    def create_corrected_csv_files(self, results: Dict, 
                                  azure_source_csv: str = r'd:\data\HCNC\norway\biographies\storage\AzureOCR\output_csv\extracted_all_names_portraits_biographies_final.csv',
                                  monkey_source_csv: str = r'd:\data\HCNC\norway\biographies\storage\MonkeyOCR\output_csv\extracted_all_names_portraits_biographies_final.csv',
                                  output_dir: str = r'd:\data\HCNC\norway\biographies\storage\GeminiOCR_Corrections\output_csv') -> Dict[str, str]:
        """
        Create corrected CSV files based on Gemini analysis results.
        
        Parameters:
        -----------
        results : Dict
            Results from process_flagged_records()
        azure_source_csv : str
            Path to original Azure CSV file
        monkey_source_csv : str
            Path to original Monkey CSV file
        output_dir : str
            Output directory for corrected CSV files
        
        Returns:
        --------
        Dict[str, str]
            Dictionary with paths to created files
        """
        
        logger.info("Creating corrected CSV files based on Gemini analysis...")
        
        # Create output directory
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        # Load original CSV files
        try:
            azure_df = pd.read_csv(azure_source_csv)
            monkey_df = pd.read_csv(monkey_source_csv)
            logger.info(f"Loaded Azure CSV: {len(azure_df)} records")
            logger.info(f"Loaded Monkey CSV: {len(monkey_df)} records")
        except Exception as e:
            logger.error(f"Failed to load source CSV files: {e}")
            return {"error": str(e)}
        
        # Process Gemini corrections
        azure_corrections = {}
        monkey_corrections = {}
        correction_summary = []
        
        for analysis in results['analyses']:
            if 'error' in analysis:
                continue
                
            book_id = analysis['book_id']
            name_azure = analysis['name_azure']
            name_monkey = analysis['name_monkey']
            
            # Check if we have meaningful corrections (not all null)
            correct_jobs = analysis.get('correct_job_titles', [])
            correct_locations = analysis.get('correct_job_locations', [])
            correct_years = analysis.get('correct_job_years', [])
            
            # Only create corrections if there are actual job titles
            has_corrections = any(job is not None and job != "" for job in correct_jobs)
            
            if has_corrections:
                # Create corrected job data structure
                corrected_jobs = []
                for i in range(len(correct_jobs)):
                    if i < len(correct_jobs) and correct_jobs[i] is not None and correct_jobs[i] != "":
                        job_entry = {"title": str(correct_jobs[i])}
                        
                        # Add location if available
                        if i < len(correct_locations) and correct_locations[i] is not None and correct_locations[i] != "":
                            job_entry["location"] = str(correct_locations[i])
                        else:
                            job_entry["location"] = ""
                        
                        # Add years if available
                        if i < len(correct_years) and correct_years[i] is not None and correct_years[i] != "":
                            job_entry["years"] = str(correct_years[i])
                        else:
                            job_entry["years"] = ""
                        
                        corrected_jobs.append(job_entry)
                
                # Store corrections for both Azure and Monkey systems
                # We'll apply the same corrections to both since Gemini determined the "correct" version
                correction_key = f"{book_id}_{name_azure}_{name_monkey}"
                azure_corrections[correction_key] = {
                    'book_id': book_id,
                    'name_azure': name_azure,
                    'name_monkey': name_monkey,
                    'corrected_jobs': corrected_jobs,
                    'analysis': analysis
                }
                monkey_corrections[correction_key] = azure_corrections[correction_key].copy()
                
                correction_summary.append({
                    'book_id': book_id,
                    'name_azure': name_azure,
                    'name_monkey': name_monkey,
                    'original_azure_jobs': analysis.get('original_azure_jobs', []),
                    'original_monkey_jobs': analysis.get('original_monkey_jobs', []),
                    'corrected_job_count': len(corrected_jobs),
                    'azure_rating': analysis.get('azure_accuracy_rating', 0),
                    'monkey_rating': analysis.get('monkey_accuracy_rating', 0),
                    'recommendation': analysis.get('recommendation', '')
                })
        
        logger.info(f"Found {len(azure_corrections)} records with corrections")
        
        if not azure_corrections:
            logger.warning("No corrections found to apply")
            return {"warning": "No corrections found"}
        
        # Apply corrections to Azure dataframe
        azure_corrected_df = self._apply_corrections_to_dataframe(
            azure_df.copy(), azure_corrections, "Azure"
        )
        
        # Apply corrections to Monkey dataframe  
        monkey_corrected_df = self._apply_corrections_to_dataframe(
            monkey_df.copy(), monkey_corrections, "Monkey"
        )
        
        # Save corrected files
        output_files = {}
        
        azure_output_path = output_path / "azure_extracted_all_names_portraits_biographies_final.csv"
        azure_corrected_df.to_csv(azure_output_path, index=False)
        output_files['azure_corrected'] = str(azure_output_path)
        logger.info(f"Saved Azure corrected CSV: {azure_output_path}")
        
        monkey_output_path = output_path / "monkey_extracted_all_names_portraits_biographies_final.csv"
        monkey_corrected_df.to_csv(monkey_output_path, index=False)
        output_files['monkey_corrected'] = str(monkey_output_path)
        logger.info(f"Saved Monkey corrected CSV: {monkey_output_path}")
        
        # Create a unified "best of both" corrected file
        unified_corrected_df = self._create_unified_corrected_dataframe(
            azure_df, monkey_df, azure_corrections, results
        )
        
        unified_output_path = output_path / "extracted_all_names_portraits_biographies_final.csv"
        unified_corrected_df.to_csv(unified_output_path, index=False)
        output_files['unified_corrected'] = str(unified_output_path)
        logger.info(f"Saved unified corrected CSV: {unified_output_path}")
        
        # Save correction summary
        if correction_summary:
            summary_df = pd.DataFrame(correction_summary)
            summary_path = output_path / "gemini_corrections_summary.csv"
            summary_df.to_csv(summary_path, index=False)
            output_files['corrections_summary'] = str(summary_path)
            logger.info(f"Saved corrections summary: {summary_path}")
        
        # Create metadata file
        metadata = {
            'creation_timestamp': time.strftime("%Y-%m-%d %H:%M:%S"),
            'source_azure_csv': azure_source_csv,
            'source_monkey_csv': monkey_source_csv,
            'total_corrections_applied': len(azure_corrections),
            'gemini_model': self.model,
            'files_created': output_files
        }
        
        metadata_path = output_path / "correction_metadata.json"
        with open(metadata_path, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)
        output_files['metadata'] = str(metadata_path)
        
        logger.info(f"Correction process complete. Created {len(output_files)} files in {output_dir}")
        return output_files
    
    def _apply_corrections_to_dataframe(self, df: pd.DataFrame, corrections: Dict, source_name: str) -> pd.DataFrame:
        """Apply Gemini corrections to a dataframe by updating biography_json entries"""
        
        logger.info(f"Applying corrections to {source_name} dataframe...")
        corrections_applied = 0
        
        # Add a column to track corrections if it doesn't exist
        if 'gemini_corrected' not in df.columns:
            df['gemini_corrected'] = False
        
        for correction_key, correction_data in corrections.items():
            book_id = correction_data['book_id']
            name_azure = correction_data['name_azure']
            name_monkey = correction_data['name_monkey']
            corrected_jobs = correction_data['corrected_jobs']
            
            # Find matching record in dataframe
            # Try exact match first
            matching_rows = df[df['book_id'] == book_id]
            
            if len(matching_rows) == 0:
                logger.warning(f"No matching record found for book_id: {book_id}")
                continue
            
            # If multiple matches, try to narrow down by name
            if len(matching_rows) > 1:
                # Try to match by name (handling potential encoding differences)
                name_matches = matching_rows[
                    (matching_rows['name'].str.contains(name_azure.split(',')[0], case=False, na=False)) |
                    (matching_rows['name'].str.contains(name_monkey.split(',')[0], case=False, na=False))
                ]
                if len(name_matches) > 0:
                    matching_rows = name_matches
            
            # Apply correction to the first matching row
            for idx in matching_rows.index[:1]:  # Only apply to first match
                try:
                    # Parse existing biography_json
                    biography_json_str = df.at[idx, 'biography_json']
                    
                    if pd.isna(biography_json_str) or biography_json_str == '':
                        logger.warning(f"Empty biography_json for {book_id}, skipping")
                        continue
                    
                    biography_data = json.loads(biography_json_str)
                    
                    # Update jobs section with corrected data
                    biography_data['jobs'] = corrected_jobs
                    
                    # Add correction metadata
                    biography_data['gemini_correction'] = {
                        'corrected_timestamp': time.strftime("%Y-%m-%d %H:%M:%S"),
                        'gemini_model': self.model,
                        'original_job_count_azure': len(correction_data['analysis'].get('original_azure_jobs', [])),
                        'original_job_count_monkey': len(correction_data['analysis'].get('original_monkey_jobs', [])),
                        'corrected_job_count': len(corrected_jobs),
                        'azure_accuracy_rating': correction_data['analysis'].get('azure_accuracy_rating', 0),
                        'monkey_accuracy_rating': correction_data['analysis'].get('monkey_accuracy_rating', 0)
                    }
                    
                    # Convert back to JSON string
                    updated_json = json.dumps(biography_data, ensure_ascii=False)
                    
                    # Update the dataframe
                    df.at[idx, 'biography_json'] = updated_json
                    df.at[idx, 'gemini_corrected'] = True
                    corrections_applied += 1
                    
                    logger.debug(f"Applied correction to {book_id}: {len(corrected_jobs)} jobs")
                    
                except (json.JSONDecodeError, KeyError) as e:
                    logger.error(f"Failed to apply correction to {book_id}: {e}")
                    continue
        
        logger.info(f"Applied {corrections_applied} corrections to {source_name} dataframe")
        return df
    
    def _create_unified_corrected_dataframe(self, azure_df: pd.DataFrame, monkey_df: pd.DataFrame, 
                                          corrections: Dict, results: Dict) -> pd.DataFrame:
        """Create a unified dataframe using the best source for each record based on Gemini recommendations"""
        
        logger.info("Creating unified corrected dataframe...")
        
        # Start with Azure dataframe as base
        unified_df = azure_df.copy()
        
        # Add correction tracking column if it doesn't exist
        if 'gemini_corrected' not in unified_df.columns:
            unified_df['gemini_corrected'] = False
        
        # Apply corrections first
        unified_df = self._apply_corrections_to_dataframe(unified_df, corrections, "Unified")
        
        # For records with corrections, decide which source to use based on Gemini recommendations
        for analysis in results['analyses']:
            if 'error' in analysis:
                continue
                
            book_id = analysis['book_id']
            recommendation = analysis.get('recommendation', '')
            azure_rating = analysis.get('azure_accuracy_rating', 0)
            monkey_rating = analysis.get('monkey_accuracy_rating', 0)
            
            # If Monkey performed significantly better, use Monkey data for non-job fields
            if monkey_rating > azure_rating + 2 or 'Monkey' in recommendation:
                # Find matching records
                azure_matches = unified_df[unified_df['book_id'] == book_id]
                monkey_matches = monkey_df[monkey_df['book_id'] == book_id]
                
                if len(azure_matches) > 0 and len(monkey_matches) > 0:
                    azure_idx = azure_matches.index[0]
                    monkey_idx = monkey_matches.index[0]
                    
                    # Keep the corrected jobs but use other fields from Monkey if they're better
                    try:
                        azure_bio = json.loads(unified_df.at[azure_idx, 'biography_json'])
                        monkey_bio = json.loads(monkey_df.at[monkey_idx, 'biography_json'])
                        
                        # Preserve corrected jobs from unified dataframe
                        corrected_jobs = azure_bio.get('jobs', [])
                        
                        # Use Monkey data for other fields if Monkey performed better
                        for field in ['name', 'title', 'birth_date', 'birth_place', 'death_date', 
                                     'father_name', 'father_job', 'mother_name', 'educations', 
                                     'spouses', 'children', 'stays_abroad']:
                            if field in monkey_bio and monkey_bio[field]:
                                azure_bio[field] = monkey_bio[field]
                        
                        # Restore corrected jobs and correction metadata
                        azure_bio['jobs'] = corrected_jobs
                        if 'gemini_correction' in azure_bio:
                            # Preserve the correction metadata from the original correction
                            pass  # Already there from the correction process
                        
                        # Update unified dataframe
                        unified_df.at[azure_idx, 'biography_json'] = json.dumps(azure_bio, ensure_ascii=False)
                        # Keep gemini_corrected = True since we applied corrections
                        
                        # Also update name column if available
                        if 'name' in monkey_df.columns:
                            unified_df.at[azure_idx, 'name'] = monkey_df.at[monkey_idx, 'name']
                        
                        logger.debug(f"Updated {book_id} with Monkey data (better performer)")
                        
                    except (json.JSONDecodeError, KeyError) as e:
                        logger.error(f"Failed to merge data for {book_id}: {e}")
        
        return unified_df

def main():
    """Main function"""
    
    # Initialize key vault
    api_key = None
    try:
        if KEYVAULT_AVAILABLE and KeyVault is not None:
            vault = KeyVault()
            #api_key = vault.get_key("AMDGeminiFlashKey")           
            api_key = vault.get_key("SDUGeminiAPI")
            logger.info("API key retrieved from KeyVault in main()")
        else:
            logger.info("KeyVault not available in main(), will try environment variable")
    except Exception as e:
        logger.warning(f"Could not access key vault in main(): {e}")
        api_key = None
    
    parser = argparse.ArgumentParser(description="Analyze flagged job overlap records using Gemini-2.5-Flash")
    parser.add_argument("--flagged-csv", 
                        default="flagged_job_overlap_records.csv",
                        help="Path to flagged job overlap records CSV")
    parser.add_argument("--comparison-csv", 
                        default="comprehensive_comparison_dataframe.csv",
                        help="Path to comprehensive comparison dataframe CSV")
    parser.add_argument("--output-dir", 
                        default="gemini_job_analysis_output",
                        help="Output directory for analysis results")
    parser.add_argument("--api-key", 
                        default=api_key,
                        help="Gemini API key")
    parser.add_argument("--max-records", 
                        type=int,
                        help="Maximum number of records to process (for testing)")
    parser.add_argument("--azure-source-csv",
                        default=r'd:\data\HCNC\norway\biographies\storage\AzureOCR\output_csv\extracted_all_names_portraits_biographies_final.csv',
                        help="Path to Azure source CSV file for corrections")
    parser.add_argument("--monkey-source-csv", 
                        default=r'd:\data\HCNC\norway\biographies\storage\MonkeyOCR\output_csv\extracted_all_names_portraits_biographies_final.csv',
                        help="Path to Monkey source CSV file for corrections")
    parser.add_argument("--create-corrections",
                        action="store_true",
                        help="Create corrected CSV files based on Gemini analysis")
    parser.add_argument("--log-level", 
                        default="INFO", 
                        choices=["DEBUG", "INFO", "WARNING", "ERROR"])
    
    args = parser.parse_args()
    
    # Set log level
    logging.getLogger().setLevel(getattr(logging, args.log_level))
    
    # Check for API key
    if not args.api_key:
        print("Error: Gemini API key is required!")
        print("Set it via:")
        print("1. Environment variable: AMDGeminiFlashKey")
        print("2. Command line: --api-key 'your-key-here'")
        print("3. Key vault (if available)")
        return
    
    # Check input files
    if not Path(args.flagged_csv).exists():
        print(f"Error: Flagged CSV file not found: {args.flagged_csv}")
        return
    
    if not Path(args.comparison_csv).exists():
        print(f"Error: Comparison CSV file not found: {args.comparison_csv}")
        return
    
    try:
        # Initialize resolver
        resolver = GeminiJobResolver(api_key=args.api_key)
        
        logger.info(f"Processing flagged records from: {args.flagged_csv}")
        logger.info(f"Using comparison data from: {args.comparison_csv}")
        logger.info(f"Output directory: {args.output_dir}")
        
        if args.max_records:
            logger.info(f"Limited to {args.max_records} records for testing")
        
        # Process flagged records
        results = resolver.process_flagged_records(
            args.flagged_csv,
            args.comparison_csv,
            args.output_dir,
            args.max_records
        )
        
        # Create corrected CSV files if requested and we have successful analyses
        if args.create_corrections and results['successful_analyses'] > 0:
            logger.info("Creating corrected CSV files...")
            try:
                correction_files = resolver.create_corrected_csv_files(
                    results, 
                    azure_source_csv=args.azure_source_csv,
                    monkey_source_csv=args.monkey_source_csv,
                    output_dir=args.output_dir + "_corrections"
                )
                results['corrected_files'] = correction_files
                
                if 'error' not in correction_files and 'warning' not in correction_files:
                    logger.info(f"Successfully created corrected CSV files")
                    print(f"\nCorrected CSV files created:")
                    for file_type, file_path in correction_files.items():
                        print(f"• {file_type}: {file_path}")
                else:
                    logger.warning(f"Correction file creation completed with issues")
                    print(f"Warning: {correction_files}")
                    
            except Exception as e:
                logger.error(f"Failed to create corrected CSV files: {e}")
                print(f"Error creating corrected files: {e}")
        
        # Print summary
        print(f"\n{'='*60}")
        print("GEMINI JOB ANALYSIS SUMMARY")
        print(f"{'='*60}")
        print(f"Total flagged records: {results['total_flagged_records']}")
        print(f"Successful analyses: {results['successful_analyses']}")
        print(f"Failed analyses: {results['failed_analyses']}")
        print(f"Success rate: {(results['successful_analyses'] / results['total_flagged_records'] * 100):.1f}%")
        print(f"Results saved to: {results['output_directory']}")
        
        # Show some sample results
        if results['successful_analyses'] > 0:
            print(f"\nSample analysis results:")
            count = 0
            for analysis in results['analyses']:
                if 'error' not in analysis and count < 3:
                    print(f"\n{count + 1}. {analysis['book_id']} - {analysis['name_azure']}")
                    print(f"   Correct jobs: {analysis.get('correct_job_titles', [])}")
                    print(f"   Azure rating: {analysis.get('azure_accuracy_rating', 0)}/10")
                    print(f"   Monkey rating: {analysis.get('monkey_accuracy_rating', 0)}/10")
                    print(f"   Recommendation: {analysis.get('recommendation', 'N/A')}")
                    count += 1
        
        print(f"\nDetailed results available in:")
        print(f"• gemini_job_analysis_results.json - Complete analysis")
        print(f"• gemini_job_analysis_summary.csv - Summary table")
        print(f"• Individual JSON files for each record")
        
        if args.create_corrections:
            print(f"\nTo create corrected CSV files, the analysis will generate:")
            print(f"• Azure corrected CSV with updated job data")
            print(f"• Monkey corrected CSV with updated job data") 
            print(f"• Unified best-of-both corrected CSV")
            print(f"• Corrections summary and metadata files")
        
    except Exception as e:
        logger.error(f"Processing failed: {e}")
        print(f"Error: {e}")

if __name__ == "__main__":
    main()

## python gemini_job_resolver.py --output-dir gemini_analysis_complete

## python gemini_job_resolver.py --output-dir production_run --create-corrections

## python gemini_job_resolver.py --max-records 5 --output-dir test_5_records --create-corrections

# python gemini_job_resolver.py --output-dir "D:\data\HCNC\norway\biographies\storage\GeminiOCR_validator" --create-corrections 