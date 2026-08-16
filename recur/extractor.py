from google import genai
from google.genai import types
from pydantic import BaseModel, Field
from typing import List, Optional
import os
import json

class CandidateDetails(BaseModel):
    name: str = Field(description="Full name of the person. Use 'Not verified' if not identifiable.")
    profession: Optional[str] = Field(None, description="Their current job title or role (e.g. Machine Learning Engineer)")
    skills: List[str] = Field(default_factory=list, description="Skills explicitly mentioned or clearly implied (e.g. Python, PyTorch)")
    company: Optional[str] = Field(None, description="Current or most recent company name")
    experience_years: Optional[float] = Field(None, description="Years of professional experience. Set to null if not mentioned or can't be calculated.")
    education: Optional[str] = Field(None, description="Degrees obtained (e.g. B.Tech, M.S. in CS)")
    college: Optional[str] = Field(None, description="College or university name")
    location: Optional[str] = Field(None, description="Current city or region (e.g. Bangalore, India)")
    industry: Optional[str] = Field(None, description="Industry sector (e.g. Fintech, Healthcare, SaaS)")
    source_url: str = Field(description="The source URL of this candidate profile")
    evidence: str = Field(description="Explanatory proof string showing why they match, referencing specific details from the text.")
    is_valid_person: bool = Field(description="Set to True if this result represents a specific individual's professional profile. Set to False if this is a company page, job advertisement, list of people, or general article.")

class CandidateListDetails(BaseModel):
    candidates: List[CandidateDetails] = Field(description="List of candidates successfully extracted from the search results.")

def extract_candidates_batch(search_results: List[dict], api_key: str = None) -> List[dict]:
    """
    Sends a list of search results to Gemini in a single batch call.
    Extracts and normalizes candidate details to respect the 15 RPM API limit.
    """
    if not search_results:
        return []

    if not api_key:
        api_key = os.environ.get("GEMINI_API_KEY")
    
    if not api_key:
        raise ValueError("GEMINI_API_KEY is not set.")

    client = genai.Client(api_key=api_key)

    # Format the input items for the LLM
    formatted_results = []
    for idx, r in enumerate(search_results):
        formatted_results.append(
            f"--- Result ID: {idx} ---\n"
            f"URL: {r.get('url', '')}\n"
            f"Title: {r.get('title', '')}\n"
            f"Snippet: {r.get('snippet', '')}\n"
        )
    
    prompt = f"""
    You are an expert recruitment data intelligence system.
    Analyze the following list of search results representing web snippets of professional profiles:
    
    {"".join(formatted_results)}
    
    For each Result ID, extract the candidate's professional details.
    Set 'is_valid_person' to True if the result represents or describes a specific individual's professional profile (e.g. contains a name, title, skills, or bio info).
    Only set 'is_valid_person' to False if the page is clearly a company landing page, a job posting board, a list of profiles, or a general news article. Be lenient: if there is any indication of an individual's career details, mark it as True.
    
    Return the parsed list of candidates. Ensure name, job titles, and location fields are cleaned and normalized.
    For fields that are not mentioned, set them to null/None. For Name, use 'Not verified' if not present.
    """
    
    try:
        response = client.models.generate_content(
            model='gemini-3.5-flash',
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=CandidateListDetails,
                temperature=0.1
            )
        )
        
        parsed_data = json.loads(response.text)
        candidates_raw = parsed_data.get("candidates", [])
        
        # Filter only valid persons
        valid_candidates = [c for c in candidates_raw if c.get("is_valid_person", False)]
        return valid_candidates
    except Exception as e:
        print(f"Error during batch profile extraction: {e}")
        return []

if __name__ == "__main__":
    # Test batch extraction
    test_key = os.environ.get("GEMINI_API_KEY")
    if test_key:
        mock_results = [
            {
                "url": "https://linkedin.com/in/rahul-sharma-ml",
                "title": "Rahul Sharma - Senior ML Engineer - Swiggy | LinkedIn",
                "snippet": "Bangalore. 4+ years of experience in ML, Python, TensorFlow. Built recommendation systems at Swiggy. B.Tech in CS from NIT."
            },
            {
                "url": "https://linkedin.com/company/swiggy",
                "title": "Swiggy | LinkedIn",
                "snippet": "Swiggy is India's leading on-demand delivery platform. Contact Swiggy hiring teams here."
            }
        ]
        print("Testing extraction...")
        extracted = extract_candidates_batch(mock_results, test_key)
        for cand in extracted:
            print("Name:", cand.get("name"))
            print("Profession:", cand.get("profession"))
            print("Skills:", cand.get("skills"))
            print("Company:", cand.get("company"))
            print("Evidence:", cand.get("evidence"))
            print("-" * 20)
    else:
        print("Set GEMINI_API_KEY env var to run tests.")
