from flask import Flask, request, jsonify
import joblib
import pandas as pd
import json
import os
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# Carga el modelo y las features
MODEL_PATH = 'social engineer/model/phishing_model_rf.joblib'
# SOLO usa los features que puedes calcular en el backend
FEATURES = [
    'Abnormal_URL ',
    'Prefix_Suffix ',
    'SSLfinal_State ',
    'Shortining_Service ',
    'having_At_Symbol ',
    'having_Sub_Domain '
]

model = joblib.load(MODEL_PATH)
feature_list = FEATURES

def extract_features_from_text(text):
    # Extracción básica compatible con el frontend actual
    features = {}
    features['length_url'] = len(text)
    features['num_digits'] = sum(c.isdigit() for c in text)
    features['num_links'] = text.count('http')
    features['having_At_Symbol '] = int('@' in text)
    features['having_Sub_Domain '] = int(text.count('.') > 1)
    features['Abnormal_URL '] = int('http' in text)
    features['Prefix_Suffix '] = int('-' in text)
    features['Shortining_Service '] = int(any(s in text for s in ['bit.ly', 'goo.gl', 'tinyurl', 'ow.ly', 't.co']))
    features['SSLfinal_State '] = int(text.startswith('https'))
    # El resto de features se rellenan con 0
    feature_vector = [features.get(f, 0) for f in feature_list]
    return pd.DataFrame([feature_vector], columns=feature_list)

@app.route('/predict', methods=['POST'])
def predict():
    data = request.json
    text = data.get('text', '')
    X = extract_features_from_text(text)
    proba = model.predict_proba(X)[0]
    pred = int(model.classes_[proba.argmax()])
    confidence = float(proba.max())
    return jsonify({'prediction': pred, 'confidence': confidence})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)