from flask import Flask, render_template, request, jsonify
import pdfplumber
import requests
import json
app = Flask(__name__)
OLLAMA_API_URL = "http://localhost:11434/api/generate"
def extract_text_from_pdf(pdf_file):
    text = ""
    with pdfplumber.open(pdf_file) as pdf:
        for page in pdf.pages:
            text += page.extract_text() + "\n"
    return text.strip()
def build_prompt(parsed_text):
    return f"""
Given the following medical prescription text, extract:
1. The main patient condition (diagnosis).
2. List of foods to include.
3. List of foods to avoid.
Prescription text:
\"\"\"
{parsed_text}
\"\"\"
Return in JSON format like:
{{
  "condition": "...",
  "foods_to_include": ["...", "..."],
  "foods_to_avoid": ["...", "..."]
}}
"""
@app.route('/')
def index():
    return render_template('index.html')
@app.route('/analyze', methods=['POST'])
def analyze():
    file = request.files.get('file')
    if not file:
        return jsonify({"error": "No file uploaded"}), 400
    parsed_text = extract_text_from_pdf(file)
    payload = {
        "model": "medllama2",
        "prompt": build_prompt(parsed_text)
    }
    response = requests.post(OLLAMA_API_URL, json=payload)
    if response.status_code != 200:
        return jsonify({"error": "Failed to get response from Ollama"}), 500
    result_text = response.json().get("response", "")
    try:
        start = result_text.find("{")
        end = result_text.rfind("}") + 1
        json_part = result_text[start:end]
        structured_output = json.loads(json_part)
    except Exception as e:
        return jsonify({"error": f"Failed to parse JSON: {str(e)}", "raw_output": result_text}), 500
    return jsonify(structured_output)
if __name__ == '__main__':
    app.run(port=5000, debug=True)
