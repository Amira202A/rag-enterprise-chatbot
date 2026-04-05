# app/nlp/intent_detector.py

def detect_intent(text: str) -> str:
    t = text.lower().strip()

    # 🔹 0) Very short casual replies
    casual_words = [
        "ok", "okay", "okk", "merci", "thanks", "thank you",
        "d'accord", "dac", "cool", "nice", "super", "top",
        "behi", "behy", "s7i7", "ey", "yes", "oui"
    ]
    if t in casual_words:
        return "casual_reply"

    # 🔹 1) GREETING
    greetings = [
        "bonjour", "salut", "hello", "hi", "hey", "coucou",
        "salam", "salem", "aslema", "3aslema",
        "good morning", "good evening", "السلام عليكم"
    ]
    if t in greetings:
        return "greeting"

    # 🔹 2) "cv / labes" = how are you
    wellbeing_words = [
        "cv", "ça va", "ca va", "labes", "lbes", "kifek", "kifek"
    ]
    if t in wellbeing_words:
        return "wellbeing"

    # 🔹 3) HELP REQUEST
    help_words = [
        "aide", "aidez", "help", "3aweni", "aaweni", "brabi",
        "je veux que tu m aide", "je veux que tu m'aides",
        "je veux que tu m'aides svp", "aide moi", "aide-moi",
        "ساعدني", "عاونّي", "عاونى", "3awenni"
    ]
    if any(h in t for h in help_words):
        return "help"

    # 🔹 4) ASK READY
    ask_words = [
        "nsaalek", "nsa2lek", "nsaalek", "nse2lek", "nselek",
        "nese2lek", "neselek",
        "souel", "sou2el", "question",
        "nheb nsaalek", "nheb nsa2lek", "nheb nese2lek", "nheb neselek",
        "je veux te poser", "je veux poser une question",
        "tfadhal", "es2el", "ask you"
    ]
    if any(a in t for a in ask_words):
        return "ask_ready"

    # 🔹 5) BOT CAPABILITIES
    capability_words = [
        "chnowa tnajem ta3mel",
        "que peux tu faire",
        "que peux-tu faire",
        "what can you do",
        "kifesh nekhdem bik",
        "kifeh nekhdem bik",
        "kifesh nekhdem b chatbot hedha",
        "kifeh nekhdem b chatbot hedha",
        "comment tu peux m'aider",
        "comment fonctionne ce chatbot",
        "chnowa تعمل",
        "شنوا تعمل"
    ]
    if any(c in t for c in capability_words):
        return "capabilities"

    # 🔹 6) Small talk / open chat
    smalltalk_words = [
        "kifeh", "kifesh", "aleh", "3leh", "chnowa", "chnia",
        "how are you", "who are you", "who r u", "who are u",
        "comment vas tu", "comment ça va", "comment ca va",
        "tu es qui", "qui es tu", "qui es-tu"
    ]
    if t in smalltalk_words:
        return "smalltalk"

    return "business_question"