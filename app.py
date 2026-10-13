import os
from google import genai
from google.genai import types
import streamlit as st

# --- PAGE CONFIGURATION ---
st.set_page_config(
    page_title="Hornexa Tender Intelligence Portal",
    page_icon="🏢",
    layout="wide",
    initial_sidebar_state="expanded",
)

# --- SESSION STATE INITIALIZATION ---
if "authenticated" not in st.session_state:
  st.session_state.authenticated = False
if "tender_history" not in st.session_state:
  st.session_state.history = []

# --- AUTHENTICATION SYSTEM ---
def check_password():
  """Returns True if the user logged in successfully."""
  
  def password_entered():
    # You can change the password here or load it from secrets
    if st.session_state["password_input"] == "hornexa2026":
      st.session_state.authenticated = True
      del st.session_state["password_input"]  # don't store password
    else:
      st.session_state.authenticated = False

  if not st.session_state.authenticated:
    st.markdown("<br><br>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
      st.markdown("## 🔐 Hornexa Tender Portal Login")
      st.text_input(
          "Enter Portal Password",
          type="password",
          key="password_input",
          on_change=password_entered,
      )
      if "password_input" in st.session_state and not st.session_state.authenticated:
        # Check if they just typed something wrong or hit enter
        pass
      st.info("💡 Hint for testing: Use password **'hornexa2026'**")
    return False
  return True

# Run authentication guard
if not check_password():
  st.stop()


# --- MAIN PORTAL INTERFACE ---
st.title("🏢 Hornexa Tender Intelligence & Bidding Portal")
st.markdown(
    "Manage your tender packages, verify eligibility against pre-saved company"
    " credentials, and analyze risk factors instantly."
)

# Sidebar Configuration
with st.sidebar:
  st.header("⚙️ Portal Settings")
  api_key = st.text_input(
      "Google Gemini API Key", type="password", key="api_key_input"
  )

  st.markdown("---")
  st.header("🏢 Company Vault (Hornexa)")
  
  company_profile = st.text_area(
      "Master Company Profile:",
      value="""Company Name: Hornexa Technology
Business Type: IT Services, Software Engineering, Web & App Development, Digital Solutions
Locations: Noida & Ghaziabad, Uttar Pradesh, India
Registrations & Certifications: 
- Start-up India Certified
- MSME / Udyam Registered
- GST Registered
Turnover & Experience: Established IT firm with active operations in Noida/Ghaziabad.
Past Projects: Custom software development, enterprise IT infrastructure setups, web/mobile applications, digital marketing.""",
      height=200,
  )

  company_docs = st.text_area(
      "Master Document Repository:",
      value="""- GST Certificate\n- Udyam/MSME Certificate\n- Start-up India Certificate\n- Company PAN & TAN\n- Balance Sheet / IT Returns (Last 2 years)\n- Past Project Completion Certificates""",
      height=120,
  )

  st.markdown("---")
  if st.button("🔒 Logout Portal"):
    st.session_state.authenticated = False
    st.rerun()

# --- TABS FOR PORTAL NAVIGATION ---
tab1, tab2, tab3 = st.tabs([
    "📥 New Tender Analysis",
    "📁 Analysis History",
    "📊 Portal Dashboard",
])

with tab1:
  st.subheader("🚀 Multi-PDF Tender Package Analyzer")
  st.markdown(
      "Upload all related documents of a tender (Main RFP, Corrigendums, BOQ,"
      " Technical Specs) together."
  )

  tender_name_input = st.text_input(
      "Tender / Project Name (Optional)",
      placeholder="e.g., UP Government IT Infrastructure RFP 2026",
  )

  uploaded_files = st.file_uploader(
      "Upload Tender Package PDFs",
      type=["pdf"],
      accept_multiple_files=True,
      key="tender_pdf_uploader",
  )

  if uploaded_files and api_key:
    if st.button(
        "⚡ Analyze Tender Package Instantly",
        type="primary",
        use_container_width=True,
    ):
      with st.status(
          "Processing tender package files...", expanded=True
      ) as status:
        uploaded_gemini_files = []
        client = genai.Client(api_key=api_key)

        try:
          st.write("📤 Uploading tender files to secure AI vault...")
          for uploaded_file in uploaded_files:
            temp_path = uploaded_file.name
            with open(temp_path, "wb") as f:
              f.write(uploaded_file.getbuffer())

            st.write(f"Uploading: {uploaded_file.name}")
            g_file = client.files.upload(file=temp_path)
            uploaded_gemini_files.append(g_file)

          st.write("🤖 Running deep compliance and eligibility checks...")

          prompt = f"""
                    You are an expert Government Procurement and Bidding Consultant for Hornexa Technology.
                    Analyze the attached complete tender package documents strictly based on our Master Company Profile and Document Repository.
                    
                    ---
                    MASTER COMPANY PROFILE:
                    {company_profile}
                    
                    MASTER DOCUMENT REPOSITORY:
                    {company_docs}
                    ---
                    
                    Provide a single, professional, well-structured consolidated report containing:
                    1. **Tender & Project Overview:** Issuing authority, consolidated project scope, estimated value/budget, and key submission deadlines.
                    2. **Overall Eligibility Status:** Clearly state in bold whether the company is **ELIGIBLE** or **NOT ELIGIBLE** for this tender package.
                    3. **Detailed Reasons (Why / Why Not):** Give clear, bulleted reasons explaining why we qualify or fail based on financial turnover, past experience, technical criteria, or geographical/compliance clauses.
                    4. **Missing Documents & Gaps:** List out specific certificates, turnover thresholds, EMD, or legal documents demanded that are missing from our repository.
                    5. **Actionable Recommendation & Risk Analysis:** Should we bid? Highlight hidden penalties, liabilities, or prerequisites found across any of the files.
                    """

          contents_payload = uploaded_gemini_files + [prompt]
          response = client.models.generate_content(
              model="gemini-3.8-flash", contents=contents_payload
          )

          report_text = response.text
          status.update(
              label="Analysis Generated Successfully!",
              state="complete",
              expanded=False,
          )

          # Save to History
          proj_title = (
              tender_name_input
              if tender_name_input
              else f"Tender_{len(st.session_state.history)+1}"
          )
          st.session_state.history.append({
              "title": proj_title,
              "files": [f.name for f in uploaded_files],
              "report": report_text,
          })

          st.markdown("---")
          st.markdown("### 📊 Consolidated Tender Evaluation Report")
          st.markdown(report_text)

          # Download Button
          st.download_button(
              label="📥 Download Evaluation Report (TXT)",
              data=report_text,
              file_name=f"{proj_title}_Evaluation_Report.txt",
              mime="text/plain",
          )

        except Exception as e:
          status.update(
              label="Analysis Error Encountered", state="error", expanded=True
          )
          st.error(f"An error occurred: {e}")

  elif uploaded_files and not api_key:
    st.warning("⚠️ Please enter your Google Gemini API Key in the sidebar.")
  else:
    st.info(
        "👉 Enter your API key and upload tender package PDFs to initiate"
        " analysis."
    )

with tab2:
  st.subheader("📁 Saved Tender Analysis History")
  if not st.session_state.history:
    st.info(
        "No tender reports generated in this session yet. Run an analysis from"
        " the 'New Tender Analysis' tab."
    )
  else:
    for idx, item in enumerate(reversed(st.session_state.history)):
      with st.expander(f"📌 {item['title']} (Files: {len(item['files'])})"):
        st.write(f"**Uploaded Files:** {', '.join(item['files'])}")
        st.markdown("---")
        st.markdown(item["report"])
        st.download_button(
            label=f"📥 Download Report {idx+1}",
            data=item["report"],
            file_name=f"{item['title']}_Report.txt",
            mime="text/plain",
            key=f"download_history_{idx}",
        )

with tab3:
  st.subheader("📊 Portal Overview & Statistics")
  col1, col2, col3 = st.columns(3)
  with col1:
    st.metric(
        label="Total Analyzed Tenders", value=len(st.session_state.history)
    )
  with col2:
    st.metric(label="Active Company Profile", value="Hornexa Technology")
  with col3:
    st.metric(label="System Status", value="🟢 Online (Secure)")

  st.markdown("---")
  st.markdown("### 📝 Quick Guidelines for Bidding Team")
  st.markdown(
      """
  - Always upload **all corrigendums** along with the main RFP PDF to ensure the AI catches last-minute rule changes.
  - Keep your **Master Document Repository** in the sidebar updated with your latest financial turnover and certificate details.
  - Use the download button to share reports instantly with management or partners.
  """
  )
