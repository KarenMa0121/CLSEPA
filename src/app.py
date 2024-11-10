import streamlit as st
import os
from pathlib import Path
import tempfile
from typing import Optional
from rag_processor import LegalDocumentRAG
from processor import LegalDocumentProcessor
import logging
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(level=logging.INFO,
                   format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(dotenv_path=env_path)

class LegalDocumentUI:
    def __init__(self):
        """Initialize the UI."""
        # Initialize session state
        if 'page' not in st.session_state:
            st.session_state.page = 'upload'
        if 'selected_doc' not in st.session_state:
            st.session_state.selected_doc = None
        if 'similar_docs' not in st.session_state:
            st.session_state.similar_docs = []
        if 'current_file' not in st.session_state:
            st.session_state.current_file = None
            
        # Get API key
        self.api_key = os.getenv('GOOGLE_API_KEY')
        if not self.api_key:
            st.error("🚨 Google API Key not found in .env file!")
            st.stop()
            
        # Initialize processors
        self.rag_processor = LegalDocumentRAG(self.api_key)
        self.doc_processor = LegalDocumentProcessor(self.api_key)
        self.doc_summery = None

    def process_upload(self, uploaded_file) -> None:
        """Process uploaded PDF and find similar documents."""
        try:
            # Save uploaded file temporarily
            temp_path = None
            with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
                tmp_file.write(uploaded_file.getvalue())
                temp_path = tmp_file.name

            if temp_path:
                with st.spinner('Processing document...'):
                    # Store current file
                    st.session_state.current_file = {
                        'name': uploaded_file.name,
                        'path': temp_path
                    }
                    
                    st.session_state.doc_details = self.doc_processor.process_document(temp_path)
                    
                    # Find similar documents
                    similar_docs = self.rag_processor.find_similar(temp_path)
                    if similar_docs:
                        # Add file paths
                        data_dir = Path(__file__).parent.parent / 'data' / 'pdfs'
                        for doc in similar_docs:
                            doc['file_path'] = str(data_dir / doc['filename'])
                        st.session_state.similar_docs = similar_docs
                    else:
                        st.warning("No similar documents found.")
                    
                    # Force page refresh
                    st.rerun()
                    
        except Exception as e:
            logger.error(f"Error processing upload: {str(e)}")
            st.error(f"Failed to process document: {str(e)}")

    def show_upload_page(self):
        """Show upload page with similar documents."""
        st.title("Legal Document Analysis")

        # File upload section
        uploaded_file = st.file_uploader(
            "Upload a PDF document",
            type=['pdf'],
            key='pdf_uploader'
        )

        # Process new upload
        if uploaded_file and (not st.session_state.current_file or 
                            uploaded_file.name != st.session_state.current_file['name']):
            self.process_upload(uploaded_file)
        # Display a summary section for the uploaded document
        if st.session_state.current_file:
            st.header("**Document Summary:**")
            if st.session_state.doc_details:
                st.write(st.session_state.doc_details.get('petitioner_issues_summary', 'Summary not available'))
            else:
                st.warning("No document summary available.")
        # Show similar documents if available
        if st.session_state.similar_docs:
            st.header("Similar Documents")
            
            for doc in st.session_state.similar_docs:
                col1, col2, col3 = st.columns([3, 1, 1])
                with col1:
                    st.write(f"📄 {doc['filename']}")
                with col2:
                    st.write(f"{doc['similarity_score']:.1f}% match")
                with col3:
                    if st.button('View Details', key=doc['filename']):
                        st.session_state.selected_doc = doc
                        st.session_state.page = 'details'
                        st.rerun()
                st.markdown("---")

    def show_document_details(self):
        """Show comprehensive document details."""
        try:
            # Add back button at the top
            if st.button('← Back to Search'):
                st.session_state.page = 'upload'
                st.rerun()
                return

            # Get document details
            doc_path = st.session_state.selected_doc['file_path']
            with st.spinner('Loading document details...'):
                doc_details = self.doc_processor.process_document(doc_path)

            # Main title and document info
            st.title("Document Details")
            
            # Create tabs for different sections
            tab1, tab2, tab3 = st.tabs(["Case Information", "Case Summaries", "Document Actions"])
            
            # Tab 1: Case Information
            with tab1:
                st.subheader("Basic Information")
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown("**Case Number:**")
                    st.write(doc_details['case_number'])
                    st.markdown("**Petitioner:**")
                    st.write(doc_details['petitioner_name'])
                with col2:
                    st.markdown("**City/Location:**")
                    st.write(doc_details.get('city', 'Not available'))
                    st.markdown("**Respondent:**")
                    st.write(doc_details['respondent_name'])

            # Tab 2: Case Summaries
            with tab2:
                # Petitioner's Issues
                st.subheader("Petitioner's Issues")
                st.write(doc_details.get('petitioner_issues_summary', 'Not available'))
                
                # Respondent's Issues
                st.subheader("Respondent's Issues")
                st.write(doc_details.get('respondent_issues_summary', 'Not available'))
                
                # Hearing Points
                st.subheader("Hearing Points")
                st.write(doc_details.get('hearing_points_summary', 'Not available'))
                
                # Final Decision
                st.subheader("Final Decision")
                st.write(doc_details.get('final_decision_summary', 'Not available'))
                
                # Appeal Information (if applicable)
                if doc_details.get('is_appeal'):
                    st.subheader("Appeal Information")
                    st.markdown("**Appeal Subject:**")
                    st.write(doc_details.get('appeal_subject', 'Not available'))
                    st.markdown("**Appeal Decision:**")
                    st.write(doc_details.get('appeal_decision', 'Not available'))

            # Tab 3: Document Actions
            with tab3:
                st.subheader("Document Actions")
                with open(doc_path, "rb") as pdf_file:
                    pdf_bytes = pdf_file.read()
                st.download_button(
                    label="Download Original PDF",
                    data=pdf_bytes,
                    file_name=os.path.basename(doc_path),
                    mime="application/pdf"
                )

        except Exception as e:
            logger.error(f"Error displaying document details: {str(e)}")
            st.error(f"Failed to load document details: {str(e)}")
            if st.button('← Return to Search'):
                st.session_state.page = 'upload'
                st.rerun()

    def run(self):
        """Main UI loop."""
        st.set_page_config(
            page_title="Legal Document Analysis",
            page_icon="⚖️",
            layout="wide"
        )

        # Main navigation
        if st.session_state.page == 'upload':
            self.show_upload_page()
        elif st.session_state.page == 'details':
            self.show_document_details()
        else:
            st.session_state.page = 'upload'
            st.rerun()

if __name__ == "__main__":
    app = LegalDocumentUI()
    app.run()