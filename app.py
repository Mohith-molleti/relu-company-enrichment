import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
import re
import json
from urllib.parse import urljoin
from google import genai

# Gemini Configuration

API_KEY = st.secrets["GEMINI_API_KEY"]

client = genai.Client(api_key=API_KEY)

# Page Text Extraction
def get_page_text(url):

    try:

        headers = {
            "User-Agent": "Mozilla/5.0"
        }

        response = requests.get(
            url,
            headers=headers,
            timeout=10
        )

        soup = BeautifulSoup(
            response.text,
            "html.parser"
        )

        for tag in soup(
            ["script", "style", "noscript"]
        ):
            tag.decompose()

        text = soup.get_text(
            " ",
            strip=True
        )

        text = " ".join(text.split())

        return text[:15000]

    except Exception:

        return ""

# Relevant Page Discovery

def discover_relevant_links(base_url):

    links = []

    try:

        response = requests.get(
            base_url,
            timeout=10
        )

        soup = BeautifulSoup(
            response.text,
            "html.parser"
        )

        keywords = [
            "about",
            "contact",
            "service",
            "services",
            "solution",
            "solutions",
            "company"
        ]

        for a in soup.find_all(
            "a",
            href=True
        ):

            href = a["href"]

            if any(
                keyword in href.lower()
                for keyword in keywords
            ):

                links.append(
                    urljoin(base_url, href)
                )

        return list(set(links))[:5]

    except Exception:

        return []

# Email Extraction

def extract_emails(text):

    emails = re.findall(
        r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}",
        text
    )

    return list(set(emails))

# Phone Extraction

def extract_phone(text):

    phones = re.findall(
        r"(\+\d[\d\s\-]{8,15}\d|\b\d{10}\b)",
        text
    )

    return list(set(phones))

# AI Business Analysis

def analyze_company_with_ai(text):

    prompt = f"""
You are a business analyst.

Return ONLY valid JSON.

Rules:
1. Do NOT invent information.
2. If information is unavailable use "N/A".
3. Return ONLY JSON.
4. Never use markdown.

Format:

{{
"website_name":"",
"company_name":"",
"address":"",
"mobile_number":"",
"mail":[],
"core_service":"",
"target_customer":"",
"probable_pain_point":"",
"outreach_opener":""
}}

Company Information:
{text[:12000]}
"""

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt
    )

    cleaned = response.text.replace(
        "```json",
        ""
    )

    cleaned = cleaned.replace(
        "```",
        ""
    )

    return cleaned.strip()

# Main Enrichment Function
def enrich_company(url):

    homepage_text = get_page_text(url)

    links = discover_relevant_links(url)

    extra_text = ""

    for link in links:

        extra_text += (
            "\n" + get_page_text(link)
        )

    combined_text = (
        homepage_text + "\n" + extra_text
    )

    emails = extract_emails(
        combined_text
    )

    phones = extract_phone(
        combined_text
    )

    if len(combined_text.strip()) < 50:

        return {
            "website_name": "N/A",
            "company_name": "N/A",
            "address": "N/A",
            "mobile_number": "",
            "mail": emails,
            "core_service": "N/A",
            "target_customer": "N/A",
            "probable_pain_point": "N/A",
            "outreach_opener": "N/A"
        }

    ai_output = analyze_company_with_ai(
        combined_text
    )

    try:

        result = json.loads(
            ai_output
        )

    except Exception:

        result = {
            "website_name": "N/A",
            "company_name": "N/A",
            "address": "N/A",
            "mobile_number": "",
            "mail": [],
            "core_service": "N/A",
            "target_customer": "N/A",
            "probable_pain_point": "N/A",
            "outreach_opener": "N/A"
        }

    result["mail"] = emails

    if phones:

        result["mobile_number"] = phones[0]

    return result

# Streamlit UI
st.set_page_config(
    page_title="AI Company Enrichment Dashboard",
    layout="wide"
)

if "results" not in st.session_state:

    st.session_state.results = []

st.title(
    "AI Company Enrichment Dashboard"
)

company_name = st.text_input(
    "Company Name"
)

company_url = st.text_input(
    "Company URL",
    placeholder="https://www.company.com"
)

if st.button("Enrich"):

    if not company_url:

        st.warning(
            "Please enter a company URL"
        )

    else:

        with st.spinner(
            "Analyzing company..."
        ):

            try:

                result = enrich_company(
                    company_url
                )

                if company_name:

                    result["company_name"] = company_name

                st.session_state.results.append(
                    result
                )

                st.success(
                    "Analysis completed"
                )

                st.json(result)

            except Exception as e:

                st.error(str(e))

if st.button("Show All Results"):

    if st.session_state.results:

        df = pd.DataFrame(
            st.session_state.results
        )

        st.dataframe(
            df,
            use_container_width=True
        )

    else:

        st.warning(
            "No results available"
        )
