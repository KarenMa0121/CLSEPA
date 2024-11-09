# src/main.py

import os
from dotenv import load_dotenv
from processor import LegalDocumentProcessor
import json

def process_directory(api_key: str, directory_path: str, output_file: str):
    """Process all PDF files in a directory and save results to a JSON file."""
    processor = LegalDocumentProcessor(api_key)
    results = []
    
    # Create output directory if it doesn't exist
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    
    # Process each PDF file
    for filename in os.listdir(directory_path):
        if filename.endswith('.pdf'):
            try:
                print(f"Processing {filename}...")
                pdf_path = os.path.join(directory_path, filename)
                result = processor.process_document(pdf_path)
                results.append(result)
            except Exception as e:
                print(f"Failed to process {filename}: {str(e)}")
    
    # Save results to JSON file
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    print(f"Results saved to {output_file}")

def main():
    # Load environment variables
    load_dotenv()
    
    # Get API key from environment variable
    api_key = os.getenv('GOOGLE_API_KEY')  # Changed from GROQ_API_KEY
    if not api_key:
        raise ValueError("GOOGLE_API_KEY not found in environment variables")
    
    # Set up paths
    pdf_directory = os.path.join('data', 'pdfs')
    output_file = os.path.join('data', 'results.json')
    
    # Create directories if they don't exist
    os.makedirs(pdf_directory, exist_ok=True)
    
    # Process documents
    process_directory(api_key, pdf_directory, output_file)

if __name__ == "__main__":
    main()