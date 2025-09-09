import json
import os
from transformers import pipeline
import sympy

# -------- CONFIGURATIE --------
BASE_FILE = "base_knowledge.txt"
MEMORY_FILE = "memory.json"
USERS_FILE = "users.json"
MAX_MEMORY_SIZE = 1 * 1024 * 1024  # 1 MB
CONTEXT_SIZE = 5  # aantal recente berichten onthouden

# -------- LOGIN SYSTEM --------
def load_users():
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, "r") as f:
            return json.load(f)
    else:
        # standaard admin account
        users = {"admin": "wachtwoord123"}
        with open(USERS_FILE, "w") as f:
            json.dump(users, f, indent=2)
        return users

def login():
    users = load_users()
    print("Welkom! Log in om de AI Chatbot te gebruiken.")
    while True:
        username = input("Gebruikersnaam: ")
        password = input("Wachtwoord: ")
        if username in users and users[username] == password:
            print(f"Ingelogd als {username}\n")
            return username
        else:
            print("Fout! Probeer het opnieuw.\n")

current_user = login()

# -------- LAAD BASISKENNIS --------
base_knowledge = {}
if os.path.exists(BASE_FILE):
    with open(BASE_FILE, "r", encoding="utf-8") as f:
        for line in f:
            if ":" in line:
                key, value = line.strip().split(":", 1)
                base_knowledge[key.strip()] = value.strip()

bot_name = base_knowledge.get("Botnaam", "ChatBuddy")
owner_name = base_knowledge.get("Eigenaar", "Sem")
skills = [s.strip() for s in base_knowledge.get("Skills", "").split(",")]

# -------- LAAD GEHEUGEN --------
if os.path.exists(MEMORY_FILE):
    with open(MEMORY_FILE, "r") as f:
        memory_data = json.load(f)
else:
    memory_data = {"memory": []}

conversation_history = []

# -------- AI MODEL --------
print(f"{bot_name} laadt AI model... even geduld!")
chatbot_ai = pipeline("text-generation", model="distilgpt2")

# -------- FUNCTIES --------
def save_memory():
    data_str = json.dumps(memory_data)
    if len(data_str.encode("utf-8")) > MAX_MEMORY_SIZE:
        print("⚠ Max geheugen bereikt! Oude info wordt verwijderd...")
        if memory_data["memory"]:
            memory_data["memory"].pop(0)
            save_memory()
    else:
        with open(MEMORY_FILE, "w") as f:
            json.dump(memory_data, f, indent=2)

def add_memory(topic, summary):
    memory_data["memory"].append({"topic": topic, "summary": summary})
    save_memory()

def math_solver(question):
    try:
        expr = sympy.sympify(question)
        return str(expr.evalf())
    except:
        return "Sorry, ik kan dit niet oplossen."

# -------- CHAT FUNCTIE --------
def chat():
    print(f"\n{bot_name} klaar om te chatten! (type 'quit' om te stoppen)")
    print(f"Ik kan helpen met: {', '.join(skills)}\n")
    while True:
        user_input = input(f"{current_user}: ")
        if user_input.lower() == "quit":
            print(f"{bot_name}: Tot ziens!")
            break

        conversation_history.append(f"{current_user}: {user_input}")
        context = "\n".join(conversation_history[-CONTEXT_SIZE:])

        if any(word in user_input.lower() for word in ["+", "-", "*", "/", "=", "wiskunde", "reken"]):
            response_text = math_solver(user_input)
        else:
            try:
                response = chatbot_ai(context, max_length=100, num_return_sequences=1)
                response_text = response[0]["generated_text"].replace(context, "").strip()
                if not response_text:
                    response_text = "Sorry, ik begrijp het niet."
            except:
                response_text = "Sorry, ik begrijp het niet."

        print(f"{bot_name}: {response_text}")

        # geheugen toevoegen (samenvatting = korte versie)
        add_memory("last_input", user_input[:100])

# -------- START CHATBOT --------
if __name__ == "__main__":
    print(f"Hallo! Ik ben {bot_name}, de AI van {owner_name}.")
    chat()
