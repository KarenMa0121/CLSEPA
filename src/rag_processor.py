import chromadb
from chromadb.utils import embedding_functions
from typing import List, Dict, Optional
import os
import json
from sentence_transformers import SentenceTransformer
import fitz  # PyMuPDF
import logging
import google.generativeai as genai
import time

logger = logging.getLogger(__name__)



class LegalDocumentRAG:
    def __init__(self, api_key: str, collection_name: str = "petitioner_issues"):
        self.api_key = api_key
        genai.configure(api_key=api_key)
        
        # Configure Gemini with low temperature for consistent outputs
        generation_config = {
            "temperature": 0.01,  # Low temperature for consistency
            "top_p": 0.8,
            "top_k": 40
        }
        self.model = genai.GenerativeModel('gemini-pro', generation_config=generation_config)
        
        # Initialize embedding model
        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        
        # Initialize ChromaDB
        self.client = chromadb.PersistentClient(path="chroma_db")
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            embedding_function=embedding_functions.SentenceTransformerEmbeddingFunction(
                model_name='all-MiniLM-L6-v2'
            )
        )

    def extract_text(self, pdf_path: str) -> str:
        """Extract text content from PDF file."""
        try:
            with fitz.open(pdf_path) as doc:
                text = ""
                for page in doc:
                    text += page.get_text()
                return text.strip()
        except Exception as e:
            logger.error(f"Failed to extract text from PDF {pdf_path}: {str(e)}")
            raise

    def extract_petitioner_issues(self, text: str) -> Optional[str]:
        """Extract petitioner issues with consistent output."""
        max_retries = 3
        retry_delay = 2
        
        for attempt in range(max_retries):
            try:
                if attempt > 0:
                    time.sleep(retry_delay * attempt)
                
                prompt = """Extract the main issues raised by the petitioner from this legal document.

                STRICT GUIDELINES:
                1. Focus ONLY on core legal issues and primary arguments
                2. Extract exactly 3-4 main points
                3. Use consistent formatting:
                   - One issue per line
                   - Start each line with "Issue: "
                   - Use clear, factual language
                   - Maintain same level of detail for each issue
                4. Exclude:
                   - Secondary arguments
                   - Procedural details
                   - Background information
                
                Text: {text}
                
                Return ONLY the numbered list of main issues, no additional text or commentary."""
                
                response = self.model.generate_content(prompt.format(text=text[:5000]))
                return response.text.strip()
            
            except Exception as e:
                logger.warning(f"Attempt {attempt + 1} failed: {str(e)}")
                if attempt == max_retries - 1:
                    logger.error(f"Failed to extract petitioner issues after {max_retries} attempts")
                    return None
        return None

    def add_to_rag(self, pdf_path: str) -> None:
        """Add document to RAG with consistent processing."""
        try:
            filename = os.path.basename(pdf_path)
            text = self.extract_text(pdf_path)
            
            # Extract petitioner issues
            petitioner_issues = self.extract_petitioner_issues(text)
            if not petitioner_issues:
                logger.warning(f"Skipping {filename} - could not extract petitioner issues")
                return
            
            metadata = {
                'filename': filename,
                'path': pdf_path,
                'processed_at': time.strftime('%Y-%m-%d %H:%M:%S')
            }
            
            # Add to collection
            self.collection.add(
                documents=[petitioner_issues],
                metadatas=[metadata],
                ids=[filename]
            )
            
            logger.info(f"Successfully processed {filename}")
            time.sleep(1)  # Rate limiting
            
        except Exception as e:
            logger.error(f"Failed to process {pdf_path}: {str(e)}")

    def find_similar(self, query_pdf: str, top_k: int = 5) -> List[Dict]:
        """Find similar documents with consistent similarity scoring."""
        try:
            # Extract query document's petitioner issues
            query_text = self.extract_text(query_pdf)
            query_issues = self.extract_petitioner_issues(query_text)
            
            if not query_issues:
                logger.error("Could not extract petitioner issues from query document")
                return []
            
            # Get similar documents
            results = self.collection.query(
                query_texts=[query_issues],
                n_results=top_k,
                include=["metadatas", "distances", "documents"]
            )
            
            similar_docs = []
            if results['distances'] and results['distances'][0]:
                for metadata, distance, issues in zip(
                    results['metadatas'][0],
                    results['distances'][0],
                    results['documents'][0]
                ):
                    similarity_score = (1 - distance) * 100
                    similar_docs.append({
                        'filename': metadata['filename'],
                        'similarity_score': round(similarity_score, 2),
                        'petitioner_issues': issues
                    })
                
                # Sort by similarity score
                similar_docs.sort(key=lambda x: x['similarity_score'], reverse=True)
                similar_docs = similar_docs[:5]  # Keep only top 5
            
            return similar_docs
            
        except Exception as e:
            logger.error(f"Error in similarity search: {str(e)}")
            return []
