# app/nlp/tunisian_normalizer.py

import re

NORMALIZATION_MAP = {
    "n7eb": "nheb",
    "n7ib": "nheb",
    "3aweni": "aaweni",
    "sou2el": "souel",
    "s2el": "souel",
    "nsa2lek": "nsaalek",
    "chnia": "chnowa",
    "chniya": "chnowa",
    "chnoua": "chnowa",
    "kifesh": "kifeh",
    "kifach": "kifeh",
    "kifech": "kifeh",
    "3leh": "aleh",
    "3lech": "aleh",
    "eyh": "ey",
    "3aslema": "aslema",
    "fama": "famma",
    "barsha": "barcha",
    "mteek": "mte3ek",
    "mte3i": "mte3i",
    "najemch": "ma najemch",
    "ma3andich": "ma andich",
    "3andi": "andi",
    "sa77a": "sahha"
}


def normalize_tunisian(text: str) -> str:
    if not text:
        return text

    text = text.lower().strip()

    # enlever espaces multiples
    text = re.sub(r"\s+", " ", text)

    words = text.split()
    normalized_words = []

    for w in words:
        # 1) remplacement direct si existe
        if w in NORMALIZATION_MAP:
            normalized_words.append(NORMALIZATION_MAP[w])
        else:
            normalized_words.append(w)

    normalized_text = " ".join(normalized_words)

    return normalized_text