
import streamlit as st
import openai
import os
import fitz  # PyMuPDF
from docx import Document
from dotenv import load_dotenv

# Load API key
load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")
client = openai.OpenAI(api_key=api_key)

st.title("📜 Contract Risk Summarizer")
st.markdown("""
Upload an IT or vendor contract (PDF or DOCX).  
GPT-4 will extract key clauses like:
- Change of control
- Licensing limits
- Termination terms
- Data compliance
- Integration blockers
""")

# Upload
uploaded_file = st.file_uploader("📄 Upload Contract File", type=["pdf", "docx"])

# Text extractors
def extract_text_from_pdf(uploaded_file):
    text = ""
    with fitz.open(stream=uploaded_file.read(), filetype="pdf") as doc:
        for page in doc:
            text += page.get_text()
    return text

def extract_text_from_docx(uploaded_file):
    doc = Document(uploaded_file)
    return "\n".join([para.text for para in doc.paragraphs])

# Prompt builder
def build_prompt(contract_text):
    return f"""
You are a senior M&A legal analyst. Review this IT/vendor contract and summarize key risks:

---

### 📜 Change of Control
- What happens in case of acquisition or merger?
- What kind of restrictions are in place

### 🧾 Licensing & Restrictions
- Any seat/user/platform-based limits?

### 📅 Termination & Renewal
- Describe contract ending and notice terms.

### 🔐 Data & Compliance
- GDPR, PII, data residency clauses?

### ⚠️ Integration Concerns
- Restrictions on platform, region, domain, or company name?

If unclear, respond with "Needs review" or "Not found". Provide a clear and detailed explanation for each section. Also highlight each section heading and apply bulleted points where applicable

---

Contract Text:
{contract_text[:4000]}
"""

if uploaded_file:
    ext = uploaded_file.name.split(".")[-1].lower()
    contract_text = ""

    if ext == "pdf":
        contract_text = extract_text_from_pdf(uploaded_file)
    elif ext == "docx":
        contract_text = extract_text_from_docx(uploaded_file)

    if contract_text:
        st.text_area("📄 Preview of Extracted Text", contract_text[:1000], height=200)

        if st.button("🔍 Analyze Contract"):
            with st.spinner("Running GPT-4 analysis..."):
                try:
                    prompt = build_prompt(contract_text)
                    response = client.chat.completions.create(
                        model="gpt-4",
                        messages=[
                            {"role": "system", "content": "You are a senior contract reviewer."},
                            {"role": "user", "content": prompt}
                        ],
                        temperature=0.3
                    )
                    result = response.choices[0].message.content
                    st.session_state["contract_text"] = contract_text
                    st.session_state["initial_result"] = result
                    st.success("✅ Contract Analysis Complete")
                    #st.markdown(result)
                except Exception as e:
                    st.error(f"❌ Error: {e}")

# --- Persistent AI Analysis Display ---
if "initial_result" in st.session_state:
    st.markdown("### 📊 AI Contract Analysis")
    tab1, tab2 = st.tabs(["📄 Uploaded Contract", "📋 Initial Analysis"])
    with tab1:
        st.markdown(uploaded_file.name)

    with tab2:
        st.markdown("### 📋 AI-Generated Analysis")
        sections = st.session_state["initial_result"].split("###")
        for section in sections:
            st.markdown(f"### {section.strip()}")
        st.download_button("📥 Download Analysis", st.session_state["initial_result"], file_name="Contract_analysis.txt")

# Follow-up Prompt Section
if "initial_result" in st.session_state:
    st.divider()
    st.markdown("### 💬 Follow-Up Prompt")
    followup = st.text_area("Ask a follow-up about this contract:", placeholder="e.g. Does this agreement limit reassignment or sublicensing?")
    if st.button("🧠 Run Follow-Up"):
        with st.spinner("Getting GPT-4 response..."):
            followup_prompt = f"""
Here's the original contract (truncated):

{st.session_state['contract_text'][:4000]}

Here's the initial risk summary:

{st.session_state['initial_result']}

Follow-up request:
{followup}
"""
            try:
                response = client.chat.completions.create(
                    model="gpt-4",
                    messages=[
                        {"role": "system", "content": "You are a senior M&A contract specialist."},
                        {"role": "user", "content": followup_prompt}
                    ],
                    temperature=0.3
                )
                followup_result = response.choices[0].message.content
                st.success("✅ Follow-Up Complete")
                st.markdown("### 📝 Follow-Up Response")
                st.markdown(followup_result)
            except Exception as e:
                st.error(f"❌ GPT Error: {e}")
