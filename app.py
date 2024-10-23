from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS, cross_origin
from werkzeug.utils import secure_filename
import fitz
from openai import OpenAI
import os
from dotenv import load_dotenv
from openai_assistant import IEPAssistant


load_dotenv()  # Load variables from .env file

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Initialize OpenAI
openai_api_key = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=openai_api_key)
original_file = None
assistant = None  # Define a global variable for the assistant

@app.route('/upload', methods=['POST'])
@cross_origin(origin='http://localhost:3000', headers=['Content- Type', 'Authorization'])
def upload_file():
    global original_file
    global assistant
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'})

    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'})

    if file:
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        original_file = filename
        file.save(file_path)

        # Perform Step 2: Rewrite the uploaded file as a text file and html file
        convert_to_text_and_html(file_path)

        # Perform Step 3A: Upload text file to OpenAI API
        txt_file_path = file_path.replace('.pdf', '.txt')

        if assistant is None:
            assistant = IEPAssistant(api_key=openai_api_key, language='English')
        assistant.upload_file(txt_file_path)

        return jsonify({'message': 'File uploaded successfully'})

def convert_to_text_and_html(file_path):

    doc = fitz.open(file_path)

    txt_file_path = file_path.replace('.pdf', '.txt')
    html_file_path = file_path.replace('.pdf', '.html')

    txt = ''
    with open(txt_file_path, 'w', encoding='utf-8') as txt_file:
        for page_number in range(doc.page_count):
            page = doc[page_number]
            text = page.get_text()
            txt += text
            txt_file.write(text)
    doc.close()

    response = client.chat.completions.create(
    model="gpt-3.5-turbo-1106",
    response_format={ "type": "text" },
    messages=[
        {"role": "system", "content": "You are a helpful assistant designed to display .txt files in an aesthetically pleasing way."},
        {"role": "user", "content": "Take this string of text and clean it up into an HTML file that is legible. The original document"+
        "includes checkboxes and redacted information. Here is the"+ f"string of text: {txt}"}
            ]
        )

    with open(html_file_path, 'w', encoding='utf-8') as html_file:
        html_file.write(response.choices[0].message.content)


@app.route('/simulate-chat-bot', methods=['POST'])
@cross_origin()
def simulate_chat_bot():
    global assistant

    data = request.get_json()
    user_message = data.get('message', '')

    # Now user_message is a string
    bot_response = assistant.create_message(message=user_message)

    return jsonify({'message': bot_response})

@app.route('/get-html-content', methods=['GET'])
def get_html_content():
    
    try:
        return send_from_directory('uploads/', 'iep.html')
    except FileNotFoundError:
        return jsonify({'error': 'File not found'}), 404

    

@app.route('/test')
def test_route():
    return jsonify({'message': 'Test route successful'})


if __name__ == '__main__':
    app.config['UPLOAD_FOLDER'] = 'uploads'
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    app.run(debug=True, port=7000)
