from flask import Flask, render_template_string, request, redirect, url_for, session
import sqlite3

app = Flask(__name__)
app.secret_key = 'cricxabhi_perfect_secret'
DB_NAME = 'fantasy_web.db'

def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT UNIQUE, coins INTEGER DEFAULT 1000)')
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

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        uname = request.form.get('username', '').strip()
        if uname:
            conn = sqlite3.connect(DB_NAME)
            c = conn.cursor()
            user = c.execute('SELECT * FROM users WHERE username = ?', (uname,)).fetchone()
            if user:
                session['user_id'] = user[0]
            else:
                c.execute('INSERT INTO users (username, coins) VALUES (?, 1000)', (uname,))
                conn.commit()
                session['user_id'] = c.lastrowid
            conn.close()
        return redirect(url_for('index'))
    if 'user_id' not in session: session['user_id'] = 1
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    user = c.execute('SELECT * FROM users WHERE id = ?', (session['user_id'],)).fetchone()
    matches = c.execute('SELECT * FROM matches').fetchall()
    conn.close()
    return render_template_string('''
    <!DOCTYPE html>
    <html lang="hi">
    <head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>CRICXABHI Fantasy</title><script src="https://cdn.tailwindcss.com"></script></head>
    <body class="bg-gray-950 text-white font-sans p-4 pb-20">
        <div class="bg-indigo-600 p-4 rounded-2xl flex justify-between items-center shadow-lg mb-4">
            <div><h1 class="font-bold text-base">CRICXABHI Fantasy 🏏</h1><p class="text-xs text-indigo-200">Hi, <b>{{user.username}}</b></p></div>
            <div class="flex gap-2 items-center"><span class="bg-indigo-900 px-3 py-1 rounded-full text-xs font-bold">🪙 {{user.coins}}</span><a href="/admin" class="bg-emerald-500 text-black px-3 py-1 rounded-xl font-bold text-xs">Admin</a></div>
        </div>
        <div class="bg-gray-900 p-4 rounded-2xl mb-4 border border-gray-800">
            <form method="POST" class="flex gap-2"><input type="text" name="username" placeholder="Apna naam daalo..." required class="bg-gray-800 border border-gray-700 p-2.5 rounded-xl text-xs w-full text-white"><button class="bg-indigo-600 px-4 py-2.5 rounded-xl text-xs font-bold">Login</button></form>
        </div>
        <h2 class="text-sm font-bold mb-3 text-gray-300">Upcoming & Live Matches</h2>
        {% for m in matches %}
        <div class="bg-gray-900 border border-gray-800 p-4 rounded-2xl mb-3 shadow">
            <div class="flex justify-between font-bold text-base mb-1"><span>{{m.team1}} vs {{m.team2}}</span><span class="text-xs {% if m.status=='Live' %}bg-amber-400 text-black animate-pulse{% elif m.status=='Completed' %}bg-rose-500 text-white{% else %}bg-emerald-400 text-black{% endif %} px-2.5 py-1 rounded-full uppercase">{{m.status}}</span></div>
            <div class="text-xs text-amber-300 mb-3 font-mono" id="timer-{{m.id}}">🕒 Timer Loading...</div>
            <script>
                (function() {
                    const matchTime = new Date("{{m.match_time}}").getTime();
                    const timerElem = document.getElementById("timer-{{m.id}}");
                    const status = "{{m.status}}";
                    if(status === 'Completed') { timerElem.innerHTML = "🏁 Match Completed"; return; }
                    if(status === 'Live') { timerElem.innerHTML = "🔴 Match is LIVE NOW!"; return; }
                    setInterval(function() {
                        const now = new Date().getTime();
                        const dist = matchTime - now;
                        if (dist < 0) { timerElem.innerHTML = "🔴 Match Started / Live"; }
                        else {
                            const d = Math.floor(dist / (1000 * 60 * 60 * 24));
                            const h = Math.floor((dist % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
                            const m = Math.floor((dist % (1000 * 60 * 60)) / (1000 * 60));
                            const s = Math.floor((dist % (1000 * 60)) / 1000);
                            timerElem.innerHTML = "⏳ Starts in: " + d + "d " + h + "h " + m + "m " + s + "s";
                        }
                    }, 1000);
                })();
            </script>
            <a href="/match/{{m.id}}" class="block text-center bg-indigo-600 py-2.5 rounded-xl font-bold text-xs shadow">Enter Match & Contests</a>
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
    <html lang="hi">
    <head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>Match Detail</title><script src="https://cdn.tailwindcss.com"></script></head>
    <body class="bg-gray-950 text-white font-sans p-4 pb-20">
        <div class="bg-indigo-600 p-3 rounded-xl flex items-center mb-4 shadow"><a href="/" class="mr-3 font-bold bg-indigo-700 px-2.5 py-1 rounded-lg text-xs">←</a><h1 class="text-sm font-bold">{{match.team1}} vs {{match.team2}}</h1></div>
        <div class="bg-gray-900 border border-indigo-500 p-3 rounded-2xl mb-4">
            <h3 class="font-bold text-indigo-300 text-xs mb-2">🔒 My Created Teams</h3>
            {% if not my_teams %}<p class="text-[11px] text-gray-400 mb-2">Abhi tak koi team nahi banayi.</p>{% endif %}
            {% for t in my_teams %}
            <div class="bg-gray-800 p-2.5 rounded-xl mb-2 text-xs border border-gray-700">
                <div class="font-bold text-emerald-400 mb-1">{{t.team_name}}</div>
                <div class="text-gray-300 text-[11px] mb-1">⭐ C: <b>{{t.captain}}</b> | 🌟 VC: <b>{{t.vice_captain}}</b></div>
                <div class="text-gray-400 text-[10px] mb-2">Players: {{t.players}}</div>
                {% if match.status == 'Upcoming' %}
                <a href="/create_team/{{match.id}}/0?edit={{t.id}}" class="bg-amber-500 text-black font-bold px-2.5 py-1 rounded text-[10px]">✏️ Edit Lineup</a>
                {% endif %}
            </div>
            {% endfor %}
        </div>
        {% if match.status in ['Live', 'Completed'] %}
        <div class="bg-gray-900 border border-amber-500 p-3 rounded-2xl mb-4">
            <h3 class="font-bold text-amber-400 text-xs mb-2">🔓 All Users Public Teams</h3>
            {% for t in all_teams %}
            <div class="bg-gray-800 p-2.5 rounded-xl mb-2 text-xs border border-gray-700">
                <div class="flex justify-between font-bold mb-1"><span class="text-indigo-300">{{t.team_name}}</span><span class="text-gray-400 text-[10px]">By: {{t.username}}</span></div>
                <div class="text-gray-300 text-[11px] mb-1">⭐ C: {{t.captain}} | 🌟 VC: {{t.vice_captain}}</div>
                <div class="text-gray-400 text-[10px]">Players: {{t.players}}</div>
            </div>
            {% endfor %}
        </div>
        {% endif %}
        <h3 class="text-xs font-bold mb-2 text-gray-300">Contests</h3>
        {% for con in contests %}
        <div class="bg-gray-900 border border-gray-800 p-3 rounded-2xl mb-2">
            <div class="flex justify-between font-bold text-xs mb-1"><span>{{con.name}}</span><span class="text-emerald-400">🪙 {{con.prize_pool}}</span></div>
            <p class="text-[10px] text-gray-400 mb-2">Fee: 🪙 {{con.entry_fee}} | Spots: {{con.spots}}</p>
            <a href="/create_team/{{match.id}}/{{con.id}}" class="block text-center bg-emerald-600 py-2 rounded-xl font-bold text-xs">Join Contest / Create Team</a>
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
    edit_id = request.args.get('edit')
    existing_team = None
    if edit_id:
        existing_team = c.execute('SELECT * FROM teams WHERE id = ? AND user_id = ?', (edit_id, session.get('user_id', 1))).fetchone()
    if request.method == 'POST':
        t_name = request.form.get('team_name')
        capt = request.form.get('captain')
        v_capt = request.form.get('vice_captain')
        plrs = request.form.getlist('players')
        if len(plrs) != 11: return "Error: Exact 11 players select karne honge! <a href='javascript:history.back()'>Go Back</a>"
        p_str = ",".join(plrs)
        if edit_id and existing_team:
            c.execute('UPDATE teams SET team_name = ?, captain = ?, vice_captain = ?, players = ? WHERE id = ?', (t_name, capt, v_capt, p_str, edit_id))
        else:
            c.execute('INSERT INTO teams (match_id, user_id, team_name, captain, vice_captain, players) VALUES (?, ?, ?, ?, ?, ?)', (match_id, session.get('user_id', 1), t_name, capt, v_capt, p_str))
        conn.commit()
        conn.close()
        return redirect(url_for('match_detail', match_id=match_id))
    players = c.execute('SELECT * FROM players WHERE match_id = ?', (match_id,)).fetchall()
    conn.close()
    return render_template_string('''
    <!DOCTYPE html>
    <html lang="hi">
    <head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>Create Team</title><script src="https://cdn.tailwindcss.com"></script></head>
    <body class="bg-gray-950 text-white font-sans p-4 pb-20">
        <div class="bg-indigo-600 p-3 rounded-xl mb-4"><h1 class="text-sm font-bold">{% if edit_id %}Edit Lineup{% else %}Select 11 Players{% endif %}</h1></div>
        <form method="POST">
            <div class="mb-3"><input type="text" name="team_name" value="{% if existing_team %}{{existing_team.team_name}}{% endif %}" placeholder="Team Name (e.g. CricXabhi XI)" required class="w-full bg-gray-900 border border-gray-700 p-2.5 rounded-xl text-xs text-white"></div>
            <h3 class="text-xs font-bold text-indigo-300 mb-2">Pick 11 Players & Select C/VC:</h3>
            <div class="space-y-2 mb-4">
                {% for p in players %}
                <label class="flex justify-between items-center bg-gray-900 border border-gray-800 p-2.5 rounded-xl text-xs">
                    <div class="flex items-center gap-2"><input type="checkbox" name="players" value="{{p.name}}" {% if existing_team and p.name in existing_team.players %}checked{% endif %} class="accent-indigo-500"><div><span class="font-bold">{{p.name}}</span><span class="text-[10px] text-gray-400 block">{{p.team}} • {{p.role}}</span></div></div>
                    <div class="flex gap-2 text-[11px]"><label><input type="radio" name="captain" value="{{p.name}}" {% if existing_team and existing_team.captain == p.name %}checked{% endif %} required> C</label><label><input type="radio" name="vice_captain" value="{{p.name}}" {% if existing_team and existing_team.vice_captain == p.name %}checked{% endif %} required> VC</label></div>
                </label>
                {% endfor %}
            </div>
            <button class="w-full bg-emerald-600 py-3 rounded-xl font-bold text-xs shadow">{% if edit_id %}Update Lineup{% else %}Save Team & Join{% endif %}</button>
        </form>
    </body>
    </html>
    ''', players=players, existing_team=existing_team, edit_id=edit_id)

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
            c.execute('UPDATE users SET coins = coins + ? WHERE id = ?', (request.form.get('coins'), request.form.get('user_id')))
            msg = "Coins sent successfully!"
        elif action == 'contest':
            c.execute('INSERT INTO contests (match_id, name, prize_pool, entry_fee, spots) VALUES (?, ?, ?, ?, ?)', (request.form.get('match_id'), request.form.get('c_name'), request.form.get('prize'), request.form.get('fee'), request.form.get('spots')))
            msg = "Contest added!"
        conn.commit()
    matches = c.execute('SELECT * FROM matches').fetchall()
    users = c.execute('SELECT * FROM users').fetchall()
    conn.close()
    return render_template_string('''
    <!DOCTYPE html>
    <html lang="hi">
    <head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>Admin Panel</title><script src="https://cdn.tailwindcss.com"></script></head>
    <body class="bg-gray-950 text-white font-sans p-4 pb-20">
        <div class="flex justify-between items-center mb-4"><h1 class="text-sm font-bold text-emerald-400">👑 Admin Panel</h1><a href="/" class="text-indigo-400 text-xs bg-indigo-950 px-3 py-1 rounded-lg">Home</a></div>
        {% if msg %}<div class="bg-emerald-900 text-emerald-200 p-2.5 rounded-xl mb-3 text-xs font-bold">{{msg}}</div>{% endif %}
        <form method="POST" class="bg-gray-900 border border-gray-800 p-3 rounded-2xl mb-3"><input type="hidden" name="action" value="match">
            <h3 class="font-bold mb-2 text-indigo-300 text-xs">1. Add Match & Time</h3>
            <input type="text" name="t1" placeholder="Team 1 (e.g. IND)" required class="w-full bg-gray-800 p-2.5 rounded-xl mb-2 text-xs text-white">
            <input type="text" name="t2" placeholder="Team 2 (e.g. AUS)" required class="w-full bg-gray-800 p-2.5 rounded-xl mb-2 text-xs text-white">
            <input type="datetime-local" name="time" required class="w-full bg-gray-800 p-2.5 rounded-xl mb-2 text-xs text-white">
            <button class="w-full bg-indigo-600 py-2.5 rounded-xl font-bold text-xs">Add Match</button>
        </form>
        <form method="POST" class="bg-gray-900 border border-gray-800 p-3 rounded-2xl mb-3"><input type="hidden" name="action" value="status">
            <h3 class="font-bold mb-2 text-indigo-300 text-xs">2. Match Status</h3>
            <select name="match_id" class="w-full bg-gray-800 p-2.5 rounded-xl mb-2 text-xs text-white">{% for m in matches %}<option value="{{m.id}}">{{m.team1}} vs {{m.team2}} ({{m.status}})</option>{% endfor %}</select>
            <select name="status" class="w-full bg-gray-800 p-2.5 rounded-xl mb-2 text-xs text-white"><option value="Upcoming">Upcoming</option><option value="Live">Live</option><option value="Completed">Completed</option></select>
            <button class="w-full bg-amber-500 text-black py-2.5 rounded-xl font-bold text-xs">Update Status</button>
        </form>
        <form method="POST" class="bg-gray-900 border border-gray-800 p-3 rounded-2xl mb-3"><input type="hidden" name="action" value="player">
            <h3 class="font-bold mb-2 text-indigo-300 text-xs">3. Add Player</h3>
            <select name="match_id" class="w-full bg-gray-800 p-2.5 rounded-xl mb-2 text-xs text-white">{% for m in matches %}<option value="{{m.id}}">{{m.team1}} vs {{m.team2}}</option>{% endfor %}</select>
            <input type="text" name="p_name" placeholder="Player Name" required class="w-full bg-gray-800 p-2.5 rounded-xl mb-2 text-xs text-white">
            <input type="text" name="p_team" placeholder="Team Code" required class="w-full bg-gray-800 p-2.5 rounded-xl mb-2 text-xs text-white">
            <select name="p_role" class="w-full bg-gray-800 p-2.5 rounded-xl mb-2 text-xs text-white"><option value="Batsman">Batsman</option><option value="Bowler">Bowler</option><option value="All-Rounder">All-Rounder</option><option value="WK">WK</option></select>
            <button class="w-full bg-emerald-600 py-2.5 rounded-xl font-bold text-xs">Add Player</button>
        </form>
        <form method="POST" class="bg-gray-900 border border-gray-800 p-3 rounded-2xl mb-3"><input type="hidden" name="action" value="contest">
            <h3 class="font-bold mb-2 text-indigo-300 text-xs">4. Add Contest</h3>
            <select name="match_id" class="w-full bg-gray-800 p-2.5 rounded-xl mb-2 text-xs text-white">{% for m in matches %}<option value="{{m.id}}">{{m.team1}} vs {{m.team2}}</option>{% endfor %}</select>
            <input type="text" name="c_name" placeholder="Contest Name" required class="w-full bg-gray-800 p-2.5 rounded-xl mb-2 text-xs text-white">
            <input type="number" name="prize" placeholder="Prize Pool" required class="w-full bg-gray-800 p-2.5 rounded-xl mb-2 text-xs text-white">
            <input type="number" name="fee" placeholder="Entry Fee" required class="w-full bg-gray-800 p-2.5 rounded-xl mb-2 text-xs text-white">
            <input type="number" name="spots" placeholder="Spots" required class="w-full bg-gray-800 p-2.5 rounded-xl mb-2 text-xs text-white">
            <button class="w-full bg-indigo-600 py-2.5 rounded-xl font-bold text-xs">Create Contest</button>
        </form>
        <form method="POST" class="bg-gray-900 border border-gray-800 p-3 rounded-2xl"><input type="hidden" name="action" value="coins">
            <h3 class="font-bold mb-2 text-indigo-300 text-xs">5. Give Coins</h3>
            <select name="user_id" class="w-full bg-gray-800 p-2.5 rounded-xl mb-2 text-xs text-white">{% for u in users %}<option value="{{u.id}}">{{u.username}} (🪙 {{u.coins}})</option>{% endfor %}</select>
            <input type="number" name="coins" placeholder="Coins amount" required class="w-full bg-gray-800 p-2.5 rounded-xl mb-2 text-xs text-white">
            <button class="w-full bg-purple-600 py-2.5 rounded-xl font-bold text-xs">Send Coins</button>
        </form>
    </body>
    </html>
    ''', matches=matches, users=users, msg=msg)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
