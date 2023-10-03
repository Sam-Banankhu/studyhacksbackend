from flask import Flask, jsonify, request, session, redirect, url_for, render_template,send_file,send_from_directory
from pymongo import MongoClient
from bson import ObjectId
import datetime
from waitress import serve
from datetime import timedelta
from flask_jwt_extended import JWTManager, jwt_required, create_access_token, get_jwt_identity
import uuid
import os
import PyPDF2
from flask_bcrypt import Bcrypt
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user

import openai
# Set your OpenAI API key
api_key = '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'

# Initialize the OpenAI API client
openai.api_key = api_key



app = Flask(__name__)
app.secret_key = "HSHSHSHSSHHS"
app.config['UPLOAD_FOLDER'] = os.path.join(os.getcwd(), 'uploads')
# Initialize Flask-Bcrypt
bcrypt = Bcrypt(app)
jwt = JWTManager(app)
expires_in = timedelta(minutes=30)

# Initialize the MongoDB client and database
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)


client = MongoClient("mongodb+srv://userxyz:userxyz@cluster0.5be8y.mongodb.net/?retryWrites=true&w=majority")
db = client["studyhacks"]
collection = db["chats"]
users_collection = db["users"]
documents = db["documents"]
# db.command({
#   "collMod": "users",
#   "validator": {
#     "$jsonSchema": {
#       "type": "object",
#       "required": ["email","name","password"],
#       "properties": {
#         "email": {
#           "type": "string"
#         },
#         "password": {
#           "type": "string"
#         },
#         "role": {
#           "type": "string"
#         },
#         "profile_complete": {
#           "type": "boolean"
#         },
#         "profile_photo": {
#           "type": "string"
#         }
#       }
#     }
#   }
# })

# db.command({
#   "collMod": "chats",
#   "validator": {
#     "$jsonSchema": {
#       "type": "object",
#       "required": ["user_id","pdf_id","content","timestamp"],
#       "properties": {
#         "user_id": {
#           "type": "string"
#         },
#         "pdf_id": {
#           "type": "string"
#         },
#         "content": {
#           "type": "string"
#         },
#         "timestamp": {
#           "type": "boolean"
#         }
#       }
#     }
#   }
# })

# db.command({
#   "collMod": "documents",
#   "validator": {
#     "$jsonSchema": {
#       "type": "object",
#       "required": ["user_id","pdf_name","chat_ids","timestamp",'extracted_text'],
#       "properties": {
#         "user_id": {
#           "type": "string"
#         },
#         "pdf_name": {
#           "type": "string"
#         },
#         "chat_ids": {
#           "type": "list"
#         },
#         "timestamp": {
#           "type": "string"
#         },
#         'extracted_text': {
#           "type": "string"
#         },
#       }
#     }
#   }
# })
# db.command({
#   "collMod": "collection",
#   "validator": {
#     "$jsonSchema": {
#       "type": "object",
#       "required": ["user_id","pdf_id","content","timestamp"],
#       "properties": {
#         "user_id": {
#           "type": "string"
#         },
#         "pdf_id": {
#           "type": "string"
#         },
#         "content": {
#           "type": "string"
#         },
#         "timestamp": {
#           "type": "string"
#         }
#       }
#     }
#   }
# })

# Define a User class that inherits from UserMixin
class User(UserMixin):
    def __init__(self, user_id):
        self.id = user_id

# Initialize Flask-Login and LoginManager
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"


# User loader function
@login_manager.user_loader
def load_user(user_id):
    user = users_collection.find_one({'user_id': user_id})
    if user:
        return User(user['user_id'])
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
    profile_photo = data.get('profile_photo')
   
    password = data.get('password')

    if not email or not password:
        return jsonify({'msg': 'Email and password are required'}), 400

    # Check if the user already exists
    existing_user = users_collection.find_one({'email': email})
    if existing_user:
        return jsonify({'msg': 'User already exists'}), 400

    # Generate a unique user ID
    user_id = str(ObjectId())


    hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')

    user = {
        'user_id': user_id,
        "name":name,
        'email': email,
        "role": role,
        'password': hashed_password,
        "profile_complete":profile_complete,
        "profile_photo":profile_photo
        
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


    user_obj = User(user['user_id'])
    login_user(user_obj)
    access_token = create_access_token(identity=user['user_id'],expires_delta=expires_in)

    user={
        "user_id":user['user_id'],
        "profile_complete":user["profile_complete"],
         "profile_photo":user[ "profile_photo"],
        "email":user['email'],
      
    }
    return jsonify({'msg': 'Login successful', 'access_token': access_token, 'user': user}), 200


 
#  getting all users of the system . attach token in the request header# 
@app.route('/users', methods=['GET'])
@jwt_required()
def get_all_users():
    users = list(users_collection.find({}, {'_id': False}))
    for user in users:
        user['user_id'] = str(user['user_id'])
    
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



@app.route('/users/<string:user_id>', methods=['GET'])
@jwt_required()
def get_user(user_id):
    user = users_collection.find_one({'user_id': user_id}, {'_id': False})

    if user:
        user['user_id'] = str(user['user_id'])
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

    user = users_collection.find_one({'user_id': current_user.id})

    if not user or not bcrypt.check_password_hash(user['password'], current_password):
        return jsonify({'msg': 'Current password is incorrect'}), 401
    
    hashed_new_password = bcrypt.generate_password_hash(new_password).decode('utf-8')

    users_collection.update_one({'user_id': current_user.id}, {'$set': {'password': hashed_new_password}})

    return jsonify({'msg': 'Password updated successfully'}), 200





# PDF PROCESSING ENDpOINTS

# uploading a pdf file to the server append the file and token in the header
@app.route('/pdfs', methods=['POST'])
@jwt_required()
@login_required
def upload_file():
    if 'file' not in request.files:
        return "No file part", 400
    
    file = request.files['file']
    
    if file.filename == '':
        return "No selected file", 400
    
    unique_id = uuid.uuid4()
    pdf_loc=os.path.join(app.config['UPLOAD_FOLDER'],  str(unique_id)+".pdf")
    file.save(pdf_loc)
    extracted_text = extract_text_from_pdf(pdf_loc)
    data = {}
    data['user_id']=current_user.id
    data["extracted_text"]=True
    data["extracted_text1"]=extracted_text
    data["pdf_name"]=str(unique_id)+".pdf"
    data["chat_ids"]=[]
    document = documents.insert_one(data)
    return jsonify({"msg": "Document processed successfully"}),201


# getting all pdf files from server append  token in the header
@app.route('/pdfs', methods=['GET'])
@jwt_required()
@login_required
def get_files():
    documents_list = list(documents.find())
    files_list = []
    for document in documents_list:
        document["_id"] = str(document["_id"])
        
        files_list.append(document)
    
    return jsonify(files_list), 200


# download a pdf file from server append  token in the header and pdf id
@app.route('/pdfs/download/<pdf_id>', methods=['GET'])
@jwt_required()
@login_required
def download_file(pdf_id):
    document = documents.find_one({"_id": ObjectId(pdf_id)})
    
    if document:
        pdf_name = document["pdf_name"]
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
    document = documents.find_one({"_id": ObjectId(pdf_id)})
    context=document['extracted_text1']
    response = openai.Completion.create(
        engine="text-davinci-002",
        prompt=f"Context: {context}\nQuestion: {question}\nAnswer:",
        max_tokens=50  
    )
    answer = response.choices[0].text.strip()
    data['content']=answer
    data['answer']=answer
    data['question']=question
    data['timestamp']=str(datetime.datetime.now())
    data['pdf_id']=pdf_id
    data['created_at'] = str(datetime.datetime.now())
    
    data['user_id'] = current_user.id  
    chat_id = collection.insert_one(data).inserted_id
    return jsonify({"msg": "Chat created successfully",'question':question, "answer":answer,'pdf_id':pdf_id}), 201


@app.route("/sammary/<string:pdf_id>", methods=["GET"])
@jwt_required()
@login_required
def create_sammary(pdf_id):
    document = documents.find_one({"_id": ObjectId(pdf_id)})
    context=document['extracted_text1']
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
    chats = list(collection.find({'user_id': user_id}))

    for chat in chats:
        chat["_id"] = str(chat["_id"])
    
    return jsonify(chats), 200





# Get a specific chat by ID include chat id and token
@app.route("/chats/<string:chat_id>", methods=["GET"])
@jwt_required()
@login_required
def get_chat(chat_id):
    user_id = current_user.id
    chat = collection.find_one({"_id": ObjectId(chat_id), 'user_id': user_id})
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
    user_id = current_user.id
    data = request.get_json()
    result = collection.update_one({"_id": ObjectId(chat_id), 'user_id': user_id}, {"$set": data})
    if result.modified_count == 1:
        return jsonify({"msg": "Chat updated successfully"}), 200
    else:
        return jsonify({"msg": "Chat not found"}), 404




# delete a specific chat by ID include chat id and token
@app.route("/chats/<string:chat_id>", methods=["DELETE"])
@jwt_required()
@login_required
def delete_chat(chat_id):
    user_id = current_user.id
    result = collection.delete_one({"_id": ObjectId(chat_id), 'user_id': user_id})
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
if __name__ == "__main__":
   serve(app, host="0.0.0.0", port=8080)
