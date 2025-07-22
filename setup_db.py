import sqlite3
import os

os.makedirs("data", exist_ok=True)

conn = sqlite3.connect("data/invoices.db")
c = conn.cursor()

c.execute('''CREATE TABLE IF NOT EXISTS invoices (
    invoice_number TEXT PRIMARY KEY,
    client_name TEXT,
    invoice_date TEXT,
    items TEXT,
    total REAL,
    tax_percent REAL,
    notes TEXT
)''')

conn.commit()
conn.close()

print("✅ Database initialized successfully.")
