from flask import Flask, request, jsonify
from flask_cors import CORS, cross_origin
from werkzeug.utils import secure_filename
import fitz
from openai import OpenAI
import os
from dotenv import load_dotenv

load_dotenv()  # Load variables from .env file

app = Flask(__name__)
CORS(app, resources={r"/upload": {"origins": "http://localhost:3000"}})

# Initialize OpenAI
openai_api_key = os.getenv("OPENAI_API_KEY")
openai = OpenAI(api_key=openai_api_key)

@app.route('/upload', methods=['POST'])
@cross_origin()
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'})

    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'})

    if file:
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)

        # Perform Step 2: Rewrite the uploaded file as a text file
        convert_to_text(file_path)

        # Perform Step 3A: Upload text file to OpenAI API
        assistant = IEPAssistant(api_key=openai_api_key, language='English')
        assistant.upload_file(file_path)
        response = assistant.create_message(message='What does my child struggle with in school')

        # Perform Step 3B: Convert text file to HTML
        convert_to_html(file_path)

        return jsonify({'message': 'File uploaded successfully', 'response': response})

def convert_to_text(file_path):
    doc = fitz.open(file_path)
    output_file_path = file_path.replace('.pdf', '.txt')
    with open(output_file_path, 'w', encoding='utf-8') as txt_file:
        for page_number in range(doc.page_count):
            page = doc[page_number]
            text = page.get_text()
            txt_file.write(text)
    doc.close()

def convert_to_html(file_path):
    response = client.chat.completions.create(
    model="gpt-3.5-turbo-1106",
    response_format={ "type": "text" },
    messages=[
        {"role": "system", "content": "You are a helpful assistant designed to turn your input into a well formatted HTML."},
        {"role": "user", "content": "Take this string of text and clean it up into an HTML file that is legible. The original document"+
        "includes checkboxes and redacted information. Try to maintain as much of the original structure as possible. Here is the"+
        f"string of text: {file_path}"}
            ]
        )
    output_file_path = file_path.replace('.txt', '.html')
    with open(output_file_path, 'w', encoding='utf-8') as html_file:
        html_file.write(response.choices[0].message.content)

@app.route('/test')
def test_route():
    return jsonify({'message': 'Test route successful'})


if __name__ == '__main__':
    app.config['UPLOAD_FOLDER'] = 'uploads'
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    app.run(debug=True, port=7000)




'''
# app.py
from flask import Flask, request, jsonify
from openai import OpenAI
from flask_cors import CORS  # Import CORS
import traceback

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Replace 'your_openai_api_key' with your actual OpenAI API key
openai_api_key = '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'
openai_api = OpenAI(api_key=openai_api_key)

# Replace 'your_assistant_id' with your actual Assistant ID
assistant_id = 'your_assistant_id'

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400

    file = request.files['file']

    try:
        # Upload file to OpenAI
        uploaded_file = openai_api.files.create(
            file=open(file, "rb"),
            purpose='assistants'
        )

        # Create a Thread with an initial message
        thread = openai_api.threads.create(
            messages=[
                {
                    "role": "user",
                    "content": f'Tell me a random fact from the file I uploaded: [{uploaded_file.id}]'
                }
            ]
        )

        # Run the Thread with the Assistant
        run = openai_api.threads.runs.create(
            thread_id=thread.id,
            assistant_id=assistant_id  # Replace with your actual Assistant ID
        )

        # Retrieve and return the response
        response = openai_api.threads.runs.retrieve(
            thread_id=thread.id,
            run_id=run.id
        )

        return jsonify({'output': response.choices[0].message.content[0].text.strip()})
    
    except Exception as e:
        traceback.print_exc()  # This will print the traceback to the console
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    app.run(port=7000, debug=True)


# app.py
from flask import Flask, request, jsonify
from flask_cors import CORS
from openai import OpenAI

app = Flask(__name__)
CORS(app)

# Set your OpenAI API key
client = OpenAI(api_key='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')

@app.route('/upload', methods=['POST'])
def upload_file():
    try:
        uploaded_file = request.files['file']

        # Ensure that the file content is read as bytes
        file_content = uploaded_file.read()

        # Decode the bytes using utf-8, ignoring errors
        prompt_text = file_content.decode('utf-8', errors='ignore')

        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": prompt_text}
            ]
            )

        return jsonify(response.choices[0].message)
    except Exception as e:
        print(e)
        return jsonify({'error': 'Error processing the file'}), 500

if __name__ == '__main__':
    app.run(debug=True)

'''


