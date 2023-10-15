from flask import Flask, jsonify, request, session, redirect, url_for, render_template, send_file
# from pymongo import MongoClient
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

from app import models
from app.routes import *

