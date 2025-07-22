from budget_engine import analyze_transaction

txn = {
    "amount": 800,
    "category": "Bank Debit",
    "merchant": "Canara Bank",
    "date": "2025-07-21",
    "account": "XXX413",
    "source": "Manual Test"
}

analyze_transaction(txn)
