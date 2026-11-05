import streamlit as st
from pathlib import Path

from wethaq_backend import (
    analyze_project,
    generate_saip_patent_draft,
    build_patent_draft_pdf,
    generate_strategic_recommendations,
)

# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="Wethaq | وثاق",
    page_icon="🔐",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ============================================================
# THEME
# ============================================================

st.markdown(
    """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

html, body, [class*="css"] {
font-family: "Inter", sans-serif;
}

.stApp {
background: #17253b; /* درجة أفتح وأكثر إشراقاً */
color: #f8fafc;
}

.block-container {
max-width: 1180px;
padding: 2rem 2rem 4rem;
}

[data-testid="stHeader"] {
background: transparent;
}

#MainMenu, footer {
visibility: hidden;
}

/* Sidebar */
[data-testid="stSidebar"] {
background: #0d1526;
border-right: 1px solid rgba(255,255,255,.06);
}

[data-testid="stSidebar"] img,
.block-container img {
    filter: drop-shadow(0 0 4px rgba(255,255,255,.65))
            drop-shadow(0 0 10px rgba(80,160,255,.35));
}

/* Brand */
[data-testid="stSidebar"] img {
    filter: drop-shadow(0 0 4px rgba(255,255,255,.65))
            drop-shadow(0 0 10px rgba(80,160,255,.35));
}
.brand-row {
display: flex;
align-items: center;
gap: 14px;
margin-bottom: 22px;
}

.brand-mark {
width: 54px;
height: 54px;
border-radius: 16px;
background: linear-gradient(135deg, #173f73, #2f7757);
display: flex;
align-items: center;
justify-content: center;
color: white;
font-weight: 800;
font-size: 24px;
box-shadow: 0 10px 24px rgba(0,0,0,.4);
}

.brand-title {
color: #f2f5fa;
font-size: 30px;
font-weight: 800;
line-height: 1;
margin: 0;
}

.brand-subtitle {
color: #8a97b0;
font-size: 12px;
margin: 5px 0 0;
}

/* Hero */
.hero-box {
background:
    radial-gradient(circle at 90% 10%, rgba(255,255,255,.10) 0, rgba(255,255,255,0) 30%),
    linear-gradient(135deg, #0d2647 0%, #173f73 55%, #1f5c47 100%);
border-radius: 28px;
padding: 46px 48px;
color: white;
margin: 8px 0 30px;
box-shadow: 0 20px 48px rgba(0,0,0,.35);
overflow: hidden;
}

.hero-small {
color: #a9c5e0;
font-size: 11px;
font-weight: 700;
letter-spacing: 1.8px;
text-transform: uppercase;
margin-bottom: 10px;
}

.hero-title {
color: white;
font-size: 52px;
font-weight: 800;
line-height: 1.08;
margin: 0;
}

.hero-text {
color: rgba(255,255,255,.82);
font-size: 14px;
line-height: 1.7;
max-width: 760px;
margin-top: 15px;
}

/* Section headings */
.section-title {
color: #4f9cf9;
font-size: 27px;
font-weight: 800;
margin-top: 30px;
margin-bottom: 4px;
}

.section-subtitle {
color: #8a97b0;
font-size: 16px;
margin-bottom: 18px;
}

/* Workflow cards */
.steps {
display: grid;
grid-template-columns: repeat(5, 1fr);
gap: 14px;
margin: 0 0 30px;
}

.step-card {
background: #121a2c;
border: 1px solid rgba(255,255,255,.08);
border-radius: 17px;
padding: 18px;
min-height: 125px;
box-shadow: 0 7px 22px rgba(0,0,0,.3);
}

.step-number {
color: #34d399;
font-size: 14px;
font-weight: 800;
letter-spacing: 1px;
}

.step-title {
color: #eef1f7;
font-weight: 750;
font-size: 19px;
margin-top: 9px;
}

.step-text {
color: #97a3ba;
font-size: 13px;
line-height: 1.55;
margin-top: 4px;
}

/* Upload card */
.upload-card {
background: #121a2c;
border: 1px solid rgba(255,255,255,.08);
border-radius: 20px;
padding: 22px;
box-shadow: 0 9px 26px rgba(0,0,0,.3);
}

[data-testid="stFileUploader"] {
border: 1.5px dashed #3a4a66;
border-radius: 15px;
background: #0e1524;
transition: border-color .2s ease, background .2s ease;
}

[data-testid="stFileUploader"]:hover {
border-color: #1f9d6b;
background: #0f1f1a;
}

[data-testid="stFileUploader"] section {
padding: 12px;
background: transparent;
}

.stButton > button {
border-radius: 12px;
min-height: 44px;
font-weight: 700;
border: 0;
background: linear-gradient(135deg, #1f5c47 0%, #173f73 100%);
color: #ffffff;
box-shadow: 0 8px 18px rgba(23,63,115,.35);
}

.stButton > button:hover {
background: linear-gradient(135deg, #257255 0%, #1d4c8a 100%);
color: #ffffff;
}

/* Generic result cards */
.result-card {
background: #121a2c;
border: 1px solid rgba(255,255,255,.08);
border-radius: 18px;
padding: 20px 22px;
margin: 10px 0;
box-shadow: 0 7px 22px rgba(0,0,0,.28);
}

.result-card-title {
color: #34d399;
font-size: 14px;
font-weight: 750;
margin-bottom: 8px;
}

.muted {
color: #99a5bd;
font-size: 14px;
line-height: 1.65;
}

/* Metric */
.metric-card {
background: linear-gradient(135deg, rgba(23,63,115,.25), rgba(47,119,87,.25));
border: 1px solid rgba(47,119,87,.25);
border-radius: 18px;
padding: 20px;
text-align: center;
margin: 10px 0;
}

.metric-label {
color: #34d399;
font-size: 10px;
font-weight: 800;
letter-spacing: 1.1px;
text-transform: uppercase;
}

.metric-value {
color: #34d399;
font-size: 38px;
font-weight: 800;
margin-top: 5px;
}

/* Native st.metric widget */
[data-testid="stMetricValue"] {
color: #2f7757 !important;
}

[data-testid="stMetricLabel"] {
color: #93a1b8 !important;
}

/* Progress bar */
[data-testid="stProgress"] > div > div {
background: linear-gradient(90deg, #2563eb, #16c78a) !important;
}

/* Pills */
.pill {
display: inline-block;
background: rgba(34,211,238,.12);
color: #67e8f9;
border-radius: 999px;
padding: 5px 9px;
margin: 3px 4px 3px 0;
font-size: 10px;
font-weight: 650;
}

/* IP */
.ip-box {
background: rgba(47,119,87,.12);
border: 1px solid rgba(47,119,87,.35);
border-left: 5px solid #2f7757;
padding: 18px 20px;
border-radius: 14px;
margin: 10px 0;
color: #dbe9e0;
}
/* Radio buttons */
[data-testid="stRadio"] label {
    color: #dbe7f5 !important;
}

[data-testid="stRadio"] p {
    color: #dbe7f5 !important;
}

[data-testid="stRadio"] div[role="radiogroup"] {
    color: #dbe7f5 !important;
}
/* Links */
a {
color: #34d399 !important;
font-weight: 600;
text-decoration: none !important;
}

/* Footer */
.footer {
text-align: center;
color: #6d7a92;
font-size: 11px;
margin-top: 48px;
}

@media (max-width: 800px) {
.steps {
    grid-template-columns: repeat(2, 1fr);
}
.hero-box {
    padding: 34px 28px;
}
.hero-title {
    font-size: 34px;
}
}

@media (max-width: 520px) {
.steps {
    grid-template-columns: 1fr;
}
.block-container {
    padding-left: 1rem;
    padding-right: 1rem;
}
}
</style>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# BRAND HEADER
# ============================================================

logo_path = Path(__file__).parent / "122.png"

if "wethaq_page" not in st.session_state:
    st.session_state["wethaq_page"] = "home"

with st.sidebar:
    if logo_path.exists():
        st.image(str(logo_path), width=125)
    st.markdown(
        "<div style='font-weight:800;font-size:15px;color:#f2f5fa;margin:8px 0 20px;'>Navigation Menu</div>",
        unsafe_allow_html=True,
    )

    if st.button("🏠  Home", use_container_width=True):
        st.session_state["wethaq_page"] = "home"

    if st.button("🔒  Data Privacy", use_container_width=True):
        st.session_state["wethaq_page"] = "privacy"

    if st.button("📊  Project Analysis", use_container_width=True):
        st.session_state["wethaq_page"] = "analyze"

    if st.button("🧭  Strategic Recommendations", use_container_width=True):
        st.session_state["wethaq_page"] = "recommendations"

    if st.button("📄  IP Readiness", use_container_width=True):
        st.session_state["wethaq_page"] = "settings"

page = st.session_state.get("wethaq_page", "home")

brand_left, brand_right = st.columns([5, 1])

with brand_left:
    if logo_path.exists():
        st.image(str(logo_path), width=130)
    st.markdown(
        """
<div class="brand-row">
    <div>
        <div class="brand-title">Wethaq | وثاق</div>
        <div class="brand-subtitle">Research originality & IP-readiness</div>
    </div>
</div>
        """,
        unsafe_allow_html=True,
    )

with brand_right:
    st.write("")

# ============================================================
# HERO
# ============================================================
if page == "home":
    
    st.markdown(
        """
    <div class="hero-box">
    <div class="hero-small">
        AI-POWERED RESEARCH & IP ASSISTANT
    </div>
    
    <div class="hero-title">
        From Research to Innovation Readiness 
    </div>
    
    <div class="hero-text">
        Upload your project and let Wethaq analyze similarity,
        uncover related research and patents, identify innovation gaps,
        provide AI-powered recommendations, and generate an initial
        intellectual property draft.
    </div>
    </div>
        """,
        unsafe_allow_html=True,
    )
    
    # ============================================================
    # HOW WETHAQ WORKS
    # ============================================================
    
    st.markdown(
        '<div class="section-title">From Analysis to Action</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<div class="section-subtitle">A guided workflow that analyzes your project, provides actionable recommendations, and helps you move toward intellectual property readiness.</div>',
        unsafe_allow_html=True,
    )
    
    st.markdown(
        """
    <div class="steps">
    <div class="step-card">
        <div class="step-number">01</div>
        <div class="step-title">Upload</div>
        <div class="step-text">Upload your project PDF.</div>
    </div>

    <div class="step-card">
        <div class="step-number">02</div>
        <div class="step-title">Discover</div>
        <div class="step-text">Discover similar research and relevant patents.</div>
    </div>

    <div class="step-card">
        <div class="step-number">03</div>
        <div class="step-title">Analyze</div>
        <div class="step-text">Analyze similarity and identify potential innovation gaps.</div>
    </div>

    <div class="step-card">
        <div class="step-number">04</div>
        <div class="step-title">Recommend</div>
        <div class="step-text">Get AI-powered recommendations to improve and strengthen your project.</div>
    </div>

    <div class="step-card">
        <div class="step-number">05</div>
        <div class="step-title">Protect</div>
        <div class="step-text">Generate an AI-assisted intellectual property draft.</div>
    </div>
    </div>
        """,
        unsafe_allow_html=True,
    )
    
# ============================================================
# DATA PRIVACY PAGE
# ============================================================
elif page == "privacy":

    st.markdown(
        '<div class="section-title">Data Privacy & Intellectual Property Assurance</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<div class="section-subtitle">Our strict commitment to protecting your research and intellectual property.</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <div class="result-card" style="border-left: 5px solid #34d399; padding: 30px;">
            <div class="result-card-title" style="color: #34d399; font-size: 18px; margin-bottom: 15px;">🔒 Security & Confidentiality Guarantee</div>
            <div class="muted" style="font-size: 14px; line-height: 1.8;">
                At Wethaq, we strictly prioritize the security and confidentiality of your intellectual property:
                <ul style="margin: 12px 0 0 20px; padding: 0; line-height: 1.8;">
                    <li><b>No Storage or Plagiarism:</b> Wethaq does not store, archive, or claim ownership of your uploaded research papers. Your work remains entirely yours.</li>
                    <li><b>Analysis Purpose Only:</b> Uploaded files are processed dynamically solely for the purpose of checking similarity, finding gaps, and assessing IP readiness.</li>
                    <li><b>Absolute Confidentiality:</b> We ensure that your proprietary ideas and data are never exposed, shared, or leaked to external parties.</li>
                </ul>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    
# ============================================================
# UPLOAD
# ============================================================
elif page == "analyze":

    st.markdown(
        '<div class="section-title">Analyze your project</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<div class="section-subtitle">Upload a research proposal or project PDF to begin.</div>',
        unsafe_allow_html=True,
    )
    
    st.markdown('<div class="upload-card">', unsafe_allow_html=True)
    
    uploaded_file = st.file_uploader(
        "Project PDF",
        type=["pdf"],
        label_visibility="collapsed",
    )
    
    if uploaded_file:
        st.success(f"Ready to analyze: {uploaded_file.name}")
    
    st.markdown("</div>", unsafe_allow_html=True)
    
    analyze = st.button(
        "Analyze Project",
        type="primary",
        use_container_width=True,
    )
    
    # ============================================================
    # ANALYZE
    # ============================================================
    
    if analyze:
    
        if uploaded_file is None:
    
            st.warning(
                "Please upload a PDF first."
            )
    
        else:
    
            with st.spinner(
                "Analyzing your project..."
            ):
    
                try:
    
                    result = analyze_project(
                        uploaded_file
                    )
    
                    st.session_state[
                        "wethaq_result"
                    ] = result
    
                    st.session_state[
                        "wethaq_file_name"
                    ] = uploaded_file.name
    
                except Exception as error:
    
                    st.error(
                        "Something went wrong while analyzing the PDF."
                    )
    
                    st.exception(error)
    
    
    # ============================================================
    # RESULTS
    # ============================================================
    
    result = st.session_state.get(
        "wethaq_result"
    )
    
    
    if result:
    
        research_info = result.get(
            "research_info",
            {},
        ) or {}
    
        similar_research = result.get(
            "similar_research",
            [],
        ) or []
    
        patent_sources = result.get(
            "patent_sources",
            [],
        ) or []
    
        comparison = result.get(
            "comparison",
            {},
        ) or {}
    
        ip_readiness = result.get(
            "ip_readiness",
            {},
        ) or {}
    
        references = result.get(
            "references",
            [],
        ) or []
    
    
        # ========================================================
        # RESULTS HEADER
        # ========================================================
    
        st.divider()
    
        st.markdown(
            '<div class="section-title">Analysis Results</div>',
            unsafe_allow_html=True,
        )
    
        st.markdown(
            '<div class="section-subtitle">Key findings from your uploaded project.</div>',
            unsafe_allow_html=True,
        )
    
        st.caption(
            "File: "
            + st.session_state.get(
                "wethaq_file_name",
                "Project PDF",
            )
        )
    
    
# ========================================================
# PROJECT OVERVIEW
# ========================================================
    
        st.markdown(
            '<div class="section-title">Project Overview</div>',
            unsafe_allow_html=True,
        )
    
        title = research_info.get(
            "Title"
        )
    
        keywords = research_info.get(
            "Keywords"
        )
    
        problem = research_info.get(
            "Research Problem"
        )
    
        objectives = research_info.get(
            "Objectives"
        )
    
        methodology = research_info.get(
            "Methodology"
        )
    
    
        if title:
    
            st.markdown(
                '<div class="result-card"><div class="result-card-title">Project Title</div>'
                + f'<div class="muted" style="font-size:15px;color:#dbe7f5">{title}</div></div>',
                unsafe_allow_html=True,
            )
    
    
        if keywords:

            if isinstance(keywords, list):
                keywords_text = ", ".join(str(x) for x in keywords)
            else:
                keywords_text = keywords

            st.markdown(
                f'<div class="result-card"><div class="result-card-title">Keywords</div>'
                f'<div class="muted">{keywords_text}</div></div>',
                unsafe_allow_html=True,
            )
    
    
        overview_left, overview_right = st.columns(2)
    
    
        with overview_left:
    
            if problem:
    
                st.markdown(
                    f'<div class="result-card"><div class="result-card-title">Research Problem</div>'
                    f'<div class="muted">{problem}</div></div>',
                    unsafe_allow_html=True,
                )
    
    
            if objectives:
    
                st.markdown(
                    f'<div class="result-card"><div class="result-card-title">Objectives</div>'
                    f'<div class="muted">{objectives}</div></div>',
                    unsafe_allow_html=True,
                )
    
    
        with overview_right:
    
            if methodology:
    
                st.markdown(
                    f'<div class="result-card"><div class="result-card-title">Methodology</div>'
                    f'<div class="muted">{methodology}</div></div>',
                    unsafe_allow_html=True,
                )
    
    
            st.markdown(
                f"""
                <div class="metric-card">
                    <div class="metric-label">References Extracted</div>
                    <div class="metric-value">{len(references)}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
    
    
        # ========================================================
        # SIMILAR RESEARCH
        # ========================================================
    
        st.markdown(
            '<div class="section-title">Similar Research</div>',
            unsafe_allow_html=True,
        )
    
        st.markdown(
            '<div class="section-subtitle">Related research identified during the search process.</div>',
            unsafe_allow_html=True,
        )
    
    
        if similar_research:
    
            for index, item in enumerate(
                similar_research,
                start=1,
            ):
    
                if isinstance(
                    item,
                    dict,
                ):
    
                    title = (
                        item.get("title")
                        or item.get("name")
                        or item.get("label")
                        or "Related research"
                    )
    
                    url = (
                        item.get("link")
                        or item.get("url")
                    )
    
                    description = (
                        item.get("description")
                        or item.get("summary")
                        or item.get("abstract")
                    )
    
                    with st.container(
                        border=True,
                    ):
    
                        st.markdown(
                            f"**{index}. {title}**"
                        )
    
                        if url:
    
                            st.markdown(
                                f"[Open source ↗]({url})"
                            )
    
                else:

                    text = str(item).strip()

                    with st.container(border=True):

                        st.markdown(f"**{index}.**")

                        if len(text) > 400:
                            text = text[:400].rstrip() + "…"

                        st.write(text)

        else:

            st.info(
                "No similar research was returned."
            )
    
    
        # ========================================================
        # PATENTS
        # ========================================================
    
        st.markdown(
            '<div class="section-title">Patent Search</div>',
            unsafe_allow_html=True,
        )
    
        st.markdown(
            '<div class="section-subtitle">Search entry points related to the project topic.</div>',
            unsafe_allow_html=True,
        )
    
        if isinstance(patent_sources, dict):
            patent_items = [
                ("Google Patents", patent_sources.get("google_patents")),
                ("WIPO PATENTSCOPE", patent_sources.get("wipo_patentscope")),
            ]
            patent_items = [(name, url) for name, url in patent_items if url]
    
            if patent_items:
                patent_left, patent_right = st.columns(2)
                for column, (name, url) in zip(
                    [patent_left, patent_right],
                    patent_items
                ):
                    with column:
                        st.markdown(
                            f"""
                    <div class="result-card">
                        <div class="result-card-title">{name}</div>
                        <div class="muted">Open the external patent search for further validation.</div>
                    </div>
                            """,
                            unsafe_allow_html=True,
                        )
                        st.link_button("Open search ↗", url, use_container_width=True)
            else:
                st.info("No patent search sources were returned.")
        elif patent_sources:
            for item in patent_sources:
                if isinstance(item, dict):
                    title = (
                        item.get("title")
                        or item.get("name")
                        or "Patent resource"
                    )
                    url = item.get("url") or item.get("link")
                    st.markdown(
                        f"""
                <div class="result-card">
                    <div class="result-card-title">{title}</div>
                </div>
                        """,
                        unsafe_allow_html=True,
                    )
                    if url:
                        st.link_button("Open patent search ↗", url)
                else:
                    st.write(f"• {item}")
        else:
            st.info("No patent sources were returned.")
    
    # ========================================================
    # COMPARISON
    # ========================================================
    
        st.markdown(
            '<div class="section-title">Comparison & Innovation Gap</div>',
            unsafe_allow_html=True,
        )
    
        st.markdown(
            '<div class="section-subtitle">Similarity reflects similarity with retrieved works; it does not prove plagiarism, novelty, or patentability.</div>',
            unsafe_allow_html=True,
        )
    
    
        similarity = (
            comparison.get(
                "average_similarity"
            )
            or comparison.get(
                "Average Similarity"
            )
            or comparison.get(
                "average"
            )
        )
    
    
        if similarity is not None:
    
            try:
    
                similarity_value = float(
                    similarity
                )
    
                st.markdown(
                    f"""
            <div class="metric-card">
                <div class="metric-label">Similarity Score</div>
                <div class="metric-value">{similarity_value:.1f}%</div>
            </div>
                    """,
                    unsafe_allow_html=True,
                )
    
            except Exception:
    
                st.metric(
                    "Similarity Score",
                    str(similarity),
                )
    
    
        comparison_results = comparison.get("results", []) or []

        top_result = (
            max(comparison_results, key=lambda r: r.get("similarity", 0))
            if comparison_results
            else None
        )

        similarities = top_result.get("common_words") if top_result else None
        differences = top_result.get("unique_words") if top_result else None
        innovation_gap = top_result.get("innovation_gap") if top_result else None
    
    
        compare_left, compare_right = st.columns(2)
    
    
        with compare_left:
    
            st.markdown(
                "### Similarities"
            )
    
            if similarities:
    
                if isinstance(
                    similarities,
                    list,
                ):
    
                    for item in similarities:
    
                        st.write(
                            f"• {item}"
                        )
    
                else:
    
                    st.write(
                        similarities
                    )
    
            else:
    
                st.caption(
                    "No similarity details available."
                )
    
    
        with compare_right:
    
            st.markdown(
                "### Differences"
            )
    
            if differences:
    
                if isinstance(
                    differences,
                    list,
                ):
    
                    for item in differences:
    
                        st.write(
                            f"• {item}"
                        )
    
                else:
    
                    st.write(
                        differences
                    )
    
            else:
    
                st.caption(
                    "No difference details available."
                )
    
    
        if innovation_gap:

            st.markdown(
                "### Potential Innovation Gap"
            )

            st.success(
                innovation_gap
            )

elif page == "recommendations":

    st.markdown(
        '<div class="section-title">Strategic Recommendations</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div class="section-subtitle">AI-generated guidance on how to strengthen your project\'s originality based on your comparison results.</div>',
        unsafe_allow_html=True,
    )

    result = st.session_state.get("wethaq_result")

    if not result:
        st.info("Please analyze a project first from the 'Project Analysis' page.")
    else:
        research_info = result.get("research_info", {}) or {}
        comparison = result.get("comparison", {}) or {}

        comparison_results = comparison.get("results", []) or []

        top_result = (
            max(comparison_results, key=lambda r: r.get("similarity", 0))
            if comparison_results
            else None
        )

        if not top_result:
            st.info("No comparison data was found for this project yet. Analyze a project with similar research results first.")
        else:
            generate_recs = st.button(
                "🧭 Generate Strategic Recommendations",
                type="primary",
                use_container_width=True,
            )

            if generate_recs:

                with st.spinner("Analyzing comparison data and generating recommendations..."):

                    try:

                        recommendations = generate_strategic_recommendations(
                            research_info,
                            top_result,
                        )

                        st.session_state["wethaq_recommendations"] = recommendations

                    except Exception as e:

                        error_text = str(e)

                        if "429" in error_text or "quota" in error_text.lower():
                            st.error(
                                "⏳ Daily AI generation limit reached for this project. "
                                "Please try again later (the free-tier quota resets every 24 hours)."
                            )
                        else:
                            st.error("Could not generate recommendations.")
                            st.exception(e)

            recommendations = st.session_state.get("wethaq_recommendations")

            if recommendations:

                st.markdown(
                    f'<div class="result-card"><div class="result-card-title">Where to Shift Focus</div>'
                    f'<div class="muted">{recommendations.get("focus_shift", "")}</div></div>',
                    unsafe_allow_html=True,
                )

                st.markdown(
                    f'<div class="result-card"><div class="result-card-title">Unexplored Research Angles</div>'
                    f'<div class="muted">{recommendations.get("unexplored_angles", "").replace(chr(10), "<br>")}</div></div>',
                    unsafe_allow_html=True,
                )

                st.markdown(
                    f'<div class="result-card"><div class="result-card-title">How to Differentiate Your Project</div>'
                    f'<div class="muted">{recommendations.get("differentiation_tips", "").replace(chr(10), "<br>")}</div></div>',
                    unsafe_allow_html=True,
                )
                
# ========================================================
# IP READINESS & SAIP AI AGENT
# ========================================================

elif page == "settings":

    st.markdown(
        '<div class="section-title">AI Patent & IP Readiness Assistant</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div class="section-subtitle">Generate official digital filing drafts for the Saudi Authority for Intellectual Property (SAIP).</div>',
        unsafe_allow_html=True,
    )

    result = st.session_state.get("wethaq_result")

    if not result:
        st.info("Please analyze a project first from the 'Project Analysis' page.")
    else:
        research_info = result.get("research_info", {}) or {}
        
        project_title = research_info.get("Title") or "Your Project Title"
        project_abstract = research_info.get("Abstract") or "Not specified"
        project_methodology = research_info.get("Methodology") or "Not specified"
        project_field = research_info.get("Keywords") or "Computer Science & Information Technology"

        st.markdown(
            """
            <div class="result-card" style="border-left: 5px solid #34d399; padding: 20px;">
                <div class="result-card-title" style="color: #34d399; font-size: 16px;">SAIP Digital Filing Workflow</div>
                <div class="muted" style="font-size: 13px; line-height: 1.6;">
                    The Saudi Authority for Intellectual Property (SAIP) utilizes a fully digital interactive e-services portal. 
                    No physical or paper forms are required. You can generate your automated patent specification draft below and submit it directly via the 
                    <a href="https://eservices.saip.gov.sa/" target="_blank">SAIP e-services portal</a> using National Unified Access.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        generate_ai_draft = st.button(
            "Generate AI SAIP Patent Draft 🤖",
            type="primary",
            use_container_width=True,
        )

        if generate_ai_draft:
            with st.spinner("AI Agent is drafting your patent application components for SAIP..."):
                try:
                    draft = generate_saip_patent_draft(research_info)
                    st.session_state["saip_ai_draft"] = draft
                except Exception as e:
                    error_text = str(e)

                    if "429" in error_text or "quota" in error_text.lower():
                        st.error(
                            "⏳ Daily AI generation limit reached for this project. "
                            "Please try again later (the free-tier quota resets every 24 hours)."
                        )
                        st.exception(e)
                        
                    else:
                        st.error("Could not generate AI draft. Please ensure your Gemini API key is configured correctly in Streamlit Secrets.")
                        st.exception(e)

        ai_draft = st.session_state.get("saip_ai_draft")

        if ai_draft:

            st.markdown(
                '<div class="section-title" style="font-size:18px;margin-top:25px;">📄 AI-Generated SAIP Patent Specification Draft</div>',
                unsafe_allow_html=True,
            )

            st.markdown(
                f'<div class="result-card"><div class="result-card-title">Invention Title</div>'
                f'<div class="muted"><b>EN:</b> {ai_draft.get("title_en", "")}<br>'
                f'<b>AR:</b> {ai_draft.get("title_ar", "")}</div></div>',
                unsafe_allow_html=True,
            )

            st.markdown(
                f'<div class="result-card"><div class="result-card-title">Abstract</div>'
                f'<div class="muted">{ai_draft.get("abstract", "")}</div></div>',
                unsafe_allow_html=True,
            )

            with st.expander("Description"):
                st.write(ai_draft.get("description", ""))

            with st.expander("Claims"):
                st.write(ai_draft.get("claims", ""))

            pdf_buffer = build_patent_draft_pdf(ai_draft)

            st.download_button(
                label="📥 Download Draft as PDF",
                data=pdf_buffer,
                file_name="wethaq_saip_patent_draft.pdf",
                mime="application/pdf",
                use_container_width=True,
            )

# ============================================================
# FOOTER
# ============================================================

st.divider()

st.caption(
    "Wethaq 2026 — نحو ابتكارات موثقة"
)
