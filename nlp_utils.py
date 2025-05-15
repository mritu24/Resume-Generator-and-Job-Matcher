import spacy
from typing import List

# Load the large English NLP model with word vectors
nlp = spacy.load("en_core_web_sm")

# Expanded list of skills
predefined_skills = [
    "python", "python3", "java", "javascript", "js", "html", "html5", "css", "css3",
    "react", "reactjs", "nodejs", "node", "sql", "machine learning", "ml",
    "data analysis", "data analytics", "pandas", "pd", "numpy", "np",
    "django", "flask", "c++", "cpp", "git", "version control", "api", "rest api",
    "graphql", "linux", "unix", "cloud", "cloud computing", "aws", "amazon web services",
    "azure", "microsoft azure", "docker", "containerization", "kubernetes", "k8s",
    "web development", "backend", "frontend", "full stack", "devops"
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

    # Similarity-based matching with lower threshold
    for skill in predefined_skills:
        skill_doc = nlp(skill)
        if skill_doc.has_vector:
            for token in doc:
                if token.has_vector and token.similarity(skill_doc) > 0.65:
                    if skill not in extracted:
                        extracted.add(skill)

    return list(extracted)