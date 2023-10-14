from app import app, jsonify, request, openai, ObjectId, datetime
from app.models import chats_collection, content_collection
from auth import *


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


# update chats
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
