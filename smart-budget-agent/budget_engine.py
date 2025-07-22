import os
import smtplib
import ssl
from dotenv import load_dotenv
import firebase_admin
from firebase_admin import credentials, firestore

# 🔐 Load environment variables
load_dotenv()

# 🔧 Firebase setup
cred = credentials.Certificate(os.getenv("GOOGLE_APPLICATION_CREDENTIALS"))
if not firebase_admin._apps:
    firebase_admin.initialize_app(cred)
db = firestore.client()
COLLECTION_NAME = "financial_advisor"

# 💰 Budget limits
budget_limits = {
    "Dining": 3000,
    "Groceries": 5000,
    "Travel": 4000,
    "Entertainment": 2000,
    "Google Pay": 3500,
    "Bank Debit": 2500
}

# 📧 Send email alert
def send_email_alert(category, amount, limit):
    sender = "yaswanthgrandhi2580@gmail.com"
    receiver = "yaswanthgrandhi2580@gmail.com"  # 🔁 Replace with destination
    password = os.getenv("EMAIL_APP_PASSWORD")

    message = f"""\
Subject: Budget Alert – {category} Overspend

You’ve spent ₹{amount} in {category}, exceeding your limit of ₹{limit}.
Smart Budget Agent recommends reviewing your expenses.
"""

    try:
        context = ssl.create_default_context()
        with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as server:
            server.login(sender, password)
            server.sendmail(sender, receiver, message)
        print(f"📬 Email alert sent to {receiver}.")
    except Exception as e:
        print(f"❌ Email failed:", e)

# 🧠 Analyze transaction
def analyze_transaction(transaction):
    print("🔍 analyze_transaction triggered with:", transaction)

    category = transaction.get("category")
    current_amount = transaction.get("amount", 0)

    print(f"\n🧠 Analyzing: {category}, ₹{current_amount}")

    if category not in budget_limits:
        print(f"⚠️ No budget configured for '{category}'. Skipping.")
        return

    # Get all transactions for this category
    query = db.collection(COLLECTION_NAME).where("category", "==", category)
    docs = list(query.stream())  # Convert to list to ensure we can iterate multiple times
    
    # Calculate total including the current transaction
    previous_total = sum(doc.to_dict().get("amount", 0) for doc in docs if doc.to_dict().get("amount"))
    total_spent = previous_total + current_amount
    limit = budget_limits[category]
    usage_percent = (total_spent / limit) * 100

    print(f"📈 Previous total: ₹{previous_total}")
    print(f"➕ New transaction: ₹{current_amount}")

    print(f"📊 Budget Analysis:")
    print(f"🧾 Category: {category}")
    print(f"💰 Spent: ₹{total_spent} / ₹{limit} ({usage_percent:.1f}%)")

    if usage_percent >= 100:
        print(f"🚨 ALERT: Over budget for '{category}'!")
        send_email_alert(category, total_spent, limit)
    elif usage_percent >= 90:
        print(f"⚠️ WARNING: You're at {usage_percent:.1f}% of your '{category}' budget.")
    else:
        print(f"✅ Within budget for '{category}'.")
