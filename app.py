import os
from flask import Flask, render_template, request, redirect
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

# Route d'upload du fichier Excel
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

            # ✅ Conversion en tableau brut (tableau de lignes)
            # ✅ Convertir tout le DataFrame en texte
            df_str = df.astype(str)
            data_list = [df_str.columns.tolist()] + df_str.values.tolist()


            # ✅ Enregistrement au bon format
            with open("static/donnees.json", "w", encoding="utf-8") as f:
                json.dump(data_list, f, ensure_ascii=False)

        except Exception as e:
            return f"Erreur de lecture Excel : {e}", 500

        return redirect('/?reload=1')  # recharge la page avec redirection vers stats

    return "Fichier non autorisé", 400

# Lancement local
if __name__ == '__main__':
    app.run(debug=True)