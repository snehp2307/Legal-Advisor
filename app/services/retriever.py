from app.models.embedding import EmbeddingModel
from app.services.vector_store import client
from app.utils.config import COLLECTION_NAME

embedder = EmbeddingModel()

LAW_TYPE_BOOST = 1.5
RETRIEVAL_MULTIPLIER = 4
KEYWORD_BOOST = 0.5


def detect_law_type(query: str) -> str | None:
    query = query.lower()

    law_keywords = {
        "constitution": [
            ("right to life", 4),
            ("personal liberty", 4),
            ("fundamental right", 4),
            ("pardon", 4),
            ("self incrimination", 4),
            ("witness against himself", 4),
            ("compelled to be a witness", 4),
            ("forced to be a witness", 4),
            ("double jeopardy", 4),
            ("right to privacy", 4),
            ("right to education", 4),
            ("right to equality", 3),
            ("freedom of speech", 3),
            ("directive principles", 3),
            ("president power", 3),
            ("article", 2),
            ("constitution", 2),
            ("preamble", 1),
            ("amendment", 1),
            ("citizenship", 1),
        ],
        "bns": [
            ("murder", 4),
            ("cheating", 4),
            ("theft", 4),
            ("rape", 4),
            ("sedition", 4),
            ("culpable homicide", 4),
            ("false promise of marriage", 4),
            ("minor death penalty", 3),
            ("robbery", 3),
            ("fraud", 3),
            ("crime", 2),
            ("punishment", 2),
            ("criminal offense", 2),
            ("criminal", 1),
            ("offense", 1),
        ],
        "crpc": [
            ("anticipatory bail", 4),
            ("arrested without warrant", 4),
            ("arrest without warrant", 4),
            ("bail", 3),
            ("arrest", 3),
            ("fir", 3),
            ("warrant", 3),
            ("trial", 2),
            ("investigation", 2),
            ("police", 1),
            ("procedure", 1),
        ],
        "cpc": [
            ("civil suit", 4),
            ("injunction", 3),
            ("decree", 3),
            ("appeal", 2),
            ("plaint", 2),
            ("civil", 1),
        ],
        "ida": [
            ("industrial dispute", 4),
            ("illegally terminates", 4),
            ("wrongful termination", 4),
            ("retrenchment", 4),
            ("illegally fired", 4),
            ("company terminates", 3),
            ("strike", 2),
            ("lockout", 2),
            ("labour", 2),
            ("worker", 2),
            ("employee", 2),
            ("wages", 1),
        ],
        "mva": [
            ("speed limit", 4),
            ("maximum speed", 4),
            ("drunk driving", 4),
            ("highway speed", 4),
            ("traffic violation", 3),
            ("license", 2),
            ("traffic", 2),
            ("vehicle", 2),
            ("accident", 2),
            ("highway", 2),
            ("road", 1),
        ],
    }

    scores = {law: 0 for law in law_keywords}
    for law, keywords in law_keywords.items():
        for keyword, weight in keywords:
            if keyword in query:
                scores[law] += weight

    best = max(scores, key=scores.get)
    return best if scores[best] > 0 else None


SPECIFIC_REWRITES = {
    # Constitution — Article 20
    "compelled to be a witness":          "Article 20 self incrimination accused compelled witness against himself constitution fundamental right",
    "forced to be a witness":             "Article 20 self incrimination accused compelled witness against himself constitution fundamental right",
    "witness against himself":            "Article 20 self incrimination accused compelled witness against himself constitution fundamental right",
    "self-incrimination":                 "Article 20 self incrimination accused compelled witness constitution",
    "double jeopardy":                    "Article 20 double jeopardy convicted prosecuted same offense constitution protection",

    # Constitution — Article 21
    "right to life":                      "Article 21 right to life personal liberty no person deprived constitution",
    "right to privacy":                   "Article 21 right to privacy personal liberty constitution",
    "right to education":                 "Article 21A free compulsory education children constitution",

    # Constitution — Article 72
    "pardon a death sentence":            "Article 72 president power grant pardon reprieve respite death sentence constitution",
    "power to pardon":                    "Article 72 president power grant pardon reprieve respite death sentence constitution",
    "pardon":                             "Article 72 president power grant pardon reprieve respite death sentence constitution",

    # BNS
    "false promise of marriage":          "section 69 sexual intercourse deceitful means false promise marriage consent BNS",
    "consensual physical relationship":   "section 69 sexual intercourse deceitful means false promise marriage consent BNS",
    "dies during a strike":               "section 103 murder culpable homicide death group acts punishment BNS",
    "minor death penalty":                "section 103 section 27 minor child age offender punishment death sentence BNS",
    "minor be given death":               "section 103 section 27 minor child age offender punishment death sentence BNS",
    "sedition":                           "section 152 acts endangering sovereignty integrity unity india punishment BNS",
    "murder":                             "section 103 murder culpable homicide death punishment imprisonment life BNS",
    "cheating":                           "section 318 cheating deceives dishonestly induces wrongful gain loss offense BNS",
    "theft":                              "section 303 theft dishonestly takes moveable property without consent BNS",

    # CrPC
    "anticipatory bail":                  "section 438 anticipatory bail apprehension arrest direction court CrPC BNSS",
    "arrested without warrant":           "section 35 section 41 arrest without warrant police cognizable offense CrPC",
    "arrest without warrant":             "section 35 section 41 arrest without warrant police cognizable offense CrPC",

    # IDA
    "illegally terminates workers":       "section 25 retrenchment workman industrial dispute compensation notice IDA",
    "illegally terminates":               "section 25 retrenchment workman industrial dispute compensation notice IDA",
    "wrongful termination":               "section 25 retrenchment workman industrial dispute compensation notice IDA",
    "penalty for a company":              "section 25 retrenchment workman industrial dispute compensation notice IDA",
    "company that illegally":             "section 25 retrenchment workman industrial dispute compensation notice IDA",

    # MVA
    "maximum speed limit":                "section 112 maximum speed limit vehicle highway road motor vehicles act MVA",
    "speed limit on highways":            "section 112 maximum speed limit vehicle highway road motor vehicles act MVA",
    "speed limit":                        "section 112 maximum speed limit vehicle highway road motor vehicles act MVA",
    "maximum speed":                      "section 112 maximum speed limit vehicle highway road motor vehicles act MVA",
}

EXPANSION_MAP = {
    "constitution": "Indian constitution fundamental rights article: ",
    "bns": "Indian penal law BNS offense definition section: ",
    "crpc": "Indian criminal procedure code CrPC section: ",
    "cpc": "Indian civil procedure code section: ",
    "ida": "Indian industrial disputes act section: ",
    "mva": "Indian motor vehicles act section: ",
}


def build_query(original_query: str, law_type: str | None) -> str:
    # Sort by key length descending — match most specific phrase first
    sorted_rewrites = sorted(SPECIFIC_REWRITES.items(), key=lambda x: len(x[0]), reverse=True)

    for phrase, rewrite in sorted_rewrites:
        if phrase in original_query:
            return rewrite

    prefix = EXPANSION_MAP.get(law_type, "Indian law: ")
    return f"{prefix}{original_query}"



def dual_retrieve(original_query: str, enriched_query: str, fetch_limit: int):
    vec_enriched = embedder.encode([enriched_query])[0]
    vec_original = embedder.encode([original_query])[0]

    results_enriched = client.query_points(
        collection_name=COLLECTION_NAME,
        query=vec_enriched,
        limit=fetch_limit,
    ).points

    results_original = client.query_points(
        collection_name=COLLECTION_NAME,
        query=vec_original,
        limit=fetch_limit // 2,
    ).points

    # Merge by id — keep highest score per chunk
    seen = {}
    for r in results_enriched + results_original:
        key = (r.payload.get("id"), r.payload.get("text", "")[:50])
        if key not in seen or r.score > seen[key].score:
            seen[key] = r

    return list(seen.values())


def keyword_rerank(results, query: str, boost: float = KEYWORD_BOOST):
    query_words = set(query.lower().split())

    for r in results:
        title = r.payload.get("title") or ""
        doc_id = r.payload.get("id") or ""

        title_words = set(title.lower().split())
        overlap = len(query_words & title_words)

        if overlap > 0:
            r.score += boost * overlap

        if doc_id.lower() in query.lower():
            r.score += boost * 2

    return results


def retrieve(query: str, top_k: int = 5):
    original_query = query.lower()

    
    law_type = detect_law_type(original_query)

    
    enriched_query = build_query(original_query, law_type)

    print(f"[DEBUG] Law: {law_type} | Query: {enriched_query}")

    bge_enriched = f"query: {enriched_query}"
    bge_original = f"query: {original_query}"

    fetch_limit = top_k * RETRIEVAL_MULTIPLIER
    results = dual_retrieve(bge_original, bge_enriched, fetch_limit)

   
    if law_type:
        for r in results:
            if r.payload.get("type") == law_type:
                r.score *= LAW_TYPE_BOOST

   
    results = keyword_rerank(results, original_query)

    results = sorted(results, key=lambda x: x.score, reverse=True)[:top_k]

    return [
        {
            "type": r.payload["type"],
            "id": r.payload["id"],
            "title": r.payload["title"],
            "text": r.payload["text"],
            "score": r.score,
        }
        for r in results
    ]