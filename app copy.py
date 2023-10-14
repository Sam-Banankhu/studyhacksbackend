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
