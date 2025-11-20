import datetime
from flask import Flask, request, jsonify, session
from pymongo import MongoClient, ASCENDING
from werkzeug.security import generate_password_hash, check_password_hash
from pymongo.errors import DuplicateKeyError
import time
import threading
import os
from bson import ObjectId

os.environ["TF_CPP_MIN_LOG_LEVEL"] = "2"
os.environ["TF_ENABLE_ONEDNN_OPTS"] = "0"

from icecream import ic

from transformers import pipeline, AutoTokenizer, AutoModelForSequenceClassification
from transformers.utils import logging

from  src.match import matching
import werkzeug
from werkzeug.utils import secure_filename



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





UPLOAD_FOLDER = "assets/img/uploads"
ALLOWED_EXT = {"png", "jpg", "jpeg"}

# 确保上传目录存在
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

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

    if not askfor:
        return jsonify(success=False, message="Please select at least one service"), 401
    
    if not appointment:
        return jsonify(success=False, message="Please select at least one time slot"), 402

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

    requirement = f"I live in @@@@{senior_info['city']}@@@@, I speak in {'English' if (senior_info['language']=='en') else 'French'}, "
    # requirement +=  f'I need {','.join([parse_skill(item) for item in askfor])} service'
    requirement +=  f"I need @@##{','.join(askfor)}@@## service"
    # requirement +=  f' on {', '.join([parse_weekday(item)  for item in appointment])}.' if len(appointment)>0 else ''
    requirement +=  f" on ####{', '.join(appointment)}####." if len(appointment)>0 else ''
    requirement +=  f" My addition requirement is {addition}" if len(addition)>0 else ''

    condition=[]
    all_volunteers= volunteers.find()
    lookup_dict={}
    for i, vol in enumerate(all_volunteers):
        # ic(askfor,vol['skills'])

        s = f"I live in @@@@{vol['city']}@@@@, I am a {vol['gender']}, "
        # s += f'I can provide service on {', '.join([parse_weekday(item)  for item in vol['availabilities']])}. ' 
        s += f"I can provide service on ####{', '.join(vol['availabilities'])}####"

        if len(vol['language'])>=1:
            s += f"I speak in {'English' if (vol['language'])[0]=='en' else 'French'}. "        
        if len(vol['language'])==2:
            s += f"I speak in {'English' if (vol['language'])[1]=='en' else 'French'}. "

        # s += f"I can provide {', '.join([parse_skill(item) for item in vol['skills']])} service. " 
        s += f"I can provide @@##{', '.join(vol['skills'])}@@## service. " 
        s += f"My description is: "+ vol['self_description']
        
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
        # print(f"  volunteer snippet: {vol[:120]}...")
        print("-" * 80)

    print('End')
    print("Elapsed time:", time.time() - start, "seconds")



@app.route("/volunteer/profile", methods=["GET", "PUT"])
def api_volunteer_profile():
    user = current_user()
    if not user:
        return jsonify(success=False, message="Unauthorized"), 401

    # 先在 users 里找到当前登录用户
    user_doc = users.find_one({"_id": ObjectId(user["id"])})
    if not user_doc or "volunteer_id" not in user_doc:
        return jsonify(success=False, message="Not a volunteer account"), 403

    vol_id = user_doc["volunteer_id"]
    if isinstance(vol_id, str):
        vol_id = ObjectId(vol_id)

    # ---------- GET：读取资料并返回给前端自动填充 ----------
    if request.method == "GET":
        vol = volunteers.find_one({"_id": vol_id})
        if not vol:
            return jsonify(success=False, message="Volunteer profile not found"), 404

        data = {
            "firstname": vol.get("firstname", ""),
            "lastname": vol.get("lastname", ""),
            "gender": vol.get("gender", ""),
            "phone": vol.get("phone", ""),
            "city": vol.get("city", ""),
            "address": vol.get("address", ""),
            "background": vol.get("background", ""),
            "language": vol.get("language", []),
            "availabilities": vol.get("availabilities", []),
            "skills": vol.get("skills", []),
            "self_description": vol.get("self_description", ""),
            "email": user_doc.get("email", ""),
            "photo_url": vol.get("photo_url", "")
        }
        return jsonify(success=True, data=data)

    # ---------- PUT：局部更新志愿者资料 ----------
    data = request.get_json(silent=True) or {}

    allowed_scalar = ["gender", "phone", "city", "address", "self_description"]
    allowed_array_client = ["language", "availability", "skills"]

    update_fields = {}

    # 文本类字段：只有在请求里出现的才更新
    for key in allowed_scalar:
        if key in data:
            val = (data.get(key) or "").strip()
            update_fields[key] = val

    # 数组类字段：language / availability / skills
    for key in allowed_array_client:
        if key in data:
            val = data.get(key) or []
            if key == "availability":
                # 数据库里叫 availabilities
                update_fields["availabilities"] = val
            else:
                update_fields[key] = val

    if update_fields:
        update_fields["updated_at"] = datetime.datetime.now(datetime.timezone.utc)
        volunteers.update_one({"_id": vol_id}, {"$set": update_fields})

    return jsonify(success=True)

@app.route("/volunteer/photo", methods=["POST"])
def api_volunteer_photo():
    user = current_user()
    if not user:
        return jsonify(success=False, message="Unauthorized"), 401

    user_doc = users.find_one({"_id": ObjectId(user["id"])})
    if not user_doc or "volunteer_id" not in user_doc:
        return jsonify(success=False, message="Not a volunteer account"), 403

    vol_id = user_doc["volunteer_id"]
    if isinstance(vol_id, str):
        vol_id = ObjectId(vol_id)

    # 检查文件
    if "photo" not in request.files:
        return jsonify(success=False, message="No file uploaded"), 400

    file = request.files["photo"]
    filename = secure_filename(file.filename)

    if not filename:
        return jsonify(success=False, message="Invalid filename"), 400

    ext = filename.rsplit(".", 1)[-1].lower()
    if ext not in ALLOWED_EXT:
        return jsonify(success=False, message="Invalid file type"), 400

    # 使用用户 ID 命名头像，保证唯一
    newname = f"{user['id']}.{ext}"
    save_path = os.path.join(UPLOAD_FOLDER, newname)

    # 保存文件
    file.save(save_path)

    # 前端访问路径（注意前面的 /vs）
    photo_url = f"../assets/img/uploads/{newname}"

    # 更新数据库
    volunteers.update_one(
        {"_id": vol_id},
        {"$set": {"photo_url": photo_url}}
    )

    return jsonify(success=True, url=photo_url)



if __name__ == "__main__":
    app.run(host=BIND_HOST, port=BIND_PORT, debug=True)
