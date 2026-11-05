# ==========================================
# WETHAQ BACKEND
# ==========================================

import re
import urllib.parse
import requests
import pdfplumber
from difflib import SequenceMatcher
import streamlit as st
from openai import OpenAI

_openai_api_key = st.secrets.get("OPENAI_API_KEY")



openai_client = OpenAI(api_key=_openai_api_key) if _openai_api_key else None
# ==========================================
# 01 — PDF Text Extraction
# ==========================================

def extract_text_from_any_pdf(uploaded_file):
    """
    Extracts and returns the full text from all pages
    of an uploaded PDF file using pdfplumber.
    """

    full_text = ""

    with pdfplumber.open(uploaded_file) as pdf:

        for page_num, page in enumerate(pdf.pages):

            extracted = page.extract_text()

            if extracted:
                full_text += (
                    f"\n--- Page {page_num + 1} ---\n"
                    + extracted
                )

    return full_text


# ==========================================
# 02 — Research Information Extraction
# ==========================================

def extract_research_info(full_text):
    """
    Extract research information from PDFs with flexible section headings.
    Handles titles split across lines and numbered section headings.
    """

    sections = {
        "Title": "",
        "Abstract": "",
        "Research Problem": "",
        "Objectives": "",
        "Methodology": "",
        "Keywords": "",
        "References": ""
    }

    lines = [
        re.sub(r"\s+", " ", line).strip()
        for line in full_text.splitlines()
        if line.strip()
    ]

    lines = [
        line for line in lines
        if not re.match(r"^--- Page \d+ ---$", line, re.IGNORECASE)
    ]

    def heading_text(line):
        return re.sub(
            r"^\s*\d+(?:\.\d+)*[\.\):\-]?\s*",
            "",
            line
        ).strip().lower()

    def is_heading(line, keywords):
        h = heading_text(line)
        for keyword in keywords:
            k = keyword.lower()
            if h == k or h.startswith(k + " ") or h.startswith(k + ":"):
                return True
        return False

    # --------------------------------------------------
    # TITLE
    # --------------------------------------------------
    section_start = len(lines)

    major_groups = [
        ["abstract"],
        ["introduction"],
        ["background"],
        ["objectives", "research objectives", "aim", "aims"],
        ["methodology", "methods", "materials and methods"],
    ]

    for i, line in enumerate(lines[:40]):
        if any(is_heading(line, group) for group in major_groups):
            section_start = i
            break

    title_candidates = lines[:section_start]

    ignored_title_markers = [
        "open access", "review began", "review ended", "published",
        "copyright", "doi", "license", "creativecommons",
        "corresponding author", "email", "university", "college",
        "school", "faculty", "department", "student", "grade "
    ]

    title_parts = []

    for idx, line in enumerate(title_candidates):
        lower = line.lower()

        if "@" in line or lower.startswith("http"):
            continue

        if any(marker in lower for marker in ignored_title_markers):
            if title_parts:
                break
            continue

        # If the following lines clearly look like author/institution
        # metadata, stop before the author line. This keeps multi-line
        # titles such as:
        #   Fabrication ... Enhance
        #   Photovoltaic Performance
        # while excluding the author's name.
        # Stop immediately before an author/institution line.
        # We only inspect the NEXT line here: checking two lines ahead
        # incorrectly removed the second line of a multi-line title when
        # the author was followed by a university/school line.
        next_line = title_candidates[idx + 1].lower() if idx + 1 < len(title_candidates) else ""
        if title_parts and any(
            marker in next_line
            for marker in ["university", "college", "school", "faculty", "grade ", "department"]
        ) and len(line.split()) <= 6:
            break

        if len(line) < 8:
            continue

        title_parts.append(line)

        if len(title_parts) >= 4:
            break

    def join_title_lines(parts):
        result = ""
        for line in parts:
            if not result:
                result = line
            elif result.rstrip().endswith("-"):
                result = result.rstrip()[:-1] + line
            else:
                result += " " + line
        return re.sub(r"\s+", " ", result).strip()

    sections["Title"] = join_title_lines(title_parts)

    # --------------------------------------------------
    # GENERIC SECTION EXTRACTOR
    # --------------------------------------------------
    def get_section(start_keywords, end_groups):
        start_index = -1
        first_content = ""

        for i, line in enumerate(lines):
            if is_heading(line, start_keywords):
                start_index = i
                if ":" in line:
                    first_content = line.split(":", 1)[1].strip()
                break

        if start_index == -1:
            return ""

        content_lines = []
        if first_content:
            content_lines.append(first_content)

        for i in range(start_index + 1, len(lines)):
            if any(is_heading(lines[i], group) for group in end_groups):
                break
            content_lines.append(lines[i])

        return " ".join(content_lines).strip()

    # --------------------------------------------------
    # ABSTRACT
    # --------------------------------------------------
    sections["Abstract"] = get_section(
        ["abstract"],
        [
            ["keywords", "key words"],
            ["introduction"],
            ["background"],
            ["objectives", "research objectives", "aim", "aims"],
        ]
    )

    # --------------------------------------------------
    # KEYWORDS
    # --------------------------------------------------
    keyword_match = re.search(
        r"(?:keywords|key words)\s*[:\-]?\s*(.*?)(?=\n\s*(?:"
        r"\d+(?:\.\d+)*[\.\):\-]?\s*)?"
        r"(?:introduction|background|objectives|aim|aims|"
        r"methodology|methods|materials and methods)\b|$)",
        full_text,
        re.IGNORECASE | re.DOTALL
    )

    if keyword_match:
        sections["Keywords"] = " ".join(
            keyword_match.group(1).split()
        )

    # --------------------------------------------------
    # RESEARCH PROBLEM
    # --------------------------------------------------
    sections["Research Problem"] = get_section(
        ["research problem", "problem statement"],
        [
            ["objectives", "research objectives", "aim", "aims"],
            ["methodology", "methods", "materials and methods"],
            ["results", "results and analysis"],
            ["discussion"],
            ["conclusion"],
        ]
    )

    # If the PDF has no dedicated Research Problem section, do NOT
    # dump the entire Introduction into the MVP card. Prefer the
    # abstract; otherwise use only the first few sentences of the
    # introduction as a concise problem context.
    if not sections["Research Problem"]:
        if sections["Abstract"]:
            problem_source = sections["Abstract"]
        else:
            problem_source = get_section(
                ["background", "introduction"],
                [
                    ["objectives", "research objectives", "aim", "aims"],
                    ["methodology", "methods", "materials and methods"],
                    ["results", "results and analysis"],
                    ["discussion"],
                    ["conclusion"],
                ]
            )

        problem_sentences = re.split(r"(?<=[.!?])\s+", problem_source.strip())
        sections["Research Problem"] = " ".join(problem_sentences[:3]).strip()

    # Keep the full extracted problem internally, but show a compact
    # version in the Project Overview card. This prevents long papers
    # from taking over the screen while preserving the source text for
    # downstream comparison.
    research_problem_full = sections["Research Problem"].strip()
    research_problem_preview = re.sub(r"\s+", " ", research_problem_full).strip()

    if len(research_problem_preview) > 480:
        cut = research_problem_preview[:480]
        last_dot = cut.rfind(".")
        if last_dot >= 180:
            research_problem_preview = cut[:last_dot + 1]
        else:
            research_problem_preview = cut.rstrip() + "…"

    sections["Research Problem Full"] = research_problem_full
    sections["Research Problem"] = research_problem_preview

    # --------------------------------------------------
    # OBJECTIVES
    # --------------------------------------------------
    sections["Objectives"] = get_section(
        ["objectives", "research objectives", "aim", "aims"],
        [
            ["methodology", "methods", "materials and methods"],
            ["results", "results and analysis"],
            ["discussion"],
            ["conclusion"],
        ]
    )

    if not sections["Objectives"] and sections["Abstract"]:
        sentences = re.split(r"(?<=[.!?])\s+", sections["Abstract"])
        objective_sentences = [
            sentence for sentence in sentences
            if re.search(
                r"\b(aim|aims|objective|objectives|purpose)\b",
                sentence,
                re.IGNORECASE
            )
        ]
        sections["Objectives"] = " ".join(objective_sentences).strip()

    # --------------------------------------------------
    # METHODOLOGY
    # --------------------------------------------------
    methodology_full = get_section(
        ["methodology", "methods", "materials and methods"],
        [
            ["results", "results and analysis"],
            ["discussion"],
            ["conclusion"],
            ["references", "bibliography"],
        ]
    )

    # Keep the full methodology internally for comparison, but expose
    # a readable preview to the UI so a detailed experimental procedure
    # does not take over the whole MVP screen.
    methodology_preview = methodology_full.strip()

    # The methodology section can contain many pages of experimental
    # procedures. Keep the MVP card concise while retaining the full
    # section separately for downstream comparison.
    methodology_preview = re.sub(
        r"\b\d+(?:\.\d+)+\s*[^:]{0,90}:?",
        "",
        methodology_preview,
    )
    methodology_preview = re.sub(r"\s+", " ", methodology_preview).strip()

    if len(methodology_preview) > 260:
        cut = methodology_preview[:260]
        last_dot = cut.rfind(".")
        if last_dot >= 100:
            methodology_preview = cut[:last_dot + 1]
        else:
            methodology_preview = cut.rstrip() + "…"

    sections["Methodology"] = methodology_preview
    sections["Methodology Full"] = methodology_full

    # --------------------------------------------------
    # REFERENCES
    # --------------------------------------------------
    sections["References"] = get_section(
        ["references", "bibliography"],
        []
    )

    return sections


# ==========================================
# 03 — References Extraction
# ==========================================

def extract_references(full_text):
    """Extract references from normal or numbered reference headings."""

    lines = [
        re.sub(r"\s+", " ", line).strip()
        for line in full_text.splitlines()
        if line.strip()
    ]

    references = []
    start = False

    for line in lines:
        normalized = re.sub(
            r"^\s*\d+(?:\.\d+)*[\.\):\-]?\s*",
            "",
            line
        ).strip().lower()

        if normalized in ["references", "reference", "bibliography"]:
            start = True
            continue

        if start:
            references.append(line)

    return references


# ==========================================
# 04 — Research Output Builder
# ==========================================

def create_research_output(
    research_info,
    references
):

    return {
        "title": research_info.get(
            "Title",
            ""
        ),

        "research_problem": research_info.get(
            "Research Problem",
            ""
        ),

        "objectives": research_info.get(
            "Objectives",
            ""
        ),

        "methodology": research_info.get(
            "Methodology",
            ""
        ),

        "keywords": research_info.get(
            "Keywords",
            ""
        ),

        "references": references
    }


# ==========================================
# 05 — Search & Sources
# ==========================================

def build_search_query(research_info):

    title = research_info.get(
        "Title",
        ""
    ).strip()

    keywords = research_info.get(
        "Keywords",
        ""
    ).strip()

    query = f"{title} {keywords}"

    return query.strip()


def search_crossref(
    query,
    max_results=5
):

    try:

        url = "https://api.crossref.org/works"

        params = {
            "query.bibliographic": query,
            "rows": max_results
        }

        response = requests.get(
            url,
            params=params,
            timeout=20
        )

        response.raise_for_status()

        data = response.json()

        results = []

        for item in data[
            "message"
        ]["items"]:

            title_list = item.get(
                "title",
                []
            )

            if not title_list:
                continue

            title = title_list[0]

            authors = []

            for author in item.get(
                "author",
                []
            )[:3]:

                name = (
                    author.get(
                        "given",
                        ""
                    )
                    + " "
                    + author.get(
                        "family",
                        ""
                    )
                ).strip()

                if name:
                    authors.append(name)

            year = "Unknown"

            date_parts = (
                item.get(
                    "published-print",
                    {}
                ).get("date-parts")

                or item.get(
                    "published-online",
                    {}
                ).get("date-parts")

                or item.get(
                    "created",
                    {}
                ).get("date-parts")
            )

            if date_parts:
                year = str(
                    date_parts[0][0]
                )

            abstract = item.get(
                "abstract",
                "Abstract not available."
            )

            abstract = re.sub(
                r"<[^>]+>",
                "",
                abstract
            )

            link = item.get(
                "URL",
                ""
            )

            journal = item.get(
                "container-title",
                ["Unknown"]
            )[0]

            results.append({

                "title": title,

                "authors": (
                    ", ".join(authors)
                    if authors
                    else "Unknown"
                ),

                "year": year,

                "journal": journal,

                "abstract": abstract,

                "link": link
            })

        return results

    except Exception:

        return []


def get_patent_sources(query):

    encoded_query = urllib.parse.quote_plus(
        query
    )

    google_patents = (
        "https://patents.google.com/?q="
        + encoded_query
    )

    wipo_patentscope = (
        "https://patentscope.wipo.int/"
        "search/en/search.jsf?query="
        + encoded_query
    )

    return {
        "google_patents": google_patents,
        "wipo_patentscope": wipo_patentscope
    }


# ==========================================
# 06 — Comparison & Innovation Gap
# ==========================================

def clean_text(text):

    if not text:
        return ""

    text = re.sub(
        r"<[^>]+>",
        " ",
        text
    )

    text = re.sub(
        r"[^\w\s]",
        " ",
        text.lower()
    )

    text = re.sub(
        r"\s+",
        " ",
        text
    )

    return text.strip()


def get_keywords(text):

    text = clean_text(text)

    stop_words = {
        "the",
        "and",
        "for",
        "with",
        "from",
        "this",
        "that",
        "are",
        "was",
        "were",
        "have",
        "has",
        "using",
        "into",
        "their",
        "about",
        "study",
        "research",
        "based",
        "regarding",
        "among",
        "between"
    }

    words = text.split()

    return {
        word
        for word in words
        if len(word) > 3
        and word not in stop_words
    }


def calculate_similarity(
    project_text,
    paper_text
):

    project_words = get_keywords(
        project_text
    )

    paper_words = get_keywords(
        paper_text
    )

    if (
        not project_words
        or not paper_words
    ):
        return 0

    common_words = (
        project_words.intersection(
            paper_words
        )
    )

    union_words = (
        project_words.union(
            paper_words
        )
    )

    keyword_similarity = (
        len(common_words)
        / len(union_words)
    ) * 100

    sequence_similarity = (
        SequenceMatcher(
            None,
            clean_text(project_text),
            clean_text(paper_text)
        ).ratio()
    ) * 100

    final_score = (
        keyword_similarity * 0.7
        + sequence_similarity * 0.3
    )

    return round(
        final_score,
        2
    )


def compare_with_research(
    research_info,
    filtered_papers
):

    project_title = research_info.get(
        "Title",
        ""
    )

    project_problem = research_info.get(
        "Research Problem Full",
        research_info.get("Research Problem", "")
    )

    project_objectives = research_info.get(
        "Objectives",
        ""
    )

    project_methodology = research_info.get(
        "Methodology Full",
        research_info.get("Methodology", "")
    )

    project_keywords = research_info.get(
        "Keywords",
        ""
    )

    project_text = " ".join([
        project_title,
        project_problem,
        project_objectives,
        project_methodology,
        project_keywords
    ])

    comparison_results = []

    for paper in filtered_papers[:5]:

        paper_text = " ".join([
            paper.get("title", ""),
            paper.get("abstract", "")
        ])

        similarity = calculate_similarity(
            project_text,
            paper_text
        )

        project_words = get_keywords(
            project_text
        )

        paper_words = get_keywords(
            paper_text
        )

        common_words = (
            project_words.intersection(
                paper_words
            )
        )

        unique_project_words = (
            project_words - paper_words
        )

        if similarity >= 70:

            innovation_gap = (
                "High overlap detected. "
                "The project should clearly "
                "define how its methodology, "
                "population, data, or application "
                "differs."
            )

        elif similarity >= 40:

            innovation_gap = (
                "Moderate overlap detected. "
                "Potential innovation may exist "
                "in the methodology, target "
                "population, data, or application."
            )

        else:

            innovation_gap = (
                "Low textual/keyword overlap "
                "detected based on the available "
                "search result."
            )

        comparison_results.append({

            "paper": paper,

            "similarity": similarity,

            "common_words": sorted(
                common_words,
                key=len,
                reverse=True
            )[:10],

            "unique_words": sorted(
                unique_project_words,
                key=len,
                reverse=True
            )[:10],

            "innovation_gap": innovation_gap
        })

    if comparison_results:

        average_similarity = round(
            sum(
                result["similarity"]
                for result
                in comparison_results
            )
            / len(comparison_results),
            2
        )

    else:

        average_similarity = 0

    return {
        "results": comparison_results,
        "average_similarity": average_similarity
    }


# ==========================================
# 07 — IP Readiness
# ==========================================

def generate_ip_readiness(
    full_text,
    research_info
):

    detected_university = (
        "Imam Abdulrahman Bin Faisal University"
    )

    for line in full_text.splitlines():

        clean_line = line.strip()

        if (
            (
                "university"
                in clean_line.lower()
                or
                "college"
                in clean_line.lower()
            )
            and len(clean_line) < 100
        ):

            if not any(
                bad in clean_line.lower()
                for bad in [
                    "hospital",
                    "clinic",
                    "department",
                    "distributed",
                    "terms"
                ]
            ):

                detected_university = clean_line
                break

    # --------------------------------------
    # Full title
    # --------------------------------------

    full_title = research_info.get(
        "Title",
        ""
    ).strip()

    # Try to reconstruct title if PDF
    # split it across multiple lines.

    lines_list = [
        l.strip()
        for l in full_text.splitlines()
        if l.strip()
    ]

    raw_title = full_title

    if raw_title:

        normalized_title = re.sub(
            r"\s+",
            " ",
            raw_title
        ).strip()

        title_words = normalized_title.split()

        if len(title_words) >= 5:

            first_words = " ".join(
                title_words[:5]
            ).lower()

            start_index = -1

            for i, line in enumerate(
                lines_list
            ):

                normalized_line = re.sub(
                    r"\s+",
                    " ",
                    line
                ).strip()

                if (
                    first_words
                    in normalized_line.lower()
                ):

                    start_index = i
                    break

            if start_index != -1:

                title_parts = []

                for line in lines_list[
                    start_index:
                ]:

                    lower_line = line.lower()

                    if (
                        lower_line == "abstract"
                        or
                        lower_line.startswith(
                            "abstract:"
                        )
                        or
                        "corresponding author"
                        in lower_line
                        or
                        lower_line.startswith(
                            "keywords:"
                        )
                    ):
                        break

                    if (
                        lower_line.startswith(
                            "doi:"
                        )
                        or
                        lower_line.startswith(
                            "review began"
                        )
                        or
                        lower_line.startswith(
                            "review ended"
                        )
                        or
                        lower_line.startswith(
                            "published"
                        )
                        or
                        lower_line.startswith(
                            "copyright"
                        )
                    ):
                        break

                    if len(line) < 5:
                        continue

                    title_parts.append(
                        line
                    )

                if title_parts:

                    full_title = " ".join(
                        title_parts
                    )

    full_title = re.sub(
        r"(\w)-\s+(\w)",
        r"\1-\2",
        full_title
    )

    full_title = re.sub(
        r"\s+",
        " ",
        full_title
    ).strip()

    # --------------------------------------
    # Abstract
    # --------------------------------------

    project_abstract = research_info.get(
        "Abstract",
        "Not specified"
    )

    if len(project_abstract) > 350:

        project_abstract = (
            project_abstract[:350]
        )

        last_dot = (
            project_abstract.rfind(".")
        )

        if last_dot != -1:

            project_abstract = (
                project_abstract[
                    :last_dot + 1
                ]
            )

        else:

            project_abstract += "..."

    # --------------------------------------
    # Methodology
    # --------------------------------------

    project_methodology = (
        research_info.get(
            "Methodology",
            "Not specified"
        )
    )

    if len(project_methodology) > 350:

        project_methodology = (
            project_methodology[:350]
        )

        last_dot = (
            project_methodology.rfind(".")
        )

        if last_dot != -1:

            project_methodology = (
                project_methodology[
                    :last_dot + 1
                ]
            )

        else:

            project_methodology += "..."

    # --------------------------------------
    # Keywords
    # --------------------------------------

    project_field = research_info.get(
        "Keywords",
        "Computer Science & Information Technology"
    )

    return {

        "university":
            detected_university,

        "title":
            full_title,

        "field":
            project_field,

        "abstract":
            project_abstract,

        "methodology":
            project_methodology,

        "required_documents": [

            "Complete Patent Specification "
            "(Description, Claims, and Drawings).",

            "Assignment of Invention / "
            "Declaration from inventors.",

            "Official university sponsorship "
            "or clearance letter."
        ]
    }


# ==========================================
# 08 — Main Analysis Function
# ==========================================

def analyze_project(uploaded_file):

    # --------------------------------------
    # Extract PDF
    # --------------------------------------

    full_text = extract_text_from_any_pdf(
        uploaded_file
    )

    # --------------------------------------
    # Extract research information
    # --------------------------------------

    research_info = extract_research_info(
        full_text
    )

    references = extract_references(
        full_text
    )

    research_output = create_research_output(
        research_info,
        references
    )

    # --------------------------------------
    # Search
    # --------------------------------------

    query = build_search_query(
        research_info
    )

    papers = search_crossref(
        query,
        max_results=8
    )

    current_title = research_info.get(
        "Title",
        ""
    ).strip().lower()

    filtered_papers = []

    for paper in papers:

        paper_title = paper.get(
            "title",
            ""
        ).strip().lower()

        if paper_title != current_title:

            filtered_papers.append(
                paper
            )

    # --------------------------------------
    # Patent sources
    # --------------------------------------

    patent_sources = get_patent_sources(
        query
    )

    # --------------------------------------
    # Comparison
    # --------------------------------------

    comparison = compare_with_research(
        research_info,
        filtered_papers
    )

    # --------------------------------------
    # IP readiness
    # --------------------------------------

    ip_readiness = generate_ip_readiness(
        full_text,
        research_info
    )

    # --------------------------------------
    # Final result
    # --------------------------------------

    return {

        "full_text":
            full_text,

        "research_info":
            research_info,

        "references":
            references,

        "research_output":
            research_output,

        "search_query":
            query,

        "similar_research":
            filtered_papers[:5],

        "patent_sources":
            patent_sources,

        "comparison":
            comparison,

        "ip_readiness":
            ip_readiness
    }

# ==========================================
# 09 — AI Patent Drafting Agent (SAIP)
# ==========================================

def generate_saip_patent_draft(research_info):
    """
    Uses Gemini to draft the core components required for a SAIP
    digital patent filing: title (EN/AR), abstract, description,
    and claims — based on the extracted project information.
    """

    project_title = research_info.get("Title") or "Untitled Project"
    project_abstract = research_info.get("Abstract") or "Not specified"
    project_methodology = research_info.get("Methodology") or "Not specified"
    project_field = research_info.get("Keywords") or "Computer Science & Information Technology"

    prompt = f"""
You are an expert patent attorney and AI IP assistant specializing in the
Saudi Authority for Intellectual Property (SAIP) digital filing guidelines.
SAIP has no paper form; applicants type data directly into portal fields
and upload the Description, Claims, and Abstract as separate documents.

Based on the project details below, draft each required component clearly
and formally, in English, ready to be pasted into a Word document.

Project Title: {project_title}
Field: {project_field}
Methodology: {project_methodology}
Abstract/Problem: {project_abstract}

Return the draft using exactly these section headers, nothing else:

### TITLE_EN
### TITLE_AR
### ABSTRACT
### DESCRIPTION
### CLAIMS

- TITLE_EN / TITLE_AR: a concise technical invention title, in English then Arabic.
- ABSTRACT: under 150 words, summarizing the invention and its advantage.
- DESCRIPTION: technical background, general description, and methodology.
- CLAIMS: numbered claims, starting with a broad independent claim 1, followed by 2-4 dependent claims.
"""

    response = openai_client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
    )
    text = response.choices[0].message.content or ""

    tags_order = ["TITLE_EN", "TITLE_AR", "ABSTRACT", "DESCRIPTION", "CLAIMS"]

    def extract_section(tag, remaining_tags):
        others = "|".join(remaining_tags) if remaining_tags else "$"
        pattern = rf"###\s*{tag}\s*(.*?)(?=###\s*(?:{others})|\Z)"
        match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
        return match.group(1).strip() if match else ""

    draft = {}

    for i, tag in enumerate(tags_order):
        remaining = tags_order[i + 1:]
        draft[tag.lower()] = extract_section(tag, remaining)

    return draft

# ==========================================
# 10 — SAIP Draft PDF Export
# ==========================================

def build_patent_draft_pdf(draft):
    """
    Builds a downloadable, styled PDF (in memory) from the AI-generated
    SAIP patent draft dictionary, with proper Arabic (RTL) rendering.
    """

    import io
    import os
    import arabic_reshaper
    from bidi.algorithm import get_display

    from reportlab.lib.pagesizes import letter
    from reportlab.lib.colors import HexColor
    from reportlab.lib.enums import TA_CENTER, TA_RIGHT
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    from reportlab.platypus import (
        SimpleDocTemplate,
        Paragraph,
        Spacer,
        HRFlowable,
    )

    # --------------------------------------
    # Brand colors
    # --------------------------------------

    NAVY = HexColor("#173f73")
    GREEN = HexColor("#1f5c47")
    GRAY = HexColor("#555555")
    LIGHT_GRAY = HexColor("#999999")

    # --------------------------------------
    # Register Arabic-capable font
    # --------------------------------------

    font_path = os.path.join(
        os.path.dirname(__file__),
        "fonts",
        "Amiri-Regular.ttf",
    )

    arabic_font_name = "Helvetica"

    if os.path.exists(font_path):
        pdfmetrics.registerFont(TTFont("Amiri", font_path))
        arabic_font_name = "Amiri"

    def render_arabic(text):
        reshaped = arabic_reshaper.reshape(str(text or ""))
        return get_display(reshaped)

    buffer = io.BytesIO()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        topMargin=50,
        bottomMargin=50,
        leftMargin=50,
        rightMargin=50,
    )

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "WethaqTitle",
        parent=styles["Title"],
        alignment=TA_CENTER,
        textColor=NAVY,
        fontSize=17,
        spaceAfter=4,
    )

    subtitle_style = ParagraphStyle(
        "WethaqSubtitle",
        parent=styles["Normal"],
        alignment=TA_CENTER,
        textColor=LIGHT_GRAY,
        fontSize=9,
        spaceAfter=18,
    )

    heading_style = ParagraphStyle(
        "WethaqHeading",
        parent=styles["Heading2"],
        textColor=GREEN,
        fontSize=13,
        spaceBefore=18,
        spaceAfter=6,
    )

    body_style = ParagraphStyle(
        "WethaqBody",
        parent=styles["Normal"],
        textColor=GRAY,
        fontSize=10.5,
        leading=15,
        spaceAfter=10,
    )

    arabic_style = ParagraphStyle(
        "WethaqArabic",
        parent=styles["Normal"],
        fontName=arabic_font_name,
        alignment=TA_RIGHT,
        textColor=NAVY,
        fontSize=12,
        leading=20,
        spaceAfter=10,
    )

    def safe(text):
        text = str(text or "").strip()
        text = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        return text.replace("\n", "<br/>")

    story = []

    story.append(Paragraph("Wethaq — SAIP Patent Specification Draft", title_style))
    story.append(Paragraph("AI-generated preliminary draft — for reference purposes only", subtitle_style))
    story.append(HRFlowable(width="100%", thickness=1, color=NAVY, spaceAfter=14))

    story.append(Paragraph("Invention Title (EN)", heading_style))
    story.append(Paragraph(safe(draft.get("title_en", "")), body_style))

    story.append(Paragraph("Invention Title (AR)", heading_style))
    story.append(Paragraph(render_arabic(draft.get("title_ar", "")), arabic_style))

    story.append(Paragraph("Abstract", heading_style))
    story.append(Paragraph(safe(draft.get("abstract", "")), body_style))

    story.append(Paragraph("Description", heading_style))
    story.append(Paragraph(safe(draft.get("description", "")), body_style))

    story.append(Paragraph("Claims", heading_style))
    story.append(Paragraph(safe(draft.get("claims", "")), body_style))

    story.append(Spacer(1, 20))
    story.append(HRFlowable(width="100%", thickness=0.5, color=LIGHT_GRAY, spaceAfter=8))

    disclaimer_style = ParagraphStyle(
        "WethaqDisclaimer",
        parent=styles["Normal"],
        fontSize=8,
        textColor=LIGHT_GRAY,
    )

    story.append(Paragraph(
        "This is an AI-generated preliminary draft produced by Wethaq for reference "
        "purposes only. It does not constitute legal advice and must be reviewed "
        "before submission to SAIP.",
        disclaimer_style,
    ))

    doc.build(story)

    buffer.seek(0)

    return buffer

# ==========================================
# 11 — Strategic Recommendation Agent
# ==========================================

def generate_strategic_recommendations(research_info, top_result):
    """
    Uses Gemini to generate personalized, actionable recommendations
    based on the project's comparison results against the closest
    matching research paper (common words, unique words, similarity).
    """

    title = research_info.get("Title", "")
    objectives = research_info.get("Objectives", "")
    methodology = research_info.get("Methodology", "")

    similarity = top_result.get("similarity", 0) if top_result else 0
    common_words = top_result.get("common_words", []) if top_result else []
    unique_words = top_result.get("unique_words", []) if top_result else []
    closest_paper = top_result.get("paper", {}) if top_result else {}
    closest_paper_title = closest_paper.get("title", "")

    prompt = f"""
You are a research strategy advisor helping a researcher strengthen the
originality and innovation potential of their project before submitting
it for IP protection or publication.

Project Title: {title}
Objectives: {objectives}
Methodology: {methodology}

Comparison against the closest matching existing research paper:
Closest Paper Title: {closest_paper_title}
Similarity Score: {similarity}%
Overlapping Keywords (shared with existing research): {", ".join(common_words) if common_words else "None"}
Unique Keywords (found only in this project): {", ".join(unique_words) if unique_words else "None"}

Based on this data, provide concise, specific, and actionable guidance.
Return the response using exactly these section headers, nothing else:

### FOCUS_SHIFT
### UNEXPLORED_ANGLES
### DIFFERENTIATION_TIPS

- FOCUS_SHIFT: 2-3 sentences suggesting what to emphasize more and what
  to de-emphasize, referencing the overlapping keywords specifically
  (e.g., "Consider focusing less on X and more on Y").
- UNEXPLORED_ANGLES: a bullet list (3-5 items) of unexplored research
  angles or applications suggested by the project's unique keywords,
  that are not covered by the closest existing paper.
- DIFFERENTIATION_TIPS: a bullet list (3-4 items) of concrete ways to
  clearly differentiate this project from the closest existing paper
  (e.g., different population, different methodology, different scale).
"""

    response = openai_client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
    )
    text = response.choices[0].message.content or ""

    tags_order = ["FOCUS_SHIFT", "UNEXPLORED_ANGLES", "DIFFERENTIATION_TIPS"]

    def extract_section(tag, remaining_tags):
        others = "|".join(remaining_tags) if remaining_tags else "$"
        pattern = rf"###\s*{tag}\s*(.*?)(?=###\s*(?:{others})|\Z)"
        match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
        return match.group(1).strip() if match else ""

    recommendations = {}

    for i, tag in enumerate(tags_order):
        remaining = tags_order[i + 1:]
        recommendations[tag.lower()] = extract_section(tag, remaining)

    return recommendations
