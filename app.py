import streamlit as st
import pandas as pd
import json

st.set_page_config(page_title="Company Enrichment", layout="wide")

if "results" not in st.session_state:
    st.session_state.results = []

st.title("AI Company Enrichment Dashboard")

company_name = st.text_input("Company Name")
company_url = st.text_input("Company URL")

if st.button("Enrich"):

    with st.spinner("Enriching company..."):

        result = {
            "website_name": company_name,
            "company_name": company_name,
            "address": "N/A",
            "mobile_number": "",
            "mail": [],
            "core_service": "Demo Service",
            "target_customer": "Demo Customer",
            "probable_pain_point": "Demo Pain Point",
            "outreach_opener": "Demo Outreach"
        }

        st.session_state.results.append(result)

        st.success("Company enriched successfully")

        st.json(result)

if st.button("Show All Results"):

    if st.session_state.results:

        df = pd.DataFrame(st.session_state.results)

        st.dataframe(df, use_container_width=True)

    else:

        st.warning("No results found")
