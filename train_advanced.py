# train_advanced.py
# Advanced training script for LokSeva chatbot
# Uses TF-IDF vectorization instead of basic bag-of-words
# Command: python train_advanced.py
#
# Requirements: pip install nltk scikit-learn numpy

import json
import pickle
import numpy as np
import os

import nltk
nltk.download('punkt',      quiet=True)
nltk.download('punkt_tab',  quiet=True)
nltk.download('wordnet',    quiet=True)
nltk.download('stopwords',  quiet=True)

from nltk.stem import WordNetLemmatizer
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords

from sklearn.neural_network import MLPClassifier
from sklearn.preprocessing import LabelEncoder
from sklearn.pipeline import Pipeline
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.model_selection import cross_val_score

lemmatizer    = WordNetLemmatizer()
STOP_WORDS    = set(stopwords.words('english'))

BASE_DIR      = os.path.dirname(os.path.abspath(__file__))
INTENTS_PATH  = os.path.join(BASE_DIR, 'intents.json')
MODEL_PATH    = os.path.join(BASE_DIR, 'chatbot_model.pkl')

IGNORE_CHARS  = set('?!.,;:-_')

# ── Load intents ──────────────────────────────────────────────────────────────
with open(INTENTS_PATH, 'r', encoding='utf-8') as f:
    data = json.load(f)
intents = data['intents']

# ── Build training corpus ────────────────────────────────────────────────────
def preprocess(text: str) -> str:
    """Tokenize, lemmatize, remove stopwords and punctuation."""
    tokens = word_tokenize(text.lower())
    tokens = [
        lemmatizer.lemmatize(t) for t in tokens
        if t not in IGNORE_CHARS and t not in STOP_WORDS and t.isalpha()
    ]
    return ' '.join(tokens) if tokens else text.lower()

X_raw, y_raw = [], []
all_tags     = []

for intent in intents:
    tag = intent['tag']
    all_tags.append(tag)
    for pattern in intent['patterns']:
        X_raw.append(preprocess(pattern))
        y_raw.append(tag)

print(f"✅ Total intents    : {len(set(all_tags))}")
print(f"✅ Training samples : {len(X_raw)}")

# ── Label encoding ───────────────────────────────────────────────────────────
label_encoder = LabelEncoder()
y_encoded     = label_encoder.fit_transform(y_raw)

# ── Build Pipeline: TF-IDF → MLP ────────────────────────────────────────────
# TfidfVectorizer converts text to weighted term-frequency vectors
# MLPClassifier is a feed-forward neural network
pipeline = Pipeline([
    ('tfidf', TfidfVectorizer(
        ngram_range=(1, 2),      # unigrams + bigrams for better context
        max_features=5000,       # top 5000 features
        sublinear_tf=True,       # log-scale TF
        analyzer='word',
    )),
    ('clf', MLPClassifier(
        hidden_layer_sizes=(256, 128, 64),   # deeper network for better learning
        activation='relu',
        solver='adam',
        alpha=0.001,             # L2 regularisation to prevent overfitting
        learning_rate='adaptive',
        max_iter=2000,
        random_state=42,
        early_stopping=False,
        verbose=False,
        batch_size='auto',
    )),
])

print("\n🚀 Training model with TF-IDF + MLP pipeline...")
pipeline.fit(X_raw, y_encoded)

# ── Training accuracy ────────────────────────────────────────────────────────
train_acc = pipeline.score(X_raw, y_encoded)
print(f"✅ Training accuracy : {train_acc * 100:.1f}%")

# ── Cross-validation score ───────────────────────────────────────────────────
# Only run if we have enough samples per class
min_samples = min(
    sum(1 for y in y_raw if y == tag)
    for tag in set(y_raw)
)
if min_samples >= 3:
    cv_scores = cross_val_score(pipeline, X_raw, y_encoded, cv=3, scoring='accuracy')
    print(f"✅ Cross-val accuracy: {cv_scores.mean() * 100:.1f}% ± {cv_scores.std() * 100:.1f}%")
else:
    print("ℹ️  Skipping cross-validation (too few samples per class for 3-fold CV)")

# ── Save everything ──────────────────────────────────────────────────────────
model_data = {
    'pipeline':      pipeline,       # TF-IDF + MLP pipeline
    'label_encoder': label_encoder,  # encodes/decodes intent tags
    'intents':       intents,        # original intents for response lookup
    # NOTE: preprocess_fn intentionally NOT saved in pickle.
    # Pickling a function defined in __main__ causes AttributeError when
    # loaded from a different entry point (e.g. Flask's app.py).
    # The preprocess function is defined directly in chat_routes.py instead.
    'version':       '2.0',          # model version
}

with open(MODEL_PATH, 'wb') as f:
    pickle.dump(model_data, f)

print(f"\n✅ Model saved   : {MODEL_PATH}")
print(f"✅ Model version : 2.0 (TF-IDF + MLP Pipeline)")
print("\n🎉 Training complete! Run your Flask app — LokSeva is ready.")
