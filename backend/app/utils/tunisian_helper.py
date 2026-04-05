import re

# 🔹 Dictionnaire tunisien / arabizi -> reformulation plus standard
ARABIZI_MAP = {
    "3aslema": "bonjour",
    "aslema": "bonjour",
    "salam": "bonjour",
    "salem": "bonjour",
    "cv": "comment vas-tu",
    "labes": "comment vas-tu",
    "brabi": "s'il te plaît",
    "3aweni": "aide moi",
    "aweni": "aide moi",
    "nheb": "je veux",
    "n7eb": "je veux",
    "n3ref": "savoir",
    "na3ref": "savoir",
    "kifeh": "comment",
    "kifesh": "comment",
    "chnowa": "que peux-tu faire",
    "chnoua": "que peux-tu faire",
    "najem": "peux",
    "tnajem": "tu peux",
    "sou2el": "question",
    "so2el": "question",
    "nsa2lek": "te poser",
    "chatbot": "chatbot",
    "document": "document",
    "documents": "documents",
    "nzid": "ajouter",
    "hedha": "ceci",
    "hetha": "ceci"
}


# 🔹 Intentions connues 
INTENT_PATTERNS = {
    "help": [
        "3aweni", "aweni", "aide moi", "aide", "help", "brabi 3aweni"
    ],
    "ask_question": [
        "nheb nsa2lek sou2el", "n7eb nsa2lek sou2el", "je veux te poser une question"
    ],
    "chatbot_usage": [
        "nheb n3ref kifesh nekhdem b chatbot hedha",
        "comment fonctionne ce chatbot",
        "how to use this chatbot",
        "kifesh nekhdem b chatbot hedha"
    ],
    "add_document": [
        "kifeh nzid document",
        "comment ajouter un document",
        "how to add a document",
        "nzid document"
    ],
    "bot_capabilities": [
        "chnowa tnajem ta3mel",
        "chnoua tnajem ta3mel",
        "what can you do",
        "que peux-tu faire"
    ]
}


def normalize_text(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r"[^\w\sÀ-ÿء-ي0-9]", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text


def is_tunisian_arabizi(text: str) -> bool:
    text = normalize_text(text)

    tunisian_markers = [
        "3", "7", "9", "5", "8",
        "nheb", "n7eb", "kifeh", "kifesh",
        "chnowa", "chnoua", "brabi", "3aweni",
        "sou2el", "nsa2lek", "labes", "aslema", "3aslema"
    ]

    return any(marker in text for marker in tunisian_markers)


def detect_intent(text: str) -> str:
    text = normalize_text(text)

    for intent, patterns in INTENT_PATTERNS.items():
        for pattern in patterns:
            if normalize_text(pattern) in text:
                return intent

    return "unknown"


def reformulate_tunisian(text: str) -> str:
    text_clean = normalize_text(text)
    words = text_clean.split()

    translated_words = []
    for word in words:
        translated_words.append(ARABIZI_MAP.get(word, word))

    reformulated = " ".join(translated_words)

    
    intent = detect_intent(text)

    if intent == "help":
        return "je veux de l'aide"

    elif intent == "ask_question":
        return "je veux poser une question"

    elif intent == "chatbot_usage":
        return "comment fonctionne ce chatbot"

    elif intent == "add_document":
        return "comment ajouter un document"

    elif intent == "bot_capabilities":
        return "que peux-tu faire"

    return reformulated