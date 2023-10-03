
from flask import Flask, jsonify, request, session, redirect, url_for, render_template,send_file,send_from_directory
from pymongo import MongoClient
from bson import ObjectId
import datetime
from waitress import serve
from datetime import timedelta
# 
import pytesseract
from PIL import Image
from flask_jwt_extended import JWTManager, jwt_required, create_access_token, get_jwt_identity
import uuid
import os
import PyPDF2
from flask_bcrypt import Bcrypt
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user

# from dotenv import load_dotenv 
# # Load environment variables from .env file
# load_dotenv()

import openai
# Set your OpenAI API key
api_key = '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'
backend_url = os.getenv('BACKEND_URL')
# Initialize the OpenAI API client
openai.api_key = api_key




app = Flask(__name__)
app.secret_key = "HSHSHSHSSHH"
app.config['UPLOAD_FOLDER'] = os.path.join(os.getcwd(), 'uploads')
# Initialize Flask-Bcrypt
bcrypt = Bcrypt(app)
jwt = JWTManager(app)
expires_in = timedelta(days=7)

# Initialize the MongoDB client and database
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)


client = MongoClient("mongodb+srv://userxyz:userxyz@cluster0.5be8y.mongodb.net/?retryWrites=true&w=majority")
db = client["studyhacks"]
chats_collection = db["chats"]
users_collection = db["users"]
content_collection = db["documents"]


class User(UserMixin):
    def __init__(self, _id):
        self.id = _id

# Initialize Flask-Login and LoginManager
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"


# User loader function
@login_manager.user_loader
def load_user(_id):
    user = users_collection.find_one({'_id': _id})
    if user:
        return User(user['_id'])
    else:
        return None

# Docomention
@app.route('/')
def index():
    return render_template('documentation.html')
# USER MANAGEMENT ENDPOINTS
# registering user provide email(string), password(string), role(string),profile_complete(boolean)
@app.route('/register', methods=['POST'])
def register_user():
    data = request.get_json()
    email = data.get('email')
    name = data.get('name')
    role = data.get('role')
    profile_complete = data.get('profile_complete')
    profile_picture = data.get("profile_picture")
    password = data.get('password')
    country = data.get("country")
    gender=data.get("gender")
    institution=data.get("institution")
    mobile=data.get("mobile")
    role=data.get("role")
    country=data.get("country")
    data['timestamp']=str(datetime.datetime.now())
    if not email or not password:
        return jsonify({'msg': 'Email and password are required'}), 400

    # Check if the user already exists
    existing_user = users_collection.find_one({'email': email})
    if existing_user:
        return jsonify({'msg': 'User already exists'}), 400

    # Generate a unique user ID
    _id = str(ObjectId())


    hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')

    user = {
        '_id': _id,
        "name":name,
        "mobile":mobile,
        'email': email,
        "role": role,
        'password': hashed_password,
        "profile_complete":profile_complete,
        "profile_picture":profile_picture,
        "country": country,
        "role":role,
         "gender":gender,
    "institution":institution
        
    }

    # Insert the user document into the database
    users_collection.insert_one(user)

    return jsonify({'msg': 'User registered successfully'}), 201



# User login provide user name(email) and password and you will recieve a token

@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')

    if not email or not password:
        return jsonify({'msg': 'Email and password are required'}), 400

    user = users_collection.find_one({'email': email})

    if not user or not bcrypt.check_password_hash(user['password'], password):
        return jsonify({'msg': 'Invalid credentials'}), 401


    user_obj = User(user['_id'])
    login_user(user_obj)
    access_token = create_access_token(identity=user['_id'],expires_delta=expires_in)
    return jsonify({'msg': 'Login successful', 'access_token': access_token, 'user': user}), 200


# AUTHENTICATION


#  getting all users of the system . attach token in the request header# 
@app.route('/users', methods=['GET'])
@login_required
@jwt_required()
def get_all_users():
    users = list(users_collection.find())
    for user in users:
        user['_id'] = str(user['_id'])
    
    return jsonify(users), 200





# User logout
#attach token in the request header# 
# no infor provided .. it will get user id from server session
@app.route('/logout',methods=['POST']) 
@jwt_required()
@login_required
def logout():
    logout_user()
    return jsonify({'msg': 'Logged out successfully'}), 200

# FINDALLS

@app.route('/users/<string:_id>', methods=['GET'])
@login_required
@jwt_required()
def get_user(_id):
    user = users_collection.find_one({'_id': _id})

    if user:
        user['_id'] = str(user['_id'])
        return jsonify(user), 200
    else:
        return jsonify({'message': 'User not found'}), 404
    
    
    
    
# Change user password
# provide current_password and new_password
@app.route('/change_password', methods=['POST'])
@jwt_required()
@login_required
def change_password():
    data = request.get_json()
    current_password = data.get('current_password')
    new_password = data.get('new_password')

    user = users_collection.find_one({'_id': current_user.id})

    if not user or not bcrypt.check_password_hash(user['password'], current_password):
        return jsonify({'msg': 'Current password is incorrect'}), 401
    
    hashed_new_password = bcrypt.generate_password_hash(new_password).decode('utf-8')

    users_collection.update_one({'_id': current_user.id}, {'$set': {'password': hashed_new_password}})

    return jsonify({'msg': 'Password updated successfully'}), 200





# PDF PROCESSING ENDpOINTS

# uploading a pdf file to the server append the file and token in the header
@app.route('/pdfs', methods=['POST'])
@jwt_required()
@login_required
def upload_pdf():
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
    data['user_id']=current_user.id
    data['type_']='pdf'
    data["extracted_text"]=extracted_text
    data["name"]=str(unique_id)+".pdf"
    data["chat_ids"]=[]
    data["_id"]=_id
    data["path"]=backend_url+'/files/download/'+_id
    data['timestamp']=str(datetime.datetime.now())
    document = content_collection.insert_one(data)
    return jsonify({"msg": "Document processed successfully"}),201

@app.route('/images', methods=['POST'])
@jwt_required()
@login_required
def upload_image():
    if 'file' not in request.files:
        return "No file part", 400
    
    file = request.files['file']
    
    if file.filename == '':
        return "No selected file", 400
    
    unique_id = uuid.uuid4()
    _id = str(ObjectId())
    pdf_loc=os.path.join(app.config['UPLOAD_FOLDER'],  str(unique_id)+file.filename)
    file.save(pdf_loc)
    extracted_text = extract_text_from_image(pdf_loc)
    data = {}
    data['user_id']=current_user.id
    data['type_']='image'
    data["extracted_text"]=extracted_text
    data["name"]=str(unique_id)+file.filename
    data["chat_ids"]=[]
    data["_id"]=_id
    data["path"]=backend_url+'/files/download/'+_id
    data['timestamp']=str(datetime.datetime.now())
    document = content_collection.insert_one(data)
    return jsonify({"msg": "Image processed successfully"}),201


@app.route('/text', methods=['POST'])
@jwt_required()
@login_required
def upload_text():
    data = request.get_json()
    text=data['text']
    unique_id = uuid.uuid4()
    _id = str(ObjectId())
    data = {}
    data['user_id']=current_user.id
    data['type_']='text'
    data["extracted_text"]=text
    data["name"]=''
    data["chat_ids"]=[]
    data["_id"]=_id
    data["path"]=""
    data['timestamp']=str(datetime.datetime.now())
    
    document = content_collection.insert_one(data)
    return jsonify({"msg": "Text processed successfully"}),201


@app.route('/text', methods=['GET'])
@jwt_required()
@login_required
def get_files():
    documents_list = list(content_collection.find())
    files_list = []
    for document in documents_list:
        if(document["type_"]=='text'):
                document["_id"] = str(document["_id"])
                files_list.append(document)
    
    return jsonify(files_list), 200


# getting all pdf files from server append  token in the header
@app.route('/pdfs', methods=['GET'])
@jwt_required()
@login_required
def get_pdfs():
    documents_list = list(content_collection.find())
    files_list = []
    for document in documents_list:
        if(document["type_"]=='pdf'):
            document["_id"] = str(document["_id"])
            files_list.append(document)
    
    return jsonify(files_list), 200

@app.route('/images', methods=['GET'])
@jwt_required()
@login_required
def get_images():
    documents_list = list(content_collection.find())
    files_list = []
   
    for document in documents_list:
        if document["type_"]=='image':
            document["_id"] = str(document["_id"])
            files_list.append(document)
    
    return jsonify(files_list), 200

@app.route('/pdf_images_text', methods=['GET'])
@jwt_required()
@login_required
def get_all_contents():
    documents_list = list(content_collection.find())
    files_list = []
    for document in documents_list:
        document["_id"] = str(document["_id"])
        files_list.append(document)
    return jsonify(files_list), 200

# download a pdf file from server append  token in the header and pdf id
@app.route('/files/download/<_id>', methods=['GET'])
# @jwt_required()
# @login_required
def download_file(_id):
    document = content_collection.find_one({"_id": _id})
    if document:
        pdf_name = document["name"]
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], pdf_name)
        return send_file(file_path)
    else:
        return jsonify({"msg": "File not found"}), 404
    
   


# CHAT PROCESSING ENDPOINTS
# add  chat to server append  token in the header and pdf id
@app.route("/chats/<string:pdf_id>", methods=["POST"])
@jwt_required()
@login_required
def create_chat(pdf_id):
    data = request.get_json()
    question=data["question"]
    document = content_collection.find_one({"_id": pdf_id})
    print(document)
    context=document['extracted_text']
    response = openai.Completion.create(
        engine="text-davinci-002",
        prompt=f"Context: {context}\nQuestion: {question}\nAnswer:",
        max_tokens=50  
    )
    _id = str(ObjectId())
    answer = response.choices[0].text.strip()
    data['answer']=answer
    data['question']=question
    data['timestamp']=str(datetime.datetime.now())
    data['_id']=_id
    data['user_id'] = current_user.id  
    chats_collection.insert_one(data)
    content_collection.update_one(
    {"_id": document["_id"]},
    {"$push": {"chat_ids": _id}})
    return jsonify({"msg": "Chat created successfully",'chat':data}), 201


@app.route("/sammary/<string:pdf_id>", methods=["GET"])
@jwt_required()
@login_required
def create_sammary(pdf_id):
    document = content_collection.find_one({"_id": pdf_id})
    context=document['extracted_text']
    question = "Create me a sammary"
    response = openai.Completion.create(
        engine="text-davinci-002",
        prompt=f"Context: {context}\nQuestion: {question}\nAnswer:",
        max_tokens=50  
    )
    answer = response.choices[0].text.strip()
    return jsonify({"msg": "Chat created successfully", "sammary": answer}), 201


@app.route("/sammary>", methods=["POST"])
@jwt_required()
@login_required
def create_sammary_text(pdf_id):
    data = request.get_json()
    document = content_collection.find_one({"_id": pdf_id})
    context=data['text']
    question = "Create me a sammary"
    response = openai.Completion.create(
        engine="text-davinci-002",
        prompt=f"Context: {context}\nQuestion: {question}\nAnswer:",
        max_tokens=50  
    )
    answer = response.choices[0].text.strip()
    return jsonify({"msg": "Chat created successfully", "sammary": answer}), 201

@app.route("/chats", methods=["GET"])
@jwt_required()
@login_required
def get_chats():
    user_id = current_user.id
    chats = list(chats_collection.find({'user_id': user_id}))

    for chat in chats:
        chat["_id"] = str(chat["_id"])
    
    return jsonify(chats), 200





# Get a specific chat by ID include chat id and token
@app.route("/chats/<string:chat_id>", methods=["GET"])
@jwt_required()
@login_required
def get_chat(chat_id):
    _id = current_user.id
    chat = chats_collection.find_one({"_id": chat_id, 'user_id': _id})
    if chat:
        chat["_id"] = str(chat["_id"])
        return jsonify({"chat": chat}), 200
    else:
        return jsonify({"msg": "Chat not found"}), 404




#  update a specific chat by ID include chat id and token
@app.route("/chats/<string:chat_id>", methods=["PUT"])
@jwt_required()
@login_required
def update_chat(chat_id):
    _id = current_user.id
    data = request.get_json()
    result = chats_collection.update_one({"_id": chat_id, 'user_id': _id}, {"$set": data})
    if result.modified_count == 1:
        return jsonify({"msg": "Chat updated successfully"}), 200
    else:
        return jsonify({"msg": "Chat not found"}), 404




# delete a specific chat by ID include chat id and token
@app.route("/chats/<string:chat_id>", methods=["DELETE"])
@jwt_required()
@login_required
def delete_chat(chat_id):
    _id = current_user.id
    result = chats_collection.delete_one({"_id": chat_id, 'user_id': _id})
    if result.deleted_count == 1:
        return jsonify({"msg": "Chat deleted successfully"}), 200
    else:
        return jsonify({"msg": "Chat not found"}), 404
    
    
    
    
def extract_text_from_pdf(pdf_file_path):
    try:
        text = ''
        with open(pdf_file_path, 'rb') as pdf_file:
            pdf_reader = PyPDF2.PdfReader(pdf_file)
            pages=pdf_reader.pages
            for page_number in range(len(pages)):
                page = pdf_reader.pages[page_number]
                text += page.extract_text()
            return text
        
    except Exception as e:
        return text
    
def extract_text_from_image(image_path):
    try:
        # Open the image using PIL (Python Imaging Library)
        image = Image.open(image_path)

        # Use pytesseract to perform OCR on the image
        extracted_text = pytesseract.image_to_string(image)

        return extracted_text

    except Exception as e:
        return f"Error: {str(e)}"
    
if __name__ == "__main__":
    serve(app, host="0.0.0.0", port=8080)
