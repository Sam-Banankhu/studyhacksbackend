from app import jwt, revoked_tokens, secret_key, algorithm


def get_token(id):
    paylod={
     "id": id,
    }
    token = jwt.encode(paylod, secret_key, algorithm=algorithm)
    return token

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