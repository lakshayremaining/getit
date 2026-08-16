import os
import sys
import json

def test_database():
    print("[1/4] Testing Database Cache Layer...")
    try:
        from database import set_cached_search, get_cached_search, set_cached_profile, get_cached_profile
        
        # Test Search Cache
        query = "test_sourcing_query_python"
        results = [{"title": "Test Profile", "url": "https://test.com", "snippet": "Snippets"}]
        set_cached_search(query, results)
        retrieved = get_cached_search(query)
        assert retrieved == results, "Search cache mismatch"
        print("      [OK] Search Cache read/write successful.")
        
        # Test Profile Cache
        url = "https://linkedin.com/in/test-person"
        data = {"name": "Test User", "skills": ["Python", "ML"]}
        set_cached_profile(url, data)
        retrieved_prof = get_cached_profile(url)
        assert retrieved_prof == data, "Profile cache mismatch"
        print("      [OK] Profile Cache read/write successful.")
        
        return True
    except Exception as e:
        print(f"      [FAIL] Database Test Failed: {e}")
        return False

def test_queries():
    print("[2/4] Testing Search Query Generator...")
    try:
        from searcher import generate_recruiter_queries, generate_finder_queries
        
        # Sourcing queries
        source_qs = generate_recruiter_queries("ML Engineer", ["Python", "PyTorch"], "Bangalore", True)
        assert len(source_qs) > 0, "No recruiter queries generated"
        assert any("linkedin.com" in q for q in source_qs), "LinkedIn dork missing in sourcing"
        print("      [OK] Sourcing dorks generated successfully.")
        
        # Finder queries
        finder_qs = generate_finder_queries("Rahul Sharma", "Google", "IIT", "Engineer")
        assert len(finder_qs) > 0, "No finder queries generated"
        assert any("Google" in q for q in finder_qs), "Company keyword missing in finder dorks"
        print("      [OK] Finder dorks generated successfully.")
        
        return True
    except Exception as e:
        print(f"      [FAIL] Query Generator Test Failed: {e}")
        return False

def test_ranker():
    print("[3/4] Testing AI Ranking Engine...")
    try:
        from ranker import score_candidate, get_similarity
        
        # Test semantic similarity helper
        sim = get_similarity("Machine Learning Engineer", "ML Engineer")
        assert sim > 0.5, f"Semantic similarity between 'Machine Learning Engineer' and 'ML Engineer' is too low: {sim}"
        print(f"      [OK] Semantic similarity verified (sim = {sim:.2f})")
        
        # Test candidate scoring weights
        reqs = {
            "profession": "Python Dev",
            "skills": ["Python", "Django"],
            "minimum_experience_years": 3.0,
            "location": "Bangalore",
            "startup_experience": True
        }
        candidate = {
            "name": "Alex",
            "profession": "Backend Python Developer",
            "skills": ["Python", "Django", "SQL"],
            "experience_years": 4.0,
            "location": "Bangalore",
            "evidence": "Experienced python developer at tech startup",
            "source_url": "http://example.com"
        }
        scored = score_candidate(candidate, reqs)
        assert scored["match_score"] > 80, f"Match score should be high, got {scored['match_score']}%"
        print(f"      [OK] Candidate scoring verified (score = {scored['match_score']}%)")
        
        return True
    except Exception as e:
        print(f"      [FAIL] Ranking Engine Test Failed: {e}")
        return False

def test_gemini_parser():
    print("[4/4] Checking Gemini API Credentials...")
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("      [WARN] Skipping parser test: GEMINI_API_KEY environment variable is not set.")
        return True
        
    try:
        from parser import parse_user_query
        res = parse_user_query("I need 3 Java developers in Delhi", api_key=api_key)
        assert res.mode == "recruiter", "Failed to parse mode correct"
        assert "Java" in res.recruiter_data.skills, "Failed to parse skills correct"
        print("      [OK] Gemini API integration and parser verified successfully.")
        return True
    except Exception as e:
        print(f"      [FAIL] Gemini Parser Failed: {e}")
        return False

if __name__ == "__main__":
    print("=" * 45)
    print("RUNNING AUTOMATED PIPELINE VERIFICATION")
    print("=" * 45)
    
    db_ok = test_database()
    queries_ok = test_queries()
    ranker_ok = test_ranker()
    gemini_ok = test_gemini_parser()
    
    print("=" * 45)
    if db_ok and queries_ok and ranker_ok and gemini_ok:
        print("[SUCCESS] ALL COMPONENT TESTS PASSED SUCCESSFULLY!")
        sys.exit(0)
    else:
        print("[FAILED] SOME COMPONENT TESTS FAILED. PLEASE REVIEW LOGS.")
        sys.exit(1)
