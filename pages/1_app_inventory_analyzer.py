import streamlit as st
import pandas as pd
import openai
import os
from dotenv import load_dotenv

# Load OpenAI key from .env
load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")
client = openai.OpenAI(api_key=api_key)

# UI setup
st.set_page_config(page_title="M&A Application Inventory Analyzer", layout="wide")
st.title("📊 M&A Application Inventory Analyzer")
st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/2/27/M%26A_graphic.svg/1024px-M%26A_graphic.svg.png", width=100)
st.markdown("""
# 🤖 M&A App Inventory Analyzer
Welcome! This tool uses GPT-4 to analyze your enterprise application inventory for overlap, integration risks, and system optimization opportunities.

**How to use:**
1. Upload your app inventory as a `.csv` file  
2. Click **Analyze**  
3. Get an AI-powered summary with recommendations  
4. Ask follow-up questions for deeper insights  
""")
st.sidebar.title("🛠️ Tool Info")
st.sidebar.markdown("Built by Vamshi | Powered by GPT-4")
st.sidebar.markdown("[Get Support](mailto:vamshirahul@gmail.com)")

# File Upload
uploaded_file = st.file_uploader("Upload Application Inventory CSV", type=["csv"])

if uploaded_file:
    df = pd.read_csv(uploaded_file)
    st.subheader("✅ Uploaded Inventory")
    st.dataframe(df)

    inventory_text = df.to_string(index=False)

    # --- Default Prompt ---
    default_prompt = f"""
You are an AI M&A IT Integration Advisor. Your task is to analyze the following combined enterprise application inventory:

{inventory_text}

Please return your response in clear **markdown format** and organize it using the following headings:

---

### 🔁 Duplicate or Overlapping Applications
Identify applications that serve the same business function (e.g., two CRMs, two ERPs). Highlight any system overlaps or functional duplication.
- Highlight whether the apps are cloud-based or on-premise

---

### 🧯 Legacy / Sunset Candidates
List any on-premise, unsupported, or legacy applications that may need to be decommissioned, migrated, or flagged for risk due to age or architecture.
- Highlight candidates for migration to cloud-based alternatives.

---

### ⚠️ Integration Readiness Risks
Highlight any potential risks such as:
- Missing or unclear application ownership
- Lack of cloud compatibility
- Compliance or regional usage limitations
- Flag any deployment concerns (e.g., critical apps that are still on-premise).

---

### ⚠️ List of all Applications provided
List out each application in bulleted format

---

### 🛠️ Recommendations
Provide actionable suggestions on:
- Which applications to consolidate or prioritize for retirement
- Any short-term vs long-term integration considerations
- Other insights based on the overall portfolio
- Which apps should be retained and migrated?
- Which areas need further investigation before Day 1?
- Mention any compliance, cost-efficiency, or user-experience considerations.

Keep your response concise, clear, and formatted as bullet points under each heading.
"""

    if st.button("🔍 Analyze Inventory"):
        with st.spinner("Analyzing inventory with GPT-4..."):
            try:
                response = client.chat.completions.create(
                    model="gpt-4",
                    messages=[
                        {"role": "system", "content": "You are a helpful AI assistant for M&A IT integration."},
                        {"role": "user", "content": default_prompt}
                    ],
                    temperature=0.2
                )

                result = response.choices[0].message.content

                st.success("✅ Analysis complete!")

                # Save to session state
                st.session_state["inventory_text"] = inventory_text
                st.session_state["initial_result"] = result
                st.session_state["df"] = df

            except Exception as e:
                st.error(f"❌ Error: {str(e)}")

# --- Persistent AI Analysis Display ---
if "initial_result" in st.session_state:
    st.markdown("### 📊 AI Analysis")
    tab1, tab2 = st.tabs(["📄 Uploaded Inventory", "📋 Initial Analysis"])
    with tab1:
        st.dataframe(st.session_state["df"])

    with tab2:
        st.markdown("### 📋 AI-Generated Analysis")
        sections = st.session_state["initial_result"].split("###")
        for section in sections:
            st.markdown(f"### {section.strip()}")
        st.download_button("📥 Download Analysis", st.session_state["initial_result"], file_name="analysis.txt")

# --- Follow-Up Prompt Section ---
if "inventory_text" in st.session_state and "initial_result" in st.session_state:
    st.divider()
    st.markdown("### 💬 Ask a Follow-Up Question")
    user_followup = st.text_area("Enter a follow-up prompt (e.g., Which apps are redundant based on ownership or deployment?):")

    if st.button("🧠 Run Follow-Up"):
        with st.spinner("Generating follow-up response with GPT-4..."):
            followup_prompt = f"""
Here is the original application inventory:

{st.session_state['inventory_text']}

Here is the initial AI analysis:

{st.session_state['initial_result']}

Now please respond to the following follow-up request:

{user_followup}
"""

            try:
                followup_response = client.chat.completions.create(
                    model="gpt-4",
                    messages=[
                        {"role": "system", "content": "You are a senior M&A IT integration strategist."},
                        {"role": "user", "content": followup_prompt}
                    ],
                    temperature=0.3
                )

                followup_result = followup_response.choices[0].message.content
                st.success("✅ Follow-Up Response Generated")
                st.markdown("### 📝 Follow-Up AI Response")
                st.markdown(followup_result)

            except Exception as e:
                st.error(f"❌ Error during follow-up: {str(e)}")
