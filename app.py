#vitesse actuelle : 0.12 secondes par ligne
import pandas as pd
from tqdm import tqdm
import nltk
from nltk.tokenize import word_tokenize
from nltk import pos_tag
from nltk.corpus import wordnet as wn
import gender_guesser.detector as gender_detector
from flask import Flask, render_template, request, jsonify, send_file
import pandas as pd

nltk.download('punkt')
nltk.download('averaged_perceptron_tagger')
app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/process_csv', methods=['POST'])
def process_csv():
    file = request.files['file']
    try:
        df = pd.read_csv(file)
    except:
        # Si la lecture en tant que CSV échoue, essayer de lire en tant que fichier Excel
        try:
            df = pd.read_excel(file)
        except:
            # Si les deux méthodes échouent, renvoyer une erreur
            return "Erreur de lecture du fichier : le format n'est ni CSV ni Excel."

    
    def detect_gender(name):
        detector = gender_detector.Detector(case_sensitive=False)
        return detector.get_gender(name)

    def is_commom_noun_starting_with_vowel(word):

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
        
        # Règles spécifiques pour certaines entreprises
        if nom_entreprise.lower() in ['apple', 'samsung']:
            prefixe = 'chez'
        elif nom_entreprise.lower().startswith('entreprise'):
            prefixe = 'au sein de l\''
        else:
            # Analyse des noms composés
            if ' ' in nom_entreprise:
                mots = nom_entreprise.split()
                if mots[0] in ['agence', 'institut', 'bureau']:
                    prefixe = 'à l\''
                elif mots[0] in ['restaurant', 'café', 'boulangerie']:
                    prefixe = 'à la'
                else:
                    prefixe = 'chez'
            else:
                # Règles générales pour les autres cas
                if tokens[0] in ['agence', 'institut', 'bureau']:
                    prefixe = 'a l\''
                elif tokens[0] in ['restaurant', 'café', 'boulangerie']:
                    prefixe = 'à la'
                elif tokens[0] == 'la':
                    prefixe = 'à '
                elif tokens[0] == 'le':
                    prefixe = 'au'
                    tokens.pop(0)
                elif tokens[0] == 'les':
                    prefixe = 'aux'
                    tokens.pop(0)
                elif tokens[0] == 'l\'' and len(tokens) > 1:
                    if tokens[1] == 'entreprise':
                        prefixe = 'au sein de '
                        tokens.pop(0)
                        tokens.pop(0)
                    else:
                        prefixe = 'à '
                        tokens.pop(0)
                elif is_commom_noun_starting_with_vowel(tokens[0]):
                    prefixe = "à l'"
                else:
                    prefixe = 'chez'

        if nom_entreprise[-1] == 's':
            pronom = 'les'
        else:
            pronom = 'le'

        return prefixe, pronom



    # Créer un nouveau DataFrame pour les lignes avec des valeurs d'e-mail nulles
    df_null_email = df[df['Email'].isnull()]

    total_rows = len(df)

    # Compter le nombre total de lignes où la civilité est "Monsieur"
    count_monsieur = (df['Civilité'] == 'Monsieur').sum()

    print("Nombre total de lignes avec civilité 'Monsieur':", count_monsieur, "nombre total de lignes", total_rows)


    with tqdm(total=total_rows, desc="Chargement du fichier") as pbar_load:
        for index, row in df.iterrows():
            if pd.isnull(row['Suggestion de Prénom']) and '.' not in row['lastName']:
                df.at[index, 'Suggestion de Prénom'] = row['lastName']
            
            if isinstance(row['Société'], str):
                prefixe, pronom = determiner_prefixe_pronom(row['Société'])
                df.at[index, 'Société'] = f"{prefixe} {row['Société']}"
            
            # Analyse du prénom et ajout de la civilité appropriée
            if pd.isnull(row['firstName']):
                df.at[index, 'Civilité'] = "Prénom non attribué"
            elif pd.isnull(row['Civilité']):
                # Diviser le prénom en une liste de prénoms
                first_names = row['firstName'].split()
                # Prendre le premier prénom de la liste
                first_name = first_names[0]
                gender = detect_gender(first_name)
                # Si le genre est androgyne, inconnu ou s'il y a une erreur, analyser le deuxième prénom
                if gender in ["andy", "unknown", "error"]:
                    if len(first_names) > 1:
                        second_name = first_names[1]
                        gender = detect_gender(second_name)
                # Attribuer la civilité appropriée
                if gender == "female" or gender == "mostly_female":
                    df.at[index, 'Civilité'] = "Madame"
                elif gender == "male" or gender=="mostly_male":
                    df.at[index, 'Civilité'] = "Monsieur"
                elif gender == "andy":
                    df.at[index, 'Civilité'] = "Prénom androgyne"
                elif gender == "unknown":
                    df.at[index, 'Civilité'] = "Prénom inconnu de la base de données"
                else:
                    df.at[index, 'Civilité'] = "Erreur"
            
            # Si l'email est nul, attribuer également la civilité pour la feuille Null_Email
            if pd.isnull(row['Email']):
                if pd.isnull(row['firstName']):
                    df_null_email.at[index, 'Civilité'] = "Prénom non attribué"
                else:
                    first_names = row['firstName'].split()
                    first_name = first_names[0]
                    gender = detect_gender(first_name)
                    if gender in ["andy", "unknown", "error"]:
                        if len(first_names) > 1:
                            second_name = first_names[1]
                            gender = detect_gender(second_name)
                    # Attribuer la civilité appropriée
                    if gender == "female" or gender == "mostly_female":
                        df_null_email.at[index, 'Civilité'] = "Madame"
                    elif gender == "male" or gender=="mostly_male":
                        df_null_email.at[index, 'Civilité'] = "Monsieur"
                    elif gender == "andy":
                        df_null_email.at[index, 'Civilité'] = "Prénom androgyne"
                    elif gender == "unknown":
                        if count_monsieur / total_rows < 50:
                            df_null_email.at[index, 'Civilité'] = "Madame"
                        else:
                            df_null_email.at[index, 'Civilité'] = "Monsieur"
                    else:
                        df_null_email.at[index, 'Civilité'] = "Erreur"
            
            pbar_load.update(1)

    df_combined = pd.concat([df, df_null_email], ignore_index=True)

    df_combined = df_combined.dropna(subset=['Email'])

        
    print(df)

    output_file = 'tableur.xlsx'
    df_combined.to_excel(output_file, index=False)

    return render_template('result.html', data=df.to_html())


@app.route('/download_excel')
def download_excel():
    excel_file_path = 'tableur.xlsx'
    return send_file(excel_file_path, as_attachment=True)

if __name__ == '__main__':
    app.run(debug=False)