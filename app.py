import streamlit as st
from PyPDF2 import PdfReader
import re
import string

# --- Page Configuration ---
st.set_page_config(page_title="Dilshad Smart Doc Insight", page_icon="📄", layout="centered")

# --- REFINED LOGIC FUNCTIONS ---

def clean_extracted_text(text):
    """Removes non-printable characters and fixes the '????' issue."""
    # This keeps only readable characters and standard punctuation
    printable = set(string.printable + "₹")
    cleaned = "".join(filter(lambda x: x in printable or x.isspace(), text))
    # Remove multiple spaces or weird line breaks
    return re.sub(r'\s+', ' ', cleaned).strip()

def universal_extractor(text):
    """Extracts structured data from ANY document using pattern matching."""
    data = {}
    
    # 1. Cleaner Text
    text = clean_extracted_text(text)

    # 2. Extract Document Type
    doc_type = "General Document"
    t_low = text.lower()
    if any(x in t_low for x in ["intimation", "selection", "admission"]):
        doc_type = "Selection/Admission Letter"
    elif any(x in t_low for x in ["bill", "invoice", "receipt"]):
        doc_type = "Bill / Invoice"
    elif any(x in t_low for x in ["marks", "grade", "percentage"]):
        doc_type = "Academic Record"

    # 3. Key-Value Extraction (The 'Colon' Strategy)
    # Looks for words like 'Name:', 'ID:', 'Roll No:' etc.
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

    # 4. Universal Pattern Matching (Dates & Money)
    data["Dates"] = list(set(re.findall(r'\d{2}[/-]\d{2}[/-]\d{4}', text)))
    data["Amounts"] = list(set(re.findall(r'(?:₹|Rs\.|Total)\s*[:]*\s*(\d+(?:,\d+)*(?:\.\d+)?)', text, re.IGNORECASE)))

    return doc_type, data

# --- App UI ---
st.title("📄 Dilshad Smart Doc Insight")
st.markdown("###Document Analyser")

with st.sidebar:
    st.header("App Stats")
    st.success("Mode: Pdf reader")
    st.info("Limit: Unlimited")
    st.write("This tool extracts data from your file and pdf to tell you what is file about and you can search for key words.")

uploaded_file = st.file_uploader("Upload PDF", type="pdf")

if uploaded_file:
    with st.spinner("Analyzing document structure..."):
        reader = PdfReader(uploaded_file)
        raw_text = ""
        for page in reader.pages:
            content = page.extract_text()
            if content: raw_text += content

    if not raw_text.strip():
        st.error("Could not read text. Is this a scanned image?")
    else:
        doc_type, info = universal_extractor(raw_text)
        
        # Display Results
        st.subheader(f"📑 {doc_type}")
        
        # Create 2 columns for a cleaner 'Founder' look
        col1, col2 = st.columns(2)
        
        with col1:
            if "Name" in info: st.write(f"**Name:** {info['Name']}")
            if "ID/Barcode" in info: st.write(f"**Reference ID:** {info['ID/Barcode']}")
        
        with col2:
            if "College/Org" in info: st.write(f"**Assigned To:** {info['College/Org']}")
            if "Stream/Faculty" in info: st.write(f"**Stream:** {info['Stream/Faculty']}")

        # Show Dates and Amounts
        if info["Dates"] or info["Amounts"]:
            st.write("---")
            st.write(f"📅 **Detected Dates:** {', '.join(info['Dates']) if info['Dates'] else 'None'}")
            st.write(f"💰 **Detected Values:** {', '.join(info['Amounts']) if info['Amounts'] else 'None'}")

        # Dynamic Founder Advice
        st.divider()
        st.subheader("💡 Your Next Steps")
        if "Selection" in doc_type:
            st.warning("Action Required: Confirm your admission before the deadline mentioned in the dates above.")
        elif "Bill" in doc_type:
            st.info("Action Required: Verify the total amount and save the receipt for your accounts.")
        else:
            st.write("Document successfully indexed. Use the search bar below for specific details.")

        # Local Search Feature
        st.write("---")
        query = st.text_input("🔍 Quick Search (e.g. 'Science' or 'Jehanabad')")
        if query:
            clean_text = clean_extracted_text(raw_text)
            if query.lower() in clean_text.lower():
                # Find the sentence containing the word
                sentences = clean_text.split('.')
                for s in sentences:
                    if query.lower() in s.lower():
                        st.success(f"**Found:** ...{s.strip()}...")
                        break
            else:
                st.error("Keyword not found in this document.")
