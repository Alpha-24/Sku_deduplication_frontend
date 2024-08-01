from flask import Flask, request, jsonify, render_template
from fuzzywuzzy import fuzz
from flask_cors import CORS
import pandas as pd

app = Flask(__name__)
CORS(app)

# Load SKU data
file_path = 'data/SKU_List.xlsx'
sku_data = pd.read_excel(file_path)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/api/search')
def search():
    query = request.args.get('query', '')
    if not query:
        return jsonify([])

    results = []
    for index, row in sku_data.iterrows():
        sku = row['Sku_Name']
        match = fuzz.partial_ratio(query.lower(), sku.lower())
        results.append({'sku': sku, 'match': match})

    results.sort(key=lambda x: x['match'], reverse=True)
    return jsonify(results)

if __name__ == '__main__':
    app.run(debug=True)
