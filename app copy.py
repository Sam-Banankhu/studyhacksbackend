from flask import Flask, jsonify, request, session, redirect, url_for, render_template, send_file
from pymongo import MongoClient
from bson import ObjectId
from waitress import serve
from datetime import datetime, timedelta
from flask_cors import CORS
import pytesseract
from functools import wraps
from PIL import Image
import uuid
import os
revoked_tokens = []
import PyPDF2
from time import sleep
from flask_bcrypt import Bcrypt

import openai
from dotenv import load_dotenv
import jwt
token = "your_jwt_token"  # Replace with your JWT
secret_key = "your_secret_key"
algorithm = "HS256"
exp= datetime.utcnow() + timedelta(hours=2)
load_dotenv()

GPT_API = os.getenv('GPT_API')
backend_url = "https://api-docs-studyhacks-v1.onrender.com"
openai.api_key = GPT_API

app = Flask(__name__)
CORS(app, supports_credentials=True)
app.secret_key ="srevvhhhff"
app.config['UPLOAD_FOLDER'] = os.path.join(os.getcwd(), 'uploads')
bcrypt = Bcrypt(app)


os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

client = MongoClient("mongodb+srv://userxyz:userxyz@cluster0.5be8y.mongodb.net/?retryWrites=true&w=majority")
db = client["studyhacks"]
chats_collection = db["chats"]
users_collection = db["users"]
content_collection = db["documents"]
sammaries_collection = db["summaries"]
import functools
from flask import jsonify


# GETTING DOCUMENTATION 
@app.route('/')
def index():
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], "studyhacks-docs.pdf")
    return send_file(file_path)






# create a chat message
@app.route("/chats/<string:pdf_id>", methods=["POST"])
def create_chat(pdf_id):
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
        print(data)
        question = data["question"]
        document = content_collection.find_one({"_id": pdf_id})
        context = document['extracted_text']
        response = openai.Completion.create(
            engine="text-davinci-002",
            prompt=f"Context: {context}\nQuestion: {question}\nAnswer:",
            max_tokens=50
        )
        _id = str(ObjectId())
        answer = response.choices[0].text.strip()
        answer1 = f'{context[:25]}...'
        answer = response.choices[0].text.strip()
        data['answer'] = answer
        data['title'] = answer1
        data['question'] = question
        data["pdf_id"] = document["_id"]
        data['type_'] = 'pdf'
        data['timestamp'] = str(datetime.now())
        data['_id'] = _id
        data['user_id'] = user_id
        chats_collection.insert_one(data)
        content_collection.update_one(
            {"_id": document["_id"]},
            {"$push": {"chat_ids": _id}})
        return jsonify({"msg": "Chat created successfully", 'chat': data}), 201

# create a sammary from pdf
@app.route("/sammary/<string:pdf_id>", methods=["POST"])
def create_sammary1(pdf_id):
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
        document = content_collection.find_one({"_id": pdf_id})
        context = document['extracted_text']
        question = "Create me a summary"
        _id = str(ObjectId())
        response = openai.Completion.create(
            engine="text-davinci-002",
            prompt=f"Context: {context}\nQuestion: {question}\nAnswer:",
            max_tokens=50
        )
        _id = str(ObjectId())
        
        
        answer = response.choices[0].text.strip()
        answer1 = f'{context[:25]}...'
        time = str(datetime.now())
        data = {
            'sammary': answer,
            "type": "pdf",
            "prompt":context,
            "pdf_id": str(document["_id"]),
            "title": answer1,
            'timestamp': time,
            '_id': _id,
            'user_id': user_id
        }
        sammary = sammaries_collection.insert_one(data)
        response_data = {
            "msg": "Chat created successfully",
            "sammary": answer
        }
        return jsonify(response_data), 201

# saving sammaries 
@app.route("/sammary/save", methods=["POST"])
def save_sammary1():
    
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
        
        data = request.get_json()
        sammary=data["sammary"]
        type=data["type"]
        pdf_id=data["pdf_id"]
        prompt=data["prompt"]
        time = str(datetime.now())
        timestamp= time
        _id = str(ObjectId())
        user_id= res["id"]
        answer1 = f'{prompt[:25]}...'
        data = {
            "title": answer1,
            'sammary': sammary,
            "type_": type,
            "pdf_id": pdf_id,
            'timestamp': timestamp,
            '_id': _id,
            'user_id': user_id,
            "prompt":prompt
        }
        
        sammary = sammaries_collection.insert_one(data)
        response_data = {
            "msg": "sammary created successfully"
        }
        return jsonify(response_data), 201

# create sammaries from text data
@app.route("/sammary", methods=["POST"])
def create_sammary():
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
        text = data["text"]
        context = text
        question = "Create me a summary"
        _id = str(ObjectId())
        response = openai.Completion.create(
            engine="text-davinci-002",
            prompt=f"Context: {context}\nQuestion: {question}\nAnswer:",
            max_tokens=50
        )
        answer = response.choices[0].text.strip()
        answer1 = f'{context[:25]}...'
        time = str(datetime.now())
        data = {
            'sammary': answer,
            "pdf_id": "",
            "title": answer1,
            "type_": "text",
            "prompt":text,
            'timestamp': time,
            '_id': _id,
            'user_id': user_id,
    
        }
       
            
        # sammary = sammaries_collection.insert_one(data)
        response_data = {
            "msg": "Summary created successfully",
            "sammary": answer,"prompt":text
        }
        return jsonify(response_data), 201

# get all chats
@app.route("/chats", methods=["GET"])
def get_all_chats():
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
        chats = chats_collection.find({"user_id":res["id"]})
        chat_list = [chat for chat in chats]
        return jsonify(chat_list), 200

# getting all sammaries
@app.route("/sammary", methods=["GET"])
def get_summaries():
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
        print(res)
        sammaries = list(sammaries_collection.find({"user_id":res["id"]}))
        # sammary_list = []
        # for sammary in sammaries:
        #     formatted_sammary = {
        #         "type": sammary["type"],
        #         "sammary_id": str(sammary["_id"]),
        #         "sammary": sammary["sammary"],
        #         "pdf_id": sammary["pdf_id"],
        #         "timestamp": sammary["timestamp"],
        #         "user_id": sammary["user_id"]
        #     }
        #     sammary_list.append(formatted_sammary)
        response_data = {
            "summaries": sammaries
        }
        return jsonify(response_data), 200
from flask import request

# delete one sammary
@app.route("/sammary/<summary_id>", methods=["DELETE"])
def delete_summary(sammary_id):
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
        # Add code here to delete a specific summary by summary_id
        # You can use 
        sammaries_collection.delete_one({"_id": sammary_id})
        # Return an appropriate response based on the success or failure of the deletion
        return jsonify({"message": "Sammary deleted successfully"}), 200

@app.route("/sammaries/pdfs/<string:pdf_id>", methods=["GET"])
def get_summaries_by_pdf_id(pdf_id):
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
        chats = list(sammaries_collection.find({"pdf_id": pdf_id}))
        return jsonify(chats), 200

# getting all chats
@app.route("/chats", methods=["GET"])
def get_chats():
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
        user_id =res["id"]
        chats = list(chats_collection.find({'user_id': user_id}))
        return jsonify(chats), 200

# getting all chats under pdf
@app.route("/chats/pdfs/<string:pdf_id>", methods=["GET"])
def get_chats_by_pdf_id(pdf_id):
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
        chats = list(chats_collection.find({"pdf_id": pdf_id}))
        return jsonify(chats), 200

# getting specific chat
@app.route("/chats/<string:chat_id>", methods=["GET"])
def get_chat(chat_id):
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
        _id=res["id"]
        chat = chats_collection.find_one({"_id": chat_id, 'user_id': _id})
        if chat:
            chat["_id"] = str(chat["_id"])
            return jsonify({"chat": chat}), 200
        else:
            return jsonify({"msg": "Chat not found"}), 404

@app.route("/chats/<string:chat_id>", methods=["PUT"])
def update_chat(chat_id):
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
        _id = res["id"]
        data = request.get_json()
        result = chats_collection.update_one({"_id": chat_id, 'user_id': _id}, {"$set": data})
        if result.modified_count == 1:
            return jsonify({"msg": "Chat updated successfully"}), 200
        else:
            return jsonify({"msg": "Chat not found"}), 404
# delete chat
@app.route("/chats/<string:chat_id>", methods=["DELETE"])
def delete_chat(chat_id):
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
        _id = res["id"]
        result = chats_collection.delete_one({"_id": chat_id, 'user_id': _id})
        if result.deleted_count == 1:
            return jsonify({"msg": "Chat deleted successfully"}), 200
        else:
            return jsonify({"msg": "Chat not found"}), 404

def authorise_request(request1):
    token = request1.headers.get('Authorization')
    if token:
        if(token in revoked_tokens):
            return 'revoked'
        # You can perform additional checks on the header here if needed
        try:
            decoded_payload = jwt.decode(token, secret_key, algorithms=[algorithm])
            return decoded_payload
        except jwt.ExpiredSignatureError:
            return "expired"
        except jwt.InvalidTokenError:
            return "invalid"
    else:
        return "not found"
def revoke_token(token):
    revoked_tokens1=revoked_tokens
    revoked_tokens.append(token)
    if len(revoked_tokens1)<len(revoked_tokens):
        print()
        return "revoked"
if __name__ == "__main__":
    serve(app, host="0.0.0.0", port=8085)
