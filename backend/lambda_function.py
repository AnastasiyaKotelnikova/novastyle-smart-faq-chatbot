import json
import math
import string

# ---------- Load FAQ data once (when Lambda container starts) ----------

with open("faq_data.json", "r", encoding="utf-8") as f:
    FAQS = json.load(f)

# Preprocess text: lowercase, remove punctuation, simple tokenization
PUNCT_TABLE = str.maketrans("", "", string.punctuation)
STOPWORDS = {
    "the", "is", "a", "an", "and", "or", "to", "of", "in", "for", "on",
    "with", "at", "by", "from", "how", "what", "which", "do", "you", "your"
}


def tokenize(text):
    text = text.lower().translate(PUNCT_TABLE)
    tokens = [t for t in text.split() if t and t not in STOPWORDS]
    return tokens


# Build vocabulary and IDF over FAQ questions (corpus)
VOCAB = set()
DOC_TOKENS = []  # list of token lists for each FAQ question
for faq in FAQS:
    tokens = tokenize(faq["question"])
    DOC_TOKENS.append(tokens)
    VOCAB.update(tokens)

VOCAB = sorted(VOCAB)  # fixed order
TERM_INDEX = {term: i for i, term in enumerate(VOCAB)}

# Compute document frequency for each term
doc_freq = [0] * len(VOCAB)
num_docs = len(DOC_TOKENS)
for tokens in DOC_TOKENS:
    seen = set(tokens)
    for term in seen:
        doc_freq[TERM_INDEX[term]] += 1

# Compute IDF values
IDF = [math.log((num_docs + 1) / (df + 1)) + 1 for df in doc_freq]


def tfidf_vector(tokens):
    """Compute TF-IDF vector for a token list."""
    vec = [0.0] * len(VOCAB)
    if not tokens:
        return vec
    # term frequency
    counts = {}
    for t in tokens:
        if t in TERM_INDEX:
            counts[t] = counts.get(t, 0) + 1
    # build vector
    for term, count in counts.items():
        idx = TERM_INDEX[term]
        tf = count / len(tokens)
        vec[idx] = tf * IDF[idx]
    return vec


def cosine_similarity(v1, v2):
    dot = 0.0
    norm1 = 0.0
    norm2 = 0.0
    for a, b in zip(v1, v2):
        dot += a * b
        norm1 += a * a
        norm2 += b * b
    if norm1 == 0 or norm2 == 0:
        return 0.0
    return dot / (math.sqrt(norm1) * math.sqrt(norm2))


# Precompute TF-IDF vectors for FAQ questions
FAQ_VECTORS = [tfidf_vector(tokens) for tokens in DOC_TOKENS]


def find_best_faq(user_message):
    tokens = tokenize(user_message)
    query_vec = tfidf_vector(tokens)

    best_sim = 0.0
    best_faq = None

    for faq, faq_vec in zip(FAQS, FAQ_VECTORS):
        sim = cosine_similarity(query_vec, faq_vec)
        if sim > best_sim:
            best_sim = sim
            best_faq = faq

    return best_faq, best_sim


def build_response(status_code, body_obj):
    return {
        "statusCode": status_code,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",  # allow all origins for now
            "Access-Control-Allow-Headers": "Content-Type",
            "Access-Control-Allow-Methods": "OPTIONS,POST"
        },
        "body": json.dumps(body_obj)
    }


def lambda_handler(event, context):
    """
    Expected event (from API Gateway HTTP API or REST API proxy):
    {
      "body": "{\"message\": \"your text here\"}"
    }
    """
    try:
        body = event.get("body")
        if body is None:
            return build_response(400, {"error": "Missing request body."})

        # body may be a JSON string
        if isinstance(body, str):
            body = json.loads(body)

        user_message = body.get("message", "").strip()

        if not user_message:
            return build_response(400, {"error": "Empty message."})

        # Find best matching FAQ
        best_faq, best_sim = find_best_faq(user_message)

        # Threshold for confidence
        THRESHOLD = 0.2

        if best_faq is None or best_sim < THRESHOLD:
            answer = (
                "I’m not completely sure about that one. "
                "Try rephrasing your question or asking about shipping, returns, orders, or payments."
            )
            matched_question = None
        else:
            answer = best_faq["answer"]
            matched_question = best_faq["question"]

        return build_response(200, {
            "answer": answer,
            "matched_question": matched_question,
            "similarity": round(best_sim, 3)
        })

    except Exception as e:
        # Basic error handling
        return build_response(500, {"error": "Internal server error.", "details": str(e)})
