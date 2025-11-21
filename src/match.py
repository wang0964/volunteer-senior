import time
import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification
import re
from icecream import ic
import math

# candidate_labels = [
#     "I live in Toronto / North York, I am a male, I can provide service on Monday afternoon, Monday evening, Tuesday evening, Wednesday evening, Thursday afternoon, Thursday evening, Saturday morning, Saturday afternoon, Saturday evening, Sunday morning, Sunday afternoon, Sunday evening. I speak in English. I can provide chatting, groceries-taking, technique supporting service. My description is: I enjoy helping seniors with friendly conversation and simple errands; I’m patient and reliable.",
#     "I live in Toronto / Scarborough, I am a female, I can provide service on Monday afternoon, Wednesday afternoon, Friday morning, Friday evening, Saturday morning, Saturday evening, Sunday morning, Sunday evening. I speak in English. I speak in French. I can provide video chatting, reading service. My description is: I enjoy virtual companionship and assisting seniors with reading mail and forms.",
#     "I live in Toronto / Mississauga, I am a male, I can provide service on Saturday morning, Saturday afternoon, Saturday evening, Sunday morning, Sunday afternoon, Sunday evening. I speak in English. I can provide groceries-taking, health consulting, technique supporting service. My description is: I can help with grocery runs and basic digital support.",
#     "I live in Markham, I am a female, I can provide service on Monday afternoon, Monday evening, Tuesday evening, Wednesday afternoon, Wednesday evening, Thursday evening, Friday evening, Saturday afternoon, Saturday evening. I speak in English. I can provide chatting, groceries-taking, health consulting service. My description is: Friendly volunteer who enjoys chatting with seniors and providing emotional support.",
#     "I live in Toronto / Etobicoke, I am a male, I can provide service on Monday afternoon, Tuesday afternoon, Friday afternoon, Friday evening, Saturday evening, Sunday afternoon, Sunday evening. I speak in English. I speak in French. I can provide video chatting, technique supporting service. My description is: I can assist with smartphones, tablets, and basic technology needs.",
#     "I live in Toronto (North York), I am a male, I can provide service on Monday morning, Monday evening, Tuesday afternoon, Wednesday morning, Friday afternoon, Friday evening, Sunday evening. I speak in English. I can provide chatting, video chatting, reading, technique supporting service. My description is: I enjoy connecting with seniors and helping them stay digitally confident and socially connected. I'm patient, easygoing, and love reading news together or assisting with basic tech support. I'm flexible with evenings and happy to build long-term companionship.",
#     "I live in Toronto /Scarborough, I am a female, I can provide service on Monday morning, Monday afternoon, Wednesday afternoon, Wednesday evening, Saturday morning. I speak in English. I speak in French. I can provide chatting, reading, groceries-taking, health consulting service. My description is: I love supporting seniors with weekly check-ins, grocery trips, and casual conversation. I speak both English and French and have experience helping older adults with mobility challenges. My schedule is flexible during weekdays.",
#     "I live in Toronto /Downtown, I am a male, I can provide service on Monday afternoon, Thursday morning, Thursday afternoon, Friday evening, Saturday evening, Sunday morning. I speak in English. I can provide chatting, video chatting, technique supporting service. My description is: I specialize in helping seniors learn phones, tablets, Zoom, and simple digital tools so they can stay connected with family. I'm patient, friendly, and enjoy building meaningful community connections.",
#     "I live in Toronto /East York, I am a female, I can provide service on Tuesday morning, Tuesday evening, Thursday afternoon, Saturday morning, Saturday afternoon. I speak in English. I can provide chatting, groceries-taking, health consulting service. My description is: I enjoy helping seniors maintain independence with weekly grocery support, check-ins, and warm conversation. I’m reliable, friendly, and committed to building long-term relationships.",
#     "I live in Toronto /Scarborough, I am a male, I can provide service on Monday afternoon, Monday evening, Wednesday evening, Friday afternoon. I can provide video chatting, reading, technique supporting service. My description is: I love helping seniors stay connected through technology. I’m patient, calm, and take time to ensure each person feels comfortable and supported during tech sessions.",
#     "I live in Toronto (Downtown West / Liberty Village), I am a female, I can provide service on Tuesday morning, Tuesday afternoon, Thursday afternoon, Thursday evening, Sunday morning. I speak in English. I speak in French. I can provide chatting, reading, groceries-taking, technique supporting service. My description is: I’m passionate about community care and love spending time with seniors—whether chatting, grocery shopping, or helping with digital skills. I’m warm, reliable, and enjoy making meaningful connections.",
#     "I live in Toronto (North York / Willowdale), I am a male, I can provide service on Monday morning, Monday evening, Thursday afternoon, Saturday afternoon, Sunday morning. I speak in English. I can provide chatting, reading, technique supporting service. My description is: I enjoy helping older adults stay connected and independent through patient tech guidance and friendly conversations. I'm dependable and happy to work around seniors’ schedules.",
#     "I live in Toronto (Downtown / Kensington Market), I am a female, I can provide service on Monday afternoon, Monday evening, Thursday afternoon, Sunday morning. I speak in English. I speak in French. I can provide chatting, video chatting, groceries-taking, health consulting service. My description is: I love supporting seniors with weekly check-ins, light errands, and companionship. I’m warm, attentive, and dedicated to making sure people feel heard and cared for.",
#     "I live in Toronto (Scarborough / Warden & Eglinton), I am a male, I can provide service on Monday morning, Monday afternoon, Friday morning, Saturday afternoon, Sunday evening. I speak in English. I can provide chatting, video chatting, reading, technique supporting service. My description is: I enjoy building friendships with seniors and helping them stay socially and digitally connected. I’m patient, friendly, and happy to provide support online or in person."
# ]


# senior_text = "I live in Toronto, I speak in English, I need reading service. My addition requirement is: the volunteer should be a female."


SERVICES = [
    "reading",
    "video chatting",
    "chatting",
    "groceries-taking",
    "health consulting",
    "technique supporting",
]

DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
TIMES = ["morning", "afternoon", "evening"]


def extract_info(s,patt):
    if patt=='@#':
        pattern=r'@@##(.*?)@@##'
    elif patt=='@':
        pattern=r'@@@@(.*?)@@@@'
    elif patt=='#':
        pattern=r'####(.*?)####'

    m = re.search(pattern, s, re.S)
    if m:
        result = m.group(1)
        result=result.replace('(','').replace(')','').replace(' ','')
        # print(result)
        return result.split(',') if patt!='@' else result.split('/')
    else:
        return []


def get_match_score(vol_text, senior_text,patt):
    vol_services = extract_info(vol_text,patt)
    need_services = extract_info(senior_text,patt)

    if not need_services:
        return 1.0

    miss=0

    str_vol_services=''.join(vol_services)
    for item in need_services:
        if str_vol_services.find(item)<0:
            miss += 1

    return (len(need_services)-miss) / len(need_services)


def split_senior_need(text):
    lower = text.lower()
    keywords = [
        "my addition requirement is",
        "my additional requirement is",
    ]

    for kw in keywords:
        idx = lower.find(kw)
        if idx != -1:
            core = text[:idx].strip()
            extra = text[idx:].strip()
           
            is_pos = extra.lower().find("is")
            if is_pos != -1:
                extra = extra[is_pos + 2:].strip(" :. ")
            return core, extra

    return text.strip(), ""


def nli_label_probs(model, tokenizer, premise, hypothesis):
    inputs = tokenizer(premise, hypothesis, return_tensors="pt", truncation=True)
    with torch.no_grad():
        logits = model(**inputs).logits
    probs = torch.softmax(logits, dim=-1)[0]

    label_scores = {
        model.config.id2label[i]: float(probs[i])
        for i in range(len(probs))
    }
    return label_scores



def compute_final_score(vol_text, core_need_text, entail_core, entail_extra):
    svc_score = get_match_score(vol_text, core_need_text,'@#')
    time_score = get_match_score(vol_text, core_need_text,'#')
    loc_score = get_match_score(vol_text, core_need_text,'@')

 
    threshold = 0.3

    if entail_extra is not None and entail_extra < threshold:
        return {
            "final_score": 0.0,
            "entail_core": entail_core,
            "service_match": svc_score,
            "time_overlap": time_score,
            "location_match": loc_score,
            "addition_req": entail_extra,
            "disqualified": True,
        }


    add_score = entail_extra if entail_extra is not None else 1.0

    askfor=extract_info(vol_text,'@#')
    if 'grocery' in askfor:
        final = 0.05 * entail_core + 0.30 * svc_score + 0.15 * time_score +  0.45 * loc_score + 0.05 * add_score
    else:
        final = 0.10 * entail_core + 0.35 * svc_score + 0.35 * time_score +  0.10 * loc_score + 0.10 * add_score

    return {
        "final_score": final,
        "entail_core": entail_core,
        "service_match": svc_score,
        "time_overlap": time_score,
        "location_match": loc_score,
        "addition_req": add_score,
        "disqualified": False,
    }

import math

def get_score(prob, ratio_threshold=10.0, eps=1e-6):
    w_c = -1.0
    w_n = 0.01
    w_e = 1.0

    p_c = prob["contradiction"]
    p_n = prob["neutral"]
    p_e = prob["entailment"]

    max_raw = w_e
    min_raw = w_c
    raw_score = w_e * p_e + w_n * p_n + w_c * p_c
    base_score = (raw_score - min_raw) / (max_raw - min_raw)

    eps=0.000001
    ratio_threshold=7.0

    log_ratio = math.log(p_e + eps) - math.log(p_c + eps)
    log_ratio_threshold = math.log(ratio_threshold)

    penalty=log_ratio / log_ratio_threshold

    if penalty<-1:
        result= -base_score / penalty
    elif penalty>1:
        result=base_score + (penalty-1)/penalty*(1-base_score)
    else:
        result=base_score

    return result



def matching(senior_text, candidate_labels, tokenizer,model):
    core_need_text, extra_req_text = split_senior_need(senior_text)
    results = []
    core_need_text_clr=core_need_text.replace('@@@@','').replace('####','').replace('@@##','')

    for i, volunteer in enumerate(candidate_labels):
        v_clr=volunteer.replace('@@@@','').replace('####','').replace('@@##','')
        nli_core = nli_label_probs(model, tokenizer, v_clr, core_need_text_clr)
        entail_core=get_score(nli_core)

        if extra_req_text:
            nli_extra = nli_label_probs(model, tokenizer, v_clr, extra_req_text)
            entail_extra=get_score(nli_extra)
        else:
            nli_extra = None
            entail_extra = None

        scores = compute_final_score(
            volunteer,
            core_need_text,
            entail_core,
            entail_extra,
        )

        results.append((scores["final_score"], scores, nli_core, nli_extra, i, volunteer))


    results.sort(reverse=True, key=lambda x: x[0])
    return results

