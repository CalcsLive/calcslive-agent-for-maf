import json

import streamlit as st

from agent_core import CALCSLIVE_API_URL, create_calcslive_article_from_script


st.set_page_config(page_title="CalcsLive Cloud Beta", layout="wide")

st.title("CalcsLive Cloud Beta")
st.caption(
    "Cloud-only beta for creating CalcsLive articles from PQ scripts. "
    "No local Excel bridge required."
)

with st.expander("What runs where?", expanded=False):
    st.markdown(
        "- Browser/UI: Streamlit app hosted in Azure App Service\n"
        "- Cloud API call: CalcsLive article creation endpoint\n"
        "- Not used in this app: local Excel bridge / COM watcher"
    )

default_pqs = [
    {
        "sym": "D",
        "description": "pipe diameter",
        "value": 2,
        "unit": "in",
    },
    {
        "sym": "L",
        "description": "pipe length",
        "value": 10,
        "unit": "ft",
    },
    {
        "sym": "V",
        "description": "pipe volume",
        "expression": "pi * (D/2)^2 * L",
        "unit": "gal",
    },
]

col_left, col_right = st.columns([3, 2])

with col_left:
    pqs_text = st.text_area(
        "PQ script JSON (required)",
        value=json.dumps(default_pqs, indent=2),
        height=360,
    )

with col_right:
    title = st.text_input("Title (optional)", value="Cloud Beta Test Calculation")
    description = st.text_input("Description (optional)", value="Created from cloud beta UI")
    access_level = st.selectbox("Access Level", options=["public", "private"], index=0)
    category = st.text_input("Category (optional)", value="Engineering")
    tags_csv = st.text_input("Tags (comma-separated)", value="beta,cloud,unit-aware")

st.markdown(f"**CalcsLive API base:** `{CALCSLIVE_API_URL}`")

if st.button("Create CalcsLive Article", type="primary"):
    try:
        pqs = json.loads(pqs_text)
        if not isinstance(pqs, list):
            st.error("PQ script must be a JSON array.")
        else:
            tags = [t.strip() for t in tags_csv.split(",") if t.strip()]
            with st.spinner("Creating article in CalcsLive..."):
                result = create_calcslive_article_from_script(
                    pqs=pqs,
                    title=title or None,
                    description=description or None,
                    access_level=access_level or None,
                    category=category or None,
                    tags=tags or None,
                )

            if result.get("success"):
                article = result.get("article", {})
                st.success("Article created successfully.")
                if article.get("url"):
                    st.markdown(f"- URL: {article.get('url')}")
                if article.get("id"):
                    st.markdown(f"- ID: `{article.get('id')}`")
                if article.get("title"):
                    st.markdown(f"- Title: {article.get('title')}")
                st.json(result)
            else:
                st.error(result.get("error", "Create failed"))
                if result.get("details"):
                    st.json(result.get("details"))
    except json.JSONDecodeError as e:
        st.error(f"Invalid JSON: {e}")
