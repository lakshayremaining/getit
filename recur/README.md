# AI Professional Discovery & Candidate Ranking System

A Streamlit-based web application that parses natural-language recruitment requirements, queries public search repositories, extracts and normalizes candidate information, performs local semantic candidate matching/ranking, and displays results in a premium interactive dashboard.

It also features a **Quick People Finder** mode to lookup a specific individual by name and aggregate their public social footprint in one place.

---

## Features
1.  **🔍 Recruiter Mode (Talent Sourcing):** Enter requirements in plain English (e.g. *"I need 5 Python devs in Bangalore with 3+ years experience"*), parses parameters, searches public databases, ranks candidates using semantic AI, and shows evidence.
2.  **👤 Quick People Finder Mode:** Lookup a friend or new acquaintance by name, company, or college to aggregate their public LinkedIn, GitHub, Twitter, and portfolio profiles.
3.  **✉️ Outreach Email Generator:** Uses Gemini to draft highly personalized recruitment pitches for each candidate based on their exact profile matches.
4.  **⚡ SQLite Caching:** Caches search queries and extracted profiles to optimize API quota usage.
5.  **🛟 Demo Mode:** Fully functional mock database mode that allows testing the app's features and UI immediately without providing any API keys.

---

## Local Setup & Run

### 1. Prerequisites
Make sure you have Python 3.10+ installed on your computer.

### 2. Install Dependencies
Open a command prompt in this directory (`recur/`) and run:
```bash
pip install -r requirements.txt
```

### 3. Run Pipeline Tests
Verify that all core components are configured and working:
```bash
python verify.py
```

### 4. Start Web Application
Run the Streamlit app locally:
```bash
streamlit run app.py
```
This will automatically launch the app in your default web browser (usually at `http://localhost:8501`).

---

## API Keys Configurations
To run the live search and parsing, you need to configure the following environment variables or input them directly into the sidebar of the web app:

*   `GEMINI_API_KEY`: Obtain a 100% free Gemini API key from [Google AI Studio](https://aistudio.google.com/).
*   `TAVILY_API_KEY` (Optional): Create a free search key at [Tavily AI](https://tavily.com/).
*   `BRAVE_API_KEY` (Optional): Create a free search key at [Brave Search API](https://api.search.brave.com/).

*If Tavily and Brave keys are omitted, the app will automatically fall back to **DuckDuckGo Search**, which is free, unlimited, and keyless.*

---

## Hosting on Hugging Face Spaces

This app is pre-configured to be hosted on **Hugging Face Spaces** for free:

1.  Create a free account on [Hugging Face](https://huggingface.co/).
2.  Click **New Space** and select **Streamlit** as the SDK.
3.  Upload the files in this directory:
    *   `app.py`
    *   `parser.py`
    *   `searcher.py`
    *   `extractor.py`
    *   `ranker.py`
    *   `database.py`
    *   `requirements.txt`
4.  Go to **Settings** in your Space, scroll to **Variables and Secrets**, and add your secrets (e.g. `GEMINI_API_KEY`).
5.  Hugging Face will build and launch your application instantly!
