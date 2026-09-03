import streamlit as st
import pypdf
import re
import string
import json
import pandas as pd
from rapidfuzz import fuzz

# Optional NLP enrichment using spaCy
try:
    import spacy
    nlp = spacy.load("en_core_web_sm")
except Exception:
    nlp = None

# --- Page Configuration ---
st.set_page_config(
    page_title="Smart Document Insight Pro",
    page_icon="📄",
    layout="wide"
)

# --- REFINED LOGIC & EXTRACTION FUNCTIONS ---

def clean_extracted_text(text: str) -> str:
    """Sanitizes text, preserves key currency symbols, and eliminates white space anomalies."""
    if not text:
        return ""
    printable = set(string.printable + "₹€£¥")
    cleaned = "".join(filter(lambda x: x in printable or x.isspace(), text))
    return re.sub(r'\s+', ' ', cleaned).strip()

def extract_pdf_data(file) -> tuple[str, list[list[str]]]:
    """Extracts both raw narrative text and structured tables from PDF pages."""
    raw_text = ""
    extracted_tables = []
    
    reader = pypdf.PdfReader(file)
    for page in reader.pages:
        # Text extraction
        content = page.extract_text()
        if content:
            raw_text += content + "\n"
        
        # Table extraction (pypdf feature)
        try:
            tables = page.extract_tables()
            for tbl in tables:
                if tbl:
                    extracted_tables.append(tbl)
        except Exception:
             pass

    return raw_text, extracted_tables

def advanced_entity_extraction(text: str) -> dict:
    """Uses spaCy (if available) for named entity detection alongside regex fallbacks."""
    entities = {
        "PERSON": [],
        "ORG": [],
        "DATE": [],
        "MONEY": [],
        "GPE": []
    }
    
    if nlp:
        doc = nlp(text[:100000]) # Cap to 100k chars for performance
        for ent in doc.ents:
            if ent.label_ in entities:
                if ent.text.strip() not in entities[ent.label_]:
                    entities[ent.label_].append(ent.text.strip())
    else:
        # Regex Fallbacks if spaCy is not installed
        dates = re.findall(r'\b(?:\d{1,2}[/-]\d{1,2}[/-]\d{2,4}|\d{4}[/-]\d{1,2}[/-]\d{1,2}|(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]* \d{1,2},? \d{4})\b', text, re.I)
        amounts = re.findall(r'(?:₹|Rs\.|USD|\$|EUR|€)\s*[\d,]+(?:\.\d{2})?', text, re.I)
        entities["DATE"] = list(set(dates))
        entities["MONEY"] = list(set(amounts))

    return entities

def universal_extractor(text: str) -> tuple[str, dict]:
    """Classifies document type and parses core keys using regex strategy."""
    cleaned = clean_extracted_text(text)
    t_low = cleaned.lower()

    # Document Classification Strategy
    doc_type = "General Document"
    if any(x in t_low for x in ["intimation", "selection", "admission", "enrollment"]):
        doc_type = "Selection / Admission Letter"
    elif any(x in t_low for x in ["bill", "invoice", "receipt", "tax invoice", "statement"]):
        doc_type = "Bill / Financial Invoice"
    elif any(x in t_low for x in ["marks", "grade", "transcript", "scorecard", "academic"]):
        doc_type = "Academic Record"
    elif any(x in t_low for x in ["agreement", "contract", "memorandum", "terms"]):
        doc_type = "Legal / Agreement Document"

    # Robust Key-Value Extraction Patterns
    patterns = {
        "Name": r"(?:Name|Applicant|Candidate|नाम)\s*[:ः-]\s*([A-Za-z\s\.]{3,40})",
        "ID/Barcode": r"(?:Barcode|Reference|ID|Roll\s*No|Invoice\s*No|No)\s*[:ः-]\s*([\w\d/-]+)",
        "College/Org": r"(?:College|Institution|School|Company|Organization|संस्थान)\s*[:ः-]\s*([^,\.\n\r]+)",
        "Stream/Faculty": r"(?:Stream|Faculty|Department|Branch|संकाय)\s*[:ः-]\s*([A-Za-z\s]+)"
    }

    parsed_data = {}
    for key, pattern in patterns.items():
        match = re.search(pattern, cleaned, re.IGNORECASE)
        if match:
            parsed_data[key] = match.group(1).strip()

    # Dynamic Named Entities via NLP or Fallback
    parsed_data["NLP_Entities"] = advanced_entity_extraction(cleaned)

    return doc_type, parsed_data

def fuzzy_sentence_search(text: str, query: str, threshold: int = 60) -> list[tuple[str, int]]:
    """Performs fuzzy matching across document sentences for high-precision query retrieval."""
    cleaned_text = clean_extracted_text(text)
    # Split text into sentences safely
    sentences = re.split(r'(?<=[.!?]) +', cleaned_text)
    results = []

    for sentence in sentences:
        if len(sentence.strip()) < 5:
            continue
        score = fuzz.partial_ratio(query.lower(), sentence.lower())
        if score >= threshold:
            results.append((sentence.strip(), score))

    # Sort results by match quality
    results.sort(key=lambda x: x[1], reverse=True)
    return results

# --- App UI & Rendering ---

st.title("📄 Smart Document Insight Engine")
st.caption("Automated PDF parsing, NLP entity detection, table recovery, and semantic search.")

# Sidebar Statistics
with st.sidebar:
    st.header("System Dashboard")
    st.success("Mode: Advanced Hybrid Parser")
    st.info("Created by Md Dilshad Amir")
    
    if nlp:
        st.caption("⚡ NLP Accelerator Active (spaCy)")
    else:
        st.caption("⚠️ Running in basic Regex Mode. Install `spacy` + `en_core_web_sm` for deep NLP entity tracking.")

uploaded_file = st.file_uploader("Upload PDF File", type=["pdf"])

if uploaded_file:
    with st.spinner("Analyzing document structure & parsing vectors..."):
        raw_text, extracted_tables = extract_pdf_data(uploaded_file)

    if not raw_text.strip():
        st.error("⚠️ Primary text extraction failed. The PDF might be a scanned image or digitally encrypted.")
    else:
        doc_type, parsed_info = universal_extractor(raw_text)

        # Overview Metrics
        st.subheader(f"📑 Classified Type: {doc_type}")
        
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Character Count", len(raw_text))
        c2.metric("Word Count", len(raw_text.split()))
        c3.metric("Detected Tables", len(extracted_tables))
        c4.metric("Entities Found", sum(len(v) for v in parsed_info["NLP_Entities"].values()))

        st.divider()

        # Key Information Cards
        st.markdown("### 🔍 Core Extracted Metadata")
        col1, col2 = st.columns(2)

        with col1:
            st.write(f"**Name / Target:** {parsed_info.get('Name', 'Not Detected')}")
            st.write(f"**Reference / ID:** {parsed_info.get('ID/Barcode', 'Not Detected')}")

        with col2:
            st.write(f"**Organization / College:** {parsed_info.get('College/Org', 'Not Detected')}")
            st.write(f"**Stream / Department:** {parsed_info.get('Stream/Faculty', 'Not Detected')}")

        # Structured Tabbed Interface
        tab_entities, tab_tables, tab_search, tab_export = st.tabs([
            "🏷️ Named Entities (NLP)", 
            "📊 Extracted Tables", 
            "🔎 Smart Search", 
            "📥 Export Data"
        ])

        # TAB 1: NLP Entities
        with tab_entities:
            entities = parsed_info["NLP_Entities"]
            e_col1, e_col2, e_col3 = st.columns(3)

            with e_col1:
                st.markdown("**Organizations / Institutes**")
                st.write(entities.get("ORG", []) or "None found")

            with e_col2:
                st.markdown("**Dates & Timestamps**")
                st.write(entities.get("DATE", []) or "None found")

            with e_col3:
                st.markdown("**Monetary Values & Amounts**")
                st.write(entities.get("MONEY", []) or "None found")

        # TAB 2: Tables
        with tab_tables:
            if extracted_tables:
                st.success(f"Retrieved {len(extracted_tables)} table(s) from document.")
                for idx, tbl in enumerate(extracted_tables):
                    st.markdown(f"**Table {idx + 1}**")
                    df = pd.DataFrame(tbl)
                    st.dataframe(df, use_container_width=True)
            else:
                st.info("No explicit structural tables detected in this PDF.")

        # TAB 3: Fuzzy Search Engine
        with tab_search:
            query = st.text_input("Search document contents with typo tolerance:", placeholder="e.g., Admission, Payment, Total")
            if query:
                matches = fuzzy_sentence_search(raw_text, query)
                if matches:
                    st.success(f"Found {len(matches)} matching sentence context(s):")
                    for sentence, match_score in matches[:10]:  # Limit top 10 matches
                        st.markdown(f"- ...{sentence}... `(Match Score: {match_score}%)`")
                else:
                    st.warning("No context matching your query was found.")

        # TAB 4: Export Engine
        with tab_export:
            st.markdown("### Export Processed Document Intelligence")
            export_payload = {
                "document_type": doc_type,
                "metadata": {
                    "Name": parsed_info.get("Name"),
                    "ID": parsed_info.get("ID/Barcode"),
                    "Organization": parsed_info.get("College/Org"),
                    "Stream": parsed_info.get("Stream/Faculty")
                },
                "entities": parsed_info["NLP_Entities"],
                "raw_text_snippet": raw_text[:2000]
            }

            json_str = json.dumps(export_payload, indent=4)
            st.download_button(
                label="📥 Download Structured JSON",
                data=json_str,
                file_name="document_insight.json",
                mime="application/json"
            )

        # Dynamic Next Step Instructions
        st.divider()
        st.markdown("### 💡 Recommended Next Actions")
        if "Selection" in doc_type:
            st.warning("Action Required: Check deadlines under the 'Named Entities' tab to confirm admission on time.")
        elif "Bill" in doc_type:
            st.info("Action Required: Cross-reference amounts in the 'Extracted Tables' tab against your payment receipts.")
        else:
            st.success("Document fully processed. Query terms above or export data to external workflows.")
