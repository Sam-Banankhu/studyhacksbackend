from app import app, Flask, request, session, redirect, jsonify, ObjectId, openai, datetime, timedelta, time
from auth import *
from app.models import *

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
