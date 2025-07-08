from azure.core.credentials import AzureKeyCredential
from azure.ai.documentintelligence import DocumentIntelligenceClient
from azure.ai.documentintelligence.models import AnalyzeOutputOption, AnalyzeResult

from key_vault import KeyVault
import os
import json
import argparse
import glob


keyvault = KeyVault()
endpoint = keyvault.get_key("SDUAzureDocIntelligenceEndpoint")
key = keyvault.get_key("SDUAzureDocIntelligenceKey")

document_intelligence_client = DocumentIntelligenceClient(endpoint=endpoint, credential=AzureKeyCredential(key))

def create_markdown_from_result(result: dict) -> str:
    """
    Generates a Markdown string from a Document Intelligence result object,
    placing figure placeholders in their correct reading order.
    Only includes paragraphs and figures, ignoring sections and other elements.

    Args:
        result: The AnalyzeResult object (as a dictionary).

    Returns:
        A string containing the document content in Markdown format.
    """
    markdown_parts = []
    
    # Debug: Print the structure to understand what we're working with
    print(f"Sections available: {len(result.get('sections', []))}")
    print(f"Paragraphs available: {len(result.get('paragraphs', []))}")
    print(f"Figures available: {len(result.get('figures', []))}")
    
    # Try to get elements from sections first
    element_paths = []
    if result.get('sections'):
        for section in result['sections']:
            if 'elements' in section:
                element_paths.extend(section['elements'])
                print(f"Found {len(section['elements'])} elements in section")
    
    # If no elements found in sections, create a fallback approach
    if not element_paths:
        print("No elements found in sections, using fallback approach")
        # Create element paths manually based on spans/offsets
        all_items = []
        
        # Add paragraphs with their offsets
        for i, paragraph in enumerate(result.get('paragraphs', [])):
            if paragraph.get('spans'):
                offset = paragraph['spans'][0]['offset']
                all_items.append((offset, 'paragraphs', i, paragraph))
        
        # Add figures with their offsets
        for i, figure in enumerate(result.get('figures', [])):
            if figure.get('spans'):
                offset = figure['spans'][0]['offset']
                all_items.append((offset, 'figures', i, figure))
        
        # Sort by offset to maintain reading order
        all_items.sort(key=lambda x: x[0])
        
        # Process sorted items
        for offset, element_type, index, item in all_items:
            if element_type == "paragraphs":
                # Skip page numbers and other special roles
                if item.get('role') not in ['pageNumber', 'title', 'sectionHeading']:
                    content = item['content'].strip()
                    if content:  # Only add non-empty content
                        markdown_parts.append(content)
            
            elif element_type == "figures":
                figure_id = item['id']
                placeholder = f"**[FIGURE: {figure_id}]**"
                markdown_parts.append(placeholder)
    
    else:
        # Process elements from sections
        print(f"Processing {len(element_paths)} elements from sections")
        for element_path in element_paths:
            parts = element_path.strip().split('/')
            if len(parts) != 3:
                continue
                
            element_type = parts[1]
            try:
                element_index = int(parts[2])
            except ValueError:
                continue

            if element_type == "paragraphs":
                if element_index < len(result.get('paragraphs', [])):
                    paragraph = result['paragraphs'][element_index]
                    if paragraph.get('role') not in ['pageNumber', 'title', 'sectionHeading']:
                        content = paragraph['content'].strip()
                        if content:
                            markdown_parts.append(content)
            
            elif element_type == "figures":
                if element_index < len(result.get('figures', [])):
                    figure = result['figures'][element_index]
                    figure_id = figure['id']
                    placeholder = f"**[FIGURE: {figure_id}]**"
                    markdown_parts.append(placeholder)
    
    print(f"Generated {len(markdown_parts)} markdown parts")
    
    # Join all the parts with double newlines
    content = "\n\n".join(markdown_parts)
    
    return content

def create_markdown_from_result_full(result: dict) -> str:
    """
    Generates a Markdown string from a Document Intelligence result object,
    placing figure placeholders in their correct reading order.

    Args:
        result: The AnalyzeResult object (as a dictionary).

    Returns:
        A string containing the document content in Markdown format.
    """
    markdown_parts = []
    page_numbers = []
    
    # Get the primary section and its elements which define the reading order
    if not result.get('sections'):
        # Fallback to just using paragraphs if sections aren't present
        return "\n\n".join(p['content'] for p in result.get('paragraphs', []))

    element_paths = result['sections'][0]['elements']
    
    for element_path in element_paths:
        # The path is a string like '/paragraphs/0' or '/figures/1'
        # We split it to get the type and the index
        parts = element_path.strip().split('/')
        if len(parts) != 3:
            continue # Skip malformed paths
            
        element_type = parts[1]
        try:
            element_index = int(parts[2])
        except ValueError:
            continue # Skip if the index is not a valid number

        if element_type == "paragraphs":
            if element_index < len(result.get('paragraphs', [])):
                paragraph = result['paragraphs'][element_index]
                # Collect page numbers separately instead of adding to main flow
                if paragraph.get('role') == 'pageNumber':
                    page_numbers.append(paragraph['content'])
                else:
                    markdown_parts.append(paragraph['content'])
        
        elif element_type == "figures":
            if element_index < len(result.get('figures', [])):
                figure = result['figures'][element_index]
                figure_id = figure['id']
                # Create a simpler figure placeholder that integrates better with text flow
                placeholder = f"\n\n**[FIGURE: {figure_id}]**\n\n"
                markdown_parts.append(placeholder)
        
        elif element_type == "tables":
            if element_index < len(result.get('tables', [])):
                table = result['tables'][element_index]
                # Create a placeholder for tables
                table_caption = table.get('caption', {}).get('content', f'Table {element_index}')
                placeholder = f"\n\n---\n**[TABLE: {table_caption}]**\n---\n\n"
                markdown_parts.append(placeholder)
        
        elif element_type == "sections":
            # Sections are structural elements, usually don't need direct content representation
            # but we can add a section break
            if element_index < len(result.get('sections', [])):
                section = result['sections'][element_index]
                section_title = section.get('title', f'Section {element_index}')
                if section_title:
                    markdown_parts.append(f"\n\n## {section_title}\n")
        
        elif element_type == "selectionMarks":
            if element_index < len(result.get('selectionMarks', [])):
                selection_mark = result['selectionMarks'][element_index]
                state = selection_mark.get('state', 'unselected')
                symbol = "☑" if state == 'selected' else "☐"
                markdown_parts.append(f"{symbol} ")
        
        else:
            # Handle unknown element types gracefully
            print(f"Warning: Unknown element type '{element_type}' at index {element_index} - skipping")
            # You could also add a generic placeholder:
            # markdown_parts.append(f"\n\n---\n**[{element_type.upper()}: {element_index}]**\n---\n\n")
    
    # Join all the parts with double newlines to create paragraph breaks
    content = "\n\n".join(markdown_parts)
    
    # Add page numbers at the end if any were found
    if page_numbers:
        content += f"\n\n---\n**Page Numbers:** {', '.join(page_numbers)}\n---"
    
    return content


def process_document_and_extract_figures(input_file_path: str, output_folder_name: str, use_existing_json: bool = True):
    """
    Process a document file and extract figures, saving them to a structured output folder.
    
    Args:
        input_file_path: Full path to the input document file
        output_folder_name: Name of the output folder
        use_existing_json: Whether to use existing JSON file if available
        
    Returns:
        tuple: (result object, markdown content)
    """
    # Get the basename of the input file (without extension)
    basename = os.path.splitext(os.path.basename(input_file_path))[0]
    
    # Create the output directory structure
    figures_dir = os.path.join(".", output_folder_name, "figures")
    os.makedirs(figures_dir, exist_ok=True)
    
    # Check if JSON file already exists
    json_filename = f"{basename}.json"
    json_path = os.path.join(".", output_folder_name, json_filename)
    
    result = None
    
    if use_existing_json and os.path.exists(json_path):
        print(f"📄 Using existing JSON file: {json_filename}")
        try:
            with open(json_path, "r", encoding="utf-8") as f:
                result_dict = json.load(f)
            
            # Create a simple result object for compatibility
            class SimpleResult:
                def __init__(self, data):
                    self.data = data
                    self.model_id = data.get('model_id')
                    self.figures = []
                    for fig_data in data.get('figures', []):
                        fig_obj = type('Figure', (), fig_data)()
                        self.figures.append(fig_obj)
                        
                def as_dict(self):
                    return self.data
            
            result = SimpleResult(result_dict)
            
            # Check if figure files exist
            if result.figures:
                for figure in result.figures:
                    if hasattr(figure, 'id') and figure.id:
                        figure_filename = f"{basename}_{figure.id}.png"
                        figure_path = os.path.join(figures_dir, figure_filename)
                        
                        if not os.path.exists(figure_path):
                            print(f"⚠️  Figure file missing: {figure_filename}")
                        else:
                            print(f"✅ Figure already exists: {figure_filename}")
            
        except Exception as e:
            print(f"❌ Error reading existing JSON file: {e}")
            print("📄 Falling back to processing original document...")
            result = None
    
    if result is None:
        # Process the document normally
        with open(input_file_path, "rb") as f:
            poller = document_intelligence_client.begin_analyze_document(
                "prebuilt-layout",
                body=f,
                output=[AnalyzeOutputOption.FIGURES],
            )
        result = poller.result()
        operation_id = poller.details["operation_id"]
        
        # Extract and save figures
        if result.figures:
            for figure in result.figures:
                if figure.id:
                    response = document_intelligence_client.get_analyze_result_figure(
                        model_id=result.model_id, result_id=operation_id, figure_id=figure.id
                    )
                    # Create filename with basename + figure.id
                    figure_filename = f"{basename}_{figure.id}.png"
                    figure_path = os.path.join(figures_dir, figure_filename)
                    
                    with open(figure_path, "wb") as writer:
                        writer.writelines(response)
                    print(f"Saved figure: {figure_path}")
        else:
            print("No figures found.")
        
        # Save raw result as JSON
        try:
            with open(json_path, "w", encoding="utf-8") as f:
                json.dump(result.as_dict(), f, indent=2, ensure_ascii=False)
            print(f"Saved raw result: {json_path}")
        except Exception as e:
            print(f"Error writing JSON file: {e}")
    
    # Generate markdown content
    markdown_output = create_markdown_from_result(result.as_dict())
    
    # Save markdown to output folder
    markdown_filename = f"{basename}.md"
    markdown_path = os.path.join(".", output_folder_name, markdown_filename)
    
    try:
        with open(markdown_path, "w", encoding="utf-8") as f:
            f.write(markdown_output)
        print(f"Saved markdown: {markdown_path}")
    except Exception as e:
        print(f"Error writing markdown file: {e}")
    
    return result, markdown_output


def process_file_list(folder_path: str, file_list: list, output_folder: str, use_existing_json: bool = True):
    """
    Process a list of specific files based on their 4-digit numbers.
    
    Args:
        folder_path: Folder path like 'D:/data/HCNC/norway/biographies/raw/corpus/digibok_2007031501007'
        file_list: List of 4-digit numbers like ["0067", "0097", "0148"]
        output_folder: Output folder path
        use_existing_json: Whether to use existing JSON files if available
    """
    # Extract the folder name to use as filename base
    folder_name = os.path.basename(folder_path.rstrip('/\\'))
    
    processed_count = 0
    failed_count = 0
    
    print(f"Processing {len(file_list)} specific files")
    print(f"Folder: {folder_path}")
    print(f"Base filename pattern: {folder_name}_XXXX.jpg")
    print(f"Output folder: {output_folder}")
    print(f"Use existing JSON: {use_existing_json}")
    print("-" * 60)
    
    for num_str in file_list:
        # Ensure 4-digit format
        num_str = f"{int(num_str):04d}"
        filename = f"{folder_name}_{num_str}.jpg"
        file_path = os.path.join(folder_path, filename)
        
        # Check if file exists
        if not os.path.exists(file_path):
            print(f"⚠️  File not found: {filename}")
            failed_count += 1
            continue
        
        try:
            print(f"📄 Processing: {filename}")
            result, markdown_output = process_document_and_extract_figures(file_path, output_folder, use_existing_json)
            processed_count += 1
            print(f"✅ Successfully processed: {filename}")
        except Exception as e:
            print(f"❌ Error processing {filename}: {e}")
            failed_count += 1
        
        print("-" * 40)
    
    print(f"\n📊 Processing Summary:")
    print(f"✅ Successfully processed: {processed_count} files")
    print(f"❌ Failed: {failed_count} files")
    print(f"📁 Output saved to: {output_folder}")


def process_file_range(folder_path: str, start_num: str, end_num: str, output_folder: str, use_existing_json: bool = True):
    """
    Process a range of files based on 4-digit suffix numbering.
    
    Args:
        folder_path: Folder path like 'D:/data/HCNC/norway/biographies/raw/corpus/digibok_2007031501007'
        start_num: Starting 4-digit number like "0057"
        end_num: Ending 4-digit number like "0494"
        output_folder: Output folder path
    """
    # Extract the folder name to use as filename base
    folder_name = os.path.basename(folder_path.rstrip('/\\'))
    
    # Convert start and end to integers for range processing
    start_int = int(start_num)
    end_int = int(end_num)
    
    processed_count = 0
    failed_count = 0
    
    print(f"Processing files from {start_num} to {end_num}")
    print(f"Folder: {folder_path}")
    print(f"Base filename pattern: {folder_name}_XXXX.jpg")
    print(f"Output folder: {output_folder}")
    print("-" * 60)
    
    for num in range(start_int, end_int + 1):
        # Format number as 4-digit string with leading zeros
        num_str = f"{num:04d}"
        filename = f"{folder_name}_{num_str}.jpg"
        file_path = os.path.join(folder_path, filename)
        
        # Check if file exists
        if not os.path.exists(file_path):
            print(f"⚠️  File not found: {filename}")
            failed_count += 1
            continue
        
        try:
            print(f"📄 Processing: {filename}")
            result, markdown_output = process_document_and_extract_figures(file_path, output_folder, use_existing_json)
            processed_count += 1
            print(f"✅ Successfully processed: {filename}")
        except Exception as e:
            print(f"❌ Error processing {filename}: {e}")
            failed_count += 1
        
        print("-" * 40)
    
    print(f"\n📊 Processing Summary:")
    print(f"✅ Successfully processed: {processed_count} files")
    print(f"❌ Failed: {failed_count} files")
    print(f"📁 Output saved to: {output_folder}")


# --- Main execution ---
if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Process documents with Azure Document Intelligence and extract figures",
        formatter_class=argparse.RawDescriptionHelpFormatter)
    
    parser.add_argument(
        "--input", "-i",
        required=True,
        help="Input folder path containing the image files (e.g., 'D:/data/HCNC/norway/biographies/raw/corpus/digibok_2007031501007')"
    )
    
    parser.add_argument(
        "--list",
        help="Process specific files from a list of 4-digit numbers (comma-separated, e.g., '0067,0097,0148')"
    )
    
    parser.add_argument(
        "--use-json", 
        action="store_true",
        help="Use existing JSON files if available (default: True)"
    )
    
    parser.add_argument(
        "--single",
        help="Process single file with this 4-digit number (e.g., '0115')"
    )
    
    parser.add_argument(
        "--start", "-s",
        help="Starting 4-digit number for range processing (e.g., '0057')"
    )
    
    parser.add_argument(
        "--end", "-e", 
        help="Ending 4-digit number for range processing (e.g., '0494')"
    )
    
    parser.add_argument(
        "--output", "-o",
        required=True,
        help="Output folder path"
    )
    
    args = parser.parse_args()
    
    # Determine if we should use existing JSON files
    use_existing_json = args.use_json
    
    # Ensure the output folder exists
    os.makedirs(args.output, exist_ok=True)
    
    # Check processing mode
    if args.list:
        # List processing
        if not os.path.isdir(args.input):
            print(f"Error: Input folder not found: {args.input}")
            exit(1)
        
        # Parse the list - handle both comma-separated and predefined lists
        if args.list.lower() == "failed":
            # Use the predefined failed list
            file_numbers = [
                "0067",
            ]
        else:
            # Parse comma-separated list
            file_numbers = [num.strip() for num in args.list.split(",")]
        
        try:
            process_file_list(args.input, file_numbers, args.output, use_existing_json)
        except Exception as e:
            print(f"Error in list processing: {e}")
            
    elif args.start and args.end:
        # Range processing
        if not os.path.isdir(args.input):
            print(f"Error: Input folder not found: {args.input}")
            exit(1)
            
        try:
            process_file_range(args.input, args.start, args.end, args.output, use_existing_json)
        except Exception as e:
            print(f"Error in range processing: {e}")
            
    elif args.single:
        # Single file processing using folder + number
        if not os.path.isdir(args.input):
            print(f"Error: Input folder not found: {args.input}")
            exit(1)
            
        folder_name = os.path.basename(args.input.rstrip('/\\'))
        filename = f"{folder_name}_{args.single}.jpg"
        file_path = os.path.join(args.input, filename)
        
        if not os.path.exists(file_path):
            print(f"Error: Input file not found: {file_path}")
            exit(1)
            
        print(f"Processing single document: {filename}")
        print(f"Output folder: {args.output}")
        print(f"Use existing JSON: {use_existing_json}")
        print("-" * 50)
        
        try:
            result, markdown_output = process_document_and_extract_figures(file_path, args.output, use_existing_json)
            print("-" * 50)
            print("--- Generated Markdown Preview ---")
            print(markdown_output[:500] + "..." if len(markdown_output) > 500 else markdown_output)
            print(f"\n--- Processing complete! Check the '{args.output}' folder for results ---")
        except Exception as e:
            print(f"Error processing file: {e}")
            
    else:
        print("Error: You must specify one of: --single, --start/--end, or --list")
        parser.print_help()
        exit(1)

"""
env: MonkeyOCR
python AzureOCR_extracting_text_and_figures.py --input "D:/data/HCNC/norway/biographies/raw/corpus/digibok_2007031501007" --single "0115" --output "D:\data\HCNC\norway\biographies\storage\AzureOCR\output_md_and_json"

python AzureOCR_extracting_text_and_figures.py --input "D:/data/HCNC/norway/biographies/raw/corpus/digibok_2007031501007" --single "0386" --output "D:\data\HCNC\norway\biographies\storage\AzureOCR\output_md_and_json"

# Process range of files
python AzureOCR_extracting_text_and_figures.py --input "D:/data/HCNC/norway/biographies/raw/corpus/digibok_2007031501007" --start "0057" --end "0494" --output  "D:\data\HCNC\norway\biographies\storage\AzureOCR\output_md_and_json"


List of file that was flagged when running the concatination script:
  failed = [
  "digibok_2007031501007_0067.md",
  "digibok_2007031501007_0097.md",
  "digibok_2007031501007_0148.md",  
    "digibok_2007031501007_0169.md",
    "digibok_2007031501007_0190.md",
    "digibok_2007031501007_0199.md",
    "digibok_2007031501007_0216.md",
    "digibok_2007031501007_0253.md",
    "digibok_2007031501007_0315.md",
    "digibok_2007031501007_0430.md",
    "digibok_2007031501007_0465.md",
]
 
python AzureOCR_extracting_text_and_figures.py --input "D:/data/HCNC/norway/biographies/raw/corpus/digibok_2007031501007" --list "0067,0097,0148,0169,0190,0199,0216,0253,0315,0430,0465" --output "D:\data\HCNC\norway\biographies\storage\AzureOCR\output_md_and_json" --use-json 

"""

