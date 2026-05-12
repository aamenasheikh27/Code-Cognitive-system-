import re
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from modules.metrics import generate_metrics

ZERO_SHOT_CLASSIFIER = None
EMBEDDING_MODEL = None
EMBEDDINGS_CACHE = None
FUNC_DESC_CACHE = None
FUNC_NAME_CACHE = None


def prettify_name(name):
    name = name.replace("_", " ")
    name = re.sub(r"([a-z])([A-Z])", r"\1 \2", name)
    return name.lower().strip()


def summarize_function(func_info):
    sentences = []
    sentences.append(f"Function name is {func_info.get('name', 'unknown')}")
    sentences.append(f"It takes arguments {func_info.get('args', [])}")
    sentences.append(f"It calls these functions {func_info.get('calls', [])}")

    docstring = func_info.get("docstring")
    if docstring:
        sentences.append(docstring)

    if len(sentences) < 2:
        return sentences[0] if sentences else "No info available"

    vectorizer = TfidfVectorizer()
    tfidf_matrix = vectorizer.fit_transform(sentences)
    scores = np.array(tfidf_matrix.sum(axis=1)).flatten()

    top_indices = scores.argsort()[-2:][::-1]
    summary = ". ".join([sentences[i] for i in sorted(top_indices)])
    return summary


def get_zero_shot_classifier():
    global ZERO_SHOT_CLASSIFIER
    if ZERO_SHOT_CLASSIFIER is None:
        from transformers import pipeline
        ZERO_SHOT_CLASSIFIER = pipeline(
            "zero-shot-classification",
            model="facebook/bart-large-mnli"
        )
    return ZERO_SHOT_CLASSIFIER


def detect_intent(user_question):
    intents = [
        "explain what a function does",
        "show dependencies between files",
        "show code flow",
        "find risky or buggy areas",
        "general code summary"
    ]

    try:
        classifier = get_zero_shot_classifier()
        result = classifier(user_question, candidate_labels=intents)
        return result["labels"][0]
    except Exception:
        q = user_question.lower()
        if "bug" in q or "risk" in q:
            return "find risky or buggy areas"
        if "flow" in q or "workflow" in q:
            return "show code flow"
        if "dependency" in q or "connected" in q:
            return "show dependencies between files"
        if "what does" in q or "explain" in q:
            return "explain what a function does"
        return "general code summary"


def build_function_descriptions(parsed):
    descriptions = []
    for func in parsed.get("functions", []):
        descriptions.append({
            "name": func["name"],
            "text": (
                f"Function {func['name']} takes {func.get('args', [])}, "
                f"calls {func.get('calls', [])}, "
                f"and has docstring {func.get('docstring', '')}"
            ),
            "args": func.get("args", []),
            "calls": func.get("calls", [])
        })
    return descriptions


def get_embedding_model():
    global EMBEDDING_MODEL
    if EMBEDDING_MODEL is None:
        from sentence_transformers import SentenceTransformer
        EMBEDDING_MODEL = SentenceTransformer("all-MiniLM-L6-v2")
    return EMBEDDING_MODEL


def prepare_semantic_search(parsed):
    global EMBEDDINGS_CACHE, FUNC_DESC_CACHE, FUNC_NAME_CACHE

    descriptions = build_function_descriptions(parsed)
    if not descriptions:
        EMBEDDINGS_CACHE = None
        FUNC_DESC_CACHE = []
        FUNC_NAME_CACHE = []
        return

    model = get_embedding_model()
    texts = [item["text"] for item in descriptions]

    EMBEDDINGS_CACHE = model.encode(texts, convert_to_tensor=True)
    FUNC_DESC_CACHE = descriptions
    FUNC_NAME_CACHE = [item["name"] for item in descriptions]


def find_function(user_query, parsed=None):
    global EMBEDDINGS_CACHE, FUNC_DESC_CACHE, FUNC_NAME_CACHE

    if parsed is not None:
        try:
            prepare_semantic_search(parsed)
        except Exception:
            FUNC_DESC_CACHE = build_function_descriptions(parsed)
            FUNC_NAME_CACHE = [item["name"] for item in FUNC_DESC_CACHE]
            EMBEDDINGS_CACHE = None

    if FUNC_DESC_CACHE is None:
        FUNC_DESC_CACHE = []
    if FUNC_NAME_CACHE is None:
        FUNC_NAME_CACHE = []

    if EMBEDDINGS_CACHE is None:
        q = user_query.lower()
        best = None
        best_score = -1

        for item in FUNC_DESC_CACHE:
            score = 0
            name = item["name"].lower()
            text = item["text"].lower()

            for word in q.split():
                if word in name:
                    score += 3
                if word in text:
                    score += 1

            if score > best_score:
                best_score = score
                best = item

        if best:
            return {
                "function": best["name"],
                "score": float(best_score),
                "description": best["text"],
                "args": best["args"],
                "calls": best["calls"]
            }

        return {
            "function": "No function found",
            "score": 0.0,
            "description": "No relevant function matched the question.",
            "args": [],
            "calls": []
        }

    from sentence_transformers import util

    model = get_embedding_model()
    query_embedding = model.encode(user_query, convert_to_tensor=True)
    scores = util.cos_sim(query_embedding, EMBEDDINGS_CACHE)[0]
    best_idx = int(scores.argmax())

    best = FUNC_DESC_CACHE[best_idx]
    return {
        "function": FUNC_NAME_CACHE[best_idx],
        "score": float(scores[best_idx]),
        "description": best["text"],
        "args": best["args"],
        "calls": best["calls"]
    }


def detect_system_type(parsed):
    imports = [imp.lower() for imp in parsed.get("imports", [])]
    functions = parsed.get("functions", [])
    
    names = [f["name"].lower() for f in functions]
    calls = []
    for f in functions:
        calls.extend([c.lower() for c in f.get("calls", []) if isinstance(c, str)])
        
    categories = {
        "Authentication system": {
            "imports": ["jwt", "oauth", "hashlib", "bcrypt", "hmac", "secrets"],
            "keywords": ["login", "logout", "authenticate", "verify", "hash", "token", "password", "auth", "credential"]
        },
        "CRUD system": {
            "imports": ["sqlalchemy", "pymongo", "psycopg2", "sqlite3", "mysql", "redis", "database"],
            "keywords": ["create", "read", "update", "delete", "insert", "select", "save", "load", "db", "query", "record"]
        },
        "Machine learning pipeline": {
            "imports": ["sklearn", "tensorflow", "torch", "keras", "xgboost", "lightgbm", "transformers"],
            "keywords": ["train", "predict", "fit", "evaluate", "model", "score", "dataset", "neural", "tensor"]
        },
        "Data processing": {
            "imports": ["pandas", "numpy", "csv", "json", "re", "xml", "bs4", "beautifulsoup", "lxml"],
            "keywords": ["process", "clean", "transform", "filter", "parse", "format", "extract", "aggregate", "sort", "merge"]
        },
        "API/backend system": {
            "imports": ["flask", "django", "fastapi", "requests", "urllib", "http", "werkzeug", "starlette", "httpx"],
            "keywords": ["get", "post", "put", "delete", "route", "endpoint", "request", "response", "api", "server", "middleware"]
        }
    }

    scores = {cat: 0 for cat in categories}
    reasons = {cat: [] for cat in categories}
    
    for cat, data in categories.items():
        found_imports = list(set([imp for imp in imports if any(target in imp for target in data["imports"])]))
        if found_imports:
            scores[cat] += len(found_imports) * 2
            reasons[cat].append(f"it imports {', '.join(found_imports)}")
            
        found_names = list(set([name for name in names if any(kw in name for kw in data["keywords"])]))
        if found_names:
            scores[cat] += len(found_names)
            reasons[cat].append(f"it defines functions like {', '.join(found_names)}")
            
        found_calls = list(set([call for call in calls if any(kw in call for kw in data["keywords"])]))
        if found_calls:
            scores[cat] += len(found_calls) * 0.5
            reasons[cat].append(f"it calls related functions like {', '.join(found_calls)}")
            
    best_category = max(scores, key=scores.get)
    if scores[best_category] > 0:
        reason_str = " and ".join(reasons[best_category][:2])
        return f"This code represents a {best_category} because {reason_str}."
    else:
        return "This code represents a general software system because it lacks specific domain imports or functional patterns."


def workflow_to_sentence(flow):
    readable = [prettify_name(x) for x in flow]

    if not readable:
        return "No strong workflow path was detected."

    if len(readable) == 1:
        return f"The main workflow appears to center around {readable[0]}."

    if len(readable) == 2:
        return f"The primary flow is: {readable[0]} → {readable[1]}."

    return f"The primary flow is: {' → '.join(readable)}."


def generate_nlp_explanation(parsed):
    metrics = generate_metrics(parsed)

    system_type = detect_system_type(parsed)
    workflow = workflow_to_sentence(metrics["main_flow"])
    complexity = metrics["complexity"]["level"]
    coupling = metrics["coupling"]["level"]
    modularity = metrics["modularity"]["level"]

    explanation = []
    explanation.append(system_type)
    explanation.append(workflow)
    explanation.append(
        f"The structure shows {complexity.lower()} complexity, {coupling.lower()} coupling, and {modularity.lower()} modularity."
    )

    if metrics["isolated_functions"]:
        isolated = ", ".join(metrics["isolated_functions"])
        explanation.append(
            f"Some functions appear to be standalone utilities, such as {isolated}."
        )

    if metrics["central_function"]:
        explanation.append(
            f"The code flow is centered around {metrics['central_function']}(), which appears to coordinate much of the internal behavior."
        )

    return "\n\n".join(explanation)