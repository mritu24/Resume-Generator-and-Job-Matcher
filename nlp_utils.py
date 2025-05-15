import spacy
from typing import List

# Load the large English NLP model with word vectors
nlp = spacy.load("en_core_web_lg")

# Define a comprehensive list of skills (aligned with job_matcher.py)
predefined_skills = [
    "python", "java", "javascript", "html", "css", "react", "nodejs",
    "sql", "machine learning", "data analysis", "pandas", "numpy",
    "django", "flask", "c++", "git", "api", "linux", "cloud", "aws",
    "azure", "docker", "kubernetes"
]

def extract_skills_from_text(text: str) -> List[str]:
    """
    Extract skills from the provided text using spaCy and similarity matching.
    """
    doc = nlp(text.lower())
    extracted = set()

    # Direct matching
    for token in doc:
        if token.text in predefined_skills and token.text not in extracted:
            extracted.add(token.text)

    # Similarity-based matching
    for skill in predefined_skills:
        skill_doc = nlp(skill)
        if skill_doc.has_vector:
            for token in doc:
                if token.has_vector and token.similarity(skill_doc) > 0.75:
                    if skill not in extracted:
                        extracted.add(skill)

    return list(extracted)