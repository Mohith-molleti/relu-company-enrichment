import streamlit as st
import pandas as pd
import requests
import os
from bs4 import BeautifulSoup
import re
import json
from urllib.parse import urljoin
from google import genai

# ---------------------------
# Gemini Configuration
# ---------------------------

API_KEY = st.secrets["GEMINI_API_KEY"]

client = genai.Client(api_key=API_KEY)

# ---------------------------
# Extract Website Text
# ---------------------------

def get_page_text(url):

    try:

        headers = {
            "User-Agent": "Mozilla/5.0"
        }

        response = requests.get(
            url,
            headers=headers,
            timeout=10,
            allow_redirects=True
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


# ---------------------------
# Discover Important Pages
# ---------------------------

def discover_relevant_links(base_url):

    links = []

    try:

        response = requests.get(
            base_url,
            timeout=10,
            allow_redirects=True
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
            "company",
            "team",
            "products",
            "support",
            "careers"
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


# ---------------------------
# Extract Emails
# ---------------------------

def extract_emails(text):

    emails = re.findall(
        r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}",
        text
    )

    return list(set(emails))


# ---------------------------
# Extract Phones
# ---------------------------

def extract_phone(text):

    phones = re.findall(
        r"(\+\d[\d\s\-]{8,15}\d|\b\d{10}\b)",
        text
    )

    return list(set(phones))


# ---------------------------
# AI Analysis
# ---------------------------

def analyze_company_with_ai(text):

    prompt = f"""
You are a business analyst.

Return ONLY valid JSON.

Rules:
1. Do NOT invent information
2. If information is unavailable use "N/A"
3. Return ONLY JSON

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


# ---------------------------
# Company Enrichment
# ---------------------------

def enrich_company(url):

    homepage_text = get_page_text(url)

    links = discover_relevant_links(url)

    extra_text = ""

    for link in links:
        extra_text += "\n" + get_page_text(link)

    combined_text = homepage_text + "\n" + extra_text

    emails = extract_emails(combined_text)

    phones = extract_phone(combined_text)

    if len(combined_text.strip()) < 50:

        return {
            "website_name": "N/A",
            "company_name": "N/A",
            "address": "N/A",
            "mobile_number": "N/A",
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

        result = json.loads(ai_output)

    except Exception:

        result = {
            "website_name": "N/A",
            "company_name": "N/A",
            "address": "N/A",
            "mobile_number": "N/A",
            "mail": [],
            "core_service": "N/A",
            "target_customer": "N/A",
            "probable_pain_point": "N/A",
            "outreach_opener": "N/A"
        }

    result["mail"] = emails

    if phones:
        result["mobile_number"] = phones[0]
    else:
        result["mobile_number"] = "N/A"

    return result


# ---------------------------
# Load Previous Results
# ---------------------------

if os.path.exists("results.json"):

    try:

        with open(
            "results.json",
            "r",
            encoding="utf-8"
        ) as f:

            stored_results = json.load(f)

    except Exception:

        stored_results = []

else:

    stored_results = []


# ---------------------------
# Streamlit UI
# ---------------------------

st.set_page_config(
    page_title="AI Company Enrichment Dashboard",
    layout="wide"
)

if "results" not in st.session_state:
    st.session_state.results = stored_results

st.title(
    "AI Company Enrichment Dashboard"
)

st.metric(
    "Companies Processed",
    len(st.session_state.results)
)

company_name = st.text_input(
    "Company Name (Optional)"
)

company_url = st.text_area(
    "Company URLs (One URL Per Line)",
    placeholder="""https://www.zoho.com
https://openai.com"""
)

# ---------------------------
# Enrich Button
# ---------------------------

if st.button("Enrich"):

    if not company_url.strip():

        st.warning(
            "Please enter at least one company URL"
        )

    else:

        urls = [
            url.strip()
            for url in company_url.split("\n")
            if url.strip()
        ]

        with st.spinner(
            "Analyzing companies..."
        ):

            for url in urls:

                try:

                    result = enrich_company(url)

                    if company_name:
                        result["company_name"] = company_name

                    st.session_state.results.append(
                        result
                    )

                    st.subheader(
                        result.get(
                            "company_name",
                            "Company"
                        )
                    )

                    st.json(result)

                except Exception as e:

                    st.error(
                        f"Failed for {url}: {e}"
                    )

        with open(
            "results.json",
            "w",
            encoding="utf-8"
        ) as f:

            json.dump(
                st.session_state.results,
                f,
                indent=2,
                ensure_ascii=False
            )

        st.success(
            f"Analysis completed for {len(urls)} company(s)"
        )


# ---------------------------
# Show All Results
# ---------------------------

if st.button("Show All Results"):

    if st.session_state.results:

        st.subheader(
            "Enriched Companies"
        )

        df = pd.DataFrame(
            st.session_state.results
        )

        st.dataframe(
            df,
            use_container_width=True
        )

        json_data = json.dumps(
            st.session_state.results,
            indent=2
        )

        st.download_button(
            label="Download Results JSON",
            data=json_data,
            file_name="results.json",
            mime="application/json"
        )

    else:

        st.warning(
            "No results available"
        )
