# utils/lang_detector.py
# Language detection for LokSeva chatbot
# Strategy: Unicode script detection first (fastest, most accurate for Indian scripts)
#            then langdetect as fallback for Latin-script languages
#
# Install: pip install langdetect --break-system-packages

import re
import unicodedata

# ── Unicode script ranges for Indian languages ────────────────────────────
SCRIPT_RANGES = {
    'hi': (0x0900, 0x097F),   # Devanagari → Hindi / Marathi
    'mr': (0x0900, 0x097F),   # Devanagari → shared with Hindi
    'bn': (0x0980, 0x09FF),   # Bengali
    'ta': (0x0B80, 0x0BFF),   # Tamil
    'te': (0x0C00, 0x0C7F),   # Telugu
    'gu': (0x0A80, 0x0AFF),   # Gujarati
    'pa': (0x0A00, 0x0A7F),   # Gurmukhi (Punjabi)
    'kn': (0x0C80, 0x0CFF),   # Kannada
    'ml': (0x0D00, 0x0D7F),   # Malayalam
    'or': (0x0B00, 0x0B7F),   # Odia
}

# Devanagari ambiguity: distinguish Hindi vs Marathi by vocabulary
MARATHI_MARKERS = [
    'आहे', 'नाही', 'करा', 'आहेत', 'होते', 'केले', 'असेल',
    'कसे', 'काय', 'कधी', 'कुठे', 'माझी', 'तुमची', 'आपली',
    'तक्रार', 'सेवा', 'नोंदणी', 'समस्या'
]

SUPPORTED = {'en', 'hi', 'mr', 'bn', 'ta', 'te'}


def _count_script_chars(text: str, start: int, end: int) -> int:
    """Count characters falling in a Unicode range."""
    return sum(1 for ch in text if start <= ord(ch) <= end)


def _detect_by_script(text: str) -> str | None:
    """
    Detect language by Unicode script.
    Returns ISO 639-1 code or None if script is Latin/ambiguous.
    """
    if not text.strip():
        return None

    counts = {}
    for lang, (start, end) in SCRIPT_RANGES.items():
        count = _count_script_chars(text, start, end)
        if count > 0:
            counts[lang] = count

    if not counts:
        return None  # Latin script — fall through to langdetect

    # Get dominant script
    dominant = max(counts, key=counts.get)

    # Devanagari ambiguity: Hindi vs Marathi
    if dominant in ('hi', 'mr'):
        text_lower = text.lower()
        marathi_score = sum(1 for marker in MARATHI_MARKERS if marker in text)
        return 'mr' if marathi_score >= 2 else 'hi'

    return dominant if dominant in SUPPORTED else None


def _detect_by_langdetect(text: str) -> str:
    """Use langdetect library as fallback. Returns 'en' on failure."""
    try:
        from langdetect import detect, DetectorFactory
        DetectorFactory.seed = 42  # Deterministic results
        detected = detect(text)
        # Map to our supported set
        mapping = {
            'en': 'en', 'hi': 'hi', 'mr': 'mr',
            'bn': 'bn', 'ta': 'ta', 'te': 'te',
        }
        return mapping.get(detected, 'en')
    except Exception:
        return 'en'


def detect_language(text: str) -> str:
    """
    Main language detection function.
    Returns ISO 639-1 code: 'en', 'hi', 'mr', 'bn', 'ta', 'te'

    Strategy:
    1. Script detection (Devanagari, Bengali, Tamil, Telugu)
    2. langdetect fallback (for English and ambiguous text)
    3. Default to 'en'

    Usage:
        from utils.lang_detector import detect_language
        lang = detect_language("मेरी शिकायत का स्टेटस क्या है")
        # Returns: 'hi'
    """
    if not text or len(text.strip()) < 2:
        return 'en'

    # Step 1: Try script detection first
    script_result = _detect_by_script(text)
    if script_result:
        return script_result

    # Step 2: Latin script — use langdetect
    return _detect_by_langdetect(text)


# ── Multilingual response templates ─────────────────────────────────────────
# Used by chat_routes.py to send system messages in the detected language

LANG_TEMPLATES = {
    'en': {
        'greeting':        'Hello! How can I help you?',
        'not_understood':  "I'm not sure I understood that. Could you rephrase? I can help with complaints, services, account queries, and more.",
        'login_required':  "Please log in first to view your complaint data. Click 'Login' in the navigation bar.",
        'no_complaints':   "You haven't submitted any complaints yet. Would you like to submit one now?",
        'complaints_intro':"Here are your complaints:",
        'db_error':        "I couldn't fetch your data right now. Please try the 'Track Complaint' page directly.",
        'context_ref':     "Based on what you asked earlier",
        'language_detected': "I detected you're writing in English.",
    },
    'hi': {
        'greeting':        'नमस्ते! मैं आपकी कैसे मदद कर सकता हूं?',
        'not_understood':  'मुझे समझ नहीं आया। क्या आप दोबारा पूछ सकते हैं? मैं शिकायत, सेवाएं और खाते से जुड़े सवालों में मदद कर सकता हूं।',
        'login_required':  "शिकायत की जानकारी देखने के लिए पहले लॉग इन करें। नेविगेशन बार में 'Login' पर क्लिक करें।",
        'no_complaints':   'आपने अभी तक कोई शिकायत दर्ज नहीं की है। क्या आप अभी शिकायत दर्ज करना चाहते हैं?',
        'complaints_intro':"आपकी शिकायतें:",
        'db_error':        "अभी आपका डेटा नहीं मिल पाया। कृपया 'Track Complaint' पेज सीधे खोलें।",
        'context_ref':     'आपके पिछले सवाल के आधार पर',
        'language_detected': 'मैंने पहचाना कि आप हिंदी में लिख रहे हैं।',
    },
    'mr': {
        'greeting':        'नमस्कार! मी तुम्हाला कशी मदत करू शकतो?',
        'not_understood':  'मला समजले नाही. कृपया पुन्हा विचारा? मी तक्रार, सेवा आणि खात्याशी संबंधित प्रश्नांमध्ये मदत करू शकतो.',
        'login_required':  "तक्रारीची माहिती पाहण्यासाठी प्रथम लॉग इन करा. नेव्हिगेशन बारमध्ये 'Login' वर क्लिक करा.",
        'no_complaints':   'तुम्ही अद्याप कोणतीही तक्रार नोंदवलेली नाही. तुम्हाला आता तक्रार नोंदवायची आहे का?',
        'complaints_intro':"तुमच्या तक्रारी:",
        'db_error':        "सध्या तुमचा डेटा मिळू शकला नाही. कृपया 'Track Complaint' पेज थेट उघडा.",
        'context_ref':     'तुमच्या मागील प्रश्नावर आधारित',
        'language_detected': 'मी ओळखले की तुम्ही मराठीत लिहित आहात.',
    },
    'bn': {
        'greeting':        'নমস্কার! আমি কীভাবে আপনাকে সাহায্য করতে পারি?',
        'not_understood':  'আমি বুঝতে পারিনি। আবার বলবেন? আমি অভিযোগ, সেবা এবং অ্যাকাউন্ট সম্পর্কিত প্রশ্নে সাহায্য করতে পারি।',
        'login_required':  "অভিযোগের তথ্য দেখতে আগে লগইন করুন। নেভিগেশন বারে 'Login' ক্লিক করুন।",
        'no_complaints':   'আপনি এখনও কোনো অভিযোগ দাখিল করেননি। আপনি কি এখন একটি দাখিল করতে চান?',
        'complaints_intro':"আপনার অভিযোগগুলি:",
        'db_error':        "এখন আপনার ডেটা পাওয়া গেলনা। সরাসরি 'Track Complaint' পেজ খুলুন।",
        'context_ref':     'আপনার আগের প্রশ্নের ভিত্তিতে',
        'language_detected': 'আমি বুঝলাম আপনি বাংলায় লিখছেন।',
    },
    'ta': {
        'greeting':        'வணக்கம்! நான் உங்களுக்கு எவ்வாறு உதவலாம்?',
        'not_understood':  'புரியவில்லை. மீண்டும் கேட்க முடியுமா? புகார்கள், சேவைகள் மற்றும் கணக்கு தொடர்பான கேள்விகளில் உதவலாம்.',
        'login_required':  "புகார் தகவல் பார்க்க முதலில் உள்நுழையுங்கள். 'Login' பட்டனை க்ளிக் செய்யுங்கள்.",
        'no_complaints':   'நீங்கள் இதுவரை எந்த புகாரும் சமர்ப்பிக்கவில்லை. இப்போது சமர்ப்பிக்க விரும்புகிறீர்களா?',
        'complaints_intro':"உங்கள் புகார்கள்:",
        'db_error':        "தற்போது உங்கள் தரவை பெற முடியவில்லை. நேரடியாக 'Track Complaint' பக்கம் திறக்கவும்.",
        'context_ref':     'உங்கள் முந்தைய கேள்வியின் அடிப்படையில்',
        'language_detected': 'நீங்கள் தமிழில் எழுதுவதை கண்டறிந்தேன்.',
    },
    'te': {
        'greeting':        'నమస్కారం! నేను మీకు ఎలా సహాయం చేయగలను?',
        'not_understood':  'నాకు అర్థం కాలేదు. మళ్ళీ అడగగలరా? ఫిర్యాదులు, సేవలు మరియు ఖాతా సంబంధిత ప్రశ్నలలో సహాయం చేయగలను.',
        'login_required':  "ఫిర్యాదు సమాచారం చూడటానికి ముందు లాగిన్ చేయండి. నావిగేషన్ బార్‌లో 'Login' క్లిక్ చేయండి.",
        'no_complaints':   'మీరు ఇంతవరకు ఎటువంటి ఫిర్యాదు సమర్పించలేదు. ఇప్పుడు సమర్పించాలనుకుంటున్నారా?',
        'complaints_intro':"మీ ఫిర్యాదులు:",
        'db_error':        "ప్రస్తుతం మీ డేటా తీసుకురాలేకపోయాను. నేరుగా 'Track Complaint' పేజీ తెరవండి.",
        'context_ref':     'మీ మునుపటి ప్రశ్న ఆధారంగా',
        'language_detected': 'మీరు తెలుగులో రాస్తున్నారని గుర్తించాను.',
    },
}


def get_template(lang: str, key: str) -> str:
    """Get a response template in the given language, fallback to English."""
    lang_tmpl = LANG_TEMPLATES.get(lang, LANG_TEMPLATES['en'])
    return lang_tmpl.get(key, LANG_TEMPLATES['en'].get(key, ''))
