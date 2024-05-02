import pandas as pd
from tqdm import tqdm
from nltk.tokenize import word_tokenize
from nltk import pos_tag
from nltk.corpus import wordnet as wn
import gender_guesser.detector as gender_detector
from flask import Flask, render_template, request, send_file, session

# Importation à partir du fichier utils
from utils import detect_first_word_type, remove_parentheses, clean_societe_text

# nltk.download('punkt')
# nltk.download('averaged_perceptron_tagger')

# Lancement de l'application
app = Flask(__name__)

# Code secret de l'application pour garder en cookies les données
app.secret_key = b'_5#y2L"F4Q8z\n\xec]/'

# Créer une route avec la méthode GET pour afficher la page d'index à la racine du projet
@app.route('/')
def index():
    return render_template('index.html')

# Lorsque l'on envoie une méthode POST au serveur, avec comme adresse /process_csv, alors on exécute la fonction process_csv
@app.route('/process_csv', methods=['POST'])
def process_csv():
    # Je récupère le fichier récupérer avec l'input
    file = request.files['file']

    # J'utilise uniquement le nom de fichier
    filename = file.filename

    # Je met en session le nom de fichier pour le réutiliser plus tard
    session['filename'] = filename

    # Si j'ouvre le fichier csv sans erreur, alors j'assigne sa valeur au dataframe df
    try:
        df = pd.read_csv(file)
    except:
        # Si la lecture en tant que CSV échoue, essayer de lire en tant que fichier Excel
        try:
            df = pd.read_excel(file)
        except:
            # Si les deux méthodes échouent, renvoyer une erreur
            return "Erreur de lecture du fichier : le format n'est ni CSV ni Excel."
    
    # Détection du genre du prénom ici
    def detect_gender(name):
        detector = gender_detector.Detector(case_sensitive=False)
        return detector.get_gender(name)

    # détection de la première lettre du nom de la société ici, en retournant True si le mot commence par une voyelle, sinon, False
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

    # Fonction du choix de préposition
    def determiner_prefixe_pronom(nom_entreprise):
        # print("Choix du préfixe en cours...")

        # Tokenisation de la phrase
        tokens = word_tokenize(nom_entreprise.lower())

        # Par défaut, j'utilise "au sein", sans déterminant
        prefixe = 'au sein'
        determinant = ""

        # Si le nom de société commence par "l' ", alors le déterminant doit être égal à de
        if tokens[0][0].lower() == "l" and tokens[0][1] == "'":
            determinant = "de"

        # Si le premier mot du nom de la société est dans cette liste choisir "de l'"
        elif tokens[0].lower() in ["institut", "agence", "atelier", "assurance", "association", "alliance", "etablissement", "établissement", "afnor", "essec"]:
            determinant = "de l'"
        elif tokens[0].lower() in ["bureau", "travail", "groupe", "pavillon", "cabinet", "ministère", "ministere", "grand", "université", "universite", "réseau", "reseau"]:
            determinant = "du"
        elif tokens[0].lower() in ["bureaux", "travaux", "grands", "groupes", "pavillons", "ministeres", "ministères", "réseaux", "reseaux"]:
            determinant = "des"
        elif tokens[0].lower() in ['mission', "maison", "companie", "cci", "fiduciaire", "compagnie", "caisse", "protection", "chambre", "commune", "place", "sncf"]:
            determinant = "de la"

        # Règles spécifiques pour certaines entreprises
        # Si le nom de l'entreprise commence par une voyelle et est un nom commun, sans que les précédentes conditions soient remplies, alors le déterminant sera "d'", sinon, on utilisera "de"
        elif detect_first_word_type(nom_entreprise) == "nom_commun":
            if is_commom_noun_starting_with_vowel(nom_entreprise):
                determinant = "d'"
            else:
                determinant = "de"
        elif detect_first_word_type(nom_entreprise) == "determinant":
            if tokens[0].lower() == "les":
                # tokens = tokens[1:]   
                # determinant = "des"
                prefixe = "chez"
            elif tokens[0].lower() == "le":
                # tokens = tokens[1:]
                prefixe = "chez"
            elif tokens[0].lower() == "la":
                determinant = "de"
            
                # print(tokens)
        else:
            prefixe = "chez "

        if prefixe == "au sein" and determinant == "":
            prefixe = "chez"
        return prefixe, determinant

    # Créer un nouveau DataFrame pour les lignes avec des valeurs d'e-mail nulles
    
    df_null_email = pd.DataFrame()  
    if 'Email' in df.columns:
        df_null_email = df[df['Email'].isnull()]

    total_rows = len(df)

    # Compter le nombre total de lignes où la civilité est "Monsieur"
    if 'Civilité' in df.columns:
        count_monsieur = (df['Civilité'] == 'Monsieur').sum()
        print("Nombre total de lignes avec civilité 'Monsieur':", count_monsieur, "nombre total de lignes", total_rows)


        with tqdm(total=total_rows, desc="Chargement du fichier") as pbar_load:
            for index, row in df.iterrows():
                if pd.isnull(row['Suggestion de Prénom']) and '.' not in row['lastName']:
                    df.at[index, 'Suggestion de Prénom'] = row['lastName']
                
                if isinstance(row['Société'], str):
                    # Remove parentheses and their contents
                    row_societe_cleaned = remove_parentheses(row['Société'])

                    row_societe_cleaned = clean_societe_text(row_societe_cleaned)
                    
                    # Determine prefix and determinant
                    prefix, determinant = determiner_prefixe_pronom(row_societe_cleaned)
                    
                    # Update the DataFrame with the cleaned and processed "Société" value
                    df.at[index, 'Société'] = f"{prefix} {determinant} {row_societe_cleaned}"

                if pd.isnull(row['firstName']):
                    df.at[index, 'Civilité'] = "Prénom non attribué"
                elif pd.isnull(row['Civilité']):
                    first_names = row['firstName'].split()
                    first_name = first_names[0]
                    gender = detect_gender(first_name)
                    if gender in ["andy", "unknown", "error"]:
                        if len(first_names) > 1:
                            second_name = first_names[1]
                            gender = detect_gender(second_name)
                    if gender == "female" or gender == "mostly_female":
                        df.at[index, 'Civilité'] = "Madame"
                    elif gender == "male" or gender=="mostly_male":
                        df.at[index, 'Civilité'] = "Monsieur"
                    elif gender == "andy":
                        if total_rows / count_monsieur >= 0.5:
                            df.at[index, 'Civilité'] = "Monsieur"
                        else:
                            df.at[index, 'Civilité'] = 'Madame'
                    elif gender == "unknown":
                        if total_rows / count_monsieur >= 0.5:
                            df.at[index, 'Civilité'] = "Monsieur"
                        else:
                            df.at[index, 'Civilité'] = 'Madame'
                    else:
                        df.at[index, 'Civilité'] = "Erreur"
                
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
                        if gender == "female" or gender == "mostly_female":
                            df_null_email.at[index, 'Civilité'] = "Madame"
                        elif gender == "male" or gender=="mostly_male":
                            df_null_email.at[index, 'Civilité'] = "Monsieur"
                        elif gender == "andy":
                            if total_rows / count_monsieur >= 0.5:
                                df.at[index, 'Civilité'] = "Monsieur"
                            else:
                                df.at[index, 'Civilité'] = 'Madame'
                        elif gender == "unknown":
                            if count_monsieur / total_rows < 50:
                                df_null_email.at[index, 'Civilité'] = "Madame"
                            else:
                                df_null_email.at[index, 'Civilité'] = "Monsieur"
                        else:
                            df_null_email.at[index, 'Civilité'] = "Erreur"
                
                # Check if any part of the last name matches the company name
                if isinstance(row['lastName'], str) and isinstance(row['Société'], str):
                    last_name_parts = row['lastName'].split()
                    for part in last_name_parts:
                        if part.lower() in row['Société'].lower():
                            df.at[index, 'Match Entreprise'] = 'Oui'
                            break
                    else:
                        df.at[index, 'Match Entreprise'] = 'Non'
                
                pbar_load.update(1)
        
    print(df)

    filename = session.get('filename')
    print(filename)

    filename_without_extension = filename.rsplit('.', 1)[0]

    # Replace spaces with underscores
    filename_without_extension = filename_without_extension.replace(' ', '_')

    # Concatenate '_updated.xlsx' suffix
    output_file = filename_without_extension + '_updated.xlsx'
    session['output_file'] = output_file

    # To try
    with pd.ExcelWriter(output_file) as writer:
        # Write original DataFrame to the first sheet
        df.dropna(subset=['Email']).to_excel(writer, sheet_name='Data', index=False)

        # Write DataFrame with null email to the second sheet
        if not df_null_email.empty:
            df_null_email.to_excel(writer, sheet_name='Null-Email', index=False)
    if 'Email' in df.columns:
        df.dropna(subset=['Email'], inplace=True)
    return render_template('result.html', data=df.to_html(), df_email_data=df_null_email.to_html(), filename=output_file)

@app.route('/download_excel')
def download_excel():
    excel_file_path = session.get('output_file')
    return send_file(excel_file_path, as_attachment=True)

if __name__ == '__main__':
    # webbrowser.open('http://localhost:5000')
    app.run(debug=True)