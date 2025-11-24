import sqlite3
import datetime
import json
from flask import Flask, render_template, request, redirect, url_for, session, flash

app = Flask(__name__)
app.secret_key = 'change_this_secret_key' 

DATABASE = 'troll_data.db'
ADMIN_PASSWORD = "password123"
CONTENDERS = ["johnyard", "gdibs", "brenko", "xopher"]

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

# --- DATA PROCESSING FOR CHART ---
def get_chart_data():
    conn = get_db_connection()
    entries = conn.execute('SELECT * FROM entries').fetchall()
    conn.close()

    current_year = datetime.datetime.now().year
    
    # Structure: data_matrix[month_index (0-11)][contender_index (0-3)]
    # We use lists to easily map to Chart.js datasets
    raw_data = {name: [0]*12 for name in CONTENDERS}
    
    # 1. Aggregate Data
    for entry in entries:
        date_obj = datetime.datetime.strptime(entry['entry_date'], '%Y-%m-%d')
        if date_obj.year == current_year:
            month_idx = date_obj.month - 1 # 0 for Jan, 1 for Feb...
            if entry['name'] in raw_data:
                raw_data[entry['name']][month_idx] += entry['troll_count']

    # 2. Determine Monthly Winners (for highlighting)
    # winners_map[month_idx] = "name_of_winner"
    winners_map = {}
    for m_idx in range(12):
        current_month_scores = {name: raw_data[name][m_idx] for name in CONTENDERS}
        # Filter out 0s, we don't want a winner if everyone is 0
        valid_scores = {k: v for k, v in current_month_scores.items() if v > 0}
        
        if valid_scores:
            winner = max(valid_scores, key=valid_scores.get)
            winners_map[m_idx] = winner
        else:
            winners_map[m_idx] = None

    return raw_data, winners_map

@app.route('/')
def index():
    chart_data, monthly_winners = get_chart_data()
    
    # Calculate Totals for the "Leaderboard" text
    totals = {name: sum(scores) for name, scores in chart_data.items()}
    sorted_totals = sorted(totals.items(), key=lambda x: x[1], reverse=True)
    
    return render_template(
        'index.html', 
        contenders=CONTENDERS,
        chart_data=json.dumps(chart_data),      # Pass as JSON for JS
        monthly_winners=json.dumps(monthly_winners), # Pass as JSON for JS
        sorted_totals=sorted_totals
    )

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        if request.form['password'] == ADMIN_PASSWORD:
            session['logged_in'] = True
            return redirect(url_for('admin'))
        else:
            flash('Wrong password.')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    return redirect(url_for('index'))

@app.route('/admin', methods=['GET', 'POST'])
def admin():
    if not session.get('logged_in'):
        return redirect(url_for('login'))

    if request.method == 'POST':
        name = request.form['name']
        count = int(request.form['count'])
        date = request.form['date']
        
        conn = get_db_connection()
        conn.execute('INSERT INTO entries (name, troll_count, entry_date) VALUES (?, ?, ?)',
                     (name, count, date))
        conn.commit()
        conn.close()
        flash(f'Tracked {count} trolls for {name}.')
        
    return render_template('admin.html', contenders=CONTENDERS)

if __name__ == '__main__':
    import os
    if not os.path.exists(DATABASE):
        # Create DB if missing
        with app.app_context():
            conn = get_db_connection()
            conn.execute('CREATE TABLE IF NOT EXISTS entries (id INTEGER PRIMARY KEY, name TEXT, troll_count INTEGER, entry_date DATE)')
            conn.commit()
            conn.close()
    app.run(debug=True)