from flask import Flask, render_template_string, request, redirect, url_for, session
import sqlite3
import os

app = Flask(__name__)
app.secret_key = 'cricxabhi_custom_admin_secret'
DB_NAME = 'fantasy_web.db'

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # Tables creation
    cursor.execute('''CREATE TABLE IF NOT EXISTS users (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        username TEXT UNIQUE,
                        coins INTEGER DEFAULT 1000)''')
                        
    cursor.execute('''CREATE TABLE IF NOT EXISTS matches (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        team1 TEXT, team2 TEXT, status TEXT DEFAULT 'Upcoming')''')
                        
    cursor.execute('''CREATE TABLE IF NOT EXISTS players (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        match_id INTEGER, name TEXT, team TEXT, role TEXT, points REAL DEFAULT 0)''')
                        
    cursor.execute('''CREATE TABLE IF NOT EXISTS contests (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        match_id INTEGER, name TEXT, prize_pool INTEGER, entry_fee INTEGER, spots INTEGER)''')
                        
    cursor.execute('''CREATE TABLE IF NOT EXISTS teams (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        match_id INTEGER, user_id INTEGER, team_name TEXT, captain TEXT, vice_captain TEXT, players TEXT)''')

    # Add default user if empty
    cursor.execute("SELECT COUNT(*) FROM users")
    if cursor.fetchone()[0] == 0:
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
    <body class="bg-gray-900 text-white font-sans pb-10">
        <div class="bg-indigo-600 p-4 flex justify-between items-center shadow-md">
            <h1 class="text-xl font-bold">CRICXABHI Fantasy 🏏</h1>
            <div class="flex items-center gap-2">
                <span class="bg-indigo-800 px-3 py-1 rounded-full text-sm font-semibold">🪙 {{ user['coins'] }}</span>
                <a href="/admin" class="bg-green-600 text-xs px-3 py-1.5 rounded font-bold">Admin Panel</a>
            </div>
        </div>
        <div class="max-w-md mx-auto p-4">
            <h2 class="text-lg font-semibold mb-3 text-gray-300">Live & Upcoming Matches</h2>
            {% if not matches %}
            <p class="text-gray-400 text-sm">Koi match nahi hai abhi. Admin panel se match add karein!</p>
            {% endif %}
            {% for match in matches %}
            <div class="bg-gray-800 border border-gray-700 rounded-xl p-4 mb-4 shadow">
                <div class="flex justify-between items-center mb-3">
                    <span class="font-bold text-lg">{{ match['team1'] }} vs {{ match['team2'] }}</span>
                    <span class="text-xs bg-green-500 text-black px-2 py-1 rounded font-bold uppercase">{{ match['status'] }}</span>
                </div>
                <a href="/match/{{ match['id'] }}" class="block text-center bg-indigo-500 hover:bg-indigo-600 text-white font-bold py-2 rounded-lg transition">View Contests & Teams</a>
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
    <body class="bg-gray-900 text-white font-sans pb-10">
        <div class="bg-indigo-600 p-4 flex items-center shadow-md">
            <a href="/" class="mr-3 text-xl font-bold">←</a>
            <h1 class="text-lg font-bold">{{ match['team1'] }} vs {{ match['team2'] }} Contests</h1>
        </div>
        <div class="max-w-md mx-auto p-4">
            {% if not contests %}
            <p class="text-gray-400 text-sm mb-4">Is match ke liye koi contest nahi hai. Admin panel se contest add karein!</p>
            {% endif %}
            {% for contest in contests %}
            <div class="bg-gray-800 border border-gray-700 rounded-xl p-4 mb-4 shadow">
                <div class="flex justify-between font-bold text-gray-200 mb-1">
                    <span>{{ contest['name'] }}</span>
                    <span class="text-green-400">Prize: 🪙 {{ contest['prize_pool'] }}</span>
                </div>
                <div class="text-sm text-gray-400 mb-3">Entry Fee: 🪙 {{ contest['entry_fee'] }} | Spots: {{ contest['spots'] }}</div>
                <a href="/create_team/{{ match['id'] }}/{{ contest['id'] }}" class="block text-center bg-green-600 hover:bg-green-700 text-white font-bold py-2 rounded-lg transition">Create Team & Join</a>
            </div>
            {% endfor %}
        </div>
    </body>
    </html>
    ''', match=match, contests=contests)

@app.route('/create_team/<int:match_id>/<int:contest_id>', methods=['GET', 'POST'])
def create_team(match_id, contest_id):
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    if request.method == 'POST':
        team_name = request.form.get('team_name')
        captain = request.form.get('captain')
        vice_captain = request.form.get('vice_captain')
        selected_players = request.form.getlist('players')
        
        if len(selected_players) != 11:
            return "Error: Aapko exact 11 players select karne honge! <a href='javascript:history.back()'>Go Back</a>"
            
        players_str = ",".join(selected_players)
        cursor.execute("INSERT INTO teams (match_id, user_id, team_name, captain, vice_captain, players) VALUES (?, 1, ?, ?, ?, ?)",
                       (match_id, team_name, captain, vice_captain, players_str))
        conn.commit()
        conn.close()
        return redirect(url_for('index'))
        
    cursor.execute("SELECT * FROM players WHERE match_id = ?", (match_id,))
    players = cursor.fetchall()
    conn.close()
    return render_template_string('''
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Create Team - 11 Players</title>
        <script src="https://cdn.tailwindcss.com"></script>
    </head>
    <body class="bg-gray-900 text-white font-sans pb-12">
        <div class="bg-indigo-600 p-4 sticky top-0 z-10 shadow-md">
            <h1 class="text-lg font-bold">Select 11 Players for your Team</h1>
        </div>
        <div class="max-w-md mx-auto p-4">
            <form method="POST">
                <div class="mb-4">
                    <label class="block text-sm text-gray-400 mb-1">Team Name</label>
                    <input type="text" name="team_name" required placeholder="e.g. CricXabhi XI" class="w-full bg-gray-800 border border-gray-700 rounded p-2 text-white">
                </div>
                
                <h3 class="font-bold text-indigo-400 mb-2">Pick 11 Players (C & VC select karein):</h3>
                {% if not players %}
                <p class="text-yellow-400 text-sm mb-4">⚠️ Is match ke liye abhi tak koi players add nahi kiye gaye hain! Admin panel se players add karein.</p>
                {% endif %}
                <div class="space-y-2 mb-6">
                    {% for p in players %}
                    <label class="flex items-center justify-between bg-gray-800 border border-gray-700 p-3 rounded-lg cursor-pointer">
                        <div class="flex items-center gap-3">
                            <input type="checkbox" name="players" value="{{ p['name'] }}" class="w-5 h-5 accent-indigo-500">
                            <div>
                                <span class="font-semibold block">{{ p['name'] }}</span>
                                <span class="text-xs text-gray-400">{{ p['team'] }} - {{ p['role'] }}</span>
                            </div>
                        </div>
                        <div class="flex gap-2 text-xs">
                            <label><input type="radio" name="captain" value="{{ p['name'] }}" required> C</label>
                            <label><input type="radio" name="vice_captain" value="{{ p['name'] }}" required> VC</label>
                        </div>
                    </label>
                    {% endfor %}
                </div>
                
                <button type="submit" class="w-full bg-green-600 hover:bg-green-700 font-bold py-3 rounded-xl transition sticky bottom-4 shadow-lg">Save Team & Join Contest</button>
            </form>
            <div class="mt-4 text-center">
                <a href="/" class="text-indigo-400 text-sm">← Back to Home</a>
            </div>
        </div>
    </body>
    </html>
    ''', players=players)

@app.route('/admin', methods=['GET', 'POST'])
def admin_panel():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    msg = ""
    if request.method == 'POST':
        action = request.form.get('action')
        
        if action == 'add_match':
            t1 = request.form.get('team1')
            t2 = request.form.get('team2')
            cursor.execute("INSERT INTO matches (team1, team2, status) VALUES (?, ?, 'Upcoming')", (t1, t2))
            conn.commit()
            msg = "New match successfully added!"
            
        elif action == 'add_player':
            match_id = request.form.get('match_id')
            p_name = request.form.get('player_name')
            p_team = request.form.get('player_team')
            p_role = request.form.get('player_role')
            cursor.execute("INSERT INTO players (match_id, name, team, role) VALUES (?, ?, ?, ?)", (match_id, p_name, p_team, p_role))
            conn.commit()
            msg = "Player successfully added to match!"
            
        elif action == 'add_contest':
            match_id = request.form.get('match_id')
            c_name = request.form.get('contest_name')
            prize = request.form.get('prize_pool')
            fee = request.form.get('entry_fee')
            spots = request.form.get('spots')
            cursor.execute("INSERT INTO contests (match_id, name, prize_pool, entry_fee, spots) VALUES (?, ?, ?, ?, ?)", (match_id, c_name, prize, fee, spots))
            conn.commit()
            msg = "Contest successfully added!"
            
        elif action == 'add_coins':
            user_id = request.form.get('user_id')
            coins = request.form.get('coins')
            cursor.execute("UPDATE users SET coins = coins + ? WHERE id = ?", (coins, user_id))
            conn.commit()
            msg = "Coins successfully added to user!"
            
    cursor.execute("SELECT * FROM matches")
    matches = cursor.fetchall()
    cursor.execute("SELECT * FROM users")
    users = cursor.fetchall()
    conn.close()
    
    return render_template_string('''
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Admin Control Panel</title>
        <script src="https://cdn.tailwindcss.com"></script>
    </head>
    <body class="bg-gray-900 text-white font-sans p-4 pb-16">
        <div class="max-w-md mx-auto">
            <div class="flex justify-between items-center mb-6">
                <h1 class="text-xl font-bold text-green-400">👑 Admin Control Center</h1>
                <a href="/" class="text-indigo-400 text-sm font-semibold">Home</a>
            </div>
            
            {% if msg %}
            <div class="bg-green-800 p-3 rounded-lg mb-4 text-sm font-semibold shadow">{{ msg }}</div>
            {% endif %}
            
            <!-- 1. Add Match -->
            <div class="bg-gray-800 p-4 rounded-xl border border-gray-700 mb-6 shadow">
                <h2 class="font-bold mb-3 text-indigo-300">1. Add New Match</h2>
                <form method="POST">
                    <input type="hidden" name="action" value="add_match">
                    <input type="text" name="team1" placeholder="Team 1 Code (e.g. RCB)" required class="w-full bg-gray-900 border border-gray-700 rounded p-2 mb-2 text-white text-sm">
                    <input type="text" name="team2" placeholder="Team 2 Code (e.g. MI)" required class="w-full bg-gray-900 border border-gray-700 rounded p-2 mb-3 text-white text-sm">
                    <button type="submit" class="w-full bg-indigo-600 hover:bg-indigo-700 py-2 rounded font-bold text-sm">Create Match</button>
                </form>
            </div>
            
            <!-- 2. Add Player to Match -->
            <div class="bg-gray-800 p-4 rounded-xl border border-gray-700 mb-6 shadow">
                <h2 class="font-bold mb-3 text-indigo-300">2. Add Player to Match</h2>
                <form method="POST">
                    <input type="hidden" name="action" value="add_player">
                    <select name="match_id" required class="w-full bg-gray-900 border border-gray-700 rounded p-2 mb-2 text-white text-sm">
                        <option value="">Select Match</option>
                        {% for m in matches %}
                        <option value="{{ m['id'] }}">{{ m['team1'] }} vs {{ m['team2'] }} (ID: {{ m['id'] }})</option>
                        {% endfor %}
                    </select>
                    <input type="text" name="player_name" placeholder="Player Name (e.g. Virat Kohli)" required class="w-full bg-gray-900 border border-gray-700 rounded p-2 mb-2 text-white text-sm">
                    <input type="text" name="player_team" placeholder="Team Name (e.g. RCB)" required class="w-full bg-gray-900 border border-gray-700 rounded p-2 mb-2 text-white text-sm">
                    <select name="player_role" class="w-full bg-gray-900 border border-gray-700 rounded p-2 mb-3 text-white text-sm">
                        <option value="Batsman">Batsman</option>
                        <option value="Bowler">Bowler</option>
                        <option value="All-Rounder">All-Rounder</option>
                        <option value="WK">Wicketkeeper</option>
                    </select>
                    <button type="submit" class="w-full bg-green-600 hover:bg-green-700 py-2 rounded font-bold text-sm">Add Player</button>
                </form>
            </div>
            
            <!-- 3. Add Contest -->
            <div class="bg-gray-800 p-4 rounded-xl border border-gray-700 mb-6 shadow">
                <h2 class="font-bold mb-3 text-indigo-300">3. Add Contest to Match</h2>
                <form method="POST">
                    <input type="hidden" name="action" value="add_contest">
                    <select name="match_id" required class="w-full bg-gray-900 border border-gray-700 rounded p-2 mb-2 text-white text-sm">
                        <option value="">Select Match</option>
                        {% for m in matches %}
                        <option value="{{ m['id'] }}">{{ m['team1'] }} vs {{ m['team2'] }} (ID: {{ m['id'] }})</option>
                        {% endfor %}
                    </select>
                    <input type="text" name="contest_name" placeholder="Contest Name (e.g. Mega Grand League)" required class="w-full bg-gray-900 border border-gray-700 rounded p-2 mb-2 text-white text-sm">
                    <input type="number" name="prize_pool" placeholder="Prize Pool (e.g. 10000)" required class="w-full bg-gray-900 border border-gray-700 rounded p-2 mb-2 text-white text-sm">
                    <input type="number" name="entry_fee" placeholder="Entry Fee (e.g. 49)" required class="w-full bg-gray-900 border border-gray-700 rounded p-2 mb-2 text-white text-sm">
                    <input type="number" name="spots" placeholder="Total Spots (e.g. 100)" required class="w-full bg-gray-900 border border-gray-700 rounded p-2 mb-3 text-white text-sm">
                    <button type="submit" class="w-full bg-indigo-600 hover:bg-indigo-700 py-2 rounded font-bold text-sm">Create Contest</button>
                </form>
            </div>
            
            <!-- 4. Manage Coins -->
            <div class="bg-gray-800 p-4 rounded-xl border border-gray-700 shadow">
                <h2 class="font-bold mb-3 text-indigo-300">4. Give Coins to User</h2>
                <form method="POST">
                    <input type="hidden" name="action" value="add_coins">
                    <input type="hidden" name="user_id" value="1">
                    <input type="number" name="coins" placeholder="Enter coins (e.g. 5000)" required class="w-full bg-gray-900 border border-gray-700 rounded p-2 mb-3 text-white text-sm">
                    <button type="submit" class="w-full bg-purple-600 hover:bg-purple-700 py-2 rounded font-bold text-sm">Add Coins</button>
                </form>
            </div>
        </div>
    </body>
    </html>
    ''', matches=matches, users=users, msg=msg)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
    
