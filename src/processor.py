# src/processor.py

import os
from typing import Dict, List, Optional
import fitz  # PyMuPDF
from dataclasses import dataclass
import google.generativeai as genai
from concurrent.futures import ThreadPoolExecutor
import json

@dataclass
class LegalDocument:
    case_number: str
    petitioner_name: str
    respondent_name: str
    city: str
    petitioner_issues: List[str]
    respondent_issues: List[str]
    hearing_points: List[str]
    final_decision: str
    is_appeal: bool
    appeal_subject: Optional[str]
    appeal_decision: Optional[str]
    
class LegalDocumentProcessor:
    def __init__(self, api_key: str):
        genai.configure(api_key=api_key)
        # Initialize Gemini-Pro model
        self.model = genai.GenerativeModel('gemini-pro')

        
    
    def parse_llm_response(self,response_text):
        """Parses the LLM response, handling potential errors."""
        try:
            return json.loads(response_text)
        except json.JSONDecodeError as e:
            print(f"Error parsing LLM response: {e}")
            # Implement additional error handling or partial parsing logic here (optional)
            return {}  # Return an empty dictionary in case of parsing failure

        
    def extract_text_from_pdf(self, pdf_path: str) -> str:
        """Extract text content from PDF file."""
        doc = fitz.open(pdf_path)
        text = ""
        for page in doc:
            text += page.get_text()
        return text
    
    def _create_extraction_prompt(self, text: str) -> str:
        return f"""Please analyze the following legal document and extract key information.
        Focus on identifying:
        - File name
        - Case number
        - Petitioner name
        - Respondent name
        - City
        - Main issues raised by petitioner
        - Main issues raised by respondent
        - Key points made during hearing (this is not the hearing decision)
        - Final decision
        - If this is an appeal, what is the appeal about and what was the appeal decision

        Document text:
        {text}

        Please format your response as a JSON object with these fields:
        case_number, petitioner_name, respondent_name, city, petitioner_issues (array),
        respondent_issues (array), hearing_points (array), final_decision,
        is_appeal (boolean), appeal_subject (string or null), appeal_decision (string or null)
        """

    def _create_summary_prompt(self, text: str, field: str) -> str:
        return f"""Please provide a concise summary of the following {field} from a legal document:

        {text}

        Provide a clear, objective summary in 2-3 sentences.
        """


    def extract_information(self, text: str) -> LegalDocument:
        """Extract key information from document text using Gemini model."""
        prompt = self._create_extraction_prompt(text)
        response = self.model.generate_content(prompt)

        try:
            content = response.text
            if '```json' in content:
                content = content.split('```json')[1].split('```')[0].strip()
            result = json.loads(content)

            # Ensure all required fields are present in the parsed JSON
            required_fields = ['case_number', 'petitioner_name', 'respondent_name', 'city', 'petitioner_issues', 'respondent_issues', 'hearing_points', 'final_decision', 'is_appeal', 'appeal_subject', 'appeal_decision']
            for field in required_fields:
                if field not in result:
                    raise ValueError(f"Missing required field: {field}")

            return LegalDocument(**result)
        except Exception as e:
            raise ValueError(f"Failed to parse LLM output: {e}")


    def summarize_field(self, text: str, field: str) -> str:
        """Generate a summary for a specific field using Gemini model."""
        prompt = self._create_summary_prompt(text, field)
        
        response = self.model.generate_content(prompt)
        return response.text.strip()

    def process_document(self, pdf_path: str) -> Dict:
        """Process a single legal document and return structured results with summaries."""
        # Extract text from PDF
        text = self.extract_text_from_pdf(pdf_path)
        
        # Extract initial information
        doc_info = self.extract_information(text)
        
        # Generate summaries for relevant fields
        summaries = {}
        fields_to_summarize = [
            'petitioner_issues',
            'respondent_issues',
            'hearing_points',
            'final_decision'
        ]
        
        with ThreadPoolExecutor(max_workers=4) as executor:
            future_to_field = {
                executor.submit(
                    self.summarize_field,
                    '\n'.join(getattr(doc_info, field)) if isinstance(getattr(doc_info, field), list)
                    else getattr(doc_info, field),
                    field
                ): field
                for field in fields_to_summarize
            }
            
            for future in future_to_field:
                field = future_to_field[future]
                try:
                    summaries[f"{field}_summary"] = future.result()
                except Exception as e:
                    summaries[f"{field}_summary"] = f"Failed to generate summary: {str(e)}"
        
        # Combine all information
        # result = {
        #     'case_number': doc_info.case_number,
        #     'petitioner_name': doc_info.petitioner_name,
        #     'respondent_name': doc_info.respondent_name,
        #     'city': doc_info.city,
        #     'petitioner_issues': doc_info.petitioner_issues,
        #     'petitioner_issues_summary': summaries['petitioner_issues_summary'],
        #     'respondent_issues': doc_info.respondent_issues,
        #     'respondent_issues_summary': summaries['respondent_issues_summary'],
        #     'hearing_points': doc_info.hearing_points,
        #     'hearing_points_summary': summaries['hearing_points_summary'],
        #     'final_decision': doc_info.final_decision,
        #     'final_decision_summary': summaries['final_decision_summary'],
        #     'is_appeal': doc_info.is_appeal,
        #     'appeal_subject': doc_info.appeal_subject,
        #     'appeal_decision': doc_info.appeal_decision
        # }

        result = {
            'case_number': doc_info.case_number,
            'petitioner_name': doc_info.petitioner_name,
            'respondent_name': doc_info.respondent_name,
            'city': doc_info.city,
            'petitioner_issues_summary': summaries['petitioner_issues_summary'],
            'respondent_issues_summary': summaries['respondent_issues_summary'],
            'hearing_points_summary': summaries['hearing_points_summary'],
            'final_decision_summary': summaries['final_decision_summary'],
            'is_appeal': doc_info.is_appeal,
            'appeal_subject': doc_info.appeal_subject,
            'appeal_decision': doc_info.appeal_decision
        }
        
        return result