from nlp_utils import extract_skills_from_text
import streamlit as st
from resume_generator import generate_resume
from job_matcher import match_jobs, format_output, generate_skill_gap_report

st.title("🧠 AI Resume Generator & Job Matcher")
st.write("Fill in your details to generate a professional resume and get job suggestions.")

# Sidebar for job search preferences
st.sidebar.header("Job Search Preferences")
job_query = st.sidebar.text_input("Job Search Query", value="developer remote")
location = st.sidebar.text_input("Location (optional)", value="")
experience = st.sidebar.selectbox("Experience Level", ["", "entry_level", "mid_level", "senior_level"])
fuzzy_threshold = st.sidebar.slider("Fuzzy Matching Sensitivity", 70, 100, 85)

photo = st.file_uploader("📷 Upload Profile Photo (optional)", type=["jpg", "png"])

# Streamlit form
with st.form("resume_form"):
    name = st.text_input("Full Name")
    email = st.text_input("Email")
    education = st.text_area("Education")
    experience = st.text_area("Work Experience")
    skills = st.text_input("Skills (comma-separated)")
    linkedin = st.text_input("LinkedIn or Portfolio URL (for QR code)")
    submitted = st.form_submit_button("Generate Resume & Match Jobs")

if submitted:
    # Validate input
    if not name or not email:
        st.error("Please provide your name and email.")
    else:
        data = {
            "name": name,
            "email": email,
            "education": education,
            "experience": experience,
            "raw_skills": skills,
            "linkedin": linkedin,
            "extracted_skills": extract_skills_from_text(
                education + "\n" + experience + "\n" + skills
            )
        }

        st.success("✅ Resume Data Submitted Successfully!")

        # Resume preview
        st.markdown("---")
        st.subheader("📝 Resume Preview")
        st.markdown(f"**Name:** {name}")
        st.markdown(f"**Email:** {email}")
        st.markdown("**Education:**")
        st.markdown(education.replace('\n', '<br>'), unsafe_allow_html=True)
        st.markdown("**Experience:**")
        st.markdown(experience.replace('\n', '<br>'), unsafe_allow_html=True)
        st.markdown(f"**Skills:** {skills}")
        st.markdown(f"**Extracted Skills (via AI):** {', '.join(data['extracted_skills'])}")

        # Generate resume PDF
        pdf_path = generate_resume(data, photo)
        with open(pdf_path, "rb") as file:
            st.download_button(
                label="📄 Download Resume as PDF",
                data=file,
                file_name="resume.pdf",
                mime="application/pdf"
            )

        # Job matching
        st.markdown("---")
        st.subheader("💼 Recommended Jobs")
        matched_jobs, missing_skills_summary, missing_skills_frequency = match_jobs(
            data['extracted_skills'],
            query=job_query,
            location=location,
            experience=experience,
            fuzzy_threshold=fuzzy_threshold
        )

        # Display job matches
        if matched_jobs and "error" not in matched_jobs[0]:
            for job in matched_jobs:
                with st.expander(f"{job['title']} at {job['company']}"):
                    st.markdown(f"**Location:** {job['location']}")
                    st.markdown(f"**Description:** {job['description']}")
                    st.markdown(f"[Apply Here]({job['url']})")
        else:
            st.warning("No jobs matched or an error occurred.")

        # Skill gap section
        st.markdown("---")
        st.subheader("🔍 Skill Gap Analysis")
        if missing_skills_summary:
            for job, missing in missing_skills_summary.items():
                st.warning(f"**{job}** might require: {', '.join(missing)}")
            st.markdown("**Prioritized Missing Skills:**")
            for skill, count in sorted(missing_skills_frequency.items(), key=lambda x: x[1], reverse=True):
                st.markdown(f"- {skill}: Required by {count} job(s)")
        else:
            st.success("No skill gaps identified!")

        # Downloadable skill gap report
        report = generate_skill_gap_report(missing_skills_summary, missing_skills_frequency)
        st.download_button(
            label="📊 Download Skill Gap Report (Markdown)",
            data=report,
            file_name="skill_gap_report.md",
            mime="text/markdown"
        )