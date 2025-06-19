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

# S'assure que le dossier 'uploads' existe
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Vérifie si l'extension est autorisée
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Route principale
@app.route('/')
def home():
    return render_template('FREE.html')

# Route d’upload
@app.route('/upload', methods=['POST'])
def upload_file():
    if 'excelFile' not in request.files:
        return "Aucun fichier trouvé", 400

    file = request.files['excelFile']

    if file and allowed_file(file.filename):
        # Nom fixe pour écraser l'ancien fichier
        filename = "dernier_fichier.xlsx"
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)

        # Sauvegarde sur le serveur
        file.save(filepath)

        # Lecture avec pandas
        try:
            df = pd.read_excel(filepath)
            data_json = df.to_json(orient='records')

            # Sauvegarde en .json (pour le JS si besoin)
            with open("static/donnees.json", "w", encoding="utf-8") as f:
                f.write(data_json)

        except Exception as e:
            return f"Erreur de lecture Excel : {e}", 500

        return redirect('/')  # Recharge la page

    return "Fichier non autorisé", 400

# Lancement local (si besoin)
if __name__ == '__main__':
    app.run(debug=True)
