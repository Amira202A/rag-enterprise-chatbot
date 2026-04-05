# app/nlp/tunisian_detector.py

import os
import csv

# 🔹 mots tunisiens de base codés à la main
BASE_TUNISIAN_WORDS = {
    "cv", "labes", "sbeh", "aslema", "3aslema", "salam", "salem",
    "brabi", "3aweni", "aaweni", "nheb", "n7eb", "n7ib",
    "kifeh", "kifesh", "kifach", "aleh", "3leh", "9adeh",
    "chnowa", "chnia", "chniya", "chnoua", "tfadhal", "mrigel",
    "ey", "eyh", "ahawka", "bara", "sahha", "yaatik", "najem",
    "tnajem", "sou2el", "s2el", "nsa2lek", "na7ki", "hekka",
    "nese2lek", "neselek", "nsaalek", "nse2lek", "nselek",
    "s7i7", "behy", "behi", "ok", "okay"
}

DATASET_WORDS = set()


def load_dataset_words():
    """
    Charge des mots fréquents depuis le dataset Kaggle.
    """
    global DATASET_WORDS

    csv_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
        "data",
        "TuniziDataset.csv"
    )

    if not os.path.exists(csv_path):
        print("⚠️ Dataset tunisien non trouvé :", csv_path)
        return

    try:
        with open(csv_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)

            for row in reader:
                text = row.get("InputText", "")
                if text:
                    words = text.lower().strip().split()
                    for w in words:
                        w = w.strip(".,!?;:()[]{}\"'")
                        if len(w) >= 3:
                            DATASET_WORDS.add(w)

        print(f"✅ {len(DATASET_WORDS)} mots tunisiens chargés depuis le dataset.")

    except Exception as e:
        print("❌ Erreur chargement dataset tunisien :", e)


# charger au démarrage
load_dataset_words()


def is_tunisian_arabizi(text: str) -> bool:
    text = text.lower().strip()
    words = text.split()

    # 1) mots tunisiens codés à la main
    base_score = sum(1 for w in words if w in BASE_TUNISIAN_WORDS)

    # 2) mots présents dans dataset
    dataset_score = sum(1 for w in words if w in DATASET_WORDS)

    # 3) chiffres typiques arabizi
    has_arabizi_digits = any(d in text for d in ["2", "3", "5", "7", "8", "9"])

    # 4) seuil plus intelligent
    if base_score >= 1:
        return True

    if dataset_score >= 2:
        return True

    if has_arabizi_digits:
        return True

    return False