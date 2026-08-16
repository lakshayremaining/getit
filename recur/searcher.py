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
    """Generates 3-4 targeted search dorks based on recruiter requirements."""
    queries = []
    
    # 1. Primary LinkedIn site query
    skill_str = " ".join([f'"{s}"' for s in skills[:3]])
    loc_str = f'"{location}"' if location else ""
    prof_str = f'"{profession}"' if profession else ""
    startup_str = '"startup"' if startup else ""
    
    # Query 1: LinkedIn focused search
    q1 = f"site:linkedin.com/in/ {prof_str} {skill_str} {loc_str} {startup_str}".strip()
    # Normalize spaces
    q1 = " ".join(q1.split())
    queries.append(q1)
    
    # Query 2: GitHub focused search
    if skills:
        q2 = f"site:github.com/ {loc_str} {skill_str}".strip()
        q2 = " ".join(q2.split())
        queries.append(q2)
        
    # Query 3: Broader portfolio search
    q3 = f"{prof_str} {skill_str} {loc_str} {startup_str} portfolio cv".strip()
    q3 = " ".join(q3.split())
    queries.append(q3)
    
    # Query 4: Alternate LinkedIn search for title variations
    if profession:
        q4 = f"site:linkedin.com/in/ {prof_str} {loc_str}".strip()
        q4 = " ".join(q4.split())
        queries.append(q4)
        
    return list(set(queries))[:3] # Return up to 3 queries to save rate limits

def generate_finder_queries(name: str, company: str = None, college: str = None, profession: str = None) -> List[str]:
    """Generates targeted search dorks to find a specific person."""
    queries = []
    name_escaped = f'"{name}"'
    
    # Query 1: Direct LinkedIn search
    q1_terms = [f"site:linkedin.com/in/", name_escaped]
    if company:
        q1_terms.append(f'"{company}"')
    if profession:
        q1_terms.append(f'"{profession}"')
    queries.append(" ".join(q1_terms))
    
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
