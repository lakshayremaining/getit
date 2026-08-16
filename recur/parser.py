from google import genai
from google.genai import types
from pydantic import BaseModel, Field
from typing import List, Optional
import os
import json

# Define schemas for structured outputs
class RecruiterQueryModel(BaseModel):
    candidate_count: int = Field(default=10, description="Number of candidates requested, default to 10 if not specified")
    profession: Optional[str] = Field(None, description="The job title or profession (e.g. ML Engineer, Frontend Developer)")
    skills: List[str] = Field(default_factory=list, description="List of technical or soft skills requested")
    minimum_experience_years: Optional[float] = Field(None, description="Minimum years of experience required")
    location: Optional[str] = Field(None, description="Target city or country")
    startup_experience: bool = Field(default=False, description="True if startup experience is explicitly required")
    other_requirements: Optional[str] = Field(None, description="Any other specific requirements mentioned")

class PeopleFinderQueryModel(BaseModel):
    name: str = Field(description="Name of the person being searched")
    current_company: Optional[str] = Field(None, description="Company they work for or worked at")
    college: Optional[str] = Field(None, description="College, university or education institution they attended")
    profession: Optional[str] = Field(None, description="Profession or job title")

class ParsedResult(BaseModel):
    mode: str = Field(description="Must be either 'recruiter' (for sourcing/hiring a group of people) or 'finder' (for looking up a specific individual person by name)")
    recruiter_data: Optional[RecruiterQueryModel] = None
    finder_data: Optional[PeopleFinderQueryModel] = None

def parse_user_query(query: str, api_key: str = None) -> ParsedResult:
    """
    Parses natural language queries using Gemini API to extract structured parameters
    supporting both Recruiter Sourcing and People Finder modes.
    """
    if not api_key:
        api_key = os.environ.get("GEMINI_API_KEY")
    
    if not api_key:
        raise ValueError("GEMINI_API_KEY is not set. Please provide a valid key.")

    client = genai.Client(api_key=api_key)
    
    prompt = f"""
    Analyze the following user search query:
    "{query}"
    
    Determine if the user is trying to find a group of candidates (recruiter mode) or a specific person by name (finder mode).
    Then extract all relevant parameters and return them according to the schema.
    """
    
    response = client.models.generate_content(
        model='gemini-2.0-flash',
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=ParsedResult,
            temperature=0.1
        )
    )
    
    # Parse the response text as a dict and load it into our Pydantic model
    data = json.loads(response.text)
    return ParsedResult(**data)

if __name__ == "__main__":
    # Test block
    test_key = os.environ.get("GEMINI_API_KEY")
    if test_key:
        try:
            print("Testing Recruiter Query Parsing...")
            r_res = parse_user_query("I need 5 python devs with machine learning in Bangalore with 3+ years experience", api_key=test_key)
            print("Mode:", r_res.mode)
            print("Recruiter Data:", r_res.recruiter_data)
            
            print("\nTesting Finder Query Parsing...")
            f_res = parse_user_query("Rahul Sharma working at Google", api_key=test_key)
            print("Mode:", f_res.mode)
            print("Finder Data:", f_res.finder_data)
        except Exception as e:
            print("Error during test:", e)
    else:
        print("Set GEMINI_API_KEY env var to run tests.")
