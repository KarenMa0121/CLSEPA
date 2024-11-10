import os
from dotenv import load_dotenv
from rag_processor import LegalDocumentRAG
import logging
from tqdm import tqdm

logging.basicConfig(level=logging.INFO,
                   format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def build_rag_database(pdf_dir: str, api_key: str):
    """Build RAG database from PDFs."""
    rag = LegalDocumentRAG(api_key)
    
    # Get list of PDFs
    pdf_files = [f for f in os.listdir(pdf_dir) if f.endswith('.pdf')]
    logger.info(f"Found {len(pdf_files)} PDF files")
    
    # Process each PDF
    for pdf_file in tqdm(pdf_files, desc="Processing PDFs"):
        try:
            pdf_path = os.path.join(pdf_dir, pdf_file)
            rag.add_to_rag(pdf_path)
        except Exception as e:
            logger.error(f"Failed to process {pdf_file}: {str(e)}")

def find_similar_documents(query_pdf: str, api_key: str):
    """Find similar documents for a query PDF."""
    rag = LegalDocumentRAG(api_key)
    
    similar_docs = rag.find_similar(query_pdf)
    
    print("\nSimilar Documents:")
    for doc in similar_docs:
        print(f"\nFilename: {doc['filename']}")
        print(f"Similarity Score: {doc['similarity_score']}%")

def main():
    # Load environment variables
    load_dotenv()
    api_key = os.getenv('GOOGLE_API_KEY')
    if not api_key:
        raise ValueError("GOOGLE_API_KEY not found in environment variables")

    import sys
    if len(sys.argv) < 2:
        print("Usage:")
        print("  Build database: python main.py build")
        print("  Find similar: python main.py find path/to/query.pdf")
        return

    command = sys.argv[1]
    
    if command == "build":
        pdf_dir = "data/pdfs"
        build_rag_database(pdf_dir, api_key)
    elif command == "find":
        if len(sys.argv) < 3:
            print("Please provide path to query PDF")
            return
        query_pdf = sys.argv[2]
        find_similar_documents(query_pdf, api_key)
    else:
        print("Unknown command")

if __name__ == "__main__":
    main()

