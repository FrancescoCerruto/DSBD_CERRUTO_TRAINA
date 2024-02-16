import jwt
from functools import wraps
from flask import request
from .Config import Config


# funzione che dal token autentica l'utente
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None

        # c'è l'header di autenticazione?
        if "Authorization" in request.headers:
            # recupero il token
            token = request.headers["Authorization"].split(" ")[1]

        # non c'è l'header di autenticazione
        if not token:
            return {
                "message": "Authentication Token is missing!",
                "data": None,
                "error": "Unauthorized"
            }, 401

        # c'è l'header di autenticazione
        try:
            data = jwt.decode(jwt=token, key=Config.TOKEN_KEY, algorithms=[Config.TOKEN_ALGORITHM])
        except Exception as e:
            return {"error": str(e)}, 500
        return f(data['user_id'], data['user_email'], *args, **kwargs)
    return decorated
