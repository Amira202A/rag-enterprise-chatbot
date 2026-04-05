import requests
import time

BASE_URL = "http://127.0.0.1:8000"

print("🤖 Chatbot Entreprise (tape 'exit' pour quitter)\n")

# 1️⃣ Login
cin      = input("CIN : ")
password = input("Mot de passe : ")

try:
    res = requests.post(f"{BASE_URL}/auth/login", json={"cin": cin, "password": password})
    res.raise_for_status()
    token = res.json()["access_token"]
    print(f"✅ Connecté !\n")
except Exception as e:
    print(f"❌ Erreur login : {e}")
    exit()

headers = {"Authorization": f"Bearer {token}"}

# 2️⃣ Créer une conversation
try:
    res = requests.post(f"{BASE_URL}/conversation/new", headers=headers)
    res.raise_for_status()
    conversation_id = res.json()["conversation_id"]
    print(f"🆕 Conversation créée : {conversation_id}\n")
except Exception as e:
    print(f"❌ Impossible de créer la conversation : {e}")
    exit()

# 3️⃣ Boucle de chat
while True:
    question = input("Vous: ")
    if question.lower() == "exit":
        break
    try:
        start_time = time.time()
        response = requests.post(
            f"{BASE_URL}/chat",
            json={"question": question, "conversation_id": conversation_id},
            headers=headers,
            timeout=250
        )
        response.raise_for_status()
        data = response.json()
        print("🤖 Bot:", data.get("answer", "Pas de réponse."))
        print(f"⏱ Temps: {round(time.time() - start_time, 2)}s")
    except Exception as e:
        print(f"❌ Erreur : {e}")
    print("\n" + "-" * 50 + "\n")