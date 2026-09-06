
from flask import Blueprint, session, redirect, request, url_for
from utils.translations import SUPPORTED_LANGUAGES

lang_bp = Blueprint('lang', __name__)

@lang_bp.route('/set-language/<lang>')
def set_language(lang):
    """Set user's preferred language in session and redirect back."""
    if lang in SUPPORTED_LANGUAGES:
        session['lang'] = lang
    # Return to the page the user was on, or home
    return redirect(request.referrer or url_for('index'))