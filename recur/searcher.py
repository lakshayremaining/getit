import os
import requests
from duckduckgo_search import DDGS
from typing import List, Dict

def search_duckduckgo(query: str, max_results: int = 10) -> List[Dict[str, str]]:
    """Performs a free search using DuckDuckGo (no API keys required)."""
    try:
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=max_results))
            return [
                {
                    "title": r.get("title", ""),
                    "url": r.get("href", ""),
                    "snippet": r.get("body", "")
                }
                for r in results
            ]
    except Exception as e:
        print(f"DuckDuckGo search error: {e}")
        return []

def search_tavily(query: str, api_key: str, max_results: int = 10) -> List[Dict[str, str]]:
    """Performs a search using Tavily API (requires API key)."""
    try:
        url = "https://api.tavily.com/search"
        payload = {
            "api_key": api_key,
            "query": query,
            "max_results": max_results,
            "search_depth": "basic"
        }
        response = requests.post(url, json=payload, timeout=10)
        if response.status_code == 200:
            data = response.json()
            return [
                {
                    "title": r.get("title", ""),
                    "url": r.get("url", ""),
                    "snippet": r.get("content", "")
                }
                for r in data.get("results", [])
            ]
        else:
            print(f"Tavily API returned status code {response.status_code}: {response.text}")
    except Exception as e:
        print(f"Tavily search error: {e}")
    return []

def search_brave(query: str, api_key: str, max_results: int = 10) -> List[Dict[str, str]]:
    """Performs a search using Brave Search API (requires API key)."""
    try:
        url = "https://api.search.brave.com/res/v1/web/search"
        headers = {
            "Accept": "application/json",
            "X-Subscription-Token": api_key
        }
        params = {
            "q": query,
            "count": max_results
        }
        response = requests.get(url, headers=headers, params=params, timeout=10)
        if response.status_code == 200:
            data = response.json()
            results = data.get("web", {}).get("results", [])
            return [
                {
                    "title": r.get("title", ""),
                    "url": r.get("url", ""),
                    "snippet": r.get("description", "")
                }
                for r in results
            ]
        else:
            print(f"Brave API returned status code {response.status_code}: {response.text}")
    except Exception as e:
        print(f"Brave search error: {e}")
    return []

def execute_search(query: str, tavily_key: str = None, brave_key: str = None, max_results: int = 10) -> List[Dict[str, str]]:
    """
    Executes search using the best available provider (Tavily > Brave > DuckDuckGo).
    """
    if tavily_key:
        print(f"Executing Tavily search for: '{query}'")
        res = search_tavily(query, tavily_key, max_results)
        if res:
            return res
    if brave_key:
        print(f"Executing Brave search for: '{query}'")
        res = search_brave(query, brave_key, max_results)
        if res:
            return res
            
    print(f"Executing DuckDuckGo fallback search for: '{query}'")
    return search_duckduckgo(query, max_results)

def generate_recruiter_queries(profession: str, skills: List[str], location: str, startup: bool) -> List[str]:
    """
    Generates 5 broad, high-yield queries spanning the entire web:
    LinkedIn profiles, GitHub repositories, about.me directory, online portfolios, and resumes.
    """
    queries = []
    
    prof_clean = profession.strip() if profession else ""
    loc_clean = location.strip() if location else ""
    skills_clean = [s.strip() for s in skills if s.strip()]
    skills_str = " ".join(skills_clean[:2])
    startup_part = "startup" if startup else ""
    
    # Query 1: LinkedIn Public Profiles (Broad)
    q1 = f"site:linkedin.com/in/ {prof_clean} {loc_clean} {skills_str}".strip()
    queries.append(" ".join(q1.split()))
    
    # Query 2: GitHub Profiles/Activity
    if skills_clean:
        q2 = f"site:github.com/ {loc_clean} {skills_clean[0]} {prof_clean}".strip()
        queries.append(" ".join(q2.split()))
        
    # Query 3: Personal Portfolios & Professional Websites (Whole Web)
    q3 = f"{prof_clean} {loc_clean} {skills_str} {startup_part} (portfolio OR \"personal website\")".strip()
    queries.append(" ".join(q3.split()))
    
    # Query 4: Online Resumes / CVs (Whole Web)
    q4 = f"{prof_clean} {loc_clean} {skills_str} (cv OR resume OR bio)".strip()
    queries.append(" ".join(q4.split()))
    
    # Query 5: Directory & alternative networks (about.me, dev.to, medium, etc.)
    q5 = f"(site:about.me OR site:dev.to) {prof_clean} {loc_clean} {skills_str}".strip()
    queries.append(" ".join(q5.split()))
    
    # Remove empty queries and deduplicate
    final_queries = [q for q in queries if q]
    return list(dict.fromkeys(final_queries))[:5]

def generate_finder_queries(name: str, company: str = None, college: str = None, profession: str = None) -> List[str]:
    """Generates comprehensive queries to find a specific person across the entire internet."""
    queries = []
    name_clean = name.strip()
    
    # 1. LinkedIn profile
    q1 = f"site:linkedin.com/in/ {name_clean}"
    if company: q1 += f" {company.strip()}"
    queries.append(q1)
    
    # 2. General web (Portfolios, GitHub, Twitter)
    q2 = f"{name_clean} (site:github.com OR site:twitter.com OR portfolio OR cv)"
    if company: q2 += f" {company.strip()}"
    if college: q2 += f" {college.strip()}"
    queries.append(q2)
    
    # 3. Alternative professional networks (about.me, researchGate, dev.to)
    q3 = f"{name_clean} {profession.strip() if profession else ''} (site:about.me OR site:researchgate.net OR site:dev.to)"
    queries.append(q3)
    
    # 4. Global generic search
    q4 = f"\"{name_clean}\" {company.strip() if company else ''} {profession.strip() if profession else ''}"
    queries.append(q4.strip())
    
    final_queries = [q for q in queries if q]
    return list(dict.fromkeys(final_queries))


    
    # Query 2: Broader web lookup for portfolio/github
    q2_terms = [name_escaped]
    if college:
        q2_terms.append(f'"{college}"')
    if company:
        q2_terms.append(f'"{company}"')
    q2_terms.append("(site:github.com OR site:twitter.com OR portfolio)")
    queries.append(" ".join(q2_terms))
    
    # Query 3: Generic direct name search
    q3_terms = [name_escaped]
    if profession:
        q3_terms.append(f'"{profession}"')
    if company:
        q3_terms.append(f'"{company}"')
    queries.append(" ".join(q3_terms))
    
    return queries

if __name__ == "__main__":
    # Test DDG search
    print("Testing DDG Search...")
    results = search_duckduckgo("site:linkedin.com/in/ \"Rahul Sharma\" Google", 2)
    print(results)
