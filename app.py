import streamlit as st
from PyPDF2 import PdfReader
import re
from collections import Counter

# --- Page Configuration ---
st.set_page_config(page_title="Dilshad Smart Doc Insight", page_icon="📄")

# --- NON-AI LOGIC FUNCTIONS ---

def offline_summarize(text):
    """Summarizes text by finding the most frequent important words."""
    # 1. Identify Document Type based on keywords
    doc_type = "General Document"
    text_lower = text.lower()
    if any(word in text_lower for word in ["bill", "invoice", "amt", "due date", "payable"]):
        doc_type = "Bill / Invoice"
    elif any(word in text_lower for word in ["marks", "grade", "result", "percentage", "roll no"]):
        doc_type = "Marksheet / Academic Record"
    elif any(word in text_lower for word in ["aadhaar", "pan card", "passport", "dob", "identity"]):
        doc_type = "Identity Document"

    # 2. Extract Key Dates and Amounts
    dates = re.findall(r'\d{2}[/-]\d{2}[/-]\d{4}', text)
    amounts = re.findall(r'(?:₹|Rs\.|Rs|Total|Amt)\s*[:]*\s*(\d+(?:,\d+)*(?:\.\d+)?)', text, re.IGNORECASE)
    
    # 3. Simple Summary Generation
    sentences = text.split('.')
    # Filter sentences to find 'important' ones
    summary_lines = []
    for s in sentences:
        if any(key in s.lower() for key in ["total", "date", "name", "no", "id", "result"]):
            if len(s.strip()) > 10:
                summary_lines.append(s.strip())
    
    summary = f"**Document Type:** {doc_type}\n\n"
    summary += "**Key Highlights:**\n"
    for line in summary_lines[:3]: # Top 3 important lines
        summary += f"* {line}\n"
    
    if doc_type == "Bill / Invoice" and amounts:
        summary += f"\n**Founder Advice:** This looks like a bill for ₹{amounts[0]}. Make sure to check the due date to avoid late fees!"
    elif doc_type == "Marksheet / Academic Record":
        summary += f"\n**Founder Advice:** Great job on these results! Focus on the subjects with the highest marks for your portfolio."
        
    return summary

def offline_search(text, query):
    """Finds specific info in the text without AI."""
    query = query.lower()
    sentences = text.split('.')
    
    # Check for date requests
    if "date" in query:
        dates = re.findall(r'\d{2}[/-]\d{2}[/-]\d{4}', text)
        return f"I found these dates in the document: {', '.join(dates)}" if dates else "No dates found."
    
    # Check for amount requests
    if "amount" in query or "total" in query or "marks" in query:
        numbers = re.findall(r'(\d+(?:,\d+)*(?:\.\d+)?)', text)
        relevant_context = [s for s in sentences if any(k in s.lower() for k in ["total", "marks", "rs", "₹"])]
        return f"Possible values found: {', '.join(numbers[:5])}\n\nContext: {relevant_context[0] if relevant_context else 'No context found.'}"

    # General Search
    for s in sentences:
        if query in s.lower():
            return f"Match found: ...{s.strip()}..."
            
    return "I couldn't find a direct answer. Try searching for a specific keyword like 'Total' or 'Date'."

# --- App UI ---
st.title("📄 Dilshad Smart Doc Insight (Offline Mode)")
st.markdown("Upload a PDF. This version works **without AI** using fast pattern matching.")

with st.sidebar:
    st.header("Founder Path Mode")
    st.info("This version uses Regex & Logic. No API limits!")
    st.write("1. Upload PDF")
    st.write("2. Get Instant Extraction")
    st.write("3. Search for Keywords")

uploaded_file = st.file_uploader("Upload your document (PDF only)", type="pdf")

if uploaded_file is not None:
    with st.spinner("Processing locally..."):
        reader = PdfReader(uploaded_file)
        document_text = ""
        for page in reader.pages:
            content = page.extract_text()
            if content:
                document_text += content

    if document_text.strip() == "":
        st.error("Text extraction failed. This might be a scanned image.")
    else:
        # Step 1: Summary (Local Logic)
        st.subheader("📊 Document Insights")
        summary_result = offline_summarize(document_text)
        st.info(summary_result)

        st.divider()

        # Step 2: Search (Local Logic)
        st.subheader("🔍 Find Information")
        user_query = st.text_input("What would you like to find? (e.g., 'Total', 'Date', 'Marks')")

        if user_query:
            answer = offline_search(document_text, user_query)
            st.success(answer)
