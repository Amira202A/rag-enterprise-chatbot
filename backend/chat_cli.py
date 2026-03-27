import requests
import time

BASE_URL = "http://127.0.0.1:8000"

print("🤖 Chatbot Entreprise (tape 'exit' pour quitter)\n")

# 1️⃣ Créer une conversation automatiquement
try:
    res = requests.post(f"{BASE_URL}/conversation/new")
    res.raise_for_status()
    conversation_id = res.json()["conversation_id"]
    print(f"🆕 Conversation créée : {conversation_id}\n")

except Exception as e:
    print(f"❌ Impossible de créer la conversation : {e}")
    exit()

# 2️⃣ Boucle de chat
while True:

    question = input("Vous: ")

    if question.lower() == "exit":
        break

    try:
        start_time = time.time()  # ⏱ début

        response = requests.post(
            f"{BASE_URL}/chat",
            json={
                "question": question,
                "conversation_id": conversation_id
            },
            timeout=250
        )

        response.raise_for_status()
        data = response.json()

        end_time = time.time()  # ⏱ fin

        print("🤖 Bot:", data.get("answer", "Pas de réponse."))
        print(f"⏱ Temps de réponse: {round(end_time - start_time, 2)} secondes")

    except Exception as e:
        print(f"❌ Erreur : {e}")

    print("\n" + "-" * 50 + "\n")
    