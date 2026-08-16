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
    """Generates broad, high-yield search dorks to ensure search engines return results."""
    queries = []
    
    # Clean inputs
    prof_clean = profession.strip() if profession else ""
    loc_clean = location.strip() if location else ""
    skills_clean = [s.strip() for s in skills if s.strip()]
    
    # 1. Broad site search (No strict quotes) - High Yield
    skills_part = " ".join(skills_clean[:2])
    q1 = f"site:linkedin.com/in/ {prof_clean} {loc_clean} {skills_part}".strip()
    q1 = " ".join(q1.split())
    if q1:
        queries.append(q1)
        
    # 2. General search with 'linkedin' keyword (Catches indexed profiles outside /in/ or general directories)
    skills_all = " ".join(skills_clean[:3])
    startup_part = "startup" if startup else ""
    q2 = f"linkedin {prof_clean} {loc_clean} {skills_all} {startup_part}".strip()
    q2 = " ".join(q2.split())
    if q2:
        queries.append(q2)
        
    # 3. Base role + location search (Guarantees we get candidates, which we can filter later in code)
    if prof_clean or loc_clean:
        q3 = f"site:linkedin.com/in/ {prof_clean} {loc_clean}".strip()
        q3 = " ".join(q3.split())
        queries.append(q3)
        
    # 4. GitHub site search for developers
    if skills_clean:
        q4 = f"site:github.com/ {loc_clean} {skills_clean[0]}".strip()
        q4 = " ".join(q4.split())
        queries.append(q4)
        
    # Return unique list, prioritised
    return list(dict.fromkeys(queries))[:3]

def generate_finder_queries(name: str, company: str = None, college: str = None, profession: str = None) -> List[str]:
    """Generates targeted but flexible queries to find a specific person."""
    queries = []
    name_clean = name.strip()
    
    # Query 1: Direct LinkedIn site search (Name is unquoted for flexibility)
    q1 = f"site:linkedin.com/in/ {name_clean}"
    if company:
        q1 += f" {company.strip()}"
    if profession:
        q1 += f" {profession.strip()}"
    queries.append(q1)
    
    # Query 2: General name + LinkedIn/GitHub keyword search
    q2 = f"{name_clean}"
    if company:
        q2 += f" {company.strip()}"
    if college:
        q2 += f" {college.strip()}"
    q2 += " (linkedin OR github OR portfolio)"
    queries.append(q2)
    
    # Query 3: Minimal name search
    queries.append(f"site:linkedin.com/in/ {name_clean}")
    
    return list(dict.fromkeys(queries))

    
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
