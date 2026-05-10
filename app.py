import streamlit as st
from PyPDF2 import PdfReader
import re
import string

# --- Page Configuration ---
st.set_page_config(page_title="Dilshad Smart Doc Insight", page_icon="📄", layout="centered")

# --- 1. LOGIC FUNCTIONS ---

def clean_extracted_text(text):
    printable = set(string.printable + "₹")
    cleaned = "".join(filter(lambda x: x in printable or x.isspace(), text))
    return re.sub(r'\s+', ' ', cleaned).strip()

def universal_extractor(text):
    data = {}
    text_clean = clean_extracted_text(text)
    
    doc_type = "General Document"
    t_low = text_clean.lower()
    if any(x in t_low for x in ["intimation", "selection", "admission"]):
        doc_type = "Selection Letter"
    elif any(x in t_low for x in ["bill", "invoice", "receipt"]):
        doc_type = "Bill / Invoice"
    elif any(x in t_low for x in ["marks", "grade", "percentage"]):
        doc_type = "Academic Record"

    patterns = {
        "Name": r"(?:Name|नाम|आवेदक का नाम)\s*[:ः-]\s*([A-Z\s]{3,})",
        "ID/Barcode": r"(?:Barcode|Reference|ID|संख्या)\s*[:ः-]\s*(\w+)",
        "College/Org": r"(?:College|Institution|School|संस्थान|Vidyalaya)\s*[:ः-]\s*([^,\.]+)",
        "Stream/Faculty": r"(?:Stream|Faculty|संकाय)\s*[:ः-]\s*([A-Za-z]+)"
    }

    for key, pattern in patterns.items():
        match = re.search(pattern, text_clean, re.IGNORECASE)
        if match:
            data[key] = match.group(1).strip()

    data["Dates"] = list(set(re.findall(r'\d{2}[/-]\d{2}[/-]\d{4}', text_clean)))
    data["Amounts"] = list(set(re.findall(r'(?:₹|Rs\.|Total)\s*[:]*\s*(\d+(?:,\d+)*(?:\.\d+)?)', text_clean, re.IGNORECASE)))
    return doc_type, data

def chatbot_response(text, query, info):
    query = query.lower()
    if any(x in query for x in ["hi", "hello", "hey"]):
        return "Hello! I'm your offline assistant. I can see your name, college, and ID. What do you need to know?"
    
    if "name" in query or "नाम" in query or "who" in query:
        val = info.get("Name", "Not found in summary")
        return f"The document name is: **{val}**."
    
    if any(x in query for x in ["college", "school", "where", "संस्थान"]):
        val = info.get("College/Org", "Not explicitly found")
        return f"Assigned Institution: **{val}**."

    # General context search
    sentences = clean_extracted_text(text).split('.')
    for s in sentences:
        if query in s.lower():
            return f"Found in text: '...{s.strip()}...'"
    return "I couldn't find a direct answer. Try a single keyword like 'Science' or 'Tehta'."

# --- 2. APP UI ---

st.title("📄 Dilshad Smart Doc Insight")

if "messages" not in st.session_state:
    st.session_state.messages = []

with st.sidebar:
    st.header("App Stats")
    st.success("Mode: Offline Logic")
    if st.button("Clear Chat"):
        st.session_state.messages = []
        st.rerun()

uploaded_file = st.file_uploader("Upload PDF", type="pdf")

if uploaded_file:
    if "doc_text" not in st.session_state:
        reader = PdfReader(uploaded_file)
        st.session_state.doc_text = "".join([p.extract_text() for p in reader.pages if p.extract_text()])

    raw_text = st.session_state.doc_text
    doc_type, info = universal_extractor(raw_text)

    # UI: Extraction Results
    st.subheader(f"📑 {doc_type}")
    c1, c2 = st.columns(2)
    with c1:
        st.write(f"**Name:** {info.get('Name', '---')}")
        st.write(f"**ID:** {info.get('ID/Barcode', '---')}")
    with c2:
        st.write(f"**College:** {info.get('College/Org', '---')}")
        st.write(f"**Stream:** {info.get('Stream/Faculty', '---')}")

    st.divider()

    # UI: Chatbot
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    if prompt := st.chat_input("Ask about your name or college..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            ans = chatbot_response(raw_text, prompt, info)
            st.markdown(ans)
            st.session_state.messages.append({"role": "assistant", "content": ans})
