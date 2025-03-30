import sqlite3
import yfinance as yf
import pandas as pd
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext

# Database setup
def create_table():
    with sqlite3.connect("stocks.db") as conn:
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS stocks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT NOT NULL,
                date TEXT NOT NULL,
                open_price REAL NOT NULL,
                high_price REAL NOT NULL,
                low_price REAL NOT NULL,
                close_price REAL NOT NULL,
                volume INTEGER NOT NULL
            )
        ''')
        conn.commit()

# Fetch stock data
def fetch_stock_data(symbol):
    try:
        stock_data = yf.download(symbol, period="7d", interval="1d")
        if stock_data.empty:
            return None
        return stock_data
    except Exception as e:
        return None

# Add stock data
def add_stock(symbol_entry, output_text):
    symbol = symbol_entry.get().upper()
    if not symbol:
        messagebox.showerror("Error", "Please enter a stock symbol!")
        return

    stock_data = fetch_stock_data(symbol)
    if stock_data is None:
        output_text.insert(tk.END, f"⚠️ Unable to fetch data for {symbol} or invalid symbol!\n")
        return

    with sqlite3.connect("stocks.db") as conn:
        cursor = conn.cursor()
        for date, row in stock_data.iterrows():
            if row.isnull().any():
                output_text.insert(tk.END, f"⚠️ {symbol} {date.strftime('%Y-%m-%d')} has missing data, skipped!\n")
                continue

            cursor.execute('''
                INSERT INTO stocks (symbol, date, open_price, high_price, low_price, close_price, volume)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (symbol, date.strftime("%Y-%m-%d"), float(row["Open"]), float(row["High"]),
                  float(row["Low"]), float(row["Close"]), int(row["Volume"])))

        conn.commit()
        output_text.insert(tk.END, f"✅ Stock {symbol} data successfully added!\n")

# View all stocks
def view_stocks(output_text):
    output_text.delete(1.0, tk.END)
    with sqlite3.connect("stocks.db") as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM stocks")
        rows = cursor.fetchall()

        if not rows:
            output_text.insert(tk.END, "⚠️ No stock data available!\n")
            return

        header = "ID | Symbol | Date       | Open   | High   | Low    | Close  | Volume\n" + "-" * 80 + "\n"
        output_text.insert(tk.END, header)
        for row in rows:
            output_text.insert(tk.END, f"{row[0]:<3} | {row[1]:<6} | {row[2]:<10} | "
                                          f"{row[3]:<6.2f} | {row[4]:<6.2f} | {row[5]:<6.2f} | "
                                          f"{row[6]:<6.2f} | {row[7]:<10}\n")

# Update stock data
def update_stock(symbol_entry, date_entry, price_entry, output_text):
    symbol = symbol_entry.get().upper()
    date = date_entry.get()
    new_price = price_entry.get()

    if not all([symbol, date, new_price]):
        messagebox.showerror("Error", "Please fill all fields for update!")
        return

    try:
        new_price = float(new_price)
    except ValueError:
        messagebox.showerror("Error", "Invalid price! Please enter a numeric value.")
        return

    with sqlite3.connect("stocks.db") as conn:
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE stocks SET close_price = ? WHERE symbol = ? AND date = ?
        ''', (new_price, symbol, date))
        conn.commit()

        if cursor.rowcount > 0:
            output_text.insert(tk.END, f"✅ {symbol} {date} close price updated to {new_price}!\n")
        else:
            output_text.insert(tk.END, f"⚠️ No data found for {symbol} on {date}!\n")

# Delete stock data
def delete_stock(symbol_entry, date_entry, output_text):
    symbol = symbol_entry.get().upper()
    date = date_entry.get()

    if not all([symbol, date]):
        messagebox.showerror("Error", "Please enter symbol and date to delete!")
        return

    with sqlite3.connect("stocks.db") as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM stocks WHERE symbol = ? AND date = ?", (symbol, date))
        conn.commit()

        if cursor.rowcount > 0:
            output_text.insert(tk.END, f"✅ {symbol} {date} data deleted!\n")
        else:
            output_text.insert(tk.END, f"⚠️ No data found for {symbol} on {date}!\n")

# Setup GUI
def setup_gui():
    root = tk.Tk()
    root.title("Stock Management System")
    root.geometry("800x600")

    # Create table if not exists
    create_table()

    # Main frame
    main_frame = ttk.Frame(root, padding="15")
    main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

    # Input fields
    ttk.Label(main_frame, text="Stock Symbol (e.g., AAPL, 2330.TW):").grid(row=0, column=0, pady=5)
    symbol_entry = ttk.Entry(main_frame)
    symbol_entry.grid(row=0, column=1, pady=5)

    ttk.Label(main_frame, text="Date (YYYY-MM-DD):").grid(row=1, column=0, pady=5)
    date_entry = ttk.Entry(main_frame)
    date_entry.grid(row=1, column=1, pady=5)

    ttk.Label(main_frame, text="New Close Price (for update):").grid(row=2, column=0, pady=5)
    price_entry = ttk.Entry(main_frame)
    price_entry.grid(row=2, column=1, pady=5)

    # Output area
    output_text = scrolledtext.ScrolledText(main_frame, width=110, height=25)
    output_text.grid(row=6, column=0, columnspan=2, pady=10)

    # Buttons
    ttk.Button(main_frame, text="Add Stock", 
               command=lambda: add_stock(symbol_entry, output_text)).grid(row=3, column=0, pady=5)
    ttk.Button(main_frame, text="View Stocks", 
               command=lambda: view_stocks(output_text)).grid(row=3, column=1, pady=5)
    ttk.Button(main_frame, text="Update Stock", 
               command=lambda: update_stock(symbol_entry, date_entry, price_entry, output_text)).grid(row=4, column=0, pady=5)
    ttk.Button(main_frame, text="Delete Stock", 
               command=lambda: delete_stock(symbol_entry, date_entry, output_text)).grid(row=4, column=1, pady=5)
    ttk.Button(main_frame, text="Exit", 
               command=root.quit).grid(row=5, column=0, columnspan=2, pady=5)

    root.mainloop()

# Start the application
if __name__ == "__main__":
    setup_gui()
