# routes/chat_routes.py
# LokSeva Advanced Chatbot — v2.0
#
# Features:
#   ✅ Session-based conversation memory (remembers full chat history)
#   ✅ Live DB queries for complaint data
#   ✅ Auto language detection (script + langdetect)
#   ✅ Clarifying questions for ambiguous queries
#   ✅ Context-aware follow-up handling
#   ✅ ML intent classification with TF-IDF pipeline
#   ✅ Special DB intents: __DB_COMPLAINT_STATUS__
#
# Place utils/lang_detector.py in your utils/ folder
# Install: pip install langdetect --break-system-packages

import os
import pickle
import random
from datetime import datetime
from flask import Blueprint, request, jsonify, session
from flask_login import current_user

# ── Blueprint ────────────────────────────────────────────────────────────────
chat_bp = Blueprint('chat', __name__)

# ── Paths ────────────────────────────────────────────────────────────────────
BASE_DIR   = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(BASE_DIR, '..', 'chatbot_model.pkl')

# ── Preprocessing (defined here, NOT loaded from pickle) ─────────────────────
# Keeping this in chat_routes.py avoids the AttributeError that occurs when
# a pickled function defined in train_advanced.py's __main__ is unpickled
# from Flask's app.py __main__ context.
import nltk
try:
    from nltk.stem import WordNetLemmatizer
    from nltk.tokenize import word_tokenize
    from nltk.corpus import stopwords
    nltk.download('punkt',     quiet=True)
    nltk.download('punkt_tab', quiet=True)
    nltk.download('wordnet',   quiet=True)
    nltk.download('stopwords', quiet=True)
    _lemmatizer = WordNetLemmatizer()
    _stop_words = set(stopwords.words('english'))
    _IGNORE_CHARS = set('?!.,;:-_')

    def _preprocess_text(text: str) -> str:
        tokens = word_tokenize(text.lower())
        tokens = [
            _lemmatizer.lemmatize(t) for t in tokens
            if t not in _IGNORE_CHARS and t not in _stop_words and t.isalpha()
        ]
        return ' '.join(tokens) if tokens else text.lower()

except Exception:
    def _preprocess_text(text: str) -> str:
        return text.lower()

# ── Model globals (loaded once at startup) ───────────────────────────────────
_pipeline      = None
_label_encoder = None
_intents       = None
_model_version = None

# ── Confidence threshold ─────────────────────────────────────────────────────
CONFIDENCE_THRESHOLD  = 0.35   # below this → clarifying question
CLARIFY_THRESHOLD     = 0.20   # below this → full fallback


def load_model():
    global _pipeline, _label_encoder, _intents, _preprocess, _model_version
    if not os.path.exists(MODEL_PATH):
        raise FileNotFoundError(
            f"Model not found at {MODEL_PATH}. Run: python train_advanced.py"
        )
    with open(MODEL_PATH, 'rb') as f:
        data = pickle.load(f)

    _model_version = data.get('version', '1.0')

    if _model_version == '2.0':
        # New TF-IDF pipeline
        _pipeline      = data['pipeline']
        _label_encoder = data['label_encoder']
        _intents       = data['intents']
        # NOTE: preprocess_fn is intentionally NOT loaded from pickle.
        # We use _preprocess_text() defined above in this file instead.
    else:
        # Legacy bag-of-words model — wrap for compatibility
        _pipeline      = _LegacyWrapper(data)
        _label_encoder = data['label_encoder']
        _intents       = data['intents']

    print(f"✅ LokSeva model v{_model_version} loaded.")


class _LegacyWrapper:
    """Wraps old BOW model to look like a sklearn Pipeline."""
    def __init__(self, data):
        import numpy as np
        from nltk.stem import WordNetLemmatizer
        from nltk.tokenize import word_tokenize
        self._model   = data['model']
        self._vocab   = data['vocabulary']
        self._lem     = WordNetLemmatizer()

    def predict_proba(self, X_list):
        import numpy as np
        from nltk.tokenize import word_tokenize
        text = X_list[0]
        tokens = word_tokenize(text.lower())
        tokens = [self._lem.lemmatize(t) for t in tokens]
        bow = np.array(
            [1 if w in tokens else 0 for w in self._vocab],
            dtype=np.float32
        ).reshape(1, -1)
        return self._model.predict_proba(bow)

    def score(self, X, y):
        return 0.0


# ── Load on import ────────────────────────────────────────────────────────────
try:
    load_model()
except FileNotFoundError as e:
    print(f"⚠️  {e}")


# ════════════════════════════════════════════════════════════════════════════
#  LANGUAGE DETECTION
# ════════════════════════════════════════════════════════════════════════════
def detect_lang(text: str) -> str:
    try:
        from utils.lang_detector import detect_language
        return detect_language(text)
    except ImportError:
        return 'en'


# ════════════════════════════════════════════════════════════════════════════
#  SESSION MEMORY HELPERS
# ════════════════════════════════════════════════════════════════════════════
SESSION_KEY      = 'lokseva_memory'
MAX_HISTORY      = 20    # max turns to keep in memory

def get_memory() -> dict:
    """Get or initialise the session memory dict."""
    if SESSION_KEY not in session:
        session[SESSION_KEY] = {
            'history':          [],   # list of {role, text, intent, lang, ts}
            'last_intent':      None,
            'last_lang':        'en',
            'pending_clarify':  None, # intent we were clarifying
            'user_name':        None,
            'complaint_context': None,  # last complaint ID mentioned
        }
    return session[SESSION_KEY]


def save_turn(memory: dict, role: str, text: str,
              intent: str = None, lang: str = 'en'):
    """Append a turn to memory and trim to MAX_HISTORY."""
    memory['history'].append({
        'role':   role,
        'text':   text,
        'intent': intent,
        'lang':   lang,
        'ts':     datetime.utcnow().isoformat(),
    })
    if len(memory['history']) > MAX_HISTORY:
        memory['history'] = memory['history'][-MAX_HISTORY:]
    session.modified = True


def get_context_summary(memory: dict) -> str:
    """
    Build a short context string from recent history for context-aware replies.
    e.g. "User previously asked about: track_complaint, rural_services"
    """
    recent = memory['history'][-6:]   # last 3 exchanges
    intents_seen = [
        t['intent'] for t in recent
        if t.get('intent') and t['role'] == 'user'
    ]
    if intents_seen:
        return f"[Context: user recently asked about {', '.join(set(intents_seen))}]"
    return ""


# ════════════════════════════════════════════════════════════════════════════
#  LIVE DATABASE QUERY
# ════════════════════════════════════════════════════════════════════════════
def fetch_user_complaints(user_id: int, lang: str) -> str:
    """
    Fetch complaints for the logged-in user from the database.
    Returns a formatted string response.
    """
    try:
        from extensions import db
        from models.db_models import Complaint
        from utils.lang_detector import get_template

        complaints = (
            Complaint.query
            .filter_by(user_id=user_id)
            .order_by(Complaint.date.desc())
            .limit(5)
            .all()
        )

        if not complaints:
            return get_template(lang, 'no_complaints')

        STATUS_EMOJI = {
            'Submitted':   '📥',
            'In Progress': '⚙️',
            'Resolved':    '✅',
            'Closed':      '🔒',
        }

        intro = get_template(lang, 'complaints_intro')
        lines = [intro, '']

        for c in complaints:
            emoji = STATUS_EMOJI.get(c.status, '📋')
            date_str = c.date.strftime('%d %b %Y') if c.date else 'N/A'
            lines.append(
                f"{emoji} #{c.complaint_id} — {c.category}\n"
                f"   Status: {c.status}  |  {date_str}\n"
                f"   {c.description[:80]}{'...' if len(c.description) > 80 else ''}"
            )

        if len(complaints) == 5:
            lines.append(
                "\n📋 Showing your 5 most recent complaints. "
                "Visit 'Track Complaint' to see all."
            )

        return '\n'.join(lines)

    except Exception as e:
        print(f"DB fetch error: {e}")
        from utils.lang_detector import get_template
        return get_template(lang, 'db_error')


# ════════════════════════════════════════════════════════════════════════════
#  CLARIFYING QUESTIONS
# ════════════════════════════════════════════════════════════════════════════
CLARIFYING_QUESTIONS = {
    'services': [
        "Could you tell me which type of area you're in? 🏡\n\n"
        "1️⃣ Rural (village / gram panchayat)\n"
        "2️⃣ Urban (town / city)\n"
        "3️⃣ Metro (Mumbai, Delhi, Bangalore, etc.)\n\n"
        "This helps me show you the most relevant services!"
    ],
    'complaint': [
        "To help you better, could you tell me:\n\n"
        "What type of issue are you facing?\n"
        "🛣️ Roads & Infrastructure\n"
        "💧 Water Supply\n"
        "⚡ Electricity\n"
        "🏥 Public Health\n"
        "🗑️ Sanitation\n"
        "🌳 Environment\n"
        "🏫 Education\n"
        "📋 Other\n\n"
        "I can give you specific guidance based on your issue type!"
    ],
    'track': [
        "Are you asking about:\n\n"
        "1️⃣ A specific complaint (do you have your Complaint ID?)\n"
        "2️⃣ All your complaints (I can fetch them from the database)\n"
        "3️⃣ How to track complaints in general\n\n"
        "Just reply with 1, 2, or 3 — or describe your query!"
    ],
}

CLARIFY_TRIGGERS = {
    'services':  ['service', 'seva', 'सेवा', 'সেবা', 'சேவை', 'సేవ'],
    'complaint': ['complain', 'problem', 'issue', 'shikayat', 'शिकायत', 'taqrar', 'তক্রার'],
    'track':     ['track', 'status', 'where', 'kahan', 'कहाँ', 'स्थिति'],
}


def should_clarify(text: str, intent: str, confidence: float) -> str | None:
    """
    Returns a clarifying question if query is ambiguous,
    or None if we should proceed with normal response.
    """
    text_lower = text.lower()

    # Short vague messages (< 4 words) that match a broad topic
    if len(text_lower.split()) <= 3 and confidence < 0.65:
        for topic, keywords in CLARIFY_TRIGGERS.items():
            if any(kw in text_lower for kw in keywords):
                return random.choice(CLARIFYING_QUESTIONS[topic])

    return None


# ════════════════════════════════════════════════════════════════════════════
#  CONTEXT-AWARE FOLLOW-UP DETECTION
# ════════════════════════════════════════════════════════════════════════════
FOLLOWUP_PATTERNS = {
    'yes':     ['yes', 'yeah', 'yep', 'sure', 'ok', 'okay', 'ha', 'haan',
                'हाँ', 'हां', 'हो', 'होय', 'হ্যাঁ', 'ஆம்', 'అవును'],
    'no':      ['no', 'nope', 'nahi', 'na', 'नहीं', 'नाही', 'না', 'இல்லை', 'కాదు'],
    'more':    ['more', 'tell me more', 'details', 'elaborate', 'explain more',
                'aur batao', 'और बताएं', 'আরো বলুন'],
    'number1': ['1', 'one', 'first', 'option 1', 'पहला', 'प्रथम'],
    'number2': ['2', 'two', 'second', 'option 2', 'दूसरा', 'दुसरा'],
    'number3': ['3', 'three', 'third', 'option 3', 'तीसरा', 'तिसरा'],
}


def detect_followup(text: str) -> str | None:
    """Detect if the message is a follow-up response (yes/no/number)."""
    text_lower = text.lower().strip()
    for ftype, patterns in FOLLOWUP_PATTERNS.items():
        if text_lower in patterns or any(text_lower == p for p in patterns):
            return ftype
    return None


def handle_followup(followup_type: str, memory: dict, lang: str) -> str | None:
    """
    Handle a follow-up response based on the last bot context.
    Returns a response string or None if no context to follow up on.
    """
    last_intent = memory.get('last_intent')
    pending     = memory.get('pending_clarify')

    # Handling response to "Would you like to submit a complaint?"
    if followup_type == 'yes' and last_intent == 'my_complaint_status':
        return (
            "Great! Here's how to submit a complaint:\n\n"
            "1️⃣ Click 'Submit Complaint' in the menu\n"
            "2️⃣ Choose your issue category\n"
            "3️⃣ Describe the problem with location\n"
            "4️⃣ Attach a photo (optional)\n"
            "5️⃣ Submit — you'll get a Complaint ID!\n\n"
            "Want me to guide you through any specific step?"
        )

    # Handling clarify follow-up: "1" → Rural services
    if pending == 'services':
        responses = {
            'number1': "🌾 Rural Services on LokBandhu:\n\n🌱 Village Health Outreach — Mobile clinics, vaccinations\n📚 Rural Education Initiative — Literacy centers, vocational training\n👩‍👩‍👧 Women's Self-Help Groups — Microfinance, skill development\n🌾 Agricultural Support — Crop advisory, irrigation schemes\n\nVisit the Service Directory for full details!",
            'number2': "🏙️ Urban Services on LokBandhu:\n\n🚌 Public Transport — Bus routes, connectivity\n🛣️ Roads & Infrastructure — Pothole repairs, streetlights\n💧 Water & Sanitation — Supply complaints, drainage\n⚡ Electricity — Power outages, billing\n🏪 Municipal — Property tax, certificates\n\nVisit the Service Directory for full details!",
            'number3': "🌆 Metro Services on LokBandhu:\n\n🌫️ Air Quality Monitoring — Real-time AQI, health alerts\n🏥 Smart Healthcare — Telemedicine kiosks, hospital network\n🚇 Metro Rail — Route info, ticketing complaints\n🌐 Digital Services — E-governance, DigiLocker\n🏗️ Smart City — Public Wi-Fi, CCTV issues\n\nVisit the Service Directory for full details!",
        }
        if followup_type in responses:
            memory['pending_clarify'] = None
            session.modified = True
            return responses[followup_type]

    # Handling clarify follow-up: track complaint options
    if pending == 'track':
        if followup_type == 'number1':
            memory['pending_clarify'] = None
            session.modified = True
            return ("To track a specific complaint by ID:\n\n"
                    "1️⃣ Login → Track Complaint\n"
                    "2️⃣ Find your complaint by ID or category\n\n"
                    "💡 If you've lost your ID, all complaints are listed there automatically!")
        if followup_type == 'number2':
            memory['pending_clarify'] = None
            session.modified = True
            # Trigger live DB fetch
            if current_user.is_authenticated:
                return fetch_user_complaints(current_user.id, lang)
            else:
                from utils.lang_detector import get_template
                return get_template(lang, 'login_required')
        if followup_type == 'number3':
            memory['pending_clarify'] = None
            session.modified = True
            return ("Tracking complaints on LokBandhu is easy! 📊\n\n"
                    "After submitting a complaint you get a unique Complaint ID.\n\n"
                    "Status flow:\n📥 Submitted → ⚙️ In Progress → ✅ Resolved → 🔒 Closed\n\n"
                    "To track: Login → Click 'Track Complaint' in the menu.\n"
                    "You also receive email updates whenever the status changes!")

    return None


# ════════════════════════════════════════════════════════════════════════════
#  INTENT PREDICTION
# ════════════════════════════════════════════════════════════════════════════
def predict_intent(text: str) -> tuple[str, float]:
    """Returns (intent_tag, confidence)."""
    if _pipeline is None:
        return ('help', 0.0)

    preprocessed = _preprocess_text(text)
    probs        = _pipeline.predict_proba([preprocessed])[0]
    max_idx      = int(probs.argmax())
    confidence   = float(probs[max_idx])
    intent_tag   = _label_encoder.inverse_transform([max_idx])[0]
    return (intent_tag, confidence)


def get_intent_response(tag: str) -> str:
    """Look up a random response for the given intent tag."""
    if _intents is None:
        return "Sorry, I'm not available right now."
    for intent in _intents:
        if intent['tag'] == tag:
            resp = random.choice(intent['responses'])
            return resp
    return "I couldn't find an answer. Please try rephrasing or visit the Help section."


# ════════════════════════════════════════════════════════════════════════════
#  MAIN CHAT ENDPOINT
# ════════════════════════════════════════════════════════════════════════════
@chat_bp.route('/chat', methods=['POST'])
def chat():
    """
    POST /chat
    Body:    { "message": "user text here" }
    Returns: {
        "reply":   "...",
        "lang":    "en",
        "intent":  "submit_complaint",
        "context": "remembers N messages"
    }
    """
    data = request.get_json()
    if not data or 'message' not in data:
        return jsonify({"error": "Missing 'message' in request body"}), 400

    user_text = data.get('message', '').strip()
    if not user_text:
        return jsonify({"error": "Empty message"}), 400

    # ── Load memory ──────────────────────────────────────────────────────────
    memory = get_memory()

    # ── Detect language ──────────────────────────────────────────────────────
    lang = detect_lang(user_text)
    memory['last_lang'] = lang
    session.modified = True

    # ── Save user turn ───────────────────────────────────────────────────────
    save_turn(memory, 'user', user_text, lang=lang)

    # ── Check for follow-up response first ──────────────────────────────────
    followup_type = detect_followup(user_text)
    if followup_type and (memory.get('pending_clarify') or memory.get('last_intent')):
        followup_reply = handle_followup(followup_type, memory, lang)
        if followup_reply:
            save_turn(memory, 'bot', followup_reply, intent='followup', lang=lang)
            return jsonify({
                "reply":   followup_reply,
                "lang":    lang,
                "intent":  "followup",
                "context": f"{len(memory['history'])} messages in memory",
            })

    # ── Predict intent ───────────────────────────────────────────────────────
    intent_tag, confidence = predict_intent(user_text)

    # ── Low confidence → clarifying question or fallback ────────────────────
    if confidence < CLARIFY_THRESHOLD:
        from utils.lang_detector import get_template
        fallback = get_template(lang, 'not_understood')
        save_turn(memory, 'bot', fallback, intent='fallback', lang=lang)
        return jsonify({
            "reply":   fallback,
            "lang":    lang,
            "intent":  "fallback",
            "context": f"{len(memory['history'])} messages in memory",
        })

    # ── Medium confidence → ask clarifying question ─────────────────────────
    if CLARIFY_THRESHOLD <= confidence < CONFIDENCE_THRESHOLD:
        clarify = should_clarify(user_text, intent_tag, confidence)
        if clarify:
            # Remember what we were clarifying
            for topic, keywords in CLARIFY_TRIGGERS.items():
                if any(kw in user_text.lower() for kw in keywords):
                    memory['pending_clarify'] = topic
                    session.modified = True
                    break
            save_turn(memory, 'bot', clarify, intent='clarify', lang=lang)
            return jsonify({
                "reply":   clarify,
                "lang":    lang,
                "intent":  "clarify",
                "context": f"{len(memory['history'])} messages in memory",
            })

    # ── Clear pending clarify since we have a confident match ────────────────
    memory['pending_clarify'] = None
    memory['last_intent']     = intent_tag
    session.modified = True

    # ── Handle special DB intent ─────────────────────────────────────────────
    if intent_tag == 'my_complaint_status':
        if not current_user.is_authenticated:
            from utils.lang_detector import get_template
            reply = get_template(lang, 'login_required')
        else:
            reply = fetch_user_complaints(current_user.id, lang)
        save_turn(memory, 'bot', reply, intent=intent_tag, lang=lang)
        return jsonify({
            "reply":   reply,
            "lang":    lang,
            "intent":  intent_tag,
            "context": f"{len(memory['history'])} messages in memory",
        })

    # ── Get response for intent ──────────────────────────────────────────────
    reply = get_intent_response(intent_tag)

    # ── Handle sentinel DB marker in response ────────────────────────────────
    if '__DB_COMPLAINT_STATUS__' in reply:
        if not current_user.is_authenticated:
            from utils.lang_detector import get_template
            reply = get_template(lang, 'login_required')
        else:
            reply = fetch_user_complaints(current_user.id, lang)

    # ── Context-aware prefix for follow-up topics ────────────────────────────
    # If user's last 2 intents are related, add a bridging phrase
    recent_intents = [
        t['intent'] for t in memory['history'][-4:]
        if t.get('intent') and t['role'] == 'user'
    ]
    RELATED_GROUPS = [
        {'submit_complaint', 'complaint_categories', 'how_to_attach_file'},
        {'track_complaint', 'my_complaint_status', 'complaint_id_lost', 'complaint_not_resolved'},
        {'rural_services', 'urban_services', 'metro_services', 'all_services'},
        {'register', 'login', 'forgot_password'},
    ]
    context_prefix = ''
    for group in RELATED_GROUPS:
        if intent_tag in group and any(r in group for r in recent_intents[:-1]):
            from utils.lang_detector import get_template
            context_prefix = get_template(lang, 'context_ref') + ' — '
            break

    final_reply = context_prefix + reply if context_prefix else reply

    # ── Save bot turn ────────────────────────────────────────────────────────
    save_turn(memory, 'bot', final_reply, intent=intent_tag, lang=lang)

    return jsonify({
        "reply":   final_reply,
        "lang":    lang,
        "intent":  intent_tag,
        "context": f"{len(memory['history'])} messages in memory",
    })


# ════════════════════════════════════════════════════════════════════════════
#  CHAT HISTORY ENDPOINT
# ════════════════════════════════════════════════════════════════════════════
@chat_bp.route('/chat/history', methods=['GET'])
def chat_history():
    """
    GET /chat/history
    Returns current session's chat history (last 20 messages).
    Useful for restoring chat on page reload.
    """
    memory  = get_memory()
    history = memory.get('history', [])
    return jsonify({
        "history": [
            {"role": t['role'], "text": t['text'], "lang": t.get('lang', 'en')}
            for t in history
        ],
        "total": len(history),
        "last_lang": memory.get('last_lang', 'en'),
    })


# ════════════════════════════════════════════════════════════════════════════
#  CLEAR CHAT ENDPOINT
# ════════════════════════════════════════════════════════════════════════════
@chat_bp.route('/chat/clear', methods=['POST'])
def chat_clear():
    """POST /chat/clear — resets the session memory."""
    session.pop(SESSION_KEY, None)
    return jsonify({"message": "Chat history cleared."})


# ════════════════════════════════════════════════════════════════════════════
#  RELOAD MODEL ENDPOINT (admin only)
# ════════════════════════════════════════════════════════════════════════════
@chat_bp.route('/chat/reload', methods=['POST'])
def reload_model():
    """
    POST /chat/reload — hot-reload the model after retraining.
    Protect with @login_required + admin check in production!
    """
    try:
        load_model()
        return jsonify({"message": f"✅ Model v{_model_version} reloaded."})
    except FileNotFoundError as e:
        return jsonify({"error": str(e)}), 404
