from flask import Flask, render_template_string, request, redirect, url_for, session
import sqlite3
import os

app = Flask(__name__)
app.secret_key = 'cricxabhi_secret_key'
DB_NAME = 'fantasy_web.db'

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS users (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        username TEXT UNIQUE,
                        coins INTEGER DEFAULT 1000)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS matches (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        team1 TEXT, team2 TEXT, status TEXT DEFAULT 'Upcoming')''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS contests (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        match_id INTEGER, name TEXT, prize_pool INTEGER, entry_fee INTEGER, spots INTEGER)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS teams (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        match_id INTEGER, user_id INTEGER, team_name TEXT, players TEXT, points REAL DEFAULT 0)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS joined_contests (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        contest_id INTEGER, team_id INTEGER, user_id INTEGER)''')
    
    cursor.execute("SELECT COUNT(*) FROM matches")
    if cursor.fetchone()[0] == 0:
        cursor.execute("INSERT INTO matches (team1, team2, status) VALUES ('IND', 'AUS', 'Upcoming')")
        cursor.execute("INSERT INTO contests (match_id, name, prize_pool, entry_fee, spots) VALUES (1, 'Mega Contest', 10000, 49, 100)")
        cursor.execute("INSERT INTO users (username, coins) VALUES ('AbhiAdmin', 5000)")
    conn.commit()
    conn.close()

init_db()

@app.route('/')
def index():
    if 'user_id' not in session:
        session['user_id'] = 1
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE id = ?", (session['user_id'],))
    user = cursor.fetchone()
    cursor.execute("SELECT * FROM matches")
    matches = cursor.fetchall()
    conn.close()
    return render_template_string('''
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>CRICXABHI Fantasy</title>
        <script src="https://cdn.tailwindcss.com"></script>
    </head>
    <body class="bg-gray-900 text-white font-sans">
        <div class="bg-indigo-600 p-4 flex justify-between items-center shadow-md">
            <h1 class="text-xl font-bold">CRICXABHI Fantasy 🏏</h1>
            <div class="bg-indigo-800 px-3 py-1 rounded-full text-sm font-semibold">🪙 Coins: {{ user['coins'] }}</div>
        </div>
        <div class="max-w-md mx-auto p-4">
            <h2 class="text-lg font-semibold mb-3">Upcoming Matches</h2>
            {% for match in matches %}
            <div class="bg-gray-800 border border-gray-700 rounded-xl p-4 mb-4 shadow">
                <div class="flex justify-between items-center mb-3">
                    <span class="font-bold text-lg">{{ match['team1'] }} vs {{ match['team2'] }}</span>
                    <span class="text-xs bg-green-500 text-black px-2 py-1 rounded font-bold uppercase">{{ match['status'] }}</span>
                </div>
                <a href="/match/{{ match['id'] }}" class="block text-center bg-indigo-500 hover:bg-indigo-600 text-white font-bold py-2 rounded-lg transition">Enter Match & Contests</a>
            </div>
            {% endfor %}
        </div>
    </body>
    </html>
    ''', user=user, matches=matches)

@app.route('/match/<int:match_id>')
def match_detail(match_id):
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM matches WHERE id = ?", (match_id,))
    match = cursor.fetchone()
    cursor.execute("SELECT * FROM contests WHERE match_id = ?", (match_id,))
    contests = cursor.fetchall()
    conn.close()
    return render_template_string('''
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Contests - CRICXABHI</title>
        <script src="https://cdn.tailwindcss.com"></script>
    </head>
    <body class="bg-gray-900 text-white font-sans">
        <div class="bg-indigo-600 p-4 flex items-center shadow-md">
            <a href="/" class="mr-3 text-xl font-bold">←</a>
            <h1 class="text-lg font-bold">{{ match['team1'] }} vs {{ match['team2'] }} Contests</h1>
        </div>
        <div class="max-w-md mx-auto p-4">
            {% for contest in contests %}
            <div class="bg-gray-800 border border-gray-700 rounded-xl p-4 mb-4 shadow">
                <div class="flex justify-between font-bold text-gray-300 mb-1">
                    <span>{{ contest['name'] }}</span>
                    <span class="text-green-400">Prize: 🪙{{ contest['prize_pool'] }}</span>
                </div>
                <div class="text-sm text-gray-400 mb-3">Entry Fee: 🪙{{ contest['entry_fee'] }} | Spots: {{ contest['spots'] }}</div>
                <a href="/create_team/{{ match['id'] }}/{{ contest['id'] }}" class="block text-center bg-green-600 hover:bg-green-700 text-white font-bold py-2 rounded-lg transition">Join Contest</a>
            </div>
            {% endfor %}
        </div>
    </body>
    </html>
    ''', match=match, contests=contests)

@app.route('/create_team/<int:match_id>/<int:contest_id>', methods=['GET', 'POST'])
def create_team(match_id, contest_id):
    if request.method == 'POST':
        team_name = request.form.get('team_name')
        players = "Virat, Rohit, Bumrah, Gill, Kohli"
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute("INSERT INTO teams (match_id, user_id, team_name, players) VALUES (?, 1, ?, ?)", (match_id, team_name, players))
        conn.commit()
        conn.close()
        return redirect(url_for('index'))
    return render_template_string('''
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Create Team</title>
        <script src="https://cdn.tailwindcss.com"></script>
    </head>
    <body class="bg-gray-900 text-white font-sans p-4">
        <div class="max-w-md mx-auto bg-gray-800 p-6 rounded-xl shadow-md">
            <h2 class="text-xl font-bold mb-4">Create Your Fantasy Team</h2>
            <form method="POST">
                <label class="block text-sm text-gray-400 mb-2">Team Name</label>
                <input type="text" name="team_name" required class="w-full bg-gray-900 border border-gray-700 rounded p-2 mb-4 text-white" placeholder="e.g. CricXabhi XI">
                <button type="submit" class="w-full bg-indigo-600 hover:bg-indigo-700 font-bold py-2 rounded transition">Save & Join</button>
            </form>
        </div>
    </body>
    </html>
    ''')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
      
