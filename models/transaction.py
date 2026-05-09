# models/transaction.py
class Transaction:
    def __init__(self, date, category, description, type, amount, account, tags, note):
        self.date = date
        self.category = category
        self.description = description
        self.type = type
        self.amount = amount
        self.account = account
        self.tags = tags
        self.note = note
