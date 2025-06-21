import os
from flask import Flask, render_template, request, redirect, send_from_directory
from werkzeug.utils import secure_filename
import pandas as pd
import json

# Configuration
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'xlsx'}

# Initialisation Flask
app = Flask(__name__, static_folder="static", template_folder="templates")
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Crée le dossier uploads s'il n'existe pas
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Vérifie l'extension du fichier
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Page principale
@app.route('/')
def home():
    return render_template('FREE.html')

# Route d'upload du fichier Excel principal
@app.route('/upload', methods=['POST'])
def upload_file():
    if 'excelFile' not in request.files:
        return "Aucun fichier trouvé", 400

    file = request.files['excelFile']

    if file and allowed_file(file.filename):
        filename = "dernier_fichier.xlsx"
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)

        try:
            df = pd.read_excel(filepath)

            # ✅ Conversion en tableau brut
            df_str = df.astype(str)
            data_list = [df_str.columns.tolist()] + df_str.values.tolist()

            with open("static/donnees.json", "w", encoding="utf-8") as f:
                json.dump(data_list, f, ensure_ascii=False)

        except Exception as e:
            return f"Erreur de lecture Excel : {e}", 500

        return redirect('/?reload=1')

    return "Fichier non autorisé", 400




@app.route('/import_penalites', methods=['POST'])
def import_penalites():
    file = request.files.get('penaliteFile')
    if not file or not file.filename.endswith(('.xlsx', '.xls')):
        return "Fichier non valide", 400

    df = pd.read_excel(file)
    vendeur_to_penalite = {}

    for _, row in df.iterrows():
        vendeur = str(row["Vendeur"]).strip()
        penalite = float(row["Penalite"])
        if vendeur:
            vendeur_to_penalite[vendeur] = penalite

    with open("static/penalites.json", "w", encoding="utf-8") as f:
        json.dump(vendeur_to_penalite, f, ensure_ascii=False, indent=2)

    return redirect("/?reload=1")



@app.route("/static/donnees.json")
def serve_donnees():
    return send_from_directory("static", "donnees.json")

@app.route('/save_bonus_malus', methods=['POST'])
def save_bonus_malus():
    data = request.get_json()
    with open("static/bonus_malus.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    return {"message": "Bonus/malus enregistré"}


# Route d'import des formateurs
@app.route('/import_formateurs', methods=['POST'])
def import_formateurs():
    file = request.files.get('formateurFile')
    if not file or not file.filename.endswith(('.xlsx', '.xls')):
        return "Fichier non valide", 400

    df = pd.read_excel(file)
    vendeur_to_formateurs = {}

    for _, row in df.iterrows():
        vendeur = str(row["Vendeur"]).strip()
        formateur = str(row["Formateur"]).strip()
        if vendeur and formateur:
            vendeur_to_formateurs.setdefault(vendeur, []).append(formateur)

    # Supprimer les doublons
    for vendeur in vendeur_to_formateurs:
        vendeur_to_formateurs[vendeur] = list(set(vendeur_to_formateurs[vendeur]))

    with open("static/formateurs.json", "w", encoding="utf-8") as f:
        json.dump(vendeur_to_formateurs, f, ensure_ascii=False, indent=2)

    return redirect('/?reload=1')

@app.route("/save_bonus", methods=["POST"])
def save_bonus():
    data = request.get_json()
    vendeur = data.get("vendeur")
    value = data.get("value")

    try:
        path = "static/bonus_manuels.json"
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                bonus_data = json.load(f)
        else:
            bonus_data = {}

        bonus_data[vendeur] = value

        with open(path, "w", encoding="utf-8") as f:
            json.dump(bonus_data, f, ensure_ascii=False, indent=2)

        return "OK", 200
    except Exception as e:
        return f"Erreur: {str(e)}", 500



# Lancement local
if __name__ == '__main__':
    app.run(debug=True)