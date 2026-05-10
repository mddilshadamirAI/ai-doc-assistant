import streamlit as st
from PyPDF2 import PdfReader
import re
import string

# --- Page Configuration ---
st.set_page_config(page_title="Dilshad Smart Doc Insight", page_icon="📄", layout="centered")

# --- 1. REFINED LOGIC FUNCTIONS (Unchanged) ---

def clean_extracted_text(text):
    """Removes non-printable characters and fixes the '????' issue."""
    printable = set(string.printable + "₹")
    cleaned = "".join(filter(lambda x: x in printable or x.isspace(), text))
    return re.sub(r'\s+', ' ', cleaned).strip()

def universal_extractor(text):
    """Extracts structured data from ANY document using pattern matching."""
    data = {}
    text = clean_extracted_text(text)
    
    doc_type = "General Document"
    t_low = text.lower()
    if any(x in t_low for x in ["intimation", "selection", "admission"]):
        doc_type = "Selection/Admission Letter"
    elif any(x in t_low for x in ["bill", "invoice", "receipt"]):
        doc_type = "Bill / Invoice"
    elif any(x in t_low for x in ["marks", "grade", "percentage"]):
        doc_type = "Academic Record"

    patterns = {
        "Name": r"(?:Name|नाम)\s*[:ः-]\s*([A-Z\s]+)",
        "ID/Barcode": r"(?:Barcode|Reference|ID|No)\s*[:ः-]\s*(\w+)",
        "College/Org": r"(?:College|Institution|School|संस्थान)\s*[:ः-]\s*([^,\.]+)",
        "Stream/Faculty": r"(?:Stream|Faculty|संकाय)\s*[:ः-]\s*([A-Za-z]+)"
    }

    for key, pattern in patterns.items():
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            data[key] = match.group(1).strip()

    data["Dates"] = list(set(re.findall(r'\d{2}[/-]\d{2}[/-]\d{4}', text)))
    data["Amounts"] = list(set(re.findall(r'(?:₹|Rs\.|Total)\s*[:]*\s*(\d+(?:,\d+)*(?:\.\d+)?)', text, re.IGNORECASE)))
    return doc_type, data

# --- 2. CHATBOT ENGINE (New Refined Logic) ---

def chatbot_response(text, query):
    """Simple logic-based chatbot assistant."""
    query = query.lower()
    clean_text = clean_extracted_text(text)
    
    # Greetings
    if any(x in query for x in ["hi", "hello", "hey"]):
        return "Hello! I am your Offline Document Assistant. How can I help you with this file today?"
    
    # Search logic
    sentences = clean_text.split('.')
    for s in sentences:
        if query in s.lower():
            return f"I found this in the document: '...{s.strip()}...'"
            
    return "I couldn't find a specific match for that in the document. Try searching for keywords like 'Name', 'Date', or 'College'."

# --- 3. APP UI & SESSION STATE ---

st.title("📄 Dilshad Smart Doc Insight")
st.markdown("### Document Analyser & Private Chatbot")

# Initialize Chat History
if "messages" not in st.session_state:
    st.session_state.messages = []

with st.sidebar:
    st.header("App Stats")
    st.success("Mode: Pdf reader + Chatbot")
    st.info("Limit: Unlimited")
    st.write("This tool extracts data locally and lets you chat with your file.")
    if st.button("Clear Chat History"):
        st.session_state.messages = []
        st.rerun()

uploaded_file = st.file_uploader("Upload PDF", type="pdf")

if uploaded_file:
    # Read PDF (Cached to avoid re-reading)
    if "doc_text" not in st.session_state:
        with st.spinner("Analyzing document structure..."):
            reader = PdfReader(uploaded_file)
            raw_text = ""
            for page in reader.pages:
                content = page.extract_text()
                if content: raw_text += content
            st.session_state.doc_text = raw_text

    raw_text = st.session_state.doc_text

    if not raw_text.strip():
        st.error("Could not read text. Is this a scanned image?")
    else:
        # Step 1: Automatic Extraction UI
        doc_type, info = universal_extractor(raw_text)
        st.subheader(f"📑 {doc_type}")
        
        col1, col2 = st.columns(2)
        with col1:
            if "Name" in info: st.write(f"**Name:** {info['Name']}")
            if "ID/Barcode" in info: st.write(f"**Reference ID:** {info['ID/Barcode']}")
        with col2:
            if "College/Org" in info: st.write(f"**Assigned To:** {info['College/Org']}")
            if "Stream/Faculty" in info: st.write(f"**Stream:** {info['Stream/Faculty']}")

        if info["Dates"] or info["Amounts"]:
            st.write("---")
            st.write(f"📅 **Detected Dates:** {', '.join(info['Dates']) if info['Dates'] else 'None'}")
            st.write(f"💰 **Detected Values:** {', '.join(info['Amounts']) if info['Amounts'] else 'None'}")

        st.divider()

        # Step 2: CHATBOT INTERFACE
        st.subheader("💬 Chat with your Document")
        
        # Display chat messages
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

        # Chat Input
        if user_input := st.chat_input("Ask me something (e.g., 'Where is my college?')"):
            # Add user message
            st.session_state.messages.append({"role": "user", "content": user_input})
            with st.chat_message("user"):
                st.markdown(user_input)

            # Generate Response
            with st.chat_message("assistant"):
                response = chatbot_response(raw_text, user_input)
                st.markdown(response)
                st.session_state.messages.append({"role": "assistant", "content": response})

        # Step 3: Dynamic Founder Advice
        st.sidebar.divider()
        st.sidebar.subheader("💡 Founder Advice")
        if "Selection" in doc_type:
            st.sidebar.warning("Action: Check admission deadlines!")
        elif "Bill" in doc_type:
            st.sidebar.info("Action: Verify totals.")
