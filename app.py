from flask import Flask, render_template_string, request, redirect, url_for, session
import sqlite3

app = Flask(__name__)
app.secret_key = 'cricxabhi_key'
DB_NAME = 'fantasy_web.db'

def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT, coins INTEGER DEFAULT 1000)')
    c.execute('CREATE TABLE IF NOT EXISTS matches (id INTEGER PRIMARY KEY AUTOINCREMENT, team1 TEXT, team2 TEXT, match_time TEXT, status TEXT DEFAULT "Upcoming")')
    c.execute('CREATE TABLE IF NOT EXISTS players (id INTEGER PRIMARY KEY AUTOINCREMENT, match_id INTEGER, name TEXT, team TEXT, role TEXT, points REAL DEFAULT 0)')
    c.execute('CREATE TABLE IF NOT EXISTS contests (id INTEGER PRIMARY KEY AUTOINCREMENT, match_id INTEGER, name TEXT, prize_pool INTEGER, entry_fee INTEGER, spots INTEGER)')
    c.execute('CREATE TABLE IF NOT EXISTS teams (id INTEGER PRIMARY KEY AUTOINCREMENT, match_id INTEGER, user_id INTEGER, team_name TEXT, captain TEXT, vice_captain TEXT, players TEXT)')
    c.execute('SELECT COUNT(*) FROM users')
    if c.fetchone()[0] == 0:
        c.execute('INSERT INTO users (username, coins) VALUES ("AbhiAdmin", 5000)')
    conn.commit()
    conn.close()

init_db()

@app.route('/')
def index():
    if 'user_id' not in session: session['user_id'] = 1
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    user = c.execute('SELECT * FROM users WHERE id = ?', (session['user_id'],)).fetchone()
    matches = c.execute('SELECT * FROM matches').fetchall()
    conn.close()
    return render_template_string('''
    <!DOCTYPE html>
    <html>
    <head><title>CRICXABHI Fantasy</title><script src="https://cdn.tailwindcss.com"></script></head>
    <body class="bg-gray-900 text-white p-4">
        <div class="flex justify-between items-center bg-indigo-600 p-4 rounded-xl mb-4">
            <h1 class="font-bold">CRICXABHI Fantasy 🏏</h1>
            <div class="flex gap-2"><span class="bg-indigo-900 px-3 py-1 rounded">🪙 {{user.coins}}</span><a href="/admin" class="bg-green-600 px-3 py-1 rounded font-bold">Admin</a></div>
        </div>
        <h2 class="text-lg font-semibold mb-2">Matches</h2>
        {% for m in matches %}
        <div class="bg-gray-800 p-4 rounded-xl mb-3 border border-gray-700">
            <div class="flex justify-between font-bold text-lg mb-1"><span>{{m.team1}} vs {{m.team2}}</span><span class="text-xs bg-green-500 text-black px-2 py-1 rounded">{{m.status}}</span></div>
            <p class="text-xs text-gray-400 mb-3">Time: {{m.match_time}}</p>
            <a href="/match/{{m.id}}" class="block text-center bg-indigo-500 py-2 rounded font-bold">Open Match</a>
        </div>
        {% endfor %}
    </body>
    </html>
    ''', user=user, matches=matches)

@app.route('/match/<int:match_id>')
def match_detail(match_id):
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    match = c.execute('SELECT * FROM matches WHERE id = ?', (match_id,)).fetchone()
    contests = c.execute('SELECT * FROM contests WHERE match_id = ?', (match_id,)).fetchall()
    my_teams = c.execute('SELECT * FROM teams WHERE match_id = ? AND user_id = ?', (match_id, session.get('user_id', 1))).fetchall()
    all_teams = []
    if match['status'] in ['Live', 'Completed']:
        all_teams = c.execute('SELECT teams.*, users.username FROM teams JOIN users ON teams.user_id = users.id WHERE teams.match_id = ?', (match_id,)).fetchall()
    conn.close()
    return render_template_string('''
    <!DOCTYPE html>
    <html>
    <head><title>Match</title><script src="https://cdn.tailwindcss.com"></script></head>
    <body class="bg-gray-900 text-white p-4">
        <a href="/" class="text-indigo-400 font-bold">← Back</a>
        <h1 class="text-xl font-bold my-3">{{match.team1}} vs {{match.team2}}</h1>
        <div class="bg-gray-800 p-4 rounded-xl mb-4 border border-indigo-500">
            <h3 class="font-bold text-indigo-300 mb-2">My Teams (🔒 Private)</h3>
            {% for t in my_teams %}
            <div class="bg-gray-900 p-2 rounded mb-2 text-xs"><b>{{t.team_name}}</b> | C: {{t.captain}} | VC: {{t.vice_captain}}<br>Players: {{t.players}}</div>
            {% endfor %}
        </div>
        {% if match.status in ['Live', 'Completed'] %}
        <div class="bg-gray-800 p-4 rounded-xl mb-4 border border-yellow-500">
            <h3 class="font-bold text-yellow-400 mb-2">All Users Teams (🔓 Public)</h3>
            {% for t in all_teams %}
            <div class="bg-gray-900 p-2 rounded mb-2 text-xs"><b>{{t.team_name}}</b> (By: {{t.username}})<br>C: {{t.captain}} | VC: {{t.vice_captain}}<br>{{t.players}}</div>
            {% endfor %}
        </div>
        {% endif %}
        <h3 class="font-semibold mb-2">Contests</h3>
        {% for con in contests %}
        <div class="bg-gray-800 p-3 rounded-xl mb-3 border border-gray-700">
            <div class="flex justify-between font-bold"><span>{{con.name}}</span><span class="text-green-450 text-green-400">🪙 {{con.prize_pool}}</span></div>
            <p class="text-xs text-gray-400 mb-2">Fee: 🪙 {{con.entry_fee}}</p>
            <a href="/create_team/{{match.id}}/{{con.id}}" class="block text-center bg-green-600 py-1.5 rounded font-bold text-sm">Join Contest</a>
        </div>
        {% endfor %}
    </body>
    </html>
    ''', match=match, contests=contests, my_teams=my_teams, all_teams=all_teams)

@app.route('/create_team/<int:match_id>/<int:contest_id>', methods=['GET', 'POST'])
def create_team(match_id, contest_id):
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    if request.method == 'POST':
        team_name = request.form.get('team_name')
        captain = request.form.get('captain')
        vice_captain = request.form.get('vice_captain')
        players = request.form.getlist('players')
        if len(players) != 11: return "Select exactly 11 players! <a href='javascript:history.back()'>Back</a>"
        c.execute('INSERT INTO teams (match_id, user_id, team_name, captain, vice_captain, players) VALUES (?, ?, ?, ?, ?, ?)',
                  (match_id, session.get('user_id', 1), team_name, captain, vice_captain, ",".join(players)))
        conn.commit()
        conn.close()
        return redirect(url_for('match_detail', match_id=match_id))
    players = c.execute('SELECT * FROM players WHERE match_id = ?', (match_id,)).fetchall()
    conn.close()
    return render_template_string('''
    <!DOCTYPE html>
    <html>
    <head><title>Create Team</title><script src="https://cdn.tailwindcss.com"></script></head>
    <body class="bg-gray-900 text-white p-4">
        <h1 class="text-lg font-bold mb-3">Create Team (Pick 11)</h1>
        <form method="POST">
            <input type="text" name="team_name" placeholder="Team Name" required class="w-full bg-gray-800 p-2 rounded mb-4 text-white border border-gray-700">
            {% for p in players %}
            <label class="flex justify-between items-center bg-gray-800 p-2 rounded mb-2 border border-gray-700 text-xs">
                <div class="flex items-center gap-2"><input type="checkbox" name="players" value="{{p.name}}"> {{p.name}} ({{p.team}} - {{p.role}})</div>
                <div class="flex gap-2"><label><input type="radio" name="captain" value="{{p.name}}" required> C</label><label><input type="radio" name="vice_captain" value="{{p.name}}" required> VC</label></div>
            </label>
            {% endfor %}
            <button type="submit" class="w-full bg-green-600 py-3 rounded font-bold mt-4">Save Team</button>
        </form>
    </body>
    </html>
    ''', players=players)

@app.route('/admin', methods=['GET', 'POST'])
def admin():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    msg = ""
    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'match':
            c.execute('INSERT INTO matches (team1, team2, match_time, status) VALUES (?, ?, ?, "Upcoming")', (request.form.get('t1'), request.form.get('t2'), request.form.get('time')))
            msg = "Match added!"
        elif action == 'status':
            c.execute('UPDATE matches SET status = ? WHERE id = ?', (request.form.get('status'), request.form.get('match_id')))
            msg = "Status updated!"
        elif action == 'player':
            c.execute('INSERT INTO players (match_id, name, team, role) VALUES (?, ?, ?, ?)', (request.form.get('match_id'), request.form.get('p_name'), request.form.get('p_team'), request.form.get('p_role')))
            msg = "Player added!"
        elif action == 'coins':
            c.execute('UPDATE users SET coins = coins + ? WHERE id = 1', (request.form.get('coins'),))
            msg = "Coins added!"
        elif action == 'contest':
            c.execute('INSERT INTO contests (match_id, name, prize_pool, entry_fee, spots) VALUES (?, ?, ?, ?, ?)', (request.form.get('match_id'), request.form.get('c_name'), request.form.get('prize'), request.form.get('fee'), request.form.get('spots')))
            msg = "Contest added!"
        conn.commit()
    matches = c.execute('SELECT * FROM matches').fetchall()
    conn.close()
    return render_template_string('''
    <!DOCTYPE html>
    <html>
    <head><title>Admin</title><script src="https://cdn.tailwindcss.com"></script></head>
    <body class="bg-gray-900 text-white p-4">
        <div class="flex justify-between mb-4"><h1 class="text-xl font-bold text-green-400">Admin Panel</h1><a href="/" class="text-indigo-400">Home</a></div>
        {% if msg %}<div class="bg-green-800 p-2 rounded mb-3 text-sm">{{msg}}</div>{% endif %}
        <form method="POST" class="bg-gray-800 p-3 rounded mb-4"><input type="hidden" name="action" value="match">
            <h3 class="font-bold mb-2">1. Add Match</h3>
            <input type="text" name="t1" placeholder="Team 1" required class="w-full bg-gray-900 p-2 rounded mb-2 text-sm"><input type="text" name="t2" placeholder="Team 2" required class="w-full bg-gray-900 p-2 rounded mb-2 text-sm"><input type="text" name="time" placeholder="Time" required class="w-full bg-gray-900 p-2 rounded mb-2 text-sm">
            <button class="w-full bg-indigo-600 py-2 rounded font-bold text-sm">Add Match</button>
        </form>
        <form method="POST" class="bg-gray-800 p-3 rounded mb-4"><input type="hidden" name="action" value="status">
            <h3 class="font-bold mb-2">2. Match Status</h3>
            <select name="match_id" class="w-full bg-gray-900 p-2 rounded mb-2 text-sm">{% for m in matches %}<option value="{{m.id}}">{{m.team1}} vs {{m.team2}} ({{m.status}})</option>{% endfor %}</select>
            <select name="status" class="w-full bg-gray-900 p-2 rounded mb-2 text-sm"><option value="Upcoming">Upcoming</option><option value="Live">Live</option><option value="Completed">Completed</option></select>
            <button class="w-full bg-yellow-600 py-2 rounded font-bold text-sm text-black">Update Status</button>
        </form>
        <form method="POST" class="bg-gray-800 p-3 rounded mb-4"><input type="hidden" name="action" value="player">
            <h3 class="font-bold mb-2">3. Add Player</h3>
            <select name="match_id" class="w-full bg-gray-900 p-2 rounded mb-2 text-sm">{% for m in matches %}<option value="{{m.id}}">{{m.team1}} vs {{m.team2}}</option>{% endfor %}</select>
            <input type="text" name="p_name" placeholder="Name" required class="w-full bg-gray-900 p-2 rounded mb-2 text-sm"><input type="text" name="p_team" placeholder="Team" required class="w-full bg-gray-900 p-2 rounded mb-2 text-sm">
            <select name="p_role" class="w-full bg-gray-900 p-2 rounded mb-2 text-sm"><option value="Batsman">Batsman</option><option value="Bowler">Bowler</option><option value="All-Rounder">All-Rounder</option><option value="WK">WK</option></select>
            <button class="w-full bg-green-600 py-2 rounded font-bold text-sm">Add Player</button>
        </form>
        <form method="POST" class="bg-gray-800 p-3 rounded mb-4"><input type="hidden" name="action" value="contest">
            <h3 class="font-bold mb-2">4. Add Contest</h3>
            <select name="match_id" class="w-full bg-gray-900 p-2 rounded mb-2 text-sm">{% for m in matches %}<option value="{{m.id}}">{{m.team1}} vs {{m.team2}}</option>{% endfor %}</select>
            <input type="text" name="c_name" placeholder="Name" required class="w-full bg-gray-900 p-2 rounded mb-2 text-sm"><input type="number" name="prize" placeholder="Prize" required class="w-full bg-gray-900 p-2 rounded mb-2 text-sm"><input type="number" name="fee" placeholder="Fee" required class="w-full bg-gray-900 p-2 rounded mb-2 text-sm"><input type="number" name="spots" placeholder="Spots" required class="w-full bg-gray-900 p-2 rounded mb-2 text-sm">
            <button class="w-full bg-indigo-600 py-2 rounded font-bold text-sm">Add Contest</button>
        </form>
        <form method="POST" class="bg-gray-800 p-3 rounded"><input type="hidden" name="action" value="coins">
            <h3 class="font-bold mb-2">5. Give Coins</h3>
            <input type="number" name="coins" placeholder="Coins" required class="w-full bg-gray-900 p-2 rounded mb-2 text-sm">
            <button class="w-full bg-purple-600 py-2 rounded font-bold text-sm">Add Coins</button>
        </form>
    </body>
    </html>
    ''', matches=matches, msg=msg)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
          
