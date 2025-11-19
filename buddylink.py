import datetime
from flask import Flask, request, jsonify, session
from pymongo import MongoClient, ASCENDING
from werkzeug.security import generate_password_hash, check_password_hash
from pymongo.errors import DuplicateKeyError
import time
import threading
import os

os.environ["TF_CPP_MIN_LOG_LEVEL"] = "2"
os.environ["TF_ENABLE_ONEDNN_OPTS"] = "0"

from icecream import ic

from transformers import pipeline, AutoTokenizer, AutoModelForSequenceClassification
from transformers.utils import logging

from  src.match import matching

logging.set_verbosity_error()
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "2"


MODEL_PATH = "facebook/bart-large-mnli"
TOKENIZER = AutoTokenizer.from_pretrained(MODEL_PATH)
MODEL = AutoModelForSequenceClassification.from_pretrained(MODEL_PATH)

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

def parse_weekday(str):
    dt={
        'mon': 'Monday',
        'tue': 'Tuesday' ,
        'wed': 'Wednesday' ,
        'thu': 'Thursday' ,
        'fri': 'Friday' ,
        'sat': 'Saturday',
        'sun': 'Sunday' 
    }
    return f'{dt[str[:3]]} {str[4:]}'

@app.route('/askfor', methods=['POST','GET'])
def ask_for_service():
    data = request.get_json(silent=True) 

    email       = normalize_email(data.get("email"))
    appointment = data.get("appointment") or []
    askfor      = data.get("askfor") or []
    addition    = data.get("additional_requirement") or ""

    senior_id = users.find_one({"email": email},
                            {
                                "senior_id": 1
                            }
                        ).get("senior_id","")
    
    senior_info = seniors.find_one({"_id": senior_id},
                            {
                                "firstname": 1,
                                "lastname": 1,
                                "age": 1,
                                "phone": 1,
                                "city": 1,
                                "address": 1,
                                "contactPref": 1,
                                "language": 1,
                                "notes": 1,
                            }
                        )
    # ic(email, appointment, askfor, addition, senior_info)


    threading.Thread(target=get_matching,
                        args=(appointment, askfor, addition, senior_info),
                        daemon=True
                    ).start()

    # get_matching()
    # ic(requirement)
    return jsonify(success=True)

def parse_skill(str):
    dt={
        'chat':'chatting',
        'video':'video chatting',
        'read':'reading',
        'grocery':'groceries-taking',
        'health':'health consulting',
        'tech':'technique supporting',
    }
    return dt[str]

def get_matching(appointment, askfor, addition, senior_info):
    print('Start ... ...')
    start=time.time()

    requirement = f'I live in {senior_info['city']}, I speak in {'English' if (senior_info['language']=='en') else 'French'}, ' 
    requirement +=  f'I need {','.join([parse_skill(item) for item in askfor])} service'
    requirement +=  f' on {', '.join([parse_weekday(item)  for item in appointment])}.' if len(appointment)>0 else ''
    requirement +=  f' My addition requirement is {addition}' if len(addition)>0 else ''

    condition=[]
    all_volunteers= volunteers.find()
    lookup_dict={}
    for i, vol in enumerate(all_volunteers):
        # ic(vol)

        s = f'I live in {vol['city']}, I am a {vol['gender']}, I can provide service on {', '.join([parse_weekday(item)  for item in vol['availabilities']])}. ' 

        if len(vol['language'])>=1:
            s += f'I speak in {'English' if (vol['language'])[0]=='en' else 'French'}. '        
        if len(vol['language'])==2:
            s += f'I speak in {'English' if (vol['language'])[1]=='en' else 'French'}. '
        s += f'I can provide {', '.join([parse_skill(item) for item in vol['skills']])} service. ' 
        s += f'My description is: '+ vol['self_description']
        
        condition.append(s)
        lookup_dict[i]=vol['_id']

    results=matching(requirement,condition,TOKENIZER,MODEL)

    for rank, (final_score, scores, nli_core, nli_extra, idx, vol) in enumerate(results, start=1):
        print(f"Rank {rank}  (candidate #{idx})")
        print(f"  final_score     = {final_score:.4f}")
        print(f"  entail_core     = {scores['entail_core']:.4f}")
        print(f"  service_match   = {scores['service_match']:.4f}")
        print(f"  time_overlap    = {scores['time_overlap']:.4f}")
        print(f"  location_match  = {scores['location_match']:.4f}")
        print(f"  addition_req    = {scores['addition_req']:.4f}")
        print(f"  disqualified    = {scores.get('disqualified', False)}")
        print(f"  NLI core probs  = {nli_core}")
        if nli_extra is not None:
            print(f"  NLI extra probs = {nli_extra}")
        else:
            print("  NLI extra probs = (no extra requirement)")
        print(f"  volunteer snippet: {vol[:120]}...")
        print("-" * 80)

        print('End')
        print("Elapsed time:", time.time() - start, "seconds")



if __name__ == "__main__":
    app.run(host=BIND_HOST, port=BIND_PORT, debug=True)
