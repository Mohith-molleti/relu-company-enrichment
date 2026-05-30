# ---------------------------
# Streamlit UI
# ---------------------------

st.set_page_config(
    page_title="AI Company Enrichment Dashboard",
    layout="wide"
)

if "results" not in st.session_state:
    st.session_state.results = stored_results

st.title("AI Company Enrichment Dashboard")

st.markdown("""
Extract company intelligence from websites using AI.

Features:
- Website scraping
- Contact discovery
- AI company profiling
- Pain point analysis
- Outreach generation
""")

col1, col2, col3 = st.columns(3)

with col1:
    st.metric(
        "Total Enrichments",
        len(st.session_state.results)
    )

with col2:
    st.metric(
        "Emails Found",
        sum(
            len(r.get("mail", []))
            for r in st.session_state.results
        )
    )

with col3:
    st.metric(
        "Results Stored",
        len(st.session_state.results)
    )

company_url = st.text_area(
    "Company URLs (One URL Per Line)",
    placeholder="""https://www.zoho.com
https://openai.com
https://www.freshworks.com"""
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

        urls = list(set([
            url.strip()
            for url in company_url.split("\n")
            if url.strip()
        ]))

        with st.spinner(
            "Analyzing companies..."
        ):

            for url in urls:

                try:

                    result = enrich_company(url)

                    st.session_state.results.append(
                        result
                    )

                    company_display = result.get(
                        "company_name",
                        result.get(
                            "website_name",
                            "Company"
                        )
                    )

                    with st.expander(
                        company_display,
                        expanded=True
                    ):

                        st.write(
                            f"**Website:** {result.get('website_name')}"
                        )

                        st.write(
                            f"**Address:** {result.get('address')}"
                        )

                        st.write(
                            f"**Phone:** {result.get('mobile_number')}"
                        )

                        st.write(
                            f"**Emails:** {', '.join(result.get('mail', []))}"
                        )

                        st.write(
                            f"**Core Service:** {result.get('core_service')}"
                        )

                        st.write(
                            f"**Target Customer:** {result.get('target_customer')}"
                        )

                        st.write(
                            f"**Pain Point:** {result.get('probable_pain_point')}"
                        )

                        st.write(
                            f"**Outreach Opener:** {result.get('outreach_opener')}"
                        )

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

        csv = df.to_csv(
            index=False
        )

        st.download_button(
            label="📥 Download Results CSV",
            data=csv,
            file_name="company_results.csv",
            mime="text/csv"
        )

        json_data = json.dumps(
            st.session_state.results,
            indent=2
        )

        st.download_button(
            label="📥 Download Results JSON",
            data=json_data,
            file_name="results.json",
            mime="application/json"
        )

    else:

        st.warning(
            "No results available"
        )

st.markdown("---")

st.caption(
    "Built with Streamlit, BeautifulSoup and Gemini AI"
)
