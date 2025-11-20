import pandas as pd
import os
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend
import matplotlib.pyplot as plt
from PIL import Image
import textwrap
import warnings
import json
import argparse
import sys

warnings.filterwarnings('ignore')

def display_image(ax, path, title, is_portrait=True):
    """Helper function to display an image on a matplotlib axis."""
    try:
        if pd.notna(path) and path and os.path.exists(path):
            img = Image.open(path)
            ax.imshow(img)
            ax.set_title(title, fontsize=10, wrap=True)
            ax.set_xticks([])
            ax.set_yticks([])
        elif pd.notna(path) and path:
            # Path provided but doesn't exist - show detailed error
            ax.text(0.5, 0.5, f'File not found:\n{path}', 
                    ha='center', va='center', fontsize=7, bbox=dict(facecolor='lightyellow'),
                    wrap=True)
            ax.set_title(title, fontsize=10)
            ax.set_xticks([])
            ax.set_yticks([])
            ax.set_xlim(0, 1)
            ax.set_ylim(0, 1)
        else:
            ax.text(0.5, 0.5, 'No Portrait', 
                    ha='center', va='center', fontsize=8, bbox=dict(facecolor='lightgray'))
            ax.set_title(title, fontsize=10)
            ax.set_xticks([])
            ax.set_yticks([])
            ax.set_xlim(0, 1)
            ax.set_ylim(0, 1)
    except Exception as e:
        ax.text(0.5, 0.5, f'Error loading:\n{str(e)}\n{os.path.basename(path) if pd.notna(path) and path else "N/A"}', 
                ha='center', va='center', fontsize=7, wrap=True)
        ax.set_title(title, fontsize=8)
        ax.set_xticks([])
        ax.set_yticks([])
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)

def display_text_chunk(ax, text, title, max_chars=500):
    """Helper function to display text chunk on a matplotlib axis."""
    try:
        if pd.notna(text) and text.strip():
            display_text = text[:max_chars]
            if len(text) > max_chars:
                display_text += "\n... [TRUNCATED]"
            
            wrapped_text = textwrap.fill(display_text, width=65)
            ax.text(0.02, 0.95, wrapped_text, ha='left', va='top', fontsize=10, 
                   wrap=True, transform=ax.transAxes)
            ax.set_title(title, fontsize=10)
        else:
            ax.text(0.5, 0.5, 'No Text Chunk Available', 
                    ha='center', va='center', fontsize=8, bbox=dict(facecolor='lightgray'))
            ax.set_title(title, fontsize=8)
    except Exception as e:
        ax.text(0.5, 0.5, f'Error displaying text: {str(e)}', 
                ha='center', va='center', fontsize=7)
        ax.set_title(title, fontsize=8)
    finally:
        ax.set_xticks([])
        ax.set_yticks([])
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)

def format_biography_json(bio_json):
    """Formats the biography JSON object into a readable string."""
    if not isinstance(bio_json, dict):
        return "Invalid or missing JSON data"

    lines = []
    
    name = bio_json.get('name', 'N/A')
    title = bio_json.get('title', '')
    lines.append(f"**{name}** ({title})")
    
    birth_date = bio_json.get('birth_date', '')
    birth_place = bio_json.get('birth_place', '')
    death_date = bio_json.get('death_date', '')
    if birth_date or birth_place:
        lines.append(f"Born: {birth_date} in {birth_place}")
    if death_date:
        lines.append(f"Died: {death_date}")

    father = bio_json.get('father_name', '')
    mother = bio_json.get('mother_name', '')
    if father or mother:
        lines.append(f"Parents: {father} & {mother}")

    spouses = bio_json.get('spouses', [])
    if spouses:
        lines.append("\n**Spouse(s):**")
        for s in spouses:
            lines.append(f"- {s.get('name', '')} (b. {s.get('birth_date', 'N/A')})")
    
    children = bio_json.get('children', [])
    if children:
        lines.append("\n**Children:**")
        for c in children:
            lines.append(f"- {c.get('name', '')} (b. {c.get('birth_date', 'N/A')})")

    jobs = bio_json.get('jobs', [])
    if jobs:
        lines.append("\n**Career:**")
        for j in jobs:
            lines.append(f"- {j.get('title', '')} at {j.get('location', '')} ({j.get('years', '')})")

    educations = bio_json.get('educations', [])
    if educations:
        lines.append("\n**Education:**")
        for e in educations:
            lines.append(f"- {e.get('title', '')}, {e.get('institution', '')} ({e.get('year', '')})")
            
    return "\n".join(lines)

def display_structured_data(ax, json_str, title):
    """Helper function to display formatted JSON data on a matplotlib axis."""
    text_to_display = ""
    try:
        if pd.notna(json_str) and json_str.strip():
            bio_data = json.loads(json_str)
            text_to_display = format_biography_json(bio_data)
        else:
            text_to_display = "No JSON data available"
    except (json.JSONDecodeError, TypeError):
        text_to_display = "Error: Invalid JSON format"

    ax.text(0.02, 0.95, text_to_display, ha='left', va='top', fontsize=10, transform=ax.transAxes)
    ax.set_title(title, fontsize=8)
    ax.set_xticks([])
    ax.set_yticks([])
    ax.set_facecolor('#f9f9f9')

def visualize_individual_data(book_id, df, original_images_path, portrait_base_folder, output_folder):
    """Generate visualization for all persons in a book_id."""
    book_df = df[df['book_id'] == book_id].copy()
    
    if book_df.empty:
        print(f"  No data found for book_id: {book_id}")
        return
        
    print(f"  Generating {len(book_df)} visualizations for {book_id}")
    
    for i, (idx, row) in enumerate(book_df.iterrows()):
        fig = plt.figure(figsize=(20, 10), constrained_layout=True)
        gs_main = fig.add_gridspec(nrows=1, ncols=3, width_ratios=[1, 1, 1], wspace=0.05)
        
        # LEFT: Full biography page - look for image directly in original_images_path
        ax_full_bio = fig.add_subplot(gs_main[0, 0])
        
        # Try different image formats in the original_images_path directory
        possible_paths = [
            os.path.join(original_images_path, f"{book_id}.jpg"),
            os.path.join(original_images_path, f"{book_id}.jp2"),
            os.path.join(original_images_path, f"{book_id}.png"),
            os.path.join(original_images_path, f"{book_id}.tif"),
            os.path.join(original_images_path, f"{book_id}.tiff")
        ]
        
        full_image_path = None
        for path in possible_paths:
            if os.path.exists(path):
                full_image_path = path
                break
        
        display_image(ax_full_bio, full_image_path, f"Full Biography Page: {book_id}", is_portrait=False)
        
        # MIDDLE: Portrait + Structured Data
        gs_middle = gs_main[0, 1].subgridspec(nrows=2, ncols=1, height_ratios=[1, 2], hspace=0.15)
        
        ax_portrait = fig.add_subplot(gs_middle[0, 0])
        if pd.notna(row['portrait_filename']) and row['portrait_filename'] != '':
            # Handle multiple portraits (pipe-separated) - use the first one for visualization
            portrait_filename = str(row['portrait_filename']).split('|')[0].strip()
            
            # Portrait is in the imgs/ subfolder within the portrait base folder
            portrait_path = os.path.join(portrait_base_folder, book_id, "imgs", portrait_filename)
            
            # Show all portrait filenames in title if multiple exist
            all_portraits = str(row['portrait_filename'])
            if '|' in all_portraits:
                portrait_count = len(all_portraits.split('|'))
                portrait_title = f"Portrait 1 of {portrait_count}: {row['name']}\n{portrait_filename}"
            else:
                portrait_title = f"Portrait: {row['name']}\n{portrait_filename}"
        else:
            portrait_path = None
            portrait_title = f"No Portrait: {row['name']}"
        
        display_image(ax_portrait, portrait_path, portrait_title)
        
        ax_json = fig.add_subplot(gs_middle[1, 0])
        json_str = row.get('biography_json')
        json_title = f"Structured Data: {row['name']}"
        display_structured_data(ax_json, json_str, json_title)
        
        # RIGHT: Markdown chunk
        ax_markdown = fig.add_subplot(gs_main[0, 2])
        chunk_text = row['markdown_chunk']
        chunk_title = f"Biographical Text-Chunk: {row['name']}"
        if pd.notna(chunk_text) and chunk_text.strip():
            chunk_title += f" ({len(chunk_text)} chars)"
        
        display_text_chunk(ax_markdown, chunk_text, chunk_title, max_chars=2000)
        
        fig.suptitle(f"Data Inspection: {row['name']} ({book_id})", fontsize=16)
        
        # Save the figure
        safe_name = row['name'].replace('/', '_').replace('\\', '_').replace(',', '')
        output_file = os.path.join(output_folder, f"{book_id}_{i+1:02d}_{safe_name}.png")
        plt.savefig(output_file, dpi=150, bbox_inches='tight')
        plt.close(fig)

def main():
    parser = argparse.ArgumentParser(description='Visualize OCR pipeline results')
    parser.add_argument('csv_file', help='Path to the final CSV file with biographies')
    parser.add_argument('original_images_path', help='Path to corpus folder containing original full-page images')
    parser.add_argument('portrait_base_folder', help='Base folder containing book_id subfolders with portrait imgs/')
    parser.add_argument('output_folder', help='Folder to save visualization images')
    
    args = parser.parse_args()
    
    # Create output folder
    os.makedirs(args.output_folder, exist_ok=True)
    
    # Load data
    try:
        df = pd.read_csv(args.csv_file)
        print(f"Loaded {len(df)} entries from {args.csv_file}")
    except FileNotFoundError:
        print(f"Error: CSV file not found: {args.csv_file}")
        sys.exit(1)
    
    # Deduplicate by name - prefer entries with portraits
    print(f"Deduplicating entries by name...")
    df['has_portrait'] = df['portrait_filename'].notna() & (df['portrait_filename'] != '')
    df = df.sort_values('has_portrait', ascending=False)  # Entries with portraits first
    df_unique = df.drop_duplicates(subset=['name'], keep='first')
    print(f"  {len(df)} total entries -> {len(df_unique)} unique persons")
    print(f"  Persons with portraits: {df_unique['has_portrait'].sum()}")
    
    # Get unique book IDs from deduplicated data
    book_ids = df_unique['book_id'].unique()
    print(f"Found {len(book_ids)} unique book IDs")
    print(f"Looking for original images in: {args.original_images_path}")
    print(f"Looking for portraits in: {args.portrait_base_folder}")
    
    # Generate visualizations for each book (using deduplicated data)
    for book_id in book_ids:
        visualize_individual_data(book_id, df_unique, args.original_images_path, args.portrait_base_folder, args.output_folder)
    
    print(f"\nVisualization complete! Images saved to: {args.output_folder}")
    
    # Print summary
    total_images = len([f for f in os.listdir(args.output_folder) if f.endswith('.png')])
    print(f"Generated {total_images} visualization images")

if __name__ == "__main__":
    main()
