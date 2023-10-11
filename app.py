
from flask import Flask, jsonify, request, session, redirect, url_for, render_template,send_file,send_from_directory
from pymongo import MongoClient
from flask import Flask, session
from bson import ObjectId
import datetime
from waitress import serve
from datetime import timedelta
from flask_cors import CORS
# 
import pytesseract
from functools import wraps
from PIL import Image
from flask_jwt_extended import JWTManager, jwt_required, create_access_token, get_jwt_identity
import uuid
import os
import PyPDF2
from flask_bcrypt import Bcrypt
from flask_login import LoginManager, UserMixin, login_user, logout_user, current_user

# all sammaries
# download 1 pdf
# all the chats
# from dotenv import load_dotenv 
# # Load environment variables from .env file
# load_dotenv()
id
import openai
# Set your OpenAI API key
from dotenv import load_dotenv

load_dotenv()

GPT_API= os.getenv('GPT_API')

backend_url = "https://api-docs-studyhacks.onrender.com"
# Initialize the OpenAI API client
openai.api_key = GPT_API




app = Flask(__name__)
CORS(app,supports_credentials=True)
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
sammaries_collection = db["summaries"]

class User(UserMixin):
    def __init__(self, user):
        self.user = user
    def get_id(self):
        return str(self.user['_id']) 

# Initialize Flask-Login and LoginManager
login_manager = LoginManager()
login_manager.init_app(app)



# User loader function
@login_manager.user_loader
def load_user(_id):
    print(_id)
    user = users_collection.find_one({'_id': _id})
    if user:
        return User(user['_id'])
    else:
        return None

# Docomention
@app.route('/')
def index():
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], "studyhacks-docs.pdf")
    return send_file(file_path)
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
    gender=data.get("gender")
    institution=data.get("institution")
    mobile=data.get("mobile")
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


    user_obj = User(user)
    login_user(user_obj)
    access_token = create_access_token(identity=user['_id'],expires_delta=expires_in)
    return jsonify({'msg': 'Login successful', 'access_token': access_token, 'user': user}), 200


# AUTHENTICATION


#  getting all users of the system . attach token in the request header# 
@app.route('/users', methods=['GET'])
@jwt_required()
def get_all_users():
    headers = request.headers
    for key, value in headers.items():
        print(f"{key}: {value}")
    data = request.get_json()
    print(data)
    users = list(users_collection.find())
    for user in users:
        user['_id'] = str(user['_id'])
    
    return jsonify(users), 200


@app.route('/users/<string:user_id>', methods=['GET'])
# 
@jwt_required()
def get_single_user(user_id):
    try:
        # Convert the user_id to an ObjectId
        object_id = user_id
    except Exception as e:
        return jsonify({"message": "Invalid user_id format"}), 400

    # Query the MongoDB collection for the user with the specified ObjectId
    user = users_collection.find_one({"_id": object_id})

    if user is None:
        return jsonify({"message": "User not found"}), 404

    # Convert the ObjectId to a string for the response
    user['_id'] = str(user['_id'])

    return jsonify(user), 200



# User logout
#attach token in the request header# 
# no infor provided .. it will get user id from server session
@app.route('/logout',methods=['POST']) 
@jwt_required()
# 
def logout():
    logout_user()
    return jsonify({'msg': 'Logged out successfully'}), 200

# FINDALLS

@app.route('/users/<string:_id>', methods=['GET'])
# 
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
# 
def change_password():
    data = request.get_json()
    current_password = data.get('current_password')
    new_password = data.get('new_password')

    user = users_collection.find_one({'_id': current_user.get_id()})

    if not user or not bcrypt.check_password_hash(user['password'], current_password):
        return jsonify({'msg': 'Current password is incorrect'}), 401
    
    hashed_new_password = bcrypt.generate_password_hash(new_password).decode('utf-8')

    users_collection.update_one({'_id': current_user.get_id()}, {'$set': {'password': hashed_new_password}})

    return jsonify({'msg': 'Password updated successfully'}), 200





# PDF PROCESSING ENDpOINTS

# uploading a pdf file to the server append the file and token in the header
@app.route('/pdfs', methods=['POST'])
@jwt_required()
# 
def upload_pdf():
    print(request)
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
    data['user_id']=current_user.get_id()
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
# 
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
    data['user_id']=current_user.get_id()
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
def upload_text():
    data = request.get_json()
    text=data['text']
    unique_id = uuid.uuid4()
    _id = str(ObjectId())
    data = {}
    data['user_id']=current_user.get_id()
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
# 
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
def create_chat(pdf_id):
    print(current_user.get_id())
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
    data["pdf_id"]= document["_id"]
    data['type_']='pdf'
    data['timestamp']=str(datetime.datetime.now())
    data['_id']=_id
    data['user_id'] = current_user.get_id() 
    chats_collection.insert_one(data)
    content_collection.update_one(
    {"_id": document["_id"]},
    {"$push": {"chat_ids": _id}})
    return jsonify({"msg": "Chat created successfully",'chat':data}), 201


# @app.route("/sammary/<string:pdf_id>", methods=["GET"])
# @jwt_required()
# def create_sammary(pdf_id):
#     # _id : str(ObjectId())
#     document = content_collection.find_one({"_id": pdf_id})
#     context=document['extracted_text']
#     question = "Create me a sammary"
#     response = openai.Completion.create(
#         engine="text-davinci-002",
#         prompt=f"Context: {context}\nQuestion: {question}\nAnswer:",
#         max_tokens=50  
#     )
#     answer = response.choices[0].text.strip()
   
#     data={
#     'sammary':answer,
#     "pdf_id":str(document["_id"]),
#     'timestamp':str(datetime.datetime.now()),
#     '_id':str(ObjectId()),
#     'user_id' : str(current_user.get_id())
#     }
#     sammary=sammaries_collection.insert_one(data)
#     return jsonify(sammary), 201

@app.route("/sammary/<string:pdf_id>", methods=["POST"])
@jwt_required()
def create_sammary1(pdf_id):
    # Retrieve the document from the content_collection
    document = content_collection.find_one({"_id": pdf_id})
    context = document['extracted_text']
    question = "Create me a summary"
    
    # Generate a new ObjectId
    _id = str(ObjectId())

    # Use OpenAI to generate the summary
    response = openai.Completion.create(
        engine="text-davinci-002",
        prompt=f"Context: {context}\nQuestion: {question}\nAnswer:",
        max_tokens=50  
    )
    answer = response.choices[0].text.strip()
    time=str(datetime.datetime.now())
    # Create a dictionary with the summary data
    data = {
        'sammary': answer,
        "type": "pdf",
        "pdf_id": str(document["_id"]),
        'timestamp':time ,
        '_id': _id,
        'user_id': str(current_user.get_id())
    }

    # Insert the data into the sammaries_collection
    sammary = sammaries_collection.insert_one(data)

    # Create a JSON response with the inserted data
    response_data = {
        "msg": "Chat created successfully",
        "sammary": answer
        
    }

    return jsonify(response_data), 201

@app.route("/sammary", methods=["POST"])
@jwt_required()
def create_sammary():
    data = request.get_json()
    text=data["text"]
    # Retrieve the document from the content_collection
    context = text
    question = "Create me a summary"
    # Generate a new ObjectId
    _id = str(ObjectId())
    # Use OpenAI to generate the summary
    response = openai.Completion.create(
        engine="text-davinci-002",
        prompt=f"Context: {context}\nQuestion: {question}\nAnswer:",
        max_tokens=50  
    )
    answer = response.choices[0].text.strip()
    time=str(datetime.datetime.now())
    # Create a dictionary with the summary data
    data = {
        'sammary': answer,
        "pdf_id": "",
        "type": "pdf",
        'timestamp':time ,
        '_id': _id,
        'user_id': str(current_user.get_id())
    }

    # Insert the data into the sammaries_collection
    sammary = sammaries_collection.insert_one(data)

    # Create a JSON response with the inserted data
    response_data = {
        "msg": "Summary created successfully",
        "sammary": answer,
        # "pdf_id": "",
        # "type": "text",
        # "timestamp": time,
        # "user_id": str(current_user.get_id())
    }

    return jsonify(response_data), 201

@app.route("/chats", methods=["GET"])
@jwt_required()  # Assuming you are using JWT authentication
def get_all_chats():
    # Retrieve all documents (chats) from the chats_collection
    chats = chats_collection.find({})

    # Convert the retrieved documents to a list of dictionaries
    chat_list = [chat for chat in chats]

    # Return the list of chats as a JSON response
    return jsonify(chat_list), 200 


@app.route("/sammary", methods=["GET"])
def get_summaries():
    # Retrieve all summaries from the sammaries_collection
    sammaries = list(sammaries_collection.find())

    # Prepare a list to store the summary data
    sammary_list = []

    # Iterate through the retrieved summaries and format them
    for sammary in sammaries:
        formatted_sammary = {
            "type": sammary["type"],
            "sammary_id": str(sammary["_id"]),
            "sammary": sammary["sammary"],
            "pdf_id": sammary["pdf_id"],
            "timestamp": sammary["timestamp"],
            "user_id": sammary["user_id"]
        }
        sammary_list.append(formatted_sammary)

    # Create a JSON response with the list of summaries
    response_data = {
        "summaries": sammary_list
    }

    return jsonify(response_data), 200



@app.route("/sammaries/pdfs/<string:pdf_id>", methods=["GET"])
@jwt_required()
def get_summaries_by_pdf_id(pdf_id):
    # Find summaries that match the provided PDF ID
    sammaries = sammaries_collection.find({"pdf_id": pdf_id})

    # Prepare a list to store the summary data
    sammary_list = []

    # Iterate through the retrieved summaries and format them
    for sammary in sammaries:
        formatted_sammary = {
            "sammary_id": str(sammary["_id"]),
            "sammary": sammary["sammary"],
            "pdf_id": sammary["pdf_id"],
            "timestamp": sammary["timestamp"],
            "user_id": sammary["user_id"]
        }
        sammary_list.append(formatted_sammary)

    # Create a JSON response with the list of summaries
    response_data = {
        "sammaries": sammary_list
    }

    return jsonify(response_data), 200

# @app.route("/sammary", methods=["POST"])
# @jwt_required()
# def create_sammary_text():
#     data = request.get_json()
#     context=data['text']
#     question = "Create me a sammary"
#     response = openai.Completion.create(
#         engine="text-davinci-002",
#         prompt=f"Context: {context}\nQuestion: {question}\nAnswer:",
#         max_tokens=50  
#     )
    
#     answer = response.choices[0].text.strip()
#     return jsonify({"msg": "Chat created successfully", "sammary": answer}), 201

@app.route("/chats", methods=["GET"])
@jwt_required()
def get_chats():
    user_id = current_user.get_id()
    chats = list(chats_collection.find({'user_id': user_id}))

    for chat in chats:
        chat["_id"] = str(chat["_id"])
    
    return jsonify(chats), 200



@app.route("/chats/pdfs/<string:pdf_id>", methods=["GET"])
@jwt_required()
def get_chats_by_pdf_id(pdf_id):
    # Query the chats collection to find chats associated with the specified PDF ID
    chats = list(chats_collection.find({"pdf_id": pdf_id}))

    # Format the chats, converting ObjectId to strings for JSON serialization
    formatted_chats = []
    for chat in chats:
        chat["_id"] = str(chat["_id"])
        formatted_chats.append(chat)

    # Return the list of chats as a JSON response
    return jsonify(formatted_chats), 200


# Get a specific chat by ID include chat id and token
@app.route("/chats/<string:chat_id>", methods=["GET"])
@jwt_required()
def get_chat(chat_id):
    _id = current_user.get_id()
    chat = chats_collection.find_one({"_id": chat_id, 'user_id': _id})
    if chat:
        chat["_id"] = str(chat["_id"])
        return jsonify({"chat": chat}), 200
    else:
        return jsonify({"msg": "Chat not found"}), 404




#  update a specific chat by ID include chat id and token
@app.route("/chats/<string:chat_id>", methods=["PUT"])
@jwt_required()
def update_chat(chat_id):
    _id = current_user.get_id()
    data = request.get_json()
    result = chats_collection.update_one({"_id": chat_id, 'user_id': _id}, {"$set": data})
    if result.modified_count == 1:
        return jsonify({"msg": "Chat updated successfully"}), 200
    else:
        return jsonify({"msg": "Chat not found"}), 404




# delete a specific chat by ID include chat id and token
@app.route("/chats/<string:chat_id>", methods=["DELETE"])
@jwt_required()
def delete_chat(chat_id):
    _id = current_user.get_id()
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
