import requests

API_URL = "http://127.0.0.1:8000/chat"

print("🤖 Chatbot Entreprise (tape 'exit' pour quitter)\n")

while True:
    question = input("Vous: ")

    if question.lower() == "exit":
        break

    try:
        response = requests.post(
            API_URL,
            json={"question": question},
            timeout=250  # 🔥 IMPORTANT
        )

        response.raise_for_status()
        data = response.json()

        print("\n🤖 Bot:")
        print(data.get("answer", "Pas de réponse."))

    except Exception as e:
        print(f"❌ Erreur : {e}")

    print("\n" + "-" * 50 + "\n")
