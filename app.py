import streamlit as st
import google.generativeai as genai
from PyPDF2 import PdfReader

# --- Page Configuration ---
st.set_page_config(page_title="AI Document Assistant", page_icon="📄")

# --- Security: Get API Key from Streamlit Secrets ---
# --- Security: Get API Key from Streamlit Secrets ---
# --- Security: Get API Key from Streamlit Secrets ---
if "GOOGLE_API_KEY" in st.secrets:
    # We use 'v1' instead of letting it default to 'v1beta'
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
else:
    st.error("Please set the GOOGLE_API_KEY in your Streamlit Secrets.")
    st.stop()

# Use 'gemini-pro' - it is the most stable version for the v1 API
model = genai.GenerativeModel('gemini-pro')
# --- App UI ---
st.title("📄 Smart Doc Insight")
st.markdown("Upload any document (Bill, Marksheet, ID) and let AI analyze it.")

# Sidebar for instructions
with st.sidebar:
    st.header("How to use")
    st.write("1. Upload a PDF document.")
    st.write("2. Wait for the automatic summary.")
    st.write("3. Ask specific questions below.")
    st.warning("Privacy Note: Avoid uploading highly sensitive personal data to public tools.")

# File Uploader
uploaded_file = st.file_uploader("Upload your document (PDF only)", type="pdf")

if uploaded_file is not None:
    # Read the PDF
    with st.spinner("Reading document..."):
        reader = PdfReader(uploaded_file)
        document_text = ""
        for page in reader.pages:
            content = page.extract_text()
            if content:
                document_text += content

    if document_text.strip() == "":
        st.error("Could not extract text from this PDF. It might be an image-only scan.")
    else:
        # Step 1: Automatic Summary & Suggestion
        st.subheader("🤖 AI Analysis & Suggestions")
        
        # We tell the AI how to behave based on the document type
        summary_prompt = f"""
        Analyze the following text extracted from a document. 
        1. Identify what kind of document it is (Bill, Marksheet, ID, etc.).
        2. Provide a 3-bullet point summary of the most important info.
        3. If it is a bill, suggest how/where to pay. If it is a marksheet, highlight top performance.
        
        Document Text:
        {document_text}
        """
        
        with st.spinner("Generating summary..."):
            response = model.generate_content(summary_prompt)
            st.info(response.text)

        st.divider()

        # Step 2: Chatbot for questions
        st.subheader("💬 Ask a Question about this File")
        user_query = st.text_input("Example: 'What is the due date?' or 'What are my total marks?'")

        if user_query:
            chat_prompt = f"Using this document context: {document_text}. Answer this question: {user_query}"
            with st.spinner("Thinking..."):
                chat_response = model.generate_content(chat_prompt)
                st.success(chat_response.text)
