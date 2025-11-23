import datetime

from flask import Flask, Response, request, jsonify, session, send_file, abort

from pymongo import DESCENDING, MongoClient, ASCENDING
from werkzeug.security import generate_password_hash, check_password_hash
from pymongo.errors import DuplicateKeyError
import time
import threading
import os, re, io
from bson import ObjectId
import gridfs
from datetime import timedelta
from math import ceil


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

app.config["SESSION_PERMANENT"] = False
app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(hours=1)

BIND_HOST = "127.0.0.1"
BIND_PORT = 5000


RANK_LIMIT = 4


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
match=db['match']

fs = gridfs.GridFS(db, collection="volunteer_photos")

users.create_index([("email", ASCENDING)], unique=True)


HISTORYITEMS_LIMIT=20


def normalize_email(email):
    return (email or "").strip().lower()


def current_user():
    uid = session.get("uid")
    email = session.get("email")
    if not uid or not email:
        return None
    return {"id": uid, "email": email}


_EMAIL_RE = re.compile(
    r"^(?=.{1,254}$)"                       
    r"(?=.{1,64}@)"                         
    r"[A-Za-z0-9!#$%&'*+/=?^_`{|}~-]+"    
    r"(?:\.[A-Za-z0-9!#$%&'*+/=?^_`{|}~-]+)*"  
    r"@"
    r"(?:[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?\.)+" 
    r"[A-Za-z]{2,}$"                        # TLD
)

def is_valid_email(email):
    if not isinstance(email, str):
        return False

    email = email.strip()
    if not email:
        return False

    if email.count("@") != 1:
        return False

    local, domain = email.split("@")

    if local.startswith(".") or local.endswith(".") or ".." in local:
        return False
    if domain.startswith(".") or domain.endswith(".") or ".." in domain:
        return False

    return _EMAIL_RE.match(email) is not None


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
    
    if not is_valid_email(email):
        return jsonify(success=False, message="Email format is unvailable"), 404

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
    
    if not is_valid_email(email):
        return jsonify(success=False, message="Email format is unvailable"), 404

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
    
    if '@@' in addition:
        return jsonify(success=False, message="'@@' is not an available word"), 410

    if '##' in addition:
        return jsonify(success=False, message="'##' is not an available word"), 410

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
                        args=(appointment, askfor, addition, senior_info, senior_id),
                        daemon=True
                    ).start()

    # get_matching()
    # ic(requirement)
    return jsonify(success=True)

# def parse_skill(str):
#     dt={
#         'chat':'chatting',
#         'video':'video chatting',
#         'read':'reading',
#         'grocery':'groceries-taking',
#         'health':'health consulting',
#         'tech':'technique supporting',
#     }
#     return dt[str]

def get_matching(appointment, askfor, addition, senior_info, senior_id):
    print('Start ... ...')
    addition=re.sub(r'[^0-9A-Za-z,\.!\(\)]', '', addition)
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
    candidates=[]
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
        if rank>RANK_LIMIT:
            break
        candidates.append(lookup_dict[idx])

    for rank, (final_score, scores, nli_core, nli_extra, idx, vol) in enumerate(results, start=1):
        print(f"Rank {rank}  (candidate #{idx})")
        print(f"  _id     = {lookup_dict[idx]}")
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

    match_doc={
        'senior_id': senior_id,
        'candidates': candidates,
        'requirements':{'askfor':askfor, 'appointment':appointment, 'addition': addition},
        'status': 'pending',
        'booking_at': datetime.datetime.now(datetime.timezone.utc)
    }

    match.insert_one(match_doc)



# @app.route("/volunteer/profile", methods=["GET", "PUT"])
# def api_volunteer_profile():
#     user = current_user()
#     if not user:
#         return jsonify(success=False, message="Unauthorized"), 401

#     # 先在 users 里找到当前登录用户
#     user_doc = users.find_one({"_id": ObjectId(user["id"])})
#     if not user_doc or "volunteer_id" not in user_doc:
#         return jsonify(success=False, message="Not a volunteer account"), 403

#     vol_id = user_doc["volunteer_id"]
#     if isinstance(vol_id, str):
#         vol_id = ObjectId(vol_id)

#     # ---------- GET：读取资料并返回给前端自动填充 ----------
#     if request.method == "GET":
#         vol = volunteers.find_one({"_id": vol_id})
#         if not vol:
#             return jsonify(success=False, message="Volunteer profile not found"), 404

#         data = {
#             "firstname": vol.get("firstname", ""),
#             "lastname": vol.get("lastname", ""),
#             "gender": vol.get("gender", ""),
#             "phone": vol.get("phone", ""),
#             "city": vol.get("city", ""),
#             "address": vol.get("address", ""),
#             "background": vol.get("background", ""),
#             "language": vol.get("language", []),
#             "availabilities": vol.get("availabilities", []),
#             "skills": vol.get("skills", []),
#             "self_description": vol.get("self_description", ""),
#             "email": user_doc.get("email", ""),
#             "photo_url": vol.get("photo_url", "")
#         }
#         return jsonify(success=True, data=data)

#     # ---------- PUT：局部更新志愿者资料 ----------
#     data = request.get_json(silent=True) or {}

#     allowed_scalar = ["gender", "phone", "city", "address", "self_description"]
#     allowed_array_client = ["language", "availability", "skills"]

#     update_fields = {}

#     # 文本类字段：只有在请求里出现的才更新
#     for key in allowed_scalar:
#         if key in data:
#             val = (data.get(key) or "").strip()
#             update_fields[key] = val

#     # 数组类字段：language / availability / skills
#     for key in allowed_array_client:
#         if key in data:
#             val = data.get(key) or []
#             if key == "availability":
#                 # 数据库里叫 availabilities
#                 update_fields["availabilities"] = val
#             else:
#                 update_fields[key] = val

#     if update_fields:
#         update_fields["updated_at"] = datetime.datetime.now(datetime.timezone.utc)
#         volunteers.update_one({"_id": vol_id}, {"$set": update_fields})

#     return jsonify(success=True)

# @app.route("/volunteer/photo", methods=["POST"])
# def api_volunteer_photo():
#     user = current_user()
#     if not user:
#         return jsonify(success=False, message="Unauthorized"), 401

#     user_doc = users.find_one({"_id": ObjectId(user["id"])})
#     if not user_doc or "volunteer_id" not in user_doc:
#         return jsonify(success=False, message="Not a volunteer account"), 403

#     vol_id = user_doc["volunteer_id"]
#     if isinstance(vol_id, str):
#         vol_id = ObjectId(vol_id)

#     # 检查文件
#     if "photo" not in request.files:
#         return jsonify(success=False, message="No file uploaded"), 400

#     file = request.files["photo"]
#     filename = secure_filename(file.filename)

#     if not filename:
#         return jsonify(success=False, message="Invalid filename"), 400

#     ext = filename.rsplit(".", 1)[-1].lower()
#     if ext not in ALLOWED_EXT:
#         return jsonify(success=False, message="Invalid file type"), 400

#     # 使用用户 ID 命名头像，保证唯一
#     newname = f"{user['id']}.{ext}"
#     save_path = os.path.join(UPLOAD_FOLDER, newname)

#     # 保存文件
#     file.save(save_path)

#     # 前端访问路径（注意前面的 /vs）
#     photo_url = f"../assets/img/uploads/{newname}"

#     # 更新数据库
#     volunteers.update_one(
#         {"_id": vol_id},
#         {"$set": {"photo_url": photo_url}}
#     )

#     return jsonify(success=True, url=photo_url)

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

    if "photo" not in request.files:
        return jsonify(success=False, message="No file uploaded"), 400

    file = request.files["photo"]
    filename = secure_filename(file.filename or "")
    if not filename:
        return jsonify(success=False, message="Invalid filename"), 400

    ext = filename.rsplit(".", 1)[-1].lower()
    if ext not in ALLOWED_EXT:
        return jsonify(success=False, message="Invalid file type"), 400

    content_type = file.mimetype or f"image/{ext}"
    raw = file.read()
    if not raw:
        return jsonify(success=False, message="Empty file"), 400

    vol_doc = volunteers.find_one({"_id": vol_id}, {"photo_file_id": 1})
    old_file_id = vol_doc.get("photo_file_id") if vol_doc else None
    if old_file_id:
        try:
            fs.delete(ObjectId(old_file_id))
        except Exception:
            pass

    new_file_id = fs.put(
        raw,
        filename=filename,
        content_type=content_type,
        metadata={
            "vol_id": vol_id,
            "uploaded_by": ObjectId(user["id"]),
            "uploaded_at": datetime.datetime.now(datetime.timezone.utc)
        }
    )

    volunteers.update_one(
        {"_id": vol_id},
        {"$set": {
            "photo_file_id": str(new_file_id),
            "updated_at": datetime.datetime.now(datetime.timezone.utc)
        }}
    )

    return jsonify(success=True, url="/api/volunteer/photo", file_id=str(new_file_id))


@app.route("/volunteer/photo", methods=["GET"])
def get_current_volunteer_photo():
    user = current_user()
    if not user:
        return abort(401)

    user_doc = users.find_one({"_id": ObjectId(user["id"])})
    if not user_doc or "volunteer_id" not in user_doc:
        return abort(403)

    vol_id = user_doc["volunteer_id"]
    if isinstance(vol_id, str):
        vol_id = ObjectId(vol_id)

    vol_doc = volunteers.find_one({"_id": vol_id}, {"photo_file_id": 1})
    if not vol_doc or not vol_doc.get("photo_file_id"):
        return abort(404)

    try:
        grid_out = fs.get(ObjectId(vol_doc["photo_file_id"]))
    except Exception:
        return abort(404)

    return send_file(
        io.BytesIO(grid_out.read()),
        mimetype=grid_out.content_type or "image/jpeg",
        download_name=grid_out.filename or "photo.jpg",
        conditional=True
    )

@app.route("/volunteer/profile", methods=["GET", "PUT"])
def api_volunteer_profile():
    user = current_user()
    if not user:
        return jsonify(success=False, message="Unauthorized"), 401

    user_doc = users.find_one({"_id": ObjectId(user["id"])})
    if not user_doc or "volunteer_id" not in user_doc:
        return jsonify(success=False, message="Not a volunteer account"), 403

    vol_id = user_doc["volunteer_id"]
    if isinstance(vol_id, str):
        vol_id = ObjectId(vol_id)

    if request.method == "GET":
        vol = volunteers.find_one({"_id": vol_id})
        if not vol:
            return jsonify(success=False, message="Volunteer profile not found"), 404

        photo_url = ""
        if vol.get("photo_file_id"):
            photo_url = "/api/volunteer/photo"

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
            "photo_url": photo_url
        }
        return jsonify(success=True, data=data)

    data = request.get_json(silent=True) or {}

    allowed_scalar = ["gender", "phone", "city", "address", "self_description"]
    allowed_array_client = ["language", "availability", "skills"]

    update_fields = {}

    for key in allowed_scalar:
        if key in data:
            val = (data.get(key) or "").strip()
            update_fields[key] = val

    for key in allowed_array_client:
        if key in data:
            val = data.get(key) or []
            if key == "availability":
                update_fields["availabilities"] = val
            else:
                update_fields[key] = val

    if update_fields:
        update_fields["updated_at"] = datetime.datetime.now(datetime.timezone.utc)
        volunteers.update_one({"_id": vol_id}, {"$set": update_fields})

    return jsonify(success=True)



@app.route("/senior/services", methods=["GET"])
def get_services():
    user = current_user()
    if not user:
        return jsonify(success=False, message="Unauthorized"), 401

    user_oid = ObjectId(user["id"])
    user = users.find_one({"_id": user_oid}, {"_id": 1, "senior_id": 1})
    senior_oid = user.get("senior_id")
    if not senior_oid:
        return jsonify(success=False, message="Senior id missing"), 400

    try:
        page = int(request.args.get("page", 1))
        limit = int(request.args.get("limit", HISTORYITEMS_LIMIT))
        if page < 1: page = 1
        if limit < 1 or limit > HISTORYITEMS_LIMIT: 
            limit = HISTORYITEMS_LIMIT

    except ValueError:
        return jsonify(success=False, message="Invalid page/limit"), 400

    skip = (page - 1) * limit
    query = {"senior": senior_oid}
    total = db.services.count_documents(query)

    cursor = (
        db.services
          .find(query)
          .sort("serve_at", DESCENDING)
          .skip(skip)
          .limit(limit)
    )

    services_out = []
    for s in cursor:
        v_id = s.get("volunteer")
        volunteer_info = None
        if v_id:
            v_doc = db.volunteers.find_one(
                {"_id": v_id},
                {"firstname": 1, "lastname": 1, "gender": 1,
                 "city": 1, "language": 1, "skills": 1},
            )

            photo_doc = db["volunteer_photos.files"].find_one(
                {"metadata.vol_id": v_id},
                sort=[("uploadDate", DESCENDING)]
            )
            photo_file_id = str(photo_doc["_id"]) if photo_doc else None

            if photo_file_id:
                photo_url = f"/volunteer/photo/{photo_file_id}"
                p_url = '/api' + photo_url
            else:
                p_url = None

            if v_doc:
                volunteer_info = {
                    "_id": str(v_doc["_id"]),
                    "firstname": v_doc.get("firstname"),
                    "lastname": v_doc.get("lastname"),
                    "gender": v_doc.get("gender"),
                    "city": v_doc.get("city"),
                    "language": v_doc.get("language", []),
                    "skills": v_doc.get("skills", []),
                    "photo_file_id": photo_file_id,
                    "photo_url": p_url,
                }

        serve_at = s.get("serve_at")
        if serve_at is not None and hasattr(serve_at, "isoformat"):
            serve_at = serve_at.isoformat()

        services_out.append({
            "_id": str(s.get("_id")),
            "senior": str(s.get("senior")) if s.get("senior") else None,
            "volunteer": str(v_id) if v_id else None,
            "serve_at": serve_at,
            "rating": s.get("rating"),
            "volunteer_info": volunteer_info,
        })

    total_pages = ceil(total / limit) if limit else 1
    has_more = page < total_pages

    return jsonify(
        success=True,
        services=services_out,
        page=page,
        limit=limit,
        total=total,
        total_pages=total_pages,
        has_more=has_more
    ), 200


@app.route("/volunteer/photo/<file_id>", methods=["GET"])
def get_volunteer_photo(file_id):
    try:
        oid = ObjectId(file_id)
    except Exception:
        abort(404)

    try:
        grid_out = fs.get(oid)
    except gridfs.errors.NoFile:
        abort(404)

    content_type = grid_out.content_type or "application/octet-stream"
    return Response(
        grid_out.read(),
        mimetype=content_type,
        headers={
            "Cache-Control": "public, max-age=86400"
        }
    )



@app.route("/services/<service_id>/rating", methods=["PATCH"])
def update_service_rating(service_id):
    user = current_user()
    if not user:
        return jsonify(success=False, message="Unauthorized"), 401


    user_oid = ObjectId(user["id"])
    user = users.find_one({"_id": user_oid},
                        {
                            "_id": 1,
                            "senior_id": 1,
                        })
    senior_oid = user.get("senior_id")

    # ic(user_oid,senior_oid)
    if not senior_oid:
        return jsonify(success=False, message="Forbidden"), 403

    try:
        service_oid = ObjectId(service_id)

    except Exception:
        return jsonify(success=False, message="Invalid id"), 400

    data = request.get_json(silent=True) or {}
    rating = data.get("rating", 0)

    try:
        rating = float(rating)
    except Exception:
        return jsonify(success=False, message="Invalid rating"), 400

    if rating < 0 or rating > 5:
        return jsonify(success=False, message="Rating out of range"), 400

    result = db.services.update_one(
        {"_id": service_oid, "senior": senior_oid},
        {"$set": {"rating": rating, "rated_at": datetime.datetime.now(datetime.timezone.utc)}}
    )

    if result.matched_count == 0:
        return jsonify(success=False, message="Service not found"), 404

    return jsonify(success=True, rating=rating), 200

if __name__ == "__main__":
    app.run(host=BIND_HOST, port=BIND_PORT, debug=True)
