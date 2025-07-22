import tkinter as tk
import tkinter.ttk as ttk
from tkinter import messagebox
from datetime import datetime
import os
import webbrowser
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
import sqlite3

# Ensure folders exist
os.makedirs("invoices", exist_ok=True)
os.makedirs("data", exist_ok=True)

# Initialize database
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


class InvoiceApp:
    def __init__(self, root):
        self.root = root
        self.root.title("🧾 Invoice Generator")
        self.products = []

        # --- Variables ---
        self.client_name_var = tk.StringVar()
        self.date_var = tk.StringVar(value=datetime.today().strftime('%Y-%m-%d'))
        self.tax_var = tk.DoubleVar(value=0.0)

        # --- Header ---
        tk.Label(root, text="Invoice Generator", font=("Arial", 18, "bold")).pack(pady=10)

        # --- Invoice Info Frame ---
        form_frame = tk.Frame(root)
        form_frame.pack()

        tk.Label(form_frame, text="Client Name:").grid(row=0, column=0)
        tk.Entry(form_frame, textvariable=self.client_name_var, width=25).grid(row=0, column=1, padx=5)

        tk.Label(form_frame, text="Invoice Date:").grid(row=0, column=2)
        tk.Entry(form_frame, textvariable=self.date_var, width=15).grid(row=0, column=3)

        tk.Label(form_frame, text="GST / Tax %:").grid(row=0, column=4)
        tk.Entry(form_frame, textvariable=self.tax_var, width=5).grid(row=0, column=5)

        # --- Product List Header ---
        self.product_frame = tk.Frame(root)
        self.product_frame.pack(pady=10)

        for i, h in enumerate(["Product Name", "Quantity", "Unit Price", "Amount"]):
            tk.Label(self.product_frame, text=h, font=("Arial", 10, "bold")).grid(row=0, column=i, padx=10)

        self.add_product_row()

        # --- Notes ---
        tk.Label(root, text="Notes / Terms:").pack()
        self.notes_text = tk.Text(root, height=4, width=70)
        self.notes_text.pack()

        # --- Buttons ---
        btn_frame = tk.Frame(root)
        btn_frame.pack(pady=10)

        tk.Button(btn_frame, text="Add Product Row", command=self.add_product_row).grid(row=0, column=0, padx=5)
        tk.Button(btn_frame, text="Generate Invoice PDF", command=self.generate_invoice).grid(row=0, column=1, padx=5)
        tk.Button(btn_frame, text="Clear Form", command=self.clear_form).grid(row=0, column=2, padx=5)
        tk.Button(btn_frame, text="View Past Invoices", command=self.show_past_invoices).grid(row=0, column=3, padx=5)

    # ---------------------- Core Functions ----------------------

    def add_product_row(self):
        row = len(self.products) + 1
        name = tk.Entry(self.product_frame)
        qty = tk.Entry(self.product_frame, width=5)
        price = tk.Entry(self.product_frame, width=10)
        amt = tk.Label(self.product_frame, text="0.00")

        name.grid(row=row, column=0, padx=5)
        qty.grid(row=row, column=1)
        price.grid(row=row, column=2)
        amt.grid(row=row, column=3)

        qty.bind("<KeyRelease>", lambda e: self.update_amounts())
        price.bind("<KeyRelease>", lambda e: self.update_amounts())

        self.products.append((name, qty, price, amt))

    def update_amounts(self):
        for name, qty, price, amt in self.products:
            try:
                q = float(qty.get())
                p = float(price.get())
                amt.config(text=f"{q * p:.2f}")
            except:
                amt.config(text="0.00")

    def generate_invoice(self):
        client = self.client_name_var.get().strip()
        date = self.date_var.get().strip()
        tax = self.tax_var.get()
        notes = self.notes_text.get("1.0", "end").strip()

        if not client:
            messagebox.showerror("Missing Info", "Client name is required.")
            return

        items = []
        subtotal = 0
        for name, qty, price, amt in self.products:
            try:
                pname = name.get().strip()
                q = float(qty.get())
                p = float(price.get())
                a = q * p
                subtotal += a
                items.append((pname, q, p, a))
            except:
                continue

        if not items:
            messagebox.showerror("Missing Info", "Add at least one product.")
            return

        total = subtotal + (subtotal * tax / 100)
        invoice_num = f"INV-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
        pdf_file = f"invoices/{invoice_num}.pdf"

        # --- Generate PDF ---
        c = canvas.Canvas(pdf_file, pagesize=A4)
        width, height = A4
        y = height - 40

        c.setFont("Helvetica-Bold", 16)
        c.drawString(50, y, "INVOICE")
        y -= 30

        c.setFont("Helvetica", 10)
        c.drawString(50, y, f"Invoice No: {invoice_num}")
        c.drawString(300, y, f"Date: {date}")
        y -= 20
        c.drawString(50, y, f"Client: {client}")
        y -= 30

        # --- Table ---
        c.setFont("Helvetica-Bold", 10)
        c.drawString(50, y, "Product")
        c.drawString(200, y, "Qty")
        c.drawString(250, y, "Price")
        c.drawString(330, y, "Amount")
        y -= 15

        c.setFont("Helvetica", 10)
        for pname, q, p, a in items:
            c.drawString(50, y, pname)
            c.drawString(200, y, str(q))
            c.drawString(250, y, f"{p:.2f}")
            c.drawString(330, y, f"{a:.2f}")
            y -= 15

        y -= 15
        c.drawString(250, y, "Subtotal:")
        c.drawString(330, y, f"{subtotal:.2f}")
        y -= 15
        c.drawString(250, y, f"Tax ({tax}%):")
        c.drawString(330, y, f"{subtotal * tax / 100:.2f}")
        y -= 15
        c.setFont("Helvetica-Bold", 10)
        c.drawString(250, y, "Total:")
        c.drawString(330, y, f"{total:.2f}")
        y -= 30

        if notes:
            c.setFont("Helvetica", 10)
            c.drawString(50, y, "Notes:")
            y -= 15
            for line in notes.split('\n'):
                c.drawString(50, y, line)
                y -= 12

        c.save()
        messagebox.showinfo("Success", f"Invoice saved as {pdf_file}")

        # --- Save to DB ---
        conn = sqlite3.connect("data/invoices.db")
        c = conn.cursor()
        c.execute("INSERT INTO invoices VALUES (?, ?, ?, ?, ?, ?, ?)",
                  (invoice_num, client, date, str(items), total, tax, notes))
        conn.commit()
        conn.close()

    def clear_form(self):
        self.client_name_var.set("")
        self.date_var.set(datetime.today().strftime('%Y-%m-%d'))
        self.tax_var.set(0.0)
        self.notes_text.delete("1.0", "end")
        for widget in self.product_frame.winfo_children():
            widget.destroy()
        self.products.clear()
        self.add_product_row()

    def show_past_invoices(self):
        top = tk.Toplevel(self.root)
        top.title("📁 Past Invoices")
        top.geometry("700x400")

        tree = ttk.Treeview(top, columns=("Invoice No", "Client", "Date", "Total"), show='headings')
        for col in tree["columns"]:
            tree.heading(col, text=col)
        tree.pack(fill="both", expand=True)

        # Scrollbar
        scrollbar = tk.Scrollbar(top, command=tree.yview)
        scrollbar.pack(side="right", fill="y")
        tree.configure(yscroll=scrollbar.set)

        # Load data
        conn = sqlite3.connect("data/invoices.db")
        c = conn.cursor()
        c.execute("SELECT invoice_number, client_name, invoice_date, total FROM invoices ORDER BY invoice_date DESC")
        rows = c.fetchall()
        conn.close()

        for row in rows:
            tree.insert("", "end", values=row)

        # Buttons
        btn_frame = tk.Frame(top)
        btn_frame.pack(pady=10)

        def view_pdf():
            selected = tree.focus()
            if not selected:
                messagebox.showwarning("No selection", "Select an invoice to view.")
                return
            invoice_no = tree.item(selected)['values'][0]
            pdf_path = f"invoices/{invoice_no}.pdf"
            if os.path.exists(pdf_path):
                webbrowser.open_new(pdf_path)
            else:
                messagebox.showerror("Missing File", "PDF file not found.")

        def delete_invoice():
            selected = tree.focus()
            if not selected:
                messagebox.showwarning("No selection", "Select an invoice to delete.")
                return
            invoice_no = tree.item(selected)['values'][0]
            confirm = messagebox.askyesno("Confirm Delete", f"Delete invoice {invoice_no}?")
            if confirm:
                conn = sqlite3.connect("data/invoices.db")
                c = conn.cursor()
                c.execute("DELETE FROM invoices WHERE invoice_number = ?", (invoice_no,))
                conn.commit()
                conn.close()
                pdf_path = f"invoices/{invoice_no}.pdf"
                if os.path.exists(pdf_path):
                    os.remove(pdf_path)
                tree.delete(selected)
                messagebox.showinfo("Deleted", f"Invoice {invoice_no} deleted.")

        tk.Button(btn_frame, text="👁️ View PDF", command=view_pdf).grid(row=0, column=0, padx=10)
        tk.Button(btn_frame, text="❌ Delete Invoice", command=delete_invoice).grid(row=0, column=1, padx=10)


if __name__ == "__main__":
    root = tk.Tk()
    app = InvoiceApp(root)
    root.mainloop()
