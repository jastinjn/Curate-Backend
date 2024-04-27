from flask import Flask, request, jsonify, current_app, send_file, abort
from flask_cors import CORS, cross_origin
import os
import rag

UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'pdf'}

app = Flask(__name__)
CORS(app)

app.secret_key = "ihatestartupstudio"
app.config['SESSION_TYPE'] = 'filesystem'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# @app.route("/")
# def home():
#     #return "Hello, World!"
#     return render_template("index.html")

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'})
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'})
    if file and allowed_file(file.filename):
        
        # delete previous files
        dir = os.listdir("uploads")
        if len(dir) != 0:
            for old_file in dir:
                os.remove('uploads/'+old_file)
            for old_file in os.listdir("patient"):
                os.remove('patient/'+old_file)

        filename = file.filename
        pdf_file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(pdf_file_path)

        # Split file up
        save_path = 'patient'
        splitting_character = '==='  # Change this to your desired splitting character
        new_files = rag.split_pdf_sections(pdf_file_path, save_path, splitting_character)

        return jsonify({'message': 'File uploaded successfully. Created the following files.', 'filename': filename, 'created_files': new_files})
    else:
        return jsonify({'error': 'Invalid file format. Please upload a PDF file.'})

@app.route('/init', methods=['POST'])
def init():
    init_type = request.args.get('type')
    if init_type is not None and init_type == "new":
        graph, vector_index = rag.initialize_databases('patient')
    else:
        graph, vector_index = rag.initialize_from_existing()
    
    current_app.graph = graph
    current_app.vector = vector_index
    current_app.patient = rag.get_particulars()['name']

    if hasattr(current_app, 'problems'):
        del current_app.problems

    return jsonify({'message': f'created database for patient {current_app.patient}'})

@app.route('/patient/overview', methods=['GET'])
def overview():

    # if not hasattr(current_app, 'overview_summary'):
    particulars = rag.get_particulars()
    name = particulars['name']
    overview = rag.get_overview(name)
    problems = rag.get_problems(name)
    current_app.problems = problems
    medications = rag.get_medications(name)
    response = {'particulars': particulars, 'overview': overview, 'problems': problems, 'medications': medications}
    # current_app.overview_summary = response
    # else:
    #     response = current_app.overview_summary

    return jsonify(response)

@app.route('/patient/query', methods=['POST'])
def rag_query():
    # Check if 'question' is present in the request data
    if 'question' not in request.form:
        return jsonify({'error': 'Question field is missing'}), 400
    
    # Retrieve the question from the request data
    question = request.form['question']
    
    response = rag.query_database(question)

    return jsonify(response)

@app.route('/patient/document/<file_name>', methods=['GET'])
def get_pdf(file_name):
    # Check if the file exists
    file_path = os.path.join('patient', file_name)
    if not os.path.exists(file_path):
        abort(404)  # Return 404 Not Found if the file does not exist
    
    # Return the file
    return send_file(file_path, as_attachment=True)

@app.route('/patient/document_summary/<file_name>', methods=['GET'])
def summarize_document(file_name):
    # Check if file_name is provided
    if not file_name:
        return jsonify({'error': 'File name is missing in the request parameters'}), 400
    if file_name not in os.listdir('patient'):
        return jsonify({'error': 'File does not exist'}), 400
    
    # if not hasattr(current_app, file_name):
    response = rag.summarize_document(f'patient/{file_name}')
    #     setattr(current_app, file_name, response)
    # else:
    #     response = getattr(current_app, file_name)
    
    return jsonify(response)

@app.route('/patient/documents', methods=['GET'])
def get_order():

    # if not hasattr(current_app, 'document_order'):
    if not hasattr(current_app, 'problems'):
        problems_response = rag.get_problems(current_app.name)
    else:
        problems_response = current_app.problems

    problems = [prob['name'] for prob in problems_response]

    response = rag.organize_documents(problems)
    current_app.document_order = response
    # else:
    #     response = current_app.document_order

    return jsonify(response)

if __name__ == '__main__':
    app.run(debug=True)