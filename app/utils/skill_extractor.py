import spacy
import nltk
from typing import List

# Download required NLTK data
nltk.download('punkt')
nltk.download('averaged_perceptron_tagger')
nltk.download('maxent_ne_chunker')
nltk.download('words')

# Load spaCy model
try:
    nlp = spacy.load("en_core_web_sm")
except:
    # If model is not installed, download it
    import os
    os.system("python -m spacy download en_core_web_sm")
    nlp = spacy.load("en_core_web_sm")

def extract_skills(text: str) -> List[str]:
    """
    Extract skills from the given text using NLP techniques.
    
    Args:
        text (str): Input text containing user's query
        
    Returns:
        List[str]: List of extracted skills
    """
    # Process the text with spaCy
    doc = nlp(text.lower())
    
    # Extract noun phrases as potential skills
    skills = set()
    for chunk in doc.noun_chunks:
        skills.add(chunk.text)
    
    # Extract named entities that might be technologies or skills
    for ent in doc.ents:
        if ent.label_ in ["ORG", "PRODUCT"]:
            skills.add(ent.text)
    
    # Clean and filter the skills
    cleaned_skills = []
    for skill in skills:
        # Remove stopwords and clean the skill text
        cleaned_skill = ' '.join([token.text for token in nlp(skill) 
                                if not token.is_stop and not token.is_punct])
        if cleaned_skill:
            cleaned_skills.append(cleaned_skill)
    
    return cleaned_skills