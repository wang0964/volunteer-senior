import datetime
from flask import Flask, request, jsonify, session
from pymongo import MongoClient, ASCENDING
from werkzeug.security import generate_password_hash, check_password_hash
from pymongo.errors import DuplicateKeyError
import os

# --- 基础配置 ---
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/buddylink")
SECRET_KEY = os.getenv("FLASK_SECRET", "dev-secret-change-me")

app = Flask(__name__)
app.secret_key = SECRET_KEY


app.config.update(
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
    SESSION_COOKIE_SECURE=False  # 部署到 HTTPS 后改 True
)


BIND_HOST = "127.0.0.1"
BIND_PORT = 5000

# --- Mongo ---
mongo = MongoClient(MONGO_URI)
db = mongo.get_default_database()  
users = db['users']
seniors = db['seniors']
volunteers=db['volunteers']

users.create_index([("email", ASCENDING)], unique=True)



def normalize_email(email):
    return (email or "").strip().lower()


def current_user():
    uid = session.get("uid")
    email = session.get("email")
    if not uid or not email:
        return None
    return {"id": uid, "email": email}


# --- Routes ---



@app.route('/login', methods=['POST'])
def api_login():
    data = request.get_json(silent=True) or {}
    email = normalize_email(data.get("email"))
    password = data.get("password") or ""

    if not email or not password:
        return jsonify(success=False, message="Email and password are required"), 400

    print(f'[email]: {email} , [password]: {password}')


    user = users.find_one({"email": email},
                            {
                                "_id": 1,
                                "email": 1,
                                "password_hash": 1,
                                "type": 1
                            }
                          )
    if not user or not check_password_hash(user.get("password_hash", ""), password):
        return jsonify(success=False, message="Invalid email or password"), 401


    session["uid"] = str(user["_id"])
    session["email"] = user["email"]

    # return jsonify(success=True, data={"email": user["email"]})
    return jsonify(success=True, data={"role": user.get("type"), "email": user["email"]})


@app.post("/logout")
def api_logout():
    session.clear()
    return jsonify(success=True)


@app.get("/me")
def api_me():
    user = current_user()
    if not user:
        return jsonify(success=False, message="Unauthorized"), 401
    return jsonify(success=True, data=user)


@app.get("/health")
def api_health():
    return jsonify(ok=True)

@app.route('/register/senior', methods=['POST'])
def api_register_senior():
    print('enter')
    data = request.get_json(silent=True) 
    print(data)

    # # ---- Extract & normalize fields
    firstname    = (data.get("firstname") or "").strip()
    lastname     = (data.get("lastname") or "").strip()
    age_raw      = (data.get("age") or "").strip() if data.get("age") is not None else ""
    phone        = (data.get("phone") or "").strip()
    email        = normalize_email(data.get("email"))
    city         = (data.get("city") or "").strip()
    address      = (data.get("address") or "").strip()
    contact_pref = (data.get("contactPref") or "").strip()
    language     = (data.get("language") or "").strip()
    notes        = (data.get("notes") or "").strip()
    password     = data.get("password") or ""
    re_password  = data.get("re_password") or ""  

    # # ---- Basic validation
    if not email or not password:
        return jsonify(success=False, message="Email and password are required"), 401
    
    if password != re_password:
        return jsonify(success=False, message="Passwords do not match"), 402

    if len(password)<8:
        return jsonify(success=False, message="Password must have 8 letters at least"), 403

    try:
        age = int(age_raw)
    except ValueError:
        return jsonify(success=False, message="Age must be a number"), 404
    
    existing = users.find_one({"email": email}, {"_id": 1})
    if existing:
        return jsonify(success=False, message="Email already registered"), 409


    # # ---- Build document to insert
    senior_doc = {
        "firstname": firstname,
        "lastname": lastname,
        "age": age,
        "phone": phone,
        "city": city,
        "address": address,
        "contactPref": contact_pref,
        "language": language,
        "notes": notes,
        "updated_at": datetime.datetime.now(datetime.timezone.utc)
    }

    user_doc = {
        "email": email,
        "password_hash": generate_password_hash(password),
        "created_at": datetime.datetime.now(datetime.timezone.utc),
        "type": "senior"
    }

    senior_id=None
    try:
        senior_id = seniors.insert_one(senior_doc).inserted_id
        user_doc["senior_id"] = senior_id
        users.insert_one(user_doc)
    except DuplicateKeyError:
        if senior_id is not None:
            try:
                seniors.delete_one({"_id": senior_id})
            except Exception:
                pass 
        return jsonify(success=False, message="Email already registered"), 409
    except Exception as e:
        if senior_id is not None:
            try:
                seniors.delete_one({"_id": senior_id})
            except Exception:
                pass
        return jsonify(success=False, message=f"Failed to register: {e}"), 500

    return jsonify(success=True, data={"type":"senior", "seniorId": str(senior_id)})


@app.route('/register/volunteer', methods=['POST'])
def api_register_volunteer():
    print('enter')
    data = request.get_json(silent=True) 
    print(data)

    # # ---- Extract & normalize fields
    firstname    = (data.get("firstname") or "").strip()
    lastname     = (data.get("lastname") or "").strip()
    gender       = (data.get("gender") or "").strip()
    phone        = (data.get("phone") or "").strip()
    email        = normalize_email(data.get("email"))
    city         = (data.get("city") or "").strip()
    address      = (data.get("address") or "").strip()
    background   = (data.get("background") or "").strip()
    language     = data.get("language") or []
    availabilities = data.get("availability") or []
    skills       = data.get("skills") or []
    password     = data.get("password") or ""
    re_password  = data.get("re_password") or ""  
    self_description = (data.get("self_description") or "").strip()

    # # ---- Basic validation
    if not email or not password:
        return jsonify(success=False, message="Email and password are required"), 401
    
    if password != re_password:
        return jsonify(success=False, message="Passwords do not match"), 402

    if len(password)<8:
        return jsonify(success=False, message="Password must have 8 letters at least"), 403

    existing = users.find_one({"email": email}, {"_id": 1})
    if existing:
        return jsonify(success=False, message="Email already registered"), 409


    # # ---- Build document to insert
    volunteer_doc = {
        "firstname": firstname,
        "lastname": lastname,
        "gender": gender,
        "phone": phone,
        "city": city,
        "address": address,
        "background": background,
        "language": language,
        "availabilities": availabilities,
        "skills": skills,
        "self_description":self_description,
        "updated_at": datetime.datetime.now(datetime.timezone.utc)
    }

    user_doc = {
        "email": email,
        "password_hash": generate_password_hash(password),
        "created_at": datetime.datetime.now(datetime.timezone.utc),
        "type":"volunteer",
    }

    volunteer_id=None

    try:
        volunteer_id = volunteers.insert_one(volunteer_doc).inserted_id
        user_doc["volunteer_id"] = volunteer_id
        users.insert_one(user_doc)
    except DuplicateKeyError:
        if volunteer_id is not None:
            try:
                volunteers.delete_one({"_id": volunteer_id})
            except Exception:
                pass 
        return jsonify(success=False, message="Email already registered"), 409
    except Exception as e:
        if volunteer_id is not None:
            try:
                volunteers.delete_one({"_id": volunteer_id})
            except Exception:
                pass
        return jsonify(success=False, message=f"Failed to register: {e}"), 500

    return jsonify(success=True, data={"type":"volunteer", "volunteerId": str(volunteer_id)})



if __name__ == "__main__":
    app.run(host=BIND_HOST, port=BIND_PORT, debug=True)
