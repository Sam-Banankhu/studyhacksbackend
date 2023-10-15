from app import app, send_file
import os

from app.routes import *
# import chats, files, summeries, users

from app.routes.users import *
from app.routes.files import *
from app.routes.summeries import *
from app.routes.chats import *

# GETTING DOCUMENTATION 
@app.route('/')
def index():
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], "studyhacks-docs.pdf")
    return send_file(file_path)

