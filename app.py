 from flask import Flask, render_template_string, request, redirect, url_for, session
import sqlite3
import os

app = Flask(__name__)
app.secret_key = 'cricxabhi_clean_secret'
DB_NAME = 'fantasy_web.db'

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT UNIQUE, coins INTEGER DEFAULT 1000)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS matches (id INTEGER PRIMARY KEY AUTOINCREMENT, team1 TEXT, team2 TEXT, match_time TEXT, status TEXT DEFAULT 'Upcoming')''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS players (id INTEGER PRIMARY KEY AUTOINCREMENT, match_id INTEGER, name TEXT, team TEXT, role TEXT, points REAL DEFAULT 0)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS contests (id INTEGER PRIMARY KEY AUTOINCREMENT, match_id INTEGER, name TEXT, prize_pool INTEGER, entry_fee INTEGER, spots INTEGER)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS teams (id INTEGER PRIMARY KEY AUTOINCREMENT, match_id INTEGER, user_id INTEGER, team_name TEXT, captain TEXT, vice_captain TEXT, players TEXT)''')

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
    <head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>CRICXABHI Fantasy</title><script src="https://cdn.tailwindcss.com"></script></head>
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
            {% for match in matches %}
            <div class="bg-gray-800 border border-gray-700 rounded-xl p-4 mb-4 shadow">
                <div class="flex justify-between items-center mb-2">
                    <span class="font-bold text-lg">{{ match['team1'] }} vs {{ match['team2'] }}</span>
                    <span class="text-xs {% if match['status'] == 'Completed' %}bg-red-500{% elif match['status'] == 'Live' %}bg-yellow-500 text-black animate-pulse{% else %}bg-green-500 text-black{% endif %} px-2 py-1 rounded font-bold uppercase">{{ match['status'] }}</span>
                </div>
                <div class="text-xs text-gray-400 mb-3">🕒 Time: {{ match['match_time'] }}</div>
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
    cursor.execute("SELECT * FROM teams WHERE match_id = ? AND user_id = ?", (match_id, session['user_id']))
    my_teams = cursor.fetchall()
    all_teams = []
    if match['status'] in ['Live', 'Completed']:
        cursor.execute("SELECT teams.*, users.username FROM teams JOIN users ON teams.user_id = users.id WHERE teams.match_id = ?", (match_id,))
        all_teams = cursor.fetchall()
    conn.close()
    return render_template_string('''
    <!DOCTYPE html>
    <html lang="en">
    <head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>Contests</title><script src="https://cdn.tailwindcss.com"></script></head>
    <body class="bg-gray-900 text-white font-sans pb-10">
        <div class="bg-indigo-600 p-4 flex items-center shadow-md">
            <a href="/" class="mr-3 text-xl font-bold">←</a>
            <h1 class="text-lg font-bold">{{ match['team1'] }} vs {{ match['team2'] }}</h1>
        </div>
        <div class="max-w-md mx-auto p-4">
            <div class="bg-gray-800 border border-indigo-500 rounded-xl p-4 mb-6 shadow">
                <h3 class="font-bold text-indigo-300 mb-2">My Created Teams (🔒 Private)</h3>
                {% for t in my_teams %}
                <div class="bg-gray-900 p-3 rounded-lg mb-2 text-xs border border-gray-700">
                    <div class="font-bold text-sm text-green-400 mb-1">{{ t['team_name'] }}</div>
                    <div class="text-gray-300 mb-1">⭐ C: {{ t['captain'] }} | 🌟 VC: {{ t['vice_captain'] }}</div>
                    <div class="text-gray-400">Players: {{ t['players'] }}</div>
                </div>
                {% endfor %}
            </div>
            {% if match['status'] in ['Live', 'Completed'] %}
            <div class="bg-gray-800 border border-yellow-500 rounded-xl p-4 mb-6 shadow">
                <h3 class="font-bold text-yellow-400 mb-2">📢 All Users Teams (🔓 Public Live)</h3>
                {% for t in all_teams %}
                <div class="bg-gray-900 p-3 rounded-lg mb-2 text-xs border border-gray-700">
                    <div class="flex justify-between font-bold text-sm text-indigo-300 mb-1"><span>{{ t['team_name'] }}</span><span class="text-gray-400">By: {{ t['username'] }}</span></div>
                    <div class="text-gray-300 mb-1">⭐ C: {{ t['captain'] }} | 🌟 VC: {{ t['vice_captain'] }}</div>
                    <div class="text-gray-400">Players: {{ t['players'] }}</div>
                </div>
                {% endfor %}
            </div>
            {% endif %}
            <h2 class="text-md font-semibold mb-3 text-gray-300">Contests</h2>
            {% for contest in contests %}
            <div class="bg-gray-800 border border-gray-700 rounded-xl p-4 mb-4 shadow">
                <div class="flex justify-between font-bold text-gray-200 mb-1"><span>{{ contest['name'] }}</span><span class="text-green-400">🪙 {{ contest['prize_pool'] }}</span></div>
                <div class="text-sm text-gray-400 mb-3">Fee: 🪙 {{ contest['entry_fee'] }} | Spots: {{ contest['spots'] }}</div>
                <a href="/create_team/{{ match['id'] }}/{{ contest['id'] }}" class="block text-center bg-green-600 hover:bg-green-700 text-white font-bold py-2 rounded-lg transition">Create Team & Join</a>
            </div>
            {% endfor %}
        </div>
    </body>
    </html>
    ''', match=match, contests=contests, my_teams=my_teams, all_teams=all_teams)

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
            return "Error: Exact 11 players select karein! <a href='javascript:history.back()'>Go Back</a>"
        cursor.execute("INSERT INTO teams (match_id, user_id, team_name, captain, vice_captain, players) VALUES (?, ?, ?, ?, ?, ?)",
                       (match_id, session['user_id'], team_name, captain, vice_captain, ",".join(selected_players)))
        conn.commit()
        conn.close()
        return redirect(url_for('match_detail', match_id=match_id))
    cursor.execute("SELECT * FROM players WHERE match_id = ?", (match_id,))
    players = cursor.fetchall()
    conn.close()
    return render_template_string('''
    <!DOCTYPE html>
    <html lang="en">
    <head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>Create Team</title><script src="https://cdn.tailwindcss.com"></script></head>
    <body class="bg-gray-900 text-white font-sans pb-12">
        <div class="bg-indigo-600 p-4 sticky top-0 z-10 shadow-md"><h1 class="text-lg font-bold">Select 11 Players</h1></div>
        <div class="max-w-md mx-auto p-4">
            <form method="POST">
                <div class="mb-4"><label class="block text-sm text-gray-400 mb-1">Team Name</label><input type="text" name="team_name" required placeholder="CricXabhi XI" class="w-full bg-gray-800 border border-gray-700 rounded p-2 text-white"></div>
                <h3 class="font-bold text-indigo-400 mb-2">Pick 11 Players (C & VC):</h3>
                <div class="space-y-2 mb-6">
                    {% for p in players %}
                    <label class="flex items-center justify-between bg-gray-800 border border-gray-700 p-3 rounded-lg cursor-pointer">
                        <div class="flex items-center gap-3">
                            <input type="checkbox" name="players" value="{{ p['name'] }}" class="w-5 h-5 accent-indigo-500">
                            <div><span class="font-semibold block">{{ p['name'] }}</span><span class="text-xs text-gray-400">{{ p['team'] }} - {{ p['role'] }}</span></div>
                        </div>
                        <div class="flex gap-2 text-xs">
                            <label><input type="radio" name="captain" value="{{ p['name'] }}" required> C</label>
                            <label><input type="radio" name="vice_captain" value="{{ p['name'] }}" required> VC</label>
                        </div>
                    </label>
                    {% endfor %}
                </div>
                <button type="submit" class="w-full bg-green-600 font-bold py-3 rounded-xl sticky bottom-4 shadow-lg">Save Team & Join</button>
            </form>
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
            cursor.execute("INSERT INTO matches (team1, team2, match_time, status) VALUES (?, ?, ?, 'Upcoming')", (request.form.get('team1'), request.form.get('team2'), request.form.get('match_time')))
            conn.commit()
            msg = "Match added!"
        elif action == 'update_match_status':
            cursor.execute("UPDATE matches SET status = ? WHERE id = ?", (request.form.get('status'), request.form.get('match_id')))
            conn.commit()
            msg = "Status updated!"
        elif action == 'add_player':
            cursor.execute("INSERT INTO players (match_id, name, team, role) VALUES (?, ?, ?, ?)", (request.form.get('match_id'), request.form.get('player_name'), request.form.get('player_team'), request.form.get('player_role')))
            conn.commit()
            msg = "Player added!"
        elif action == 'update_points':
            cursor.execute("UPDATE players SET points = ? WHERE id = ?", (request.form.get('points'), request.form.get('player_id')))
            conn.commit()
            msg = "Points updated!"
        elif action == 'add_contest':
            cursor.execute("INSERT INTO contests (match_id, name, prize_pool, entry_fee, spots) VALUES (?, ?, ?, ?, ?)", (request.form.get('match_id'), request.form.get('contest_name'), request.form.get('prize_pool'), request.form.get('entry_fee'), request.form.get('spots')))
            conn.commit()
            msg = "Contest added!"
        elif action == 'add_coins':
            cursor.execute("UPDATE users SET coins = coins + ? WHERE id = ?", (request.form.get('coins'), request.form.get('user_id')))
            conn.commit()
            msg = "Coins added!"
    cursor.execute("SELECT * FROM matches")
    matches = cursor.fetchall()
    cursor.execute("SELECT * FROM players")
    players = cursor.fetchall()
    cursor.execute("SELECT * FROM users")
    users = cursor.fetchall()
    conn.close()
    return render_template_string('''
    <!DOCTYPE html>
    <html lang="en">
    <head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>Admin Panel</title><script src="https://cdn.tailwindcss.com"></script></head>
    <body class="bg-gray-900 text-white font-sans p-4 pb-16">
        <div class="max-w-md mx-auto">
            <div class="flex justify-between items-center mb-6"><h1 class="text-xl font-bold text-green-400">👑 Admin Panel</h1><a href="/" class="text-indigo-400 text-sm">Home</a></div>
            {% if msg %}<div class="bg-green-800 p-3 rounded mb-4 text-sm font-semibold">{{ msg }}</div>{% endif %}
            <div class="bg-gray-800 p-4 rounded-xl border border-gray-700 mb-6">
                <h2 class="font-bold mb-3 text-indigo-300">1. Add Match</h2>
                <form method="POST"><input type="hidden" name="action" value="add_match">
                    <input type="text" name="team1" placeholder="Team 1 (e.g. IND)" required class="w-full bg-gray-900 border border-gray-700 rounded p-2 mb-2 text-sm">
                    <input type="text" name="team2" placeholder="Team 2 (e.g. AUS)" required class="w-full bg-gray-900 border border-gray-700 rounded p-2 mb-2 text-sm">
                    <input type="text" name="match_time" placeholder="Time (e.g. 7:30 PM)" required class="w-full bg-gray-900 border border-gray-700 rounded p-2 mb-3 text-sm">
                    <button type="submit" class="w-full bg-indigo-600 py-2 rounded font-bold text-sm">Create Match</button>
                </form>
            </div>
            <div class="bg-gray-800 p-4 rounded-xl border border-gray-700 mb-6">
                <h2 class="font-bold mb-3 text-indigo-300">2. Match Status</h2>
                <form method="POST"><input type="hidden" name="action" value="update_match_status">
                    <select name="match_id" required class="w-full bg-gray-900 border border-gray-700 rounded p-2 mb-2 text-sm"><option value="">Select Match</option>{% for m in matches %}<option value="{{ m['id'] }}">{{ m['team1'] }} vs {{ m['team2'] }} ({{ m['status'] }})</option>{% endfor %}</select>
                    <select name="status" class="w-full bg-gray-900 border border-gray-700 rounded p-2 mb-3 text-sm"><option value="Upcoming">Upcoming</option><option value="Live">Live</option><option value="Completed">Completed</option></select>
                    <button type="submit" class="w-full bg-yellow-600 py-2 rounded font-bold text-sm text-black">Update Status</button>
                </form>
            </div>
            <div class="bg-gray-800 p-4 rounded-xl border border-gray-700 mb-6">
                <h2 class="font-bold mb-3 text-indigo-300">3. Add Player</h2>
                <form method="POST"><input type="hidden" name="action" value="add_player">
                    <select name="match_id" required class="w-full bg-gray-900 border border-gray-700 rounded p-2 mb-2 text-sm"><option value="">Select Match</option>{% for m in matches %}<option value="{{ m['id'] }}">{{ m['team1'] }} vs {{ m['team2'] }}</option>{% endfor %}</select>
                    <input type="text" name="player_name" placeholder="Player Name" required class="w-full bg-gray-900 border border-gray-700 rounded p-2 mb-2 text-sm">
                    <input type="text" name="player_team" placeholder="Team (e.g. IND)" required class="w-full bg-gray-900 border border-gray-700 rounded p-2 mb-2 text-sm">
                    <select name="player_role" class="w-full bg-gray-900 border border-gray-700 rounded p-2 mb-3 text-sm"><option value="Batsman">Batsman</option><option value="Bowler">Bowler</option><option value="All-Rounder">All-Rounder</option><option value="WK">Wicketkeeper</option></select>
                    <button type="submit" class="w-full bg-green-600 py-2 rounded font-bold text-sm">Add Player</button>
                </form>
            </div>
            <div class="bg-gray-800 p-4 rounded-xl border border-gray-700 mb-6">
                <h2 class="font-bold mb-3 text-indigo-300">4. Update Points</h2>
                <form method="POST"><input type="hidden" name="action" value="update_points">
                    <select name="player_id" required class="w-full bg-gray-900 border border-gray-700 rounded p-2 mb-2 text-sm"><option value="">Select Player</option>{% for p in players %}<option value="{{ p['id'] }}">{{ p['name'] }} ({{ p['team'] }})</option>{% endfor %}</select>
                    <input type="number" step="0.5" name="points" placeholder="Points" required class="w-full bg-gray-900 border border-gray-700 rounded p-2 mb-3 text-sm">
                    <button type="submit" class="w-full bg-blue-600 py-2 rounded font-bold text-sm">Update Points</button>
                </form>
            </div>
            <div class="bg-gray-800 p-4 rounded-xl border border-gray-700 mb-6">
                <h2 class="font-bold mb-3 text-indigo-300">5. Add Contest</h2>
                <form method="POST"><input type="hidden" name="action" value="add_contest">
                    <select name="match_id" required class="w-full bg-gray-900 border border-gray-700 rounded p-2 mb-2 text-sm"><option value="">Select Match</option>{% for m in matches %}<option value="{{ m['id'] }}">{{ m['team1'] }} vs {{ m['team2'] }}</option>{% endfor %}</select>
                    <input type="text" name="contest_name" placeholder="Contest Name" required class="w-full bg-gray-900 border border-gray-700 rounded p-2 mb-2 text-sm">
                    <input type="number" name="prize_pool" placeholder="Prize Pool" required class="w-full bg-gray-900 border border-gray-700 rounded p-2 mb-2 text-sm">
                    <input type="number" name="entry_fee" placeholder="Entry Fee" required class="w-full bg-gray-900 border border-gray-700 rounded p-2 mb-2 text-sm">
                    <input type="number" name="spots" placeholder="Spots" required class="w-full bg-gray-900 border border-gray-700 rounded p-2 mb-3 text-sm">
                    <button type="submit" class="w-full bg-indigo-600 py-2 rounded font-bold text-sm">Create Contest</button>
                </form>
            </div>
            <div class="bg-gray-800 p-4 rounded-xl border border-gray-700">
                <h2 class="font-bold mb-3 text-indigo-300">6. Give Coins</h2>
                <form method="POST"><input type="hidden" name="action" value="add_coins"><input type="hidden" name="user_id" value="1">
                    <input type="number" name="coins" placeholder="Coins" required class="w-full bg-gray-900 border border-gray-700 rounded p-2 mb-3 text-sm">
                    <button type="submit" class="w-full bg-purple-600 py-2 rounded font-bold text-sm">Add Coins</button>
                </form>
            </div>
        </div>
    </body>
    </html>
    ''', matches=matches, players=players, users=users, msg=msg)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
    
