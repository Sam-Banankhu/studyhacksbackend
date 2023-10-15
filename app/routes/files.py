from app import app, jsonify, ObjectId, uuid,  Image, PyPDF2, pytesseract, backend_url, send_file
import os
from datetime import datetime
from app.routes.auth import authorise_request, jwt, secret_key, algorithm
from app.models import *

def extract_text_from_pdf(pdf_file_path):
    try:
        text = ''
        with open(pdf_file_path, 'rb') as pdf_file:
            pdf_reader = PyPDF2.PdfReader(pdf_file)
            pages = pdf_reader.pages
            for page_number in range(len(pages)):
                page = pdf_reader.pages[page_number]
                text += page.extract_text()
            return text
    except Exception as e:
        return text
def get_token(id):
    paylod={
     "id": id,
    }
    token = jwt.encode(paylod, secret_key, algorithm=algorithm)
    return token

def extract_text_from_image(image_path):
    try:
        image = Image.open(image_path)
        extracted_text = pytesseract.image_to_string(image)
        return extracted_text
    except Exception as e:
        return f"Error: {str(e)}"


# UpLOAD pDF
@app.route('/pdfs', methods=['POST'])
def upload_pdf():
    res= authorise_request(request)
    if(res=="expired"):
        return jsonify({"message": "Token expired"}), 403
    elif (res=="invalid"):
        return jsonify({"message": "Token is invalid"}),403
    elif(res=="not found"):
        return jsonify({"message": "Token not found"}),403
    elif(res=="revoked"):
        return jsonify({"message": "Token is revoked"}),403
    else:
        user_id=res["id"]
        if                                                                                                                                                                                                                                                                                                                   'file' not in request.files:
            return "No file part", 400
        
        file = request.files['file']
        
        if file.filename == '':
            return "No selected file", 400
        original_name=file.filename
        unique_id = uuid.uuid4()
        _id = str(ObjectId())
        pdf_loc=os.path.join(app.config['UPLOAD_FOLDER'],  str(unique_id)+".pdf")
        file.save(pdf_loc)
        extracted_text = extract_text_from_pdf(pdf_loc)
        data = {}
        data['user_id']=user_id
        data['type_']='pdf'
        data["extracted_text"]=extracted_text
        data["name"]=str(unique_id)+".pdf"
        data["original_name"]=original_name
        data["chat_ids"]=[]
        data["_id"]=_id
        data["path"]=backend_url+'/files/download/'+_id
        data['timestamp']=str(datetime.now())
        document = content_collection.insert_one(data)
        return jsonify({"msg": "Document processed successfully","id":document.inserted_id}),201


# UpLOADING IMAGES
@app.route('/images', methods=['POST'])
def upload_image():
    res= authorise_request(request)
    if(res=="expired"):
        return jsonify({"message": "Token expired"}), 403
    elif (res=="invalid"):
        return jsonify({"message": "Token is invalid"}),403
    elif(res=="not found"):
        return jsonify({"message": "Token not found"}),403
    elif(res=="revoked"):
        return jsonify({"message": "Token is revoked"}),403
    else:
        user_id=res["id"]
        if 'file' not in request.files:
            return "No file part", 400
        
        file = request.files['file']
        
        if file.filename == '':
            return "No selected file", 400
        
        unique_id = uuid.uuid4()
        _id = str(ObjectId())
        pdf_loc=os.path.join(app.config['UPLOAD_FOLDER'],  str(unique_id)+".pdf")
        file.save(pdf_loc)
        extracted_text = extract_text_from_pdf(pdf_loc)
        data = {}
        data['user_id']=user_id
        data['type_']='pdf'
        data["extracted_text"]=extracted_text
        data["name"]=str(unique_id)+".pdf"
        data["chat_ids"]=[]
        data["_id"]=_id
        data["path"]=backend_url+'/files/download/'+_id
        data['timestamp']=str(datetime.now())
        document = content_collection.insert_one(data)
        return jsonify({"msg": "Document processed successfully"}),201

# UpLOADING TEXT documents
@app.route('/text', methods=['POST'])
def upload_text():
    res= authorise_request(request)
    if(res=="expired"):
        return jsonify({"message": "Token expired"}), 403
    elif (res=="invalid"):
        return jsonify({"message": "Token is invalid"}),403
    elif(res=="not found"):
        return jsonify({"message": "Token not found"}),403
    elif(res=="revoked"):
        return jsonify({"message": "Token is revoked"}),403
    else:
        user_id=res["id"]
        data = request.get_json()
        text = data['text']
        unique_id = uuid.uuid4()
        _id = str(ObjectId())
        data = {}  
        answer1 = f'{text[:25]}...'
        data['user_id'] = user_id
        data['type_'] = 'text'
        data["extracted_text"] = text
        data["name"] = ''
        data["title"] = answer1
        data["chat_ids"] = []
        data["_id"] = _id
        data["path"] = ""
        data['timestamp'] = str(datetime.now())
        document = content_collection.insert_one(data)
        return jsonify({"msg": "Text processed successfully"}), 201




# retrieve all text documents
@app.route('/text', methods=['GET'])
def get_files():
    res= authorise_request(request)
    if(res=="expired"):
        return jsonify({"message": "Token expired"}), 403
    elif (res=="invalid"):
        return jsonify({"message": "Token is invalid"}),403
    elif(res=="not found"):
        return jsonify({"message": "Token not found"}),403
    elif(res=="revoked"):
        return jsonify({"message": "Token is revoked"}),403
    else:
        user_id=res["id"]
        documents_list = list(content_collection.find({"user_id":user_id, "type_": "text"}))
        return jsonify(documents_list), 200
    
    # retrive one text document
@app.route('/text/<text_id>', methods=['GET'])
def get_text(text_id):
    res = authorise_request(request)
    if res == "expired":
        return jsonify({"message": "Token expired"}), 403
    elif res == "invalid":
        return jsonify({"message": "Token is invalid"}), 403
    elif res == "not found":
        return jsonify({"message": "Token not found"}), 403
    elif res == "revoked":
        return jsonify({"message": "Token is revoked"}), 403
    else:
        user_id=res["id"]
        document = content_collection.find_one({"_id": text_id,"user_id":user_id, "type_": "text"})
        if document:
            return jsonify(document), 200
        else:
            return jsonify({"message": "Text document not found"}), 404

# retrive all psf documents  
@app.route('/pdfs', methods=['GET'])
def get_pdfs():
    res= authorise_request(request)
    if(res=="expired"):
        return jsonify({"message": "Token expired"}), 403
    elif (res=="invalid"):
        return jsonify({"message": "Token is invalid"}),403
    elif(res=="not found"):
        return jsonify({"message": "Token not found"}),403
    elif(res=="revoked"):
        return jsonify({"message": "Token is revoked"}),403
    else:
        user_id=res["id"]
        documents_list = list(content_collection.find({"user_id":user_id,"type_": "pdf"}))
        return jsonify(documents_list), 200

# retrieve one pdf document 
@app.route('/pdfs/<pdf_id>', methods=['GET'])
def get_pdf(pdf_id):
    res = authorise_request(request)
    if res == "expired":
        return jsonify({"message": "Token expired"}), 403
    elif res == "invalid":
        return jsonify({"message": "Token is invalid"}), 403
    elif res == "not found":
        return jsonify({"message": "Token not found"}), 403
    elif res == "revoked":
        return jsonify({"message": "Token is revoked"}), 403
    else:
        print(res)
        document = content_collection.find_one({"_id": pdf_id, "type_": "pdf"})
        if document:
            return jsonify(document), 200
        else:
            return jsonify({"message": "PDF not found"}), 404
from flask import request


# delete one pdf document
@app.route('/pdfs/<pdf_id>', methods=['DELETE'])
def delete_pdf(pdf_id):
    res = authorise_request(request)
    if res == "expired":
        return jsonify({"message": "Token expired"}), 403
    elif res == "invalid":
        return jsonify({"message": "Token is invalid"}), 403
    elif res == "not found":
        return jsonify({"message": "Token not found"}), 403
    elif res == "revoked":
        return jsonify({"message": "Token is revoked"}), 403
    else:
        # Add code here to delete the PDF document with the specified pdf_id
        result = content_collection.delete_one({"_id": pdf_id, "type_": "pdf"})
        if result.deleted_count > 0:
            return jsonify({"message": "PDF document deleted successfully"}), 200
        else:
            return jsonify({"message": "PDF not found for deletion"}), 404

#  get all imag documents 
@app.route('/images', methods=['GET'])
def get_images():
    res= authorise_request(request)
    if(res=="expired"):
        return jsonify({"message": "Token expired"}), 403
    elif (res=="invalid"):
        return jsonify({"message": "Token is invalid"}),403
    elif(res=="not found"):
        return jsonify({"message": "Token not found"}),403
    elif(res=="revoked"):
        return jsonify({"message": "Token is revoked"}),403
    else:
        user_id=res["id"]
        documents_list = list(content_collection.find({"user_id":user_id,"type_": "image"}))
        return jsonify(documents_list), 200

# getting all documents
@app.route('/pdf_images_text', methods=['GET'])
def get_all_contents():
    res= authorise_request(request)
    if(res=="expired"):
        return jsonify({"message": "Token expired"}), 403
    elif (res=="invalid"):
        return jsonify({"message": "Token is invalid"}),403
    elif(res=="not found"):
        return jsonify({"message": "Token not found"}),403
    elif(res=="revoked"):
        return jsonify({"message": "Token is revoked"}),403
    else:
        documents_list = list(content_collection.find({"user_id":res["id"]}))
        return jsonify(documents_list), 200

# download documents
@app.route('/files/download/<_id>', methods=['GET'])
def download_file(_id):
    document = content_collection.find_one({"_id": _id})
    if document:
        pdf_name = document["name"]
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], pdf_name)
        return send_file(file_path)
    else:
        return jsonify({"msg": "File not found"}), 404
