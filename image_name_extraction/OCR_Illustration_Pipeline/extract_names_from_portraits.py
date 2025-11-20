#!/usr/bin/env python3
"""
Extract Names from Portrait Associations
Uses the portrait association JSON files to create the names list.
This is more reliable than running a separate name extraction since the portrait
associator already identified all biographical entries.
"""
import os
import json
import argparse
from pathlib import Path
from collections import defaultdict


def extract_names_from_portrait_jsons(portrait_dir: str, output_dir: str):
    """
    Extract all unique person names from portrait association JSON files
    
    Args:
        portrait_dir: Directory containing *_portrait_associations.json files
        output_dir: Directory to save the output JSON
    """
    portrait_dir = Path(portrait_dir)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Dictionary to collect names by book_id
    books = defaultdict(list)
    
    # Find all portrait association JSON files
    portrait_files = list(portrait_dir.glob("*_portrait_associations.json"))
    
    print(f"Found {len(portrait_files)} portrait association files")
    
    for json_file in portrait_files:
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Handle two file structures:
            # 1. Individual book files: {book_id: "...", biographical_entries: [...]}
            # 2. All-books summary: {books: {book_id1: {...}, book_id2: {...}}}
            
            if 'books' in data and isinstance(data['books'], dict):
                # All-books summary format - skip it, we'll process individual files
                print(f"  Skipping summary file: {json_file.name}")
                continue
            
            book_id = data.get('book_id')
            if not book_id:
                print(f"  Warning: No book_id in {json_file.name}")
                continue
            
            # Extract unique names from biographical_entries
            seen_names = set()
            
            if 'biographical_entries' in data:
                for entry in data['biographical_entries']:
                    person_name = entry.get('associated_person')
                    
                    # Skip entries with no associated person or null
                    if not person_name or person_name.lower() == 'null':
                        continue
                    
                    # Skip duplicates within the same book
                    if person_name in seen_names:
                        continue
                    
                    seen_names.add(person_name)
                    
                    # Create a biographical entry (minimal format, just the name)
                    books[book_id].append({
                        "name": person_name,
                        "source": "portrait_association"
                    })
            
            if seen_names:
                print(f"  {book_id}: {len(seen_names)} unique name(s)")
        
        except Exception as e:
            print(f"  Error processing {json_file.name}: {e}")
            continue
    
    # Create output structure matching gemini_all_names.py format
    results = {
        "input_path": str(portrait_dir),
        "output_path": str(output_dir),
        "books_found": len(books),
        "source": "portrait_associations",
        "books": {}
    }
    
    total_entries = 0
    for book_id, entries in books.items():
        results["books"][book_id] = {
            "book_id": book_id,
            "total_entries": len(entries),
            "biographical_entries": entries
        }
        total_entries += len(entries)
    
    # Save combined results
    output_file = output_dir / "all_books_names.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    print(f"\n{'='*60}")
    print(f"NAME EXTRACTION FROM PORTRAIT ASSOCIATIONS SUMMARY")
    print(f"{'='*60}")
    print(f"Input path: {portrait_dir}")
    print(f"Books found: {len(books)}")
    
    for book_id, entries in sorted(books.items()):
        print(f"  {book_id}: {len(entries)} biographical entries")
    
    print(f"\nTotal biographical entries found: {total_entries}")
    print(f"Results saved to: {output_file}")
    print(f"{'='*60}\n")


def main():
    parser = argparse.ArgumentParser(
        description='Extract names from portrait association JSON files'
    )
    parser.add_argument('input_path', help='Directory containing portrait association JSON files')
    parser.add_argument('output_path', help='Directory to save output JSON')
    
    args = parser.parse_args()
    
    extract_names_from_portrait_jsons(args.input_path, args.output_path)


if __name__ == "__main__":
    main()
