import numpy as np
from typing import List, Dict, Any

# Attempt to import sentence-transformers, with a fallback to TF-IDF cosine similarity
HAS_TRANSFORMERS = False
try:
    from sentence_transformers import SentenceTransformer, util
    # Load model lazily
    MODEL = None
    HAS_TRANSFORMERS = True
except Exception as e:
    print(f"Sentence-Transformers not available, falling back to TF-IDF matching: {e}")

# Fallback TF-IDF vectorizer if transformers are missing
if not HAS_TRANSFORMERS:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity

def get_similarity(text1: str, text2: str) -> float:
    """Calculates cosine similarity between two texts using either Sentence-Transformers or TF-IDF."""
    if not text1 or not text2:
        return 0.0
        
    global HAS_TRANSFORMERS, MODEL
    
    if HAS_TRANSFORMERS:
        try:
            if MODEL is None:
                print("Loading Sentence-Transformers model: all-MiniLM-L6-v2...")
                MODEL = SentenceTransformer('all-MiniLM-L6-v2')
            
            embeddings = MODEL.encode([text1, text2], convert_to_tensor=True)
            similarity = util.cos_sim(embeddings[0], embeddings[1]).item()
            return max(0.0, float(similarity))
        except Exception as e:
            print(f"Error in Sentence-Transformers encoding: {e}. Falling back to TF-IDF.")
            HAS_TRANSFORMERS = False # Disable for future calls
            
    # Fallback to TF-IDF cosine similarity
    try:
        vectorizer = TfidfVectorizer().fit_transform([text1, text2])
        vectors = vectorizer.todense()
        similarity = cosine_similarity(vectors[0], vectors[1])[0][0]
        return max(0.0, float(similarity))
    except Exception as e:
        print(f"Error in TF-IDF calculation: {e}")
        
    # Basic token overlap fallback
    tokens1 = set(text1.lower().split())
    tokens2 = set(text2.lower().split())
    if not tokens1 or not tokens2:
        return 0.0
    return len(tokens1.intersection(tokens2)) / max(len(tokens1), len(tokens2))

def score_candidate(candidate: Dict[str, Any], requirements: Dict[str, Any]) -> Dict[str, Any]:
    """
    Scores a candidate based on requirements.
    Formula weights:
      - Skill Match: 30%
      - Experience Match: 20%
      - Profession Match: 20%
      - Location Match: 10%
      - Startup Experience Match: 10%
      - Education Match: 5%
      - Industry/Company Match: 5%
    """
    # 1. Profession Match (20%)
    req_profession = requirements.get("profession")
    cand_profession = candidate.get("profession")
    prof_score = 1.0
    if req_profession and cand_profession:
        prof_score = get_similarity(req_profession, cand_profession)
    elif req_profession and not cand_profession:
        prof_score = 0.0
        
    # 2. Skill Match (30%)
    req_skills = requirements.get("skills", [])
    cand_skills = candidate.get("skills", [])
    
    if req_skills:
        skill_scores = []
        for req_s in req_skills:
            # For each required skill, find the best semantic match in the candidate's skills list
            best_s_score = 0.0
            for cand_s in cand_skills:
                # Exact matches get 1.0
                if req_s.strip().lower() == cand_s.strip().lower():
                    best_s_score = 1.0
                    break
                else:
                    best_s_score = max(best_s_score, get_similarity(req_s, cand_s))
            skill_scores.append(best_s_score)
        skill_score = np.mean(skill_scores) if skill_scores else 0.0
    else:
        skill_score = 1.0 # If no skills are required, default to 1.0
        
    # 3. Experience Match (20%)
    req_exp = requirements.get("minimum_experience_years")
    cand_exp = candidate.get("experience_years")
    exp_score = 1.0
    
    if req_exp is not None:
        if cand_exp is not None:
            if cand_exp >= req_exp:
                exp_score = 1.0
            else:
                # Partial score if they have some experience
                exp_score = max(0.0, float(cand_exp / req_exp) * 0.5)
        else:
            exp_score = 0.3 # Partial penalty for unverified experience

    # 4. Location Match (10%)
    req_loc = requirements.get("location")
    cand_loc = candidate.get("location")
    loc_score = 1.0
    if req_loc and cand_loc:
        loc_score = get_similarity(req_loc, cand_loc)
        # Boost exact or near-exact matches
        if req_loc.lower() in cand_loc.lower() or cand_loc.lower() in req_loc.lower():
            loc_score = 1.0
    elif req_loc and not cand_loc:
        loc_score = 0.0

    # 5. Startup Experience Match (10%)
    req_startup = requirements.get("startup_experience", False)
    cand_evidence = (str(candidate.get("evidence") or "") + " " + str(candidate.get("profession") or "")).lower()
    
    startup_score = 1.0
    if req_startup:
        # Check if startup is mentioned in the evidence, title, or skills
        if "startup" in cand_evidence or "start-up" in cand_evidence or (candidate.get("industry") or "").lower() == "startup":
            startup_score = 1.0
        else:
            startup_score = 0.0

    # 6. Education Match (5%)
    req_edu = requirements.get("education")
    cand_edu = (candidate.get("education", "") or "") + " " + (candidate.get("college", "") or "")
    edu_score = 1.0
    if req_edu and cand_edu.strip():
        edu_score = get_similarity(req_edu, cand_edu)
        if req_edu.lower() in cand_edu.lower():
            edu_score = 1.0
    elif req_edu:
        edu_score = 0.0

    # 7. Industry / Company Match (5%)
    req_company = requirements.get("company_industry")
    cand_comp = str(candidate.get("company") or "") + " " + str(candidate.get("industry") or "")
    comp_score = 1.0
    if req_company and cand_comp.strip():
        comp_score = get_similarity(req_company, cand_comp)
        if req_company.lower() in cand_comp.lower():
            comp_score = 1.0
    elif req_company:
        comp_score = 0.0

    # Calculate final weighted score
    final_score = (
        skill_score * 0.30 +
        exp_score * 0.20 +
        prof_score * 0.20 +
        loc_score * 0.10 +
        startup_score * 0.10 +
        edu_score * 0.05 +
        comp_score * 0.05
    )
    
    # Store individual matches for rendering detailed feedback
    match_breakdown = {
        "skills": skill_score,
        "experience": exp_score,
        "profession": prof_score,
        "location": loc_score,
        "startup": startup_score,
        "education": edu_score,
        "company": comp_score
    }
    
    candidate_scored = candidate.copy()
    candidate_scored["match_score"] = round(final_score * 100)
    candidate_scored["breakdown"] = match_breakdown
    
    return candidate_scored

def filter_and_rank_candidates(candidates: List[Dict[str, Any]], requirements: Dict[str, Any], apply_hard_filters: bool = True) -> List[Dict[str, Any]]:
    """
    Applies hard filters (if enabled) and ranks candidates by score.
    Hard filters:
      - Location must match (if location specified and location filter is strict)
      - Skills must overlap (must have at least one matching skill if requirements specifies skills)
      - Experience must meet the minimum (if experience specified)
    """
    ranked_list = []
    
    for cand in candidates:
        scored_cand = score_candidate(cand, requirements)
        
        # Apply hard filters if requested
        if apply_hard_filters:
            # 1. Experience filter
            req_exp = requirements.get("minimum_experience_years")
            cand_exp = cand.get("experience_years")
            if req_exp is not None and cand_exp is not None and cand_exp < req_exp:
                continue
                
            # 2. Location filter (Check if they are in the same country/city - loose check)
            req_loc = requirements.get("location")
            cand_loc = cand.get("location")
            if req_loc and cand_loc:
                # If similarity is extremely low, skip
                if get_similarity(req_loc, cand_loc) < 0.15 and req_loc.lower() not in cand_loc.lower():
                    continue
            
            # 3. Essential Skill check (Check if at least one skill matches semantically)
            req_skills = requirements.get("skills", [])
            if req_skills:
                # If they have 0 overlapping skills, they are filtered out
                skill_score = scored_cand["breakdown"]["skills"]
                if skill_score < 0.1:  # arbitrary low threshold for 0 match
                    continue
                    
        ranked_list.append(scored_cand)
        
    # Sort descending by match score
    ranked_list.sort(key=lambda x: x["match_score"], reverse=True)
    return ranked_list

if __name__ == "__main__":
    # Test scoring
    reqs = {
        "profession": "ML Engineer",
        "skills": ["Python", "TensorFlow"],
        "minimum_experience_years": 2.0,
        "location": "Bangalore",
        "startup_experience": True
    }
    
    cands = [
        {
            "name": "Rahul Sharma",
            "profession": "Senior Machine Learning Engineer",
            "skills": ["Python", "PyTorch", "TensorFlow", "NLP"],
            "experience_years": 4.0,
            "location": "Bangalore Urban, India",
            "evidence": "Works at a high growth AI startup.",
            "source_url": "http://test.com"
        },
        {
            "name": "Aman Verma",
            "profession": "Software Developer",
            "skills": ["Java", "SQL"],
            "experience_years": 1.0,
            "location": "Delhi, India",
            "evidence": "Works at Infosys.",
            "source_url": "http://test2.com"
        }
    ]
    
    print("Scoring candidates...")
    ranked = filter_and_rank_candidates(cands, reqs, apply_hard_filters=False)
    for r in ranked:
        print(f"Name: {r['name']}, Score: {r['match_score']}%, Breakdown: {r['breakdown']}")
