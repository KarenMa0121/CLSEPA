# import fitz  # PyMuPDF
# from typing import Dict, List, Optional
# import os
# import logging
# import google.generativeai as genai
# import json
# import time

# logger = logging.getLogger(__name__)

# class LegalDocumentProcessor:
#     def __init__(self, api_key: str):
#         genai.configure(api_key=api_key)
#         self.model = genai.GenerativeModel('gemini-pro')

#     def extract_text_from_pdf(self, pdf_path: str) -> str:
#         """Extract text content from PDF file with robust error handling."""
#         text = ""
#         try:
#             with fitz.open(pdf_path) as doc:
#                 for page in doc:
#                     # Try different extraction methods
#                     try:
#                         # First try blocks
#                         blocks = page.get_text("blocks")
#                         page_text = "\n".join(block[4] for block in blocks)
#                         if page_text.strip():
#                             text += page_text + "\n"
#                         else:
#                             # If blocks didn't work, try raw text
#                             raw_text = page.get_text()
#                             if raw_text.strip():
#                                 text += raw_text + "\n"
#                     except Exception as e:
#                         logger.warning(f"Error on page {page.number}: {str(e)}")
#                         # Last resort: try simple text extraction
#                         text += page.get_text() + "\n"

#                 if not text.strip():
#                     raise ValueError("No text could be extracted from the PDF")

#                 logger.info(f"Extracted {len(text)} characters from PDF")
#                 return self._clean_text(text)
#         except Exception as e:
#             logger.error(f"Failed to extract text from PDF: {str(e)}")
#             raise

#     def _clean_text(self, text: str) -> str:
#         """Clean and prepare text for analysis."""
#         # Remove extra whitespace
#         text = " ".join(line.strip() for line in text.splitlines() if line.strip())
#         # Remove non-printable characters
#         text = "".join(char for char in text if char.isprintable() or char in ['\n', '\t'])
#         # Remove duplicate spaces
#         text = " ".join(text.split())
#         return text

#     def process_document(self, pdf_path: str) -> Dict:
#         """Process document with comprehensive error handling."""
#         try:
#             logger.info(f"Starting to process: {pdf_path}")
            
#             # Extract text
#             text = self.extract_text_from_pdf(pdf_path)
            
#             # Extract all information in one go with a structured prompt
#             prompt = f"""Analyze this legal document carefully and extract the following information in detail:

# 1. Case Details:
# - Case number/identifier
# - Petitioner's name and details
# - Respondent's name and details
# - Location/jurisdiction

# 2. Petitioner's Case:
# - Main issues raised
# - Key arguments presented
# - Relief sought

# 3. Respondent's Position:
# - Main counter-arguments
# - Defense points
# - Response to petitioner's claims

# 4. Hearing Details:
# - Key points discussed
# - Evidence presented
# - Important observations made

# 5. Final Decision:
# - Main ruling/order
# - Specific directions given
# - Reasoning for decision

# 6. Appeal Information:
# - Is this an appeal? (yes/no)
# - Subject matter of appeal
# - Appeal decision/outcome

# Document text:
# {text}

# Provide a detailed JSON response with the following structure:
# {{
#     "case_number": "string",
#     "petitioner_name": "string",
#     "respondent_name": "string",
#     "city": "string",
#     "petitioner_issues_summary": "detailed string",
#     "respondent_issues_summary": "detailed string",
#     "hearing_points_summary": "detailed string",
#     "final_decision_summary": "detailed string",
#     "is_appeal": boolean,
#     "appeal_subject": "string or null",
#     "appeal_decision": "string or null"
# }}"""

#             # Get response from Gemini
#             response = self.model.generate_content(prompt)
#             content = response.text.strip()

#             # Clean up JSON response
#             if '```json' in content:
#                 content = content.split('```json')[1].split('```')[0].strip()
#             elif '```' in content:
#                 content = content.split('```')[1].strip()

#             # Parse JSON with error handling
#             try:
#                 result = json.loads(content)
#                 logger.info("Successfully parsed JSON response")
#             except json.JSONDecodeError as e:
#                 logger.error(f"JSON parsing error: {str(e)}")
#                 logger.error(f"Content causing error: {content}")
#                 # If JSON parsing fails, try to extract information using a more lenient approach
#                 result = self._extract_fallback(content)

#             # Ensure all required fields are present
#             final_result = {
#                 'filename': os.path.basename(pdf_path),
#                 'case_number': result.get('case_number', 'Not Found'),
#                 'petitioner_name': result.get('petitioner_name', 'Not Found'),
#                 'respondent_name': result.get('respondent_name', 'Not Found'),
#                 'city': result.get('city', 'Not Found'),
#                 'petitioner_issues_summary': result.get('petitioner_issues_summary', 'Summary not available'),
#                 'respondent_issues_summary': result.get('respondent_issues_summary', 'Summary not available'),
#                 'hearing_points_summary': result.get('hearing_points_summary', 'Summary not available'),
#                 'final_decision_summary': result.get('final_decision_summary', 'Summary not available'),
#                 'is_appeal': result.get('is_appeal', False),
#                 'appeal_subject': result.get('appeal_subject'),
#                 'appeal_decision': result.get('appeal_decision')
#             }

#             logger.info("Document processing completed successfully")
#             return final_result

#         except Exception as e:
#             logger.error(f"Error processing document: {str(e)}")
#             # Return a structured response even in case of error
#             return {
#                 'filename': os.path.basename(pdf_path),
#                 'case_number': 'Processing Error',
#                 'petitioner_name': 'Processing Error',
#                 'respondent_name': 'Processing Error',
#                 'city': 'Processing Error',
#                 'petitioner_issues_summary': f'Error occurred: {str(e)}',
#                 'respondent_issues_summary': 'Processing Error',
#                 'hearing_points_summary': 'Processing Error',
#                 'final_decision_summary': 'Processing Error',
#                 'is_appeal': False,
#                 'appeal_subject': None,
#                 'appeal_decision': None
#             }

#     def _extract_fallback(self, content: str) -> Dict:
#         """Fallback method to extract information if JSON parsing fails."""
#         result = {}
#         try:
#             # Try to extract information using simple text parsing
#             lines = content.split('\n')
#             for line in lines:
#                 if ':' in line:
#                     key, value = line.split(':', 1)
#                     key = key.strip().lower().replace(' ', '_')
#                     value = value.strip().strip('"\'')
#                     result[key] = value
#         except Exception as e:
#             logger.error(f"Fallback extraction failed: {str(e)}")
#         return result

import fitz  # PyMuPDF
from typing import Dict, List, Optional
import os
import logging
import google.generativeai as genai
import json
import time

logger = logging.getLogger(__name__)

# final 2 - 5 must sentences but no temp control
# class LegalDocumentProcessor:
#     def __init__(self, api_key: str):
#         genai.configure(api_key=api_key)
#         self.model = genai.GenerativeModel('gemini-pro')

#     def _clean_text(self, text: str) -> str:
#         """Clean text and limit to reasonable length."""
#         text = " ".join(text.split())
#         text = "".join(char for char in text if char.isprintable() or char in ['\n', '\t'])
#         if len(text) > 30000:
#             text = text[:30000] + "..."
#         return text

#     def _create_summary_prompt(self, text: str, section: str) -> str:
#         """Create a prompt that enforces a concise 5-sentences limit."""
#         return f"""Analyze this legal document and provide a VERY CONCISE summary of {section}.
        
#         Document text:
#         {text}
        
#         IMPORTANT RULES:
#         1. Summary MUST be 5 sentences or less
#         2. Focus ONLY on the most crucial points
#         3. Use clear, direct language
#         4. Avoid repetition or unnecessary details
        
#         Format: Write a concise paragraph with maximum 5 sentences."""

#     def process_document(self, pdf_path: str) -> Dict:
#         """Process document with strictly limited summary lengths."""
#         logger.info(f"Processing document: {pdf_path}")
        
#         try:
#             # Extract text
#             text = self._extract_text_from_pdf(pdf_path)
            
#             # Create detailed extraction prompt
#             prompt = f"""Analyze this legal document and provide structured information and VERY CONCISE summaries (max 5 sentences each).

#             Required Information:
#             1. Basic Details:
#                - Case number
#                - Petitioner name
#                - Respondent name
#                - City/location
            
#             2. Concise Summaries (MAXIMUM 5 SENTENCES EACH):
#                - Petitioner's main issues and arguments
#                - Respondent's main arguments
#                - Key hearing points
#                - Final decision
            
#             3. Appeal Information:
#                - Is this an appeal? (yes/no)
#                - Appeal subject (if applicable)
#                - Appeal decision (if applicable)

#             Document text:
#             {text}

#             IMPORTANT: Each summary section MUST NOT exceed 5 sentences.
            
#             Provide response in JSON format with these exact fields:
#             {{
#                 "case_number": "string",
#                 "petitioner_name": "string",
#                 "respondent_name": "string",
#                 "city": "string",
#                 "petitioner_issues_summary": "string (max 5 sentences)",
#                 "respondent_issues_summary": "string (max 5 sentences)",
#                 "hearing_points_summary": "string (max 5 sentences)",
#                 "final_decision_summary": "string (max 5 sentences)",
#                 "is_appeal": boolean,
#                 "appeal_subject": "string or null",
#                 "appeal_decision": "string or null"
#             }}"""

#             # Get response from model
#             response = self.model.generate_content(prompt)
#             content = response.text.strip()
            
#             # Clean up JSON response
#             if '```json' in content:
#                 content = content.split('```json')[1].split('```')[0].strip()
#             elif '```' in content:
#                 content = content.split('```')[1].strip()

#             # Parse response
#             try:
#                 result = json.loads(content)
#             except json.JSONDecodeError:
#                 logger.error("Failed to parse JSON response")
#                 return self._create_error_response(pdf_path)

#             # Enforce length limits on summaries
#             for key in ['petitioner_issues_summary', 'respondent_issues_summary', 
#                        'hearing_points_summary', 'final_decision_summary']:
#                 if key in result:
#                     lines = result[key].split('\n')
#                     result[key] = '\n'.join(lines[:5])  # Limit to 5 lines

#             # Add filename
#             result['filename'] = os.path.basename(pdf_path)
            
#             return result

#         except Exception as e:
#             logger.error(f"Failed to process document: {str(e)}")
#             return self._create_error_response(pdf_path)

#     def _extract_text_from_pdf(self, pdf_path: str) -> str:
#         """Extract text from PDF with error handling."""
#         try:
#             with fitz.open(pdf_path) as doc:
#                 text = ""
#                 for page in doc:
#                     text += page.get_text() + "\n"
#                 return self._clean_text(text)
#         except Exception as e:
#             logger.error(f"Failed to extract text from PDF: {str(e)}")
#             raise

#     def _create_error_response(self, pdf_path: str) -> Dict:
#         """Create a structured error response."""
#         return {
#             'filename': os.path.basename(pdf_path),
#             'case_number': 'Error processing document',
#             'petitioner_name': 'Not available',
#             'respondent_name': 'Not available',
#             'city': 'Not available',
#             'petitioner_issues_summary': 'Failed to extract summary',
#             'respondent_issues_summary': 'Failed to extract summary',
#             'hearing_points_summary': 'Failed to extract summary',
#             'final_decision_summary': 'Failed to extract summary',
#             'is_appeal': False,
#             'appeal_subject': None,
#             'appeal_decision': None
#         }

#     def ensure_summary_length(self, summary: str, max_lines: int = 5) -> str:
#         """Ensure summary doesn't exceed the specified number of lines."""
#         lines = summary.split('\n')
#         if len(lines) > max_lines:
#             return '\n'.join(lines[:max_lines])
#         return summary

#5 flexible sentences with temp control

class LegalDocumentProcessor:
    def __init__(self, api_key: str):
        genai.configure(api_key=api_key)
        # Set up model with lower temperature for more consistent outputs
        generation_config = {
            "temperature": 0.1,  # Lower temperature for more consistent output
            "top_p": 0.8,
            "top_k": 40
        }
        self.model = genai.GenerativeModel('gemini-pro', generation_config=generation_config)

    def _clean_text(self, text: str) -> str:
        """Clean text and limit to reasonable length."""
        text = " ".join(text.split())
        text = "".join(char for char in text if char.isprintable() or char in ['\n', '\t'])
        if len(text) > 30000:
            text = text[:30000] + "..."
        return text

    def _extract_text_from_pdf(self, pdf_path: str) -> str:
        """Extract text from PDF with error handling."""
        try:
            with fitz.open(pdf_path) as doc:
                text = ""
                for page in doc:
                    text += page.get_text() + "\n"
                return self._clean_text(text)
        except Exception as e:
            logger.error(f"Failed to extract text from PDF: {str(e)}")
            raise

    def process_document(self, pdf_path: str) -> Dict:
        """Process document with consistent summary generation."""
        logger.info(f"Processing document: {pdf_path}")
        
        try:
            # Extract text
            text = self._extract_text_from_pdf(pdf_path)
            
            # Create structured extraction prompt
            prompt = f"""Analyze this legal document and extract information following these exact guidelines:

            1. BASIC INFORMATION - Extract exactly:
               - Case number (format: alphanumeric identifier)
               - Petitioner name (full name)
               - Respondent name (full name)
               - City/location (city name only)

            2. SUMMARIES - For each section below, provide approximately 5 sentences that capture the essential information:

               A. Petitioner's Issues:
               - State the main legal claims or grievances
               - Include key arguments presented
               - Mention specific relief sought
               - Focus on factual claims only
               
               B. Respondent's Position:
               - State main counter-arguments
               - Include key defense points
               - Mention specific responses to petitioner's claims
               - Focus on factual rebuttals only
               
               C. Hearing Points:
               - List main evidence presented
               - Include key testimony highlights
               - Note important legal arguments discussed
               - Focus on factual discussions only
               
               D. Final Decision:
               - State the main ruling clearly
               - Include key reasoning points
               - Mention specific orders given
               - Focus on actual decision only

            3. APPEAL INFORMATION:
               - Is this an appeal case? (true/false only)
               - If yes, state what is the appeal about
               - If yes, state appeal decision

            Document text:
            {text}

            Return ONLY a JSON object with these exact fields. Each summary should be a single paragraph:
            {{
                "case_number": "string",
                "petitioner_name": "string",
                "respondent_name": "string",
                "city": "string",
                "petitioner_issues_summary": "string (~5 sentences)",
                "respondent_issues_summary": "string (~5 sentences)",
                "hearing_points_summary": "string (~5 sentences)",
                "final_decision_summary": "string (~5 sentences)",
                "is_appeal": boolean,
                "appeal_subject": "string or null (~5 sentences)",
                "appeal_decision": "string or null (~5 sentences)"
            }}"""

            # Get response from model
            response = self.model.generate_content(prompt)
            content = response.text.strip()
            
            # Clean up JSON response
            if '```json' in content:
                content = content.split('```json')[1].split('```')[0].strip()
            elif '```' in content:
                content = content.split('```')[1].strip()

            # Parse JSON with error handling
            try:
                result = json.loads(content)
                logger.info("Successfully parsed JSON response")
            except json.JSONDecodeError as e:
                logger.error(f"JSON parsing error: {str(e)}")
                return self._create_error_response(pdf_path)

            # Add filename to result
            result['filename'] = os.path.basename(pdf_path)
            
            # Validate and clean summaries
            summary_fields = ['petitioner_issues_summary', 'respondent_issues_summary', 
                            'hearing_points_summary', 'final_decision_summary']
            
            for field in summary_fields:
                if field in result:
                    # Clean up any extra whitespace or formatting
                    summary = result[field].strip()
                    summary = ' '.join(summary.split())  # Normalize whitespace
                    result[field] = summary

            return result

        except Exception as e:
            logger.error(f"Failed to process document: {str(e)}")
            return self._create_error_response(pdf_path)

    def _create_error_response(self, pdf_path: str) -> Dict:
        """Create a structured error response."""
        return {
            'filename': os.path.basename(pdf_path),
            'case_number': 'Error processing document',
            'petitioner_name': 'Not available',
            'respondent_name': 'Not available',
            'city': 'Not available',
            'petitioner_issues_summary': 'Failed to extract summary',
            'respondent_issues_summary': 'Failed to extract summary',
            'hearing_points_summary': 'Failed to extract summary',
            'final_decision_summary': 'Failed to extract summary',
            'is_appeal': False,
            'appeal_subject': None,
            'appeal_decision': None
        }