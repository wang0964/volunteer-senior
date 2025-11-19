import time
import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification


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



def extract_services(text):
    text_lower = text.lower()
    return {s for s in SERVICES if s in text_lower}


def service_match_score(vol_text, senior_text):
    vol_services = extract_services(vol_text)
    need_services = extract_services(senior_text)

    if not need_services:
        return 1.0

    inter = vol_services & need_services
    return len(inter) / len(need_services)


def extract_slots(text):
    slots = set()
    for d in DAYS:
        for t in TIMES:
            phrase = f"{d} {t}"
            if phrase in text:
                slots.add(phrase)
    return slots


def time_overlap_score(vol_text, senior_text):
    vol_slots = extract_slots(vol_text)
    need_slots = extract_slots(senior_text)

    if not need_slots:
        return 1.0

    inter = vol_slots & need_slots
    return len(inter) / len(need_slots)


def extract_city(text):
    text_lower = text.lower()
    if "toronto" in text_lower:
        return "toronto"
    if "markham" in text_lower:
        return "markham"
    if "mississauga" in text_lower:
        return "mississauga"
    return "other"


def location_match_score(vol_text, senior_text):
    vol_city = extract_city(vol_text)
    senior_city = extract_city(senior_text)

    if senior_city == "other":
        return 1.0

    return 1.0 if vol_city == senior_city else 0.0



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
    svc_score = service_match_score(vol_text, core_need_text)
    time_score = time_overlap_score(vol_text, core_need_text)
    loc_score = location_match_score(vol_text, core_need_text)

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

    final = 0.10 * entail_core + 0.25 * svc_score + 0.35 * time_score +  0.20 * loc_score + 0.10 * add_score

    return {
        "final_score": final,
        "entail_core": entail_core,
        "service_match": svc_score,
        "time_overlap": time_score,
        "location_match": loc_score,
        "addition_req": add_score,
        "disqualified": False,
    }

def get_score(prob):
    w_c = -0.5   
    w_n = 0.1    
    w_e = 1.0 

    p_c = prob["contradiction"]
    p_n = prob["neutral"]
    p_e = prob["entailment"]

    max_raw = w_e
    min_raw = w_c
    raw_score = w_e * p_e + w_n * p_n + w_c * p_c

    final_score = (raw_score - min_raw) / (max_raw - min_raw)
    return final_score


def matching(senior_text, candidate_labels, tokenizer,model):
    # model_path = "facebook/bart-large-mnli"
    # tokenizer = AutoTokenizer.from_pretrained(model_path)
    # model = AutoModelForSequenceClassification.from_pretrained(model_path)


    core_need_text, extra_req_text = split_senior_need(senior_text)
    # print("Core need text   :", core_need_text)
    # print("Extra req text   :", extra_req_text if extra_req_text else "(none)")
    # print("-" * 80)

    results = []

    for i, volunteer in enumerate(candidate_labels):
        nli_core = nli_label_probs(model, tokenizer, volunteer, core_need_text)
        core_score=get_score(nli_core)
        # print('core_score:' + str(core_score))
        # entail_core = nli_core.get("ENTAILMENT", nli_core.get("entailment", 0.0))
        entail_core=core_score

        if extra_req_text:
            nli_extra = nli_label_probs(model, tokenizer, volunteer, extra_req_text)
            extra_score=get_score(nli_extra)
            # print('extra_score:' + str(extra_score))
            # entail_extra = nli_extra.get("ENTAILMENT", nli_extra.get("entailment", 0.0))
            entail_extra=extra_score
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

    # end = time.time()
    # for rank, (final_score, scores, nli_core, nli_extra, idx, vol) in enumerate(results, start=1):
    #     print(f"Rank {rank}  (candidate #{idx})")
    #     print(f"  final_score     = {final_score:.4f}")
    #     print(f"  entail_core     = {scores['entail_core']:.4f}")
    #     print(f"  service_match   = {scores['service_match']:.4f}")
    #     print(f"  time_overlap    = {scores['time_overlap']:.4f}")
    #     print(f"  location_match  = {scores['location_match']:.4f}")
    #     print(f"  addition_req    = {scores['addition_req']:.4f}")
    #     print(f"  disqualified    = {scores.get('disqualified', False)}")
    #     print(f"  NLI core probs  = {nli_core}")
    #     if nli_extra is not None:
    #         print(f"  NLI extra probs = {nli_extra}")
    #     else:
    #         print("  NLI extra probs = (no extra requirement)")
    #     print(f"  volunteer snippet: {vol[:120]}...")
    #     print("-" * 80)

    # print("Elapsed time:", end - start, "seconds")



