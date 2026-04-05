# app/nlp/dataset_loader.py

import csv
import os
import re
from collections import Counter

# chemin vers le dataset
DATASET_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
    "data",
    "TuniziDataset.csv"
)

# mots inutiles fréquents à ignorer
STOPWORDS = {
    "the", "and", "for", "you", "your", "are", "with", "this", "that",
    "mais", "avec", "pour", "dans", "sur", "des", "les", "une", "est",
    "oui", "non", "all", "like", "very", "just", "have", "has", "was",
    "will", "can", "not", "donc", "par", "from", "what", "when", "where",
    "who", "why", "how", "cest", "etre", "avoir", "bon", "bien"
}


def clean_text(text: str) -> str:
    text = text.lower()
    text = re.sub(r"http\S+", " ", text)         # liens
    text = re.sub(r"[@#]\w+", " ", text)         # hashtags / mentions
    text = re.sub(r"[^a-zA-Z0-9\u0600-\u06FF\s]", " ", text)  # garder lettres/chiffres/arabe
    text = re.sub(r"\s+", " ", text).strip()
    return text


def extract_tunisian_words(min_freq: int = 8):
    """
    Lit le dataset tunisien Arabizi et retourne un set de mots fréquents utiles
    """
    if not os.path.exists(DATASET_PATH):
        print(f"⚠️ Dataset introuvable: {DATASET_PATH}")
        return set()

    counter = Counter()

    try:
        with open(DATASET_PATH, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)

            if "InputText" not in reader.fieldnames:
                print("⚠️ Colonne 'InputText' introuvable dans le dataset.")
                return set()

            for row in reader:
                text = row.get("InputText", "")
                text = clean_text(text)

                words = text.split()

                for word in words:
                    # garder les mots plausiblement tunisien / arabizi
                    if len(word) < 3:
                        continue
                    if word in STOPWORDS:
                        continue

                    # bonus si mot avec chiffres arabizi ou style tunisien
                    if any(d in word for d in "23456789") or re.match(r"^[a-z0-9]+$", word):
                        counter[word] += 1

        # garder mots assez fréquents
        frequent_words = {
            word for word, freq in counter.items()
            if freq >= min_freq
        }

        print(f"✅ {len(frequent_words)} mots tunisiens chargés depuis le dataset.")
        return frequent_words

    except Exception as e:
        print(f"⚠️ Erreur lecture dataset: {e}")
        return set()