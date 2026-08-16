import streamlit as st
import os
import time
import json
import pandas as pd
from google import genai
from parser import parse_user_query, ParsedResult, RecruiterQueryModel, PeopleFinderQueryModel
from searcher import execute_search, generate_recruiter_queries, generate_finder_queries
from extractor import extract_candidates_batch
from ranker import filter_and_rank_candidates, score_candidate
from database import get_cached_search, set_cached_search, get_cached_profile, set_cached_profile

# Set Streamlit Page Configuration
st.set_page_config(
    page_title="AI Professional Discovery & Candidate Ranking System",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Premium CSS Styling
st.markdown("""
<style>
    /* Dark Theme Core Styles */
    .reportview-container {
        background: #0E1117;
    }
    
    /* Premium Candidate Card */
    .candidate-card {
        background-color: #1A1F2C;
        border-radius: 12px;
        padding: 24px;
        margin-bottom: 20px;
        border: 1px solid #2D3748;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
        transition: all 0.25s ease-in-out;
    }
    .candidate-card:hover {
        transform: translateY(-3px);
        border-color: #00F2FE;
        box-shadow: 0 10px 15px -3px rgba(0, 242, 254, 0.15), 0 4px 6px -2px rgba(0, 242, 254, 0.05);
    }
    
    /* Heading typography */
    .main-title {
        font-family: 'Outfit', 'Inter', sans-serif;
        font-size: 2.8rem;
        font-weight: 800;
        background: linear-gradient(135deg, #00F2FE 0%, #4FACFE 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 8px;
    }
    .sub-title {
        font-family: 'Inter', sans-serif;
        font-size: 1.1rem;
        color: #8A99AD;
        margin-bottom: 30px;
    }
    
    /* Match Badges */
    .match-badge {
        background: linear-gradient(135deg, rgba(0, 242, 254, 0.15) 0%, rgba(79, 172, 254, 0.15) 100%);
        color: #00F2FE;
        padding: 5px 12px;
        border-radius: 8px;
        font-weight: 700;
        font-size: 0.9rem;
        display: inline-block;
        border: 1px solid rgba(0, 242, 254, 0.3);
        margin-right: 10px;
    }
    .evidence-check {
        color: #10B981;
        font-weight: bold;
        margin-right: 6px;
    }
    .skill-tag {
        background-color: #2D3748;
        color: #E2E8F0;
        padding: 3px 8px;
        border-radius: 6px;
        font-size: 0.8rem;
        display: inline-block;
        margin-right: 6px;
        margin-top: 4px;
        border: 1px solid #4A5568;
    }
</style>
""", unsafe_allow_html=True)

# Define Mock Database for Demo/Fallback Mode
MOCK_CANDIDATES = [
    {
        "name": "Rahul Sharma",
        "profession": "Senior Machine Learning Engineer",
        "skills": ["Python", "PyTorch", "TensorFlow", "NLP", "Scikit-Learn", "FastAPI"],
        "company": "Swiggy",
        "experience_years": 4.5,
        "education": "B.Tech in Computer Science",
        "college": "NIT Trichy",
        "location": "Bangalore, India",
        "industry": "E-commerce & Logtech",
        "source_url": "https://linkedin.com/in/rahul-sharma-mock",
        "source": "LinkedIn",
        "evidence": "Verified 4.5 YOE as ML Engineer at Swiggy, expert in building recommender systems using PyTorch and training transformer models in Python. Located in Bangalore."
    },
    {
        "name": "Priya Nair",
        "profession": "Data Scientist",
        "skills": ["Python", "SQL", "Pandas", "Scikit-Learn", "Machine Learning", "A/B Testing"],
        "company": "Groww",
        "experience_years": 3.0,
        "education": "M.Tech in Data Science",
        "college": "IIT Bombay",
        "location": "Bangalore, India",
        "industry": "Fintech",
        "source_url": "https://linkedin.com/in/priya-nair-mock",
        "source": "LinkedIn",
        "evidence": "Verified 3 years experience at Groww (Fintech startup). Skilled in Python data pipelines, building classifier models, and managing A/B testing frameworks."
    },
    {
        "name": "Aman Verma",
        "profession": "Software Engineer",
        "skills": ["Python", "Django", "FastAPI", "React", "Docker", "PostgreSQL"],
        "company": "Razorpay",
        "experience_years": 5.0,
        "education": "B.Tech in Information Technology",
        "college": "DTU Delhi",
        "location": "Bangalore, India",
        "industry": "Fintech / Payment Gateway",
        "source_url": "https://linkedin.com/in/aman-verma-mock",
        "source": "LinkedIn",
        "evidence": "Full-stack engineer at Razorpay. 5 YOE developing robust backend systems in Python/Django and building microservices in FastAPI. Located in Bangalore."
    },
    {
        "name": "Karan Malhotra",
        "profession": "Machine Learning Engineer",
        "skills": ["Python", "TensorFlow", "Keras", "Computer Vision", "OpenCV", "AWS"],
        "company": "InMobi",
        "experience_years": 2.5,
        "education": "B.Tech in CS",
        "college": "IIIT Hyderabad",
        "location": "Bangalore, India",
        "industry": "AdTech",
        "source_url": "https://github.com/karan-m-mock",
        "source": "GitHub",
        "evidence": "CV specialist at InMobi. 2.5 YOE. Deep knowledge of TensorFlow object detection models and OpenCV image filtering. Has startup experience at InMobi."
    },
    {
        "name": "Divya Gupta",
        "profession": "Lead NLP Engineer",
        "skills": ["Python", "Hugging Face", "LLMs", "LangChain", "BERT", "PyTorch"],
        "company": "Haptik",
        "experience_years": 6.0,
        "education": "B.Tech in ECE",
        "college": "BITS Pilani",
        "location": "Mumbai, India",
        "industry": "Conversational AI",
        "source_url": "https://linkedin.com/in/divya-gupta-mock",
        "source": "LinkedIn",
        "evidence": "Lead Engineer at conversational AI startup Haptik. 6 YOE specializing in Fine-tuning LLMs, retrieval-augmented generation (RAG) pipelines, and PyTorch models."
    },
    {
        "name": "Aditya Roy",
        "profession": "Backend Developer",
        "skills": ["Python", "Flask", "MongoDB", "Redis", "Celery", "GCP"],
        "company": "Unacademy",
        "experience_years": 1.5,
        "education": "B.Tech in CS",
        "college": "VIT Vellore",
        "location": "Bangalore, India",
        "industry": "EdTech",
        "source_url": "https://linkedin.com/in/aditya-roy-mock",
        "source": "LinkedIn",
        "evidence": "1.5 YOE backend developer at Unacademy. Experienced in Python Flask web services, caching using Redis, and task queues via Celery."
    },
    {
        "name": "Sneha Reddy",
        "profession": "AI Research Scientist",
        "skills": ["Python", "PyTorch", "JAX", "NLP", "Deep Learning", "Transformers"],
        "company": "Google",
        "experience_years": 5.0,
        "education": "Ph.D. in Computer Science",
        "college": "IIT Delhi",
        "location": "Hyderabad, India",
        "industry": "Big Tech / AI Research",
        "source_url": "https://linkedin.com/in/sneha-reddy-mock",
        "source": "LinkedIn",
        "evidence": "AI Researcher at Google. Ph.D. from IIT Delhi. Core expertise in Deep Learning Transformers, sequence processing in JAX, and publishing top-tier AI papers."
    }
]

# Sidebar Setup
st.sidebar.image("https://img.icons8.com/nolan/96/search.png", width=70)
st.sidebar.markdown("### Search Configurations")

# Mode Switch
app_mode = st.sidebar.radio(
    "Select Search Mode",
    ["🔍 Recruiter Mode", "👤 Quick People Finder"],
    help="Recruiter Mode is for talent sourcing and candidate ranking. People Finder is for looking up specific individuals to fetch their social footprints."
)

# API Keys Section & Caching checks
st.sidebar.markdown("---")
st.sidebar.markdown("### API Credentials")

# Pre-load keys from environment/secrets
env_gemini = os.environ.get("GEMINI_API_KEY", "")
env_tavily = os.environ.get("TAVILY_API_KEY", "")
env_brave = os.environ.get("BRAVE_API_KEY", "")

gemini_key = env_gemini
tavily_key = env_tavily
brave_key = env_brave

# UI representation: Hide if already in secrets
if env_gemini:
    st.sidebar.success("⚡ Gemini API: Active (System)")
    if env_tavily:
        st.sidebar.success("🔍 Search API: Active (Tavily)")
    elif env_brave:
        st.sidebar.success("🔍 Search API: Active (Brave)")
    else:
        st.sidebar.info("🌐 Search: DuckDuckGo Active")
        
    with st.sidebar.expander("Override System API Keys"):
        override_gemini = st.text_input("Override Gemini Key", type="password", value="")
        override_tavily = st.text_input("Override Tavily Key", type="password", value="")
        override_brave = st.text_input("Override Brave Key", type="password", value="")
        if override_gemini: gemini_key = override_gemini
        if override_tavily: tavily_key = override_tavily
        if override_brave: brave_key = override_brave
else:
    gemini_key = st.sidebar.text_input("Gemini API Key", type="password", value="", help="Provide your free Google AI Studio key.")
    tavily_key = st.sidebar.text_input("Tavily API Key (Optional)", type="password", value="")
    brave_key = st.sidebar.text_input("Brave API Key (Optional)", type="password", value="")

# Demo Mode Toggle (automatically false if system key is active, unless toggled)
demo_mode = st.sidebar.toggle("Use Mock Demo Mode", value=not bool(gemini_key), 
                             help="Enables searching within a preloaded database of candidates. Perfect for testing without active API keys.")


st.sidebar.markdown("---")
st.sidebar.info(
    "💡 **Pro Tip:** If Tavily & Brave keys are empty, search operations will automatically use **DuckDuckGo Search** (completely free & keyless)."
)

# Shared email generation logic
def generate_pitch_email(candidate: dict, job_description: str, api_key: str) -> str:
    """Uses Gemini to generate a personalized recruitment pitch email."""
    if not api_key:
        return "Please input a Gemini API Key in the sidebar to generate personalized outreach emails."
    
    try:
        client = genai.Client(api_key=api_key)
        prompt = f"""
        You are a highly professional talent sourcer. Draft a compelling, personalized cold email to the candidate below.
        
        Candidate Details:
        - Name: {candidate.get('name')}
        - Current Role: {candidate.get('profession')}
        - Company: {candidate.get('company', 'Not specified')}
        - Key Skills: {', '.join(candidate.get('skills', []))}
        - Location: {candidate.get('location')}
        - Evidence of Achievements: {candidate.get('evidence')}
        
        Job context/role to pitch:
        "{job_description}"
        
        Guidelines:
        1. Keep it concise, engaging, and personalized to their experience.
        2. Reference a specific detail from their skills or evidence.
        3. Do not invent any facts about the candidate that are not listed above.
        4. Provide placeholders for recruiter name/contact.
        5. Provide a strong subject line.
        """
        response = client.models.generate_content(
            model='gemini-1.5-flash',
            contents=prompt,
            config=types.GenerateContentConfig(temperature=0.7)
        )
        return response.text
    except Exception as e:
        return f"Error generating email: {e}"

# UI Render Logic
if app_mode == "🔍 Recruiter Mode":
    st.markdown("<h1 class='main-title'>Recruiter Sourcing & Ranking</h1>", unsafe_allow_html=True)
    st.markdown("<p class='sub-title'>Translate natural language hiring requirements into ranked, verified candidate shortlists.</p>", unsafe_allow_html=True)
    
    # NLP Search Input
    user_query = st.text_area(
        "Describe the people you are looking for:",
        value="I need 5 Python developers with Machine Learning in Bangalore with 3+ years experience and startup experience",
        height=70,
        placeholder="e.g. Find 10 React developers with Node.js and Docker in Delhi"
    )
    
    # Optional Structured Inputs
    with st.expander("🛠️ Advanced Search Filters (Optional overrides)"):
        col1, col2, col3 = st.columns(3)
        with col1:
            req_profession = st.text_input("Role / Profession Title", placeholder="e.g. ML Engineer")
            req_location = st.text_input("Location City", placeholder="e.g. Bangalore")
        with col2:
            req_skills = st.text_input("Comma Separated Skills", placeholder="e.g. Python, PyTorch")
            req_experience = st.number_input("Minimum Experience (Years)", min_value=0.0, max_value=20.0, value=0.0, step=0.5)
        with col3:
            req_startup = st.checkbox("Require Startup Experience", value=False)
            candidate_count = st.number_input("Candidates to fetch", min_value=1, max_value=100, value=5)
            
    # Search Button
    if st.button("🚀 Find & Rank Candidates", use_container_width=True):
        if not demo_mode and not gemini_key:
            st.error("⚠️ Gemini API Key is required for live search parsing. Please provide it in the sidebar or toggle 'Use Mock Demo Mode'.")
        else:
            # 1. Start Progress Bar & Spinner
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            with st.spinner("Processing pipeline..."):
                # Phase 1: Parse requirements (15%)
                status_text.markdown("🔮 **Phase 1:** Parsing natural language query with Gemini AI...")
                progress_bar.progress(15)
                
                parsed_req = None
                if demo_mode or not gemini_key:
                    # Construct manual parsed requirements for demo mode
                    parsed_req = ParsedResult(
                        mode="recruiter",
                        recruiter_data=RecruiterQueryModel(
                            candidate_count=candidate_count if candidate_count else 5,
                            profession=req_profession if req_profession else "ML Engineer",
                            skills=[s.strip() for s in req_skills.split(",")] if req_skills else ["Python", "Machine Learning"],
                            minimum_experience_years=req_experience if req_experience > 0 else 2.0,
                            location=req_location if req_location else "Bangalore",
                            startup_experience=req_startup or "startup" in user_query.lower()
                        )
                    )
                else:
                    try:
                        parsed_req = parse_user_query(user_query, gemini_key)
                        # Apply overrides if provided in advanced section
                        if req_profession: parsed_req.recruiter_data.profession = req_profession
                        if req_location: parsed_req.recruiter_data.location = req_location
                        if req_skills: parsed_req.recruiter_data.skills = [s.strip() for s in req_skills.split(",")]
                        if req_experience > 0: parsed_req.recruiter_data.minimum_experience_years = req_experience
                        if req_startup: parsed_req.recruiter_data.startup_experience = True
                        if candidate_count: parsed_req.recruiter_data.candidate_count = candidate_count
                    except Exception as e:
                        st.error(f"Failed to parse requirements: {e}")
                        st.stop()
                
                # Show parsed requirements back to user
                st.write("### Parsed Requirements:")
                r_data = parsed_req.recruiter_data
                st.json(r_data.model_dump())
                
                # Phase 2: Sourcing/Search (40%)
                status_text.markdown("🌐 **Phase 2:** Querying public search engines for public portfolios and profiles...")
                progress_bar.progress(40)
                
                candidates_pool = []
                
                if demo_mode:
                    time.sleep(1) # Fake delay
                    candidates_pool = MOCK_CANDIDATES
                else:
                    # Generate search queries
                    queries = generate_recruiter_queries(
                        profession=r_data.profession,
                        skills=r_data.skills,
                        location=r_data.location,
                        startup=r_data.startup_experience
                    )
                    
                    search_results = []
                    for q in queries:
                        # Check SQLite Cache first
                        cached = get_cached_search(q)
                        if cached:
                            search_results.extend(cached)
                        else:
                            fetched = execute_search(q, tavily_key, brave_key, max_results=8)
                            set_cached_search(q, fetched)
                            search_results.extend(fetched)
                    
                    # Deduplicate search results by URL
                    seen_urls = set()
                    unique_search_results = []
                    for r in search_results:
                        if r["url"] not in seen_urls:
                            seen_urls.add(r["url"])
                            unique_search_results.append(r)
                            
                    # Phase 3: Extraction & Normalization (70%)
                    status_text.markdown("🧹 **Phase 3:** Extracting professional data from search results...")
                    progress_bar.progress(70)
                    
                    # Check cached profiles first
                    uncached_results = []
                    for r in unique_search_results:
                        cached_prof = get_cached_profile(r["url"])
                        if cached_prof:
                            candidates_pool.append(cached_prof)
                        else:
                            uncached_results.append(r)
                            
                    # Batch extract remaining uncached profiles (max 8 at once to be safe with rate limits)
                    if uncached_results:
                        batch_extracted = extract_candidates_batch(uncached_results[:8], gemini_key)
                        for cand in batch_extracted:
                            set_cached_profile(cand["source_url"], cand)
                            candidates_pool.append(cand)
                
                # Phase 4: Scoring & Semantic Ranking (90%)
                status_text.markdown("🧠 **Phase 4:** Running Sentence-Transformers semantic match scoring...")
                progress_bar.progress(90)
                
                ranked_candidates = filter_and_rank_candidates(
                    candidates=candidates_pool,
                    requirements=r_data.model_dump(),
                    apply_hard_filters=False # Scored all and let users filter manually on screen
                )
                
                # Phase 5: Displaying Shortlist (100%)
                status_text.markdown("✅ **Phase 5:** Dashboard rendered successfully!")
                progress_bar.progress(100)
                time.sleep(0.5)
                status_text.empty()
                progress_bar.empty()
                
                # Render results in UI
                st.write(f"## Found {len(ranked_candidates)} Matching Profiles")
                
                # Quick filters in UI
                col_f1, col_f2 = st.columns(2)
                with col_f1:
                    min_score_filter = st.slider("Filter by Match Score (%)", min_value=0, max_value=100, value=50)
                with col_f2:
                    min_exp_filter = st.slider("Filter by Experience (Years)", min_value=0.0, max_value=15.0, value=0.0, step=0.5)
                
                # Display Ranked Candidate Cards
                count = 0
                for cand in ranked_candidates:
                    if cand["match_score"] < min_score_filter:
                        continue
                    if cand.get("experience_years") is not None and cand.get("experience_years") < min_exp_filter:
                        continue
                        
                    count += 1
                    if count > r_data.candidate_count:
                        break
                        
                    # Build card
                    st.markdown(f"""
                    <div class="candidate-card">
                        <div style="display: flex; justify-content: space-between; align-items: flex-start;">
                            <div>
                                <div class="candidate-name">{cand.get('name')}</div>
                                <div class="candidate-role">{cand.get('profession', 'Profession not verified')} at <strong>{cand.get('company', 'Unknown')}</strong></div>
                            </div>
                            <span class="match-badge">Match: {cand.get('match_score')}%</span>
                        </div>
                        <div style="margin-top: 10px;">
                            <strong>Experience:</strong> {cand.get('experience_years', 'Not verified')} Years &nbsp;|&nbsp;
                            <strong>Location:</strong> {cand.get('location', 'Not verified')} &nbsp;|&nbsp;
                            <strong>Education:</strong> {cand.get('education', 'Not verified')} ({cand.get('college', 'Not verified')})
                        </div>
                        <div style="margin-top: 12px; margin-bottom: 12px;">
                            {"".join([f'<span class="skill-tag">{s}</span>' for s in cand.get('skills', [])])}
                        </div>
                        <div style="background-color: #2D3748; padding: 12px; border-radius: 8px; border-left: 4px solid #00F2FE;">
                            <strong>Why Matched (AI Evidence):</strong><br/>
                            <span class="evidence-check">✓</span> {cand.get('evidence')}
                        </div>
                        <div style="margin-top: 15px; display: flex; gap: 15px; align-items: center;">
                            <a href="{cand.get('source_url')}" target="_blank" style="text-decoration: none;">
                                <button style="background-color: #00F2FE; color: #0E1117; font-weight: 700; border: none; padding: 6px 14px; border-radius: 6px; cursor: pointer;">
                                    View Source Profile
                                </button>
                            </a>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # Outreach Email Expander inside candidate block
                    with st.expander(f"✉️ Generate Outreach Pitch to {cand.get('name')}"):
                        jd_context = st.text_area(
                            "Job description / Pitch Context", 
                            value=f"Looking for a {r_data.profession} in {r_data.location} experienced with {', '.join(r_data.skills[:3])}. We are a fast-growing startup.",
                            key=f"jd_{cand.get('name')}_{count}"
                        )
                        if st.button("Generate Cold Email Draft", key=f"btn_email_{cand.get('name')}_{count}"):
                            with st.spinner("Writing personalized outreach..."):
                                email_draft = generate_pitch_email(cand, jd_context, gemini_key)
                                st.code(email_draft, language="markdown")

                if count == 0:
                    st.warning("No candidates found matching the selected slider filters. Try adjusting the thresholds.")

# Normal Mode (People Finder)
else:
    st.markdown("<h1 class='main-title'>Quick People Finder</h1>", unsafe_allow_html=True)
    st.markdown("<p class='sub-title'>Search for a specific person to aggregate all of their public social profiles (LinkedIn, GitHub, Twitter/X, Portfolios) into one dashboard.</p>", unsafe_allow_html=True)
    
    col_name, col_comp, col_coll = st.columns(3)
    with col_name:
        target_name = st.text_input("Full Name of Person", placeholder="e.g. Rahul Sharma")
    with col_comp:
        target_company = st.text_input("Current/Past Company (Optional)", placeholder="e.g. Google")
    with col_coll:
        target_college = st.text_input("College / Education (Optional)", placeholder="e.g. IIT Delhi")
        
    if st.button("🔍 Search Footprint", use_container_width=True):
        if not target_name:
            st.error("Please enter a name to search.")
        elif not demo_mode and not gemini_key:
            st.error("⚠️ Gemini API Key is required for live footprint parsing. Please input in the sidebar or toggle 'Use Mock Demo Mode'.")
        else:
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            with st.spinner("Finding footprint..."):
                status_text.markdown("🔮 **Phase 1:** Creating footprint search parameters...")
                progress_bar.progress(20)
                
                # Mock Mode logic
                if demo_mode:
                    time.sleep(1)
                    progress_bar.progress(60)
                    status_text.markdown("🌐 **Phase 2:** Sourcing mock records...")
                    time.sleep(0.5)
                    progress_bar.progress(100)
                    status_text.empty()
                    progress_bar.empty()
                    
                    # Search name in mock database
                    matches = [
                        c for c in MOCK_CANDIDATES 
                        if target_name.lower() in c["name"].lower()
                    ]
                    
                    if not matches:
                        st.warning("No matching profile found in mock database. (Try searching 'Rahul', 'Priya', or 'Aman')")
                    else:
                        for m in matches:
                            st.markdown(f"""
                            <div class="candidate-card" style="border-left: 5px solid #4FACFE;">
                                <div class="candidate-name" style="font-size: 1.5rem; color: #FFF;">{m.get('name')}</div>
                                <div class="candidate-role" style="font-size: 1.1rem; color: #00F2FE;">{m.get('profession')} at <strong>{m.get('company')}</strong></div>
                                <hr style="border: 0.5px solid #2D3748; margin: 15px 0;"/>
                                <div>
                                    <strong>Education:</strong> {m.get('education')} at {m.get('college')}<br/>
                                    <strong>Location:</strong> {m.get('location')}<br/>
                                    <strong>Sector:</strong> {m.get('industry')}<br/>
                                </div>
                                <div style="margin-top: 15px;">
                                    {"".join([f'<span class="skill-tag">{s}</span>' for s in m.get('skills', [])])}
                                </div>
                                <div style="margin-top: 20px; background-color: #2D3748; padding: 12px; border-radius: 8px;">
                                    <strong>Public Footprint Source Found:</strong><br/>
                                    🔗 <a href="{m.get('source_url')}" target="_blank" style="color: #00F2FE; font-weight: bold;">{m.get('source')} Profile URL</a>
                                </div>
                            </div>
                            """, unsafe_allow_html=True)
                
                # Live API Mode logic
                else:
                    queries = generate_finder_queries(
                        name=target_name,
                        company=target_company,
                        college=target_college
                    )
                    
                    status_text.markdown("🌐 **Phase 2:** Querying public dorks across LinkedIn, GitHub, and Twitter...")
                    progress_bar.progress(50)
                    
                    search_results = []
                    for q in queries:
                        cached = get_cached_search(q)
                        if cached:
                            search_results.extend(cached)
                        else:
                            fetched = execute_search(q, tavily_key, brave_key, max_results=5)
                            set_cached_search(q, fetched)
                            search_results.extend(fetched)
                    
                    # Deduplicate urls
                    seen_urls = set()
                    unique_results = []
                    for r in search_results:
                        if r["url"] not in seen_urls:
                            seen_urls.add(r["url"])
                            unique_results.append(r)
                            
                    status_text.markdown("🧠 **Phase 3:** Extracting and aggregating profile footprint...")
                    progress_bar.progress(85)
                    
                    # Call Gemini to extract the aggregated candidate card
                    extracted_profile = extract_candidates_batch(unique_results, gemini_key)
                    
                    progress_bar.progress(100)
                    status_text.empty()
                    progress_bar.empty()
                    
                    if not extracted_profile:
                        st.warning("Could not resolve specific candidate profile summaries from public web snippets. Try adding more context (e.g. company or college).")
                    else:
                        st.success(f"Discovered {len(extracted_profile)} potential profile connections:")
                        for p in extracted_profile:
                            st.markdown(f"""
                            <div class="candidate-card" style="border-left: 5px solid #4FACFE;">
                                <div class="candidate-name" style="font-size: 1.5rem; color: #FFF;">{p.get('name')}</div>
                                <div class="candidate-role" style="font-size: 1.1rem; color: #00F2FE;">{p.get('profession')} at <strong>{p.get('company', 'Unknown')}</strong></div>
                                <hr style="border: 0.5px solid #2D3748; margin: 15px 0;"/>
                                <div>
                                    <strong>Education:</strong> {p.get('education', 'Not verified')}<br/>
                                    <strong>College:</strong> {p.get('college', 'Not verified')}<br/>
                                    <strong>Location:</strong> {p.get('location', 'Not verified')}<br/>
                                </div>
                                <div style="margin-top: 15px;">
                                    {"".join([f'<span class="skill-tag">{s}</span>' for s in p.get('skills', [])])}
                                </div>
                                <div style="margin-top: 20px; background-color: #2D3748; padding: 12px; border-radius: 8px;">
                                    <strong>Direct Link:</strong><br/>
                                    🔗 <a href="{p.get('source_url')}" target="_blank" style="color: #00F2FE; font-weight: bold;">View Public Profile Connection</a>
                                </div>
                            </div>
                            """, unsafe_allow_html=True)
