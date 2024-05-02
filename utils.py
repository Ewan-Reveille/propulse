import spacy
import re


# Installation de la bibliothèque française de spacy. fr_core_news_sm est la bibliothèque française la plus précise actuellement (2 mai 2024)
nlp = spacy.load("fr_core_news_sm")

# En fonction de nlp, la variable prenant la bibliothèque française de spacy,
def detect_first_word_type(sentence):
    doc = nlp(sentence)
    first_token = doc[0]
    if first_token.pos_ == "DET":
        return "determinant"
    elif first_token.pos_ == "NOUN":
        if first_token.ent_type_ == "PROPN":
            return "nom_propre"
        else:
            return "nom_commun"
    else:
        return "autre"
    
def remove_parentheses(text):
    return re.sub(r'\([^)]*\)', '', text)

def clean_societe_text(text):
    text = re.sub(r'\s+', ' ', text)
    text = text.replace("' ", "'")
    return text