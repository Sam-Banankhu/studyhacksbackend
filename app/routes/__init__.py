from app import app, send_file
import os

# GETTING DOCUMENTATION 
@app.route('/')
def index():
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], "studyhacks-docs.pdf")
    return send_file(file_path)

