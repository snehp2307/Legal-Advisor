from app.models.embedding import EmbeddingModel
from app.services.vector_store import client
from app.utils.config import COLLECTION_NAME

embedder = EmbeddingModel()

# ── Constants ──────────────────────────────────────────────────────────────────
LAW_BOOST        = 1.5   # Score multiplier for matching law type
KEYWORD_BOOST    = 0.5   # Score bonus per matching keyword in title
FETCH_MULTIPLIER = 4     # How many extra results to fetch before trimming


# ── Law type detection ─────────────────────────────────────────────────────────
# Maps each law to a list of (keyword, weight) pairs.
# Higher weight = stronger signal for that law.

LAW_KEYWORDS = {
    "constitution": [
        ("right to life", 4), ("personal liberty", 4), ("fundamental right", 4),
        ("pardon", 4), ("self incrimination", 4), ("witness against himself", 4),
        ("compelled to be a witness", 4), ("forced to be a witness", 4),
        ("double jeopardy", 4), ("right to privacy", 4), ("right to education", 4),
        ("right to equality", 3), ("freedom of speech", 3), ("directive principles", 3),
        ("president power", 3), ("article", 2), ("constitution", 2),
        ("preamble", 1), ("amendment", 1), ("citizenship", 1),
    ],
    "bns": [
        ("murder", 4), ("cheating", 4), ("theft", 4), ("rape", 4),
        ("sedition", 4), ("culpable homicide", 4), ("false promise of marriage", 4),
        ("minor death penalty", 3), ("robbery", 3), ("fraud", 3),
        ("crime", 2), ("punishment", 2), ("criminal offense", 2),
        ("criminal", 1), ("offense", 1),
    ],
    "crpc": [
        ("anticipatory bail", 4), ("arrested without warrant", 4),
        ("arrest without warrant", 4), ("bail", 3), ("arrest", 3),
        ("fir", 3), ("warrant", 3), ("trial", 2), ("investigation", 2),
        ("police", 1), ("procedure", 1),
    ],
    "cpc": [
        ("civil suit", 4), ("injunction", 3), ("decree", 3),
        ("appeal", 2), ("plaint", 2), ("civil", 1),
    ],
    "ida": [
        ("industrial dispute", 4), ("illegally terminates", 4),
        ("wrongful termination", 4), ("retrenchment", 4), ("illegally fired", 4),
        ("company terminates", 3), ("strike", 2), ("lockout", 2),
        ("labour", 2), ("worker", 2), ("employee", 2), ("wages", 1),
    ],
    "mva": [
        ("speed limit", 4), ("maximum speed", 4), ("drunk driving", 4),
        ("highway speed", 4), ("traffic violation", 3), ("license", 2),
        ("traffic", 2), ("vehicle", 2), ("accident", 2), ("highway", 2), ("road", 1),
    ],
}

# Prefix added to query when no specific rewrite matches.
LAW_PREFIXES = {
    "constitution": "Indian constitution fundamental rights article: ",
    "bns":          "Indian penal law BNS offense definition section: ",
    "crpc":         "Indian criminal procedure code CrPC section: ",
    "cpc":          "Indian civil procedure code section: ",
    "ida":          "Indian industrial disputes act section: ",
    "mva":          "Indian motor vehicles act section: ",
}

# Exact phrase → enriched search query rewrites.
# Sorted longest-first at runtime so the most specific phrase matches first.
PHRASE_REWRITES = {
    # Constitution
    "compelled to be a witness":        "Article 20 self incrimination accused compelled witness against himself constitution fundamental right",
    "forced to be a witness":           "Article 20 self incrimination accused compelled witness against himself constitution fundamental right",
    "witness against himself":          "Article 20 self incrimination accused compelled witness against himself constitution fundamental right",
    "self-incrimination":               "Article 20 self incrimination accused compelled witness constitution",
    "double jeopardy":                  "Article 20 double jeopardy convicted prosecuted same offense constitution protection",
    "right to life":                    "Article 21 right to life personal liberty no person deprived constitution",
    "right to privacy":                 "Article 21 right to privacy personal liberty constitution",
    "right to education":               "Article 21A free compulsory education children constitution",
    "pardon a death sentence":          "Article 72 president power grant pardon reprieve respite death sentence constitution",
    "power to pardon":                  "Article 72 president power grant pardon reprieve respite death sentence constitution",
    "pardon":                           "Article 72 president power grant pardon reprieve respite death sentence constitution",
    # BNS
    "false promise of marriage":        "section 69 sexual intercourse deceitful means false promise marriage consent BNS",
    "consensual physical relationship": "section 69 sexual intercourse deceitful means false promise marriage consent BNS",
    "dies during a strike":             "section 103 murder culpable homicide death group acts punishment BNS",
    "minor death penalty":              "section 103 section 27 minor child age offender punishment death sentence BNS",
    "minor be given death":             "section 103 section 27 minor child age offender punishment death sentence BNS",
    "sedition":                         "section 152 acts endangering sovereignty integrity unity india punishment BNS",
    "murder":                           "section 103 murder culpable homicide death punishment imprisonment life BNS",
    "cheating":                         "section 318 cheating deceives dishonestly induces wrongful gain loss offense BNS",
    "theft":                            "section 303 theft dishonestly takes moveable property without consent BNS",
    # CrPC
    "anticipatory bail":                "section 438 anticipatory bail apprehension arrest direction court CrPC BNSS",
    "arrested without warrant":         "section 35 section 41 arrest without warrant police cognizable offense CrPC",
    "arrest without warrant":           "section 35 section 41 arrest without warrant police cognizable offense CrPC",
    # IDA
    "illegally terminates workers":     "section 25 retrenchment workman industrial dispute compensation notice IDA",
    "illegally terminates":             "section 25 retrenchment workman industrial dispute compensation notice IDA",
    "wrongful termination":             "section 25 retrenchment workman industrial dispute compensation notice IDA",
    "penalty for a company":            "section 25 retrenchment workman industrial dispute compensation notice IDA",
    "company that illegally":           "section 25 retrenchment workman industrial dispute compensation notice IDA",
    # MVA
    "maximum speed limit":              "section 112 maximum speed limit vehicle highway road motor vehicles act MVA",
    "speed limit on highways":          "section 112 maximum speed limit vehicle highway road motor vehicles act MVA",
    "speed limit":                      "section 112 maximum speed limit vehicle highway road motor vehicles act MVA",
    "maximum speed":                    "section 112 maximum speed limit vehicle highway road motor vehicles act MVA",
}


# ── Step 1: Detect which law the query is about ────────────────────────────────
def detect_law_type(query: str) -> str | None:
    """Score each law by how many of its keywords appear in the query.
    Returns the best-matching law name, or None if nothing matched."""
    scores = {law: 0 for law in LAW_KEYWORDS}

    for law, keywords in LAW_KEYWORDS.items():
        for phrase, weight in keywords:
            if phrase in query:
                scores[law] += weight

    best_law  = max(scores, key=scores.get)
    best_score = scores[best_law]

    return best_law if best_score > 0 else None


# ── Step 2: Build an enriched search query ─────────────────────────────────────
def build_enriched_query(query: str, law_type: str | None) -> str:
    """Try to match a specific phrase rewrite first (longest match wins).
    Fall back to prepending a law-specific prefix to the original query."""

    # Sort rewrites by phrase length so longer/more-specific phrases match first
    sorted_rewrites = sorted(PHRASE_REWRITES.items(), key=lambda x: len(x[0]), reverse=True)

    for phrase, rewrite in sorted_rewrites:
        if phrase in query:
            return rewrite

    # No specific rewrite found — use law prefix + original query
    prefix = LAW_PREFIXES.get(law_type, "Indian law: ")
    return f"{prefix}{query}"


# ── Step 3: Fetch results using both enriched and original query ───────────────
def fetch_results(original_query: str, enriched_query: str, fetch_limit: int) -> list:
    """Embed both queries, run vector search for each, then merge results.
    When the same chunk appears in both result sets, keep the higher score."""

    vec_enriched = embedder.encode([f"query: {enriched_query}"])[0]
    vec_original = embedder.encode([f"query: {original_query}"])[0]

    hits_enriched = client.query_points(
        collection_name=COLLECTION_NAME,
        query=vec_enriched,
        limit=fetch_limit,
    ).points

    hits_original = client.query_points(
        collection_name=COLLECTION_NAME,
        query=vec_original,
        limit=fetch_limit // 2,
    ).points

    # Deduplicate: for each unique chunk keep only the highest score
    best = {}
    for hit in hits_enriched + hits_original:
        key = (hit.payload.get("id"), hit.payload.get("text", "")[:50])
        if key not in best or hit.score > best[key].score:
            best[key] = hit

    return list(best.values())


# ── Step 4: Boost scores for chunks whose title overlaps with the query ────────
def rerank_by_keywords(results: list, query: str) -> list:
    """Give a small score bonus when query words appear in the chunk title."""
    query_words = set(query.split())

    for hit in results:
        title       = (hit.payload.get("title") or "").lower()
        title_words = set(title.split())
        overlap     = len(query_words & title_words)

        if overlap > 0:
            hit.score += KEYWORD_BOOST * overlap

        # Extra bonus if the chunk's id is mentioned directly in the query
        chunk_id = (hit.payload.get("id") or "").lower()
        if chunk_id in query:
            hit.score += KEYWORD_BOOST * 2

    return results


# ── Main entry point ───────────────────────────────────────────────────────────
def retrieve(query: str, top_k: int = 5) -> list[dict]:
    """Full retrieval pipeline:
    1. Detect law type
    2. Build enriched query
    3. Dual vector search + merge
    4. Boost chunks matching the detected law
    5. Keyword rerank
    6. Return top_k results
    """
    query = query.lower()

    law_type       = detect_law_type(query)
    enriched_query = build_enriched_query(query, law_type)

    print(f"[DEBUG] Law: {law_type} | Query: {enriched_query}")

    results = fetch_results(query, enriched_query, fetch_limit=top_k * FETCH_MULTIPLIER)

    # Boost chunks that belong to the detected law
    if law_type:
        for hit in results:
            if hit.payload.get("type") == law_type:
                hit.score *= LAW_BOOST

    results = rerank_by_keywords(results, query)
    results = sorted(results, key=lambda x: x.score, reverse=True)[:top_k]

    return [
        {
            "type":  hit.payload["type"],
            "id":    hit.payload["id"],
            "title": hit.payload["title"],
            "text":  hit.payload["text"],
            "score": hit.score,
        }
        for hit in results
    ]