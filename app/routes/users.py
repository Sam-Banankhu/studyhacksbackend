from app import app, request, jsonify, ObjectId, bcrypt
from datetime import datetime
from app.routes.auth import get_token, authorise_request, jwt, revoke_token
from app.models import *



# REGISTERATING A USER
@app.route('/register', methods=['POST'])
def register_user():
    data = request.get_json()
    email = data.get('email')
    name = data.get('name')
    role = data.get('role')
    profile_complete = data.get('profile_complete')
    profile_picture = data.get("profile_picture")
    password = data.get('password')
    gender = data.get("gender")
    institution = data.get("institution")
    mobile = data.get("mobile")
    country = data.get("country")
    data['timestamp'] = str(datetime.now())
    if not email or not password:
        return jsonify({'msg': 'Email and password are required'}), 400

    existing_user = users_collection.find_one({'email': email})
    if existing_user:
        return jsonify({'msg': 'User already exists'}), 400

    _id = str(ObjectId())

    hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')

    user = {
        '_id': _id,
        "name": name,
        "mobile": mobile,
        'email': email,
        "role": role,
        'password': hashed_password,
        "profile_complete": profile_complete,
        "profile_picture": profile_picture,
        "country": country,
        "gender": gender,
        "institution": institution
    }

    users_collection.insert_one(user)

    return jsonify({'msg': 'User registered successfully'}), 201


# LOGINING IN A USER
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
    token = get_token(user["_id"])
    return jsonify({'msg': 'Login successful', 'access_token': token, 'user': user}), 200


# GETTING USERS
@app.route('/users', methods=['GET'])
def get_all_users():
    res = authorise_request(request)
    if(res == "expired"):
        return jsonify({"message": "Token expired"}), 403
    elif (res == "invalid"):
        return jsonify({"message": "Token is invalid"}), 403
    elif(res == "not found"):
        return jsonify({"message": "Token not found"}), 403
    elif(res == "revoked"):
        return jsonify({"message": "Token revoked"}), 403
    else:
        users = list(users_collection.find())
        for user in users:
            user['_id'] = str(user['_id'])
        return jsonify(users), 200


# GETTING A USER
@app.route('/users/<string:user_id>', methods=['GET'])
def get_single_user(user_id):
    res = authorise_request(request)
    if(res == "expired"):
        return jsonify({"message": "Token expired"}), 403
    elif (res == "invalid"):
        return jsonify({"message": "Token is invalid"}), 403
    elif(res == "not found"):
        return jsonify({"message": "Token not found"}), 403
    else:
        user_id = res["id"]
        user = users_collection.find_one({"_id": user_id})

        if user is None:
            return jsonify({"message": "User not found"}), 404

        user['_id'] = str(user['_id'])

        return jsonify(user), 200


# LOGGING OUT USER
@app.route('/logout', methods=['POST'])
def logout():
    res = authorise_request(request)
    if(res == "expired"):
        return jsonify({"message": "Token expired"}), 403
    elif (res == "invalid"):
        return jsonify({"message": "Token is invalid"}), 403
    elif(res == "not found"):
        return jsonify({"message": "Token not found"}), 403
    else:
        if(revoke_token(res) == "revoked"):
            return jsonify({'msg': 'Logged out successfully'}), 200
        else:
            return jsonify({'msg': 'Logged out not successful'}), 200


# CHANGE pASWORD
@app.route('/change_password', methods=['POST'])
def change_password():
    res = authorise_request(request)
    if(res == "expired"):
        return jsonify({"message": "Token expired"}), 403
    elif (res == "invalid"):
        return jsonify({"message": "Token is invalid"}), 403
    elif(res == "not found"):
        return jsonify({"message": "Token not found"}), 403
    elif(res == "revoked"):
        return jsonify({"message": "Token is revoked"}), 403
    else:
        user_id = res["id"]
        data = request.get_json()
        current_password = data.get('current_password')
        new_password = data.get('new_password')
        user = users_collection.find_one({'_id': user_id})

        if not user or not bcrypt.check_password_hash(user['password'], current_password):
            return jsonify({'msg': 'Current password is incorrect'}), 401

        hashed_new_password = bcrypt.generate_password_hash(
            new_password).decode('utf-8')

        users_collection.update_one(
            {'_id': id}, {'$set': {'password': hashed_new_password}})

        return jsonify({'msg': 'Password updated successfully'}), 200
