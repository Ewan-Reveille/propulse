import pandas as pd
from tqdm import tqdm
from nltk.tokenize import word_tokenize
from nltk import pos_tag
from nltk.corpus import wordnet as wn
import gender_guesser.detector as gender_detector
from flask import Flask, render_template, request, send_file
import pandas as pd
import spacy

nlp = spacy.load("fr_core_news_sm")

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
    
def determiner_prefixe_pronom(nom_entreprise):
    tokens = word_tokenize(nom_entreprise.lower())
    prefixe = ""
    determinant = ""
    
    # Règles spécifiques pour certaines entreprises
    if detect_first_word_type(nom_entreprise) == "nom_commun":
        prefixe = 'au sein'
        if is_commom_noun_starting_with_vowel(nom_entreprise):
            determinant = "d'"
        else:
            determinant = "de"
    elif detect_first_word_type(nom_entreprise) == "determinant":
        if tokens[0] == "Les":
            tokens = tokens[1:]
            print(tokens)

    return prefixe, determinant
        
df = pd.read_excel('tableur.xlsx')
def is_commom_noun_starting_with_vowel(word) -> bool:

    word = word.lower()

    pos_tags = pos_tag([word])

    if pos_tags[0][1] in ['NN', 'NNS', 'NNP', 'NNPS'] and word[0] in ['a', 'e', 'i', 'o', 'u']:
        return True

    synsets = wn.synsets(word, pos=wn.NOUN)
    if synsets:
        if any(word[0] in ['a', 'e', 'i', 'o', 'u'] for synset in synsets for word in synset.lemma_names()):
            return True
    return False

def determiner_prefixe_pronom(nom_entreprise):
    tokens = word_tokenize(nom_entreprise.lower())
    prefixe = ""
    determinant = ""
    
    # Règles spécifiques pour certaines entreprises
    if detect_first_word_type(nom_entreprise) == "nom_commun":
        prefixe = 'au sein'
        if is_commom_noun_starting_with_vowel(nom_entreprise):
            determinant = "d'"
        else:
            determinant = "de"
    elif detect_first_word_type(nom_entreprise) == "determinant":
        if tokens[0] == "Les":
            tokens = tokens[1:]
            print(tokens)
print(df)

output_file = 'tableur.xlsx'

with pd.ExcelWriter('tableur.xlsx') as writer:
    # Write original DataFrame to the first sheet
    df.to_excel(writer, sheet_name='Data', index=False)

    # Write DataFrame with null email to the second sheet
    if not df_null_email.empty:
            df_null_email.to_excel(writer, sheet_name='Null-Email', index=False)
    if 'Email' in df.columns:
        df.dropna(subset=['Email'], inplace=True)
 