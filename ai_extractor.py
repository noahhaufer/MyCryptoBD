"""
AI-powered information extraction from Telegram profiles and messages.
Uses OpenAI GPT-4 to extract company, role, and topics from user bio and messages.
"""

import json
import logging
from typing import Dict, List, Optional
from openai import OpenAI
from openai import APIError, RateLimitError, APIConnectionError

logger = logging.getLogger(__name__)


class AIExtractor:
    """Extract professional information using GPT-4."""

    def __init__(self, api_key: str):
        """
        Initialize the AI extractor with OpenAI API key.

        Args:
            api_key: OpenAI API key
        """
        self.client = OpenAI(api_key=api_key)
        logger.info("AI Extractor initialized")

    def extract_company_info(
        self,
        bio: Optional[str] = None,
        messages: Optional[List[str]] = None
    ) -> Dict[str, any]:
        """
        Extract company, role, and topics from user bio and messages.

        Args:
            bio: User's Telegram bio
            messages: List of initial messages from the user

        Returns:
            Dictionary with keys: company, role, topics
            Returns 'Unknown' for fields that cannot be determined
        """
        # Handle empty inputs
        if not bio and not messages:
            logger.warning("No bio or messages provided for extraction")
            return {
                'company': 'Unknown',
                'role': 'Unknown',
                'topics': []
            }

        # Build context for GPT
        context_parts = []
        if bio:
            context_parts.append(f"Bio: {bio}")
        if messages and len(messages) > 0:
            messages_text = "\n".join([f"- {msg}" for msg in messages])
            context_parts.append(f"Initial messages:\n{messages_text}")

        context = "\n\n".join(context_parts)

        # Construct the prompt
        prompt = self._build_extraction_prompt(context)

        try:
            # Call GPT-4 for extraction
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {
                        "role": "system",
                        "content": "You are a professional information extraction assistant. "
                                   "Extract company names, job titles, and discussion topics from "
                                   "Telegram profiles and messages. Always return valid JSON."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.3,  # Lower temperature for more consistent extraction
                max_tokens=300
            )

            # Extract and parse the response
            result_text = response.choices[0].message.content.strip()
            result = self._parse_extraction_result(result_text)

            logger.info(f"Successfully extracted company info: {result.get('company', 'Unknown')}")
            return result

        except RateLimitError as e:
            logger.error(f"OpenAI rate limit exceeded: {e}")
            return self._get_default_result()

        except APIConnectionError as e:
            logger.error(f"OpenAI API connection error: {e}")
            return self._get_default_result()

        except APIError as e:
            logger.error(f"OpenAI API error: {e}")
            return self._get_default_result()

        except Exception as e:
            logger.error(f"Unexpected error during extraction: {e}")
            return self._get_default_result()

    def _build_extraction_prompt(self, context: str) -> str:
        """
        Build the prompt for GPT-4 extraction.

        Args:
            context: Combined bio and messages text

        Returns:
            Formatted prompt string
        """
        return f"""You are analyzing a Telegram profile and initial conversation to extract professional information.

{context}

Extract and return ONLY valid JSON with this structure:
{{
  "company": "company name or Unknown",
  "role": "job title or Unknown",
  "topics": ["topic1", "topic2", "topic3"]
}}

Guidelines:
- Be concise and specific
- If information isn't clearly stated, use "Unknown"
- For topics, extract 1-3 key subjects discussed or mentioned
- Company names should be official names, not abbreviations (unless that's all that's provided)
- Job titles should be formal (e.g., "Software Engineer" not just "engineer")
- Return ONLY the JSON object, no additional text

JSON output:"""

    def _parse_extraction_result(self, result_text: str) -> Dict[str, any]:
        """
        Parse the GPT-4 response into a structured dictionary.

        Args:
            result_text: Raw text response from GPT-4

        Returns:
            Dictionary with company, role, and topics
        """
        try:
            # Try to parse as JSON
            result = json.loads(result_text)

            # Validate and provide defaults
            return {
                'company': result.get('company', 'Unknown'),
                'role': result.get('role', 'Unknown'),
                'topics': result.get('topics', [])
            }

        except json.JSONDecodeError:
            logger.warning(f"Failed to parse JSON response: {result_text}")

            # Try to extract information from unstructured text as fallback
            return self._fallback_extraction(result_text)

    def _fallback_extraction(self, text: str) -> Dict[str, any]:
        """
        Fallback extraction when JSON parsing fails.
        Attempts to extract information from unstructured text.

        Args:
            text: Raw text that couldn't be parsed as JSON

        Returns:
            Dictionary with extracted or default values
        """
        result = {
            'company': 'Unknown',
            'role': 'Unknown',
            'topics': []
        }

        # Simple keyword-based extraction (very basic fallback)
        text_lower = text.lower()

        # Look for company indicators
        company_keywords = ['company:', 'works at', 'working at', 'employed by']
        for keyword in company_keywords:
            if keyword in text_lower:
                # Try to extract the next few words after the keyword
                start_idx = text_lower.index(keyword) + len(keyword)
                company_text = text[start_idx:start_idx + 50].split('\n')[0].strip()
                if company_text and len(company_text) > 2:
                    result['company'] = company_text.split(',')[0].strip()
                    break

        # Look for role indicators
        role_keywords = ['role:', 'title:', 'position:', 'job:']
        for keyword in role_keywords:
            if keyword in text_lower:
                start_idx = text_lower.index(keyword) + len(keyword)
                role_text = text[start_idx:start_idx + 50].split('\n')[0].strip()
                if role_text and len(role_text) > 2:
                    result['role'] = role_text.split(',')[0].strip()
                    break

        logger.info("Used fallback extraction method")
        return result

    def _get_default_result(self) -> Dict[str, any]:
        """
        Get default result when extraction fails.

        Returns:
            Dictionary with Unknown values
        """
        return {
            'company': 'Unknown',
            'role': 'Unknown',
            'topics': []
        }

    def summarize_contact(self, contact_data: Dict) -> str:
        """
        Generate a human-readable summary of a contact.

        Args:
            contact_data: Dictionary with contact information

        Returns:
            Formatted string summary
        """
        name = contact_data.get('name', 'Unknown')
        company = contact_data.get('company', 'Unknown')
        role = contact_data.get('role', 'Unknown')
        topics = contact_data.get('topics', [])

        summary = f"👤 {name}"

        if company != 'Unknown':
            summary += f"\n🏢 {company}"

        if role != 'Unknown':
            summary += f"\n💼 {role}"

        if topics and len(topics) > 0:
            topics_str = ", ".join(topics)
            summary += f"\n💬 Topics: {topics_str}"

        return summary
