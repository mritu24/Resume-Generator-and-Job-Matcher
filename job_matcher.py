import requests
import os
import logging
from fuzzywuzzy import fuzz
from collections import Counter
from typing import List, Dict, Tuple, Set

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Expanded synonym map
SKILL_SYNONYMS = {
    "html": ["html5"],
    "css": ["css3"],
    "javascript": ["js"],
    "python": ["py", "python3"],
    "machine learning": ["ml"],
    "data analysis": ["data analytics", "analytics"],
    "react": ["reactjs", "react.js"],
    "nodejs": ["node", "node.js"],
    "sql": ["structured query language"],
    "java": ["java se", "java ee"],
    "pandas": ["pd"],
    "numpy": ["np"],
    "django": ["django framework"],
    "flask": ["flask framework"],
    "c++": ["cpp"],
    "git": ["version control"],
    "api": ["rest api", "graphql"],
    "linux": ["unix"],
    "cloud": ["cloud computing"],
    "aws": ["amazon web services"],
    "azure": ["microsoft azure"],
    "docker": ["containerization"],
    "kubernetes": ["k8s"],
    "web development": ["web dev"],
    "backend": ["back-end"],
    "frontend": ["front-end"],
    "full stack": ["full-stack"],
    "devops": ["dev ops"]
}

def expand_skills(skills: List[str]) -> List[str]:
    """Expand a list of skills with their synonyms."""
    expanded = set(skill.lower() for skill in skills)
    for skill in skills:
        synonyms = SKILL_SYNONYMS.get(skill.lower(), [])
        expanded.update(s.lower() for s in synonyms)
    return list(expanded)

def fetch_jobs(query: str, num_pages: str = "1", location: str = "", experience: str = "") -> Dict:
    """Fetch jobs from the JSearch API without caching for fresh results."""
    url = "https://jsearch.p.rapidapi.com/search"
    headers = {
        "X-RapidAPI-Key": os.getenv("RAPIDAPI_KEY", "729b8eda10msh9f3a9ff474e3e0ap1f230bjsna967c2a0df25"),
        "X-RapidAPI-Host": "jsearch.p.rapidapi.com",
        "Content-Type": "application/json"
    }
    querystring = {
        "query": query,
        "num_pages": num_pages,
        "location": location,
        "experience": experience
    }

    try:
        logger.info(f"Fetching jobs for query: {query}")
        response = requests.get(url, headers=headers, params=querystring)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as e:
        logger.error(f"HTTP error: {e}")
        return {"error": f"HTTP error: {e}"}
    except requests.exceptions.RequestException as e:
        logger.error(f"Request failed: {e}")
        return {"error": f"Request failed: {e}"}

def fuzzy_match(skill: str, text: str, threshold: int = 85, is_title: bool = False) -> bool:
    """Check if a skill matches a text with fuzzy matching, stricter for titles."""
    threshold = 90 if is_title else threshold
    return fuzz.partial_ratio(skill.lower(), text.lower()) >= threshold

def match_jobs(
    extracted_skills: List[str],
    query: str = "developer remote",
    location: str = "",
    experience: str = "",
    fuzzy_threshold: int = 85
) -> Tuple[List[Dict], Dict[str, List[str]], Dict[str, int]]:
    """
    Match jobs to skills, identify skill gaps, and prioritize missing skills.
    Returns (matched_jobs, missing_skills_summary, missing_skills_frequency).
    """
    expanded_skills = expand_skills(extracted_skills)
    logger.info(f"Expanded skills: {expanded_skills}")

    jobs_data = fetch_jobs(query, location=location, experience=experience)
    if "error" in jobs_data:
        return [{"error": jobs_data["error"]}], {}, {}

    matched_jobs = []
    missing_skills_summary = {}
    missing_skills_counter = Counter()

    # Experience keywords for filtering
    experience_keywords = {
        "entry_level": ["entry", "junior", "associate"],
        "mid_level": ["mid", "intermediate", "developer"],
        "senior_level": ["senior", "lead", "principal"]
    }

    for job in jobs_data.get("data", []):
        job_title = job.get("job_title", "").lower()
        job_description = job.get("job_description", "").lower()
        matched_skills = []

        # Count matched skills
        for skill in expanded_skills:
            if (fuzzy_match(skill, job_title, fuzzy_threshold, is_title=True) or
                fuzzy_match(skill, job_description, fuzzy_threshold)):
                matched_skills.append(skill)

        if matched_skills:
            # Check experience compatibility
            if experience and experience_keywords.get(experience):
                if not any(keyword in job_title or keyword in job_description
                          for keyword in experience_keywords[experience]):
                    logger.info(f"Job '{job.get('job_title')}' skipped due to experience mismatch")
                    continue

            city = str(job.get("job_city", "")).strip()
            country = str(job.get("job_country", "")).strip()
            location_str = f"{city}, {country}" if city and country else city or country or "Not specified"
            matched_jobs.append({
                "title": job.get("job_title", ""),
                "company": job.get("employer_name", ""),
                "location": location_str,
                "url": job.get("job_apply_link", ""),
                "description": job.get("job_description", "")[:200] + "..." if job.get("job_description") else "",
                "matched_skills": matched_skills,
                "score": len(matched_skills)  # Score based on number of matched skills
            })
            logger.info(f"Job '{job.get('job_title')}' matched with skills: {matched_skills}")
        else:
            logger.info(f"Job '{job.get('job_title')}' not matched. Skills checked: {expanded_skills}")

        # Collect missing skills
        missing = []
        for keyword in SKILL_SYNONYMS.keys():
            all_forms = [keyword] + SKILL_SYNONYMS.get(keyword, [])
            has_skill = any(skill.lower() in expanded_skills for skill in all_forms)
            if not has_skill and any(fuzzy_match(form, job_description, fuzzy_threshold) for form in all_forms):
                missing.append(keyword)
                missing_skills_counter[keyword] += 1
        if missing:
            missing_skills_summary[job.get("job_title", "")] = missing

    # Sort jobs by score
    matched_jobs.sort(key=lambda x: x["score"], reverse=True)
    return matched_jobs, missing_skills_summary, dict(missing_skills_counter)

def format_output(
    matched_jobs: List[Dict],
    missing_skills_summary: Dict[str, List[str]],
    missing_skills_frequency: Dict[str, int]
) -> str:
    """Format the output for better readability."""
    output = ["=== Job Matching Results ==="]

    if not matched_jobs or (len(matched_jobs) == 1 and "error" in matched_jobs[0]):
        output.append("No jobs matched or an error occurred.")
        return "\n".join(output)

    output.append(f"Matched Jobs ({len(matched_jobs)}):")
    for job in matched_jobs:
        output.append(f"- {job['title']} at {job['company']} (Matched Skills: {', '.join(job['matched_skills'])})")
        output.append(f"  Location: {job['location']}")
        output.append(f"  Description: {job['description']}")
        output.append(f"  Apply: {job['url']}")

    output.append("\nSkill Gaps:")
    if not missing_skills_summary:
        output.append("No skill gaps identified.")
    else:
        for job_title, skills in missing_skills_summary.items():
            output.append(f"- {job_title}: {', '.join(skills)}")

    output.append("\nMissing Skills Frequency (Prioritized):")
    if not missing_skills_frequency:
        output.append("No missing skills.")
    else:
        for skill, count in sorted(missing_skills_frequency.items(), key=lambda x: x[1], reverse=True):
            output.append(f"- {skill}: Required by {count} job(s)")

    return "\n".join(output)

def generate_skill_gap_report(missing_skills_summary: Dict[str, List[str]], missing_skills_frequency: Dict[str, int]) -> str:
    """Generate a downloadable skill gap report."""
    report = ["# Skill Gap Analysis Report\n"]
    report.append("## Overview")
    report.append(f"This report identifies skill gaps for {len(missing_skills_summary)} matched jobs.\n")

    report.append("## Skill Gaps by Job")
    if not missing_skills_summary:
        report.append("No skill gaps identified.")
    else:
        for job_title, skills in missing_skills_summary.items():
            report.append(f"- **{job_title}**: {', '.join(skills)}")

    report.append("\n## Prioritized Missing Skills")
    if not missing_skills_frequency:
        report.append("No missing skills.")
    else:
        for skill, count in sorted(missing_skills_frequency.items(), key=lambda x: x[1], reverse=True):
            report.append(f"- **{skill}**: Required by {count} job(s)")

    return "\n".join(report)