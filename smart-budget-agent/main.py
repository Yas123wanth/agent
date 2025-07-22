import os
from dotenv import load_dotenv
import firebase_admin
from firebase_admin import credentials, firestore
from datetime import date

# 🌐 Load environment variables from .env file
load_dotenv()

# 🔐 Initialize Firebase Admin SDK
cred = credentials.Certificate(os.getenv("GOOGLE_APPLICATION_CREDENTIALS"))
firebase_admin.initialize_app(cred)

# 🔍 Connect to Firestore
db = firestore.client()

# 🧾 Sample transaction data
transaction = {
    "amount": 600,
    "category": "Utilities",
    "date": str(date.today())
}

# 🧠 Save to Firestore under 'transactions' collection
db.collection("transactions").add(transaction)

print("✅ Transaction successfully added to Firestore")
