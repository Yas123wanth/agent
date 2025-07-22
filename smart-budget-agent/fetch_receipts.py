from __future__ import print_function
import os.path
import re
import base64
from email import message_from_bytes
from dotenv import load_dotenv
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
import firebase_admin
from firebase_admin import credentials, firestore
from budget_engine import analyze_transaction

# 🔐 Load environment variables
load_dotenv()

# 🔧 Firebase setup
cred = credentials.Certificate(os.getenv("GOOGLE_APPLICATION_CREDENTIALS"))
if not firebase_admin._apps:
    firebase_admin.initialize_app(cred)

db = firestore.client()
COLLECTION_NAME = "financial_advisor"

# 📩 Gmail API setup
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']
TOKEN_PATH = 'oauth/token.json'
CLIENT_SECRET_PATH = 'oauth/client_secret.json'

# 🔑 Gmail Authentication
creds = None
if os.path.exists(TOKEN_PATH):
    from google.oauth2.credentials import Credentials
    creds = Credentials.from_authorized_user_file(TOKEN_PATH, SCOPES)
if not creds or not creds.valid:
    flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRET_PATH, SCOPES)
    creds = flow.run_local_server(port=0)
    with open(TOKEN_PATH, 'w') as token:
        token.write(creds.to_json())

service = build('gmail', 'v1', credentials=creds)

# 🔍 Search inbox
query = '(from:googlepay-noreply@google.com OR from:canarabank@canarabank.com) subject:(receipt OR debit OR transaction OR alert)'
results = service.users().messages().list(userId='me', q=query, maxResults=10).execute()
messages = results.get('messages', [])
print(f"📬 Found {len(messages)} matching emails")

for msg in messages:
    print("📥 Processing email ID:", msg["id"])
    raw_msg = service.users().messages().get(userId='me', id=msg['id'], format='raw').execute()
    raw_data = base64.urlsafe_b64decode(raw_msg['raw'].encode('ASCII'))
    email_msg = message_from_bytes(raw_data)
    body = email_msg.get_payload(decode=True)
    body_str = body.decode(errors="ignore")

    # 🧠 Google Pay block
    if 'googlepay-noreply@google.com' in body_str:
        amount_match = re.search(r'Amount paid[:\s₹]*\s?₹?(\d+)', body_str)
        merchant_match = re.search(r'Merchant[:\s]*([A-Za-z0-9 &]+)', body_str)
        date_match = re.search(r'Date[:\s]*([A-Za-z0-9 ,]+)', body_str)

        if amount_match:
            transaction = {
                "amount": int(amount_match.group(1)),
                "category": "Google Pay",
                "merchant": merchant_match.group(1) if merchant_match else "Unknown",
                "date": date_match.group(1) if date_match else "Unknown",
                "source": "Google Pay Email"
            }
            try:
                db.collection(COLLECTION_NAME).add(transaction)
                print(f"✅ Google Pay saved: {transaction}")
                analyze_transaction(transaction)
            except Exception as e:
                print("❌ Firestore error:", e)

    # 🏦 Canara Bank block
    elif 'canarabank@canarabank.com' in body_str:
        amount_match = re.search(r'amount\s+of\s+INR\s([\d,]+\.\d{2})\s+has\s+been\s+DEBITED', body_str, re.IGNORECASE)
        date_match = re.search(r'on\s(\d{2}/\d{2}/\d{4})', body_str)
        account_match = re.search(r'account\s([A-Z]{3}\d+)', body_str)

        if amount_match:
            amount = float(amount_match.group(1).replace(",", ""))
            date = date_match.group(1) if date_match else "Unknown"
            account = account_match.group(1) if account_match else "Unknown"

            transaction = {
                "amount": amount,
                "category": "Bank Debit",
                "merchant": "Canara Bank",
                "date": date,
                "account": account,
                "source": "Canara Bank Email"
            }

            try:
                db.collection(COLLECTION_NAME).add(transaction)
                print("✅ Transaction saved to Firestore.")
                analyze_transaction(transaction)
            except Exception as e:
                print("❌ Firestore save error:", e)
        else:
            print("❌ Parsing failed — amount not found")
