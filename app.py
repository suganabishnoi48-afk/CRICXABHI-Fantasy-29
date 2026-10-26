from flask import Flask, render_template_string, request, redirect, url_for, session
import sqlite3
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'cricxabhi_final_perfect_2026'
DB_NAME = 'fantasy_master.db'

def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT UNIQUE, password TEXT, coins INTEGER DEFAULT 0)')
    c.execute('CREATE TABLE IF NOT EXISTS matches (id INTEGER PRIMARY KEY AUTOINCREMENT, team1 TEXT, team2 TEXT, match_time TEXT, status TEXT DEFAULT "Upcoming")')
    c.execute('CREATE TABLE IF NOT EXISTS players (id INTEGER PRIMARY KEY AUTOINCREMENT, match_id INTEGER, name TEXT, team TEXT, role TEXT, points REAL DEFAULT 0)')
    c.execute('CREATE TABLE IF NOT EXISTS contests (id INTEGER PRIMARY KEY AUTOINCREMENT, match_id INTEGER, name TEXT, prize_pool INTEGER, entry_fee INTEGER, spots INTEGER, prize_breakup TEXT)')
    c.execute('CREATE TABLE IF NOT EXISTS teams (id INTEGER PRIMARY KEY AUTOINCREMENT, match_id INTEGER, user_id INTEGER, team_name TEXT, captain TEXT, vice_captain TEXT, players TEXT, total_points REAL DEFAULT 0)')
    c.execute('CREATE TABLE IF NOT EXISTS contest_participants (id INTEGER PRIMARY KEY AUTOINCREMENT, contest_id INTEGER, user_id INTEGER, team_id INTEGER, rank INTEGER, winnings INTEGER DEFAULT 0)')
    
    c.execute('SELECT COUNT(*) FROM users WHERE username = "AbhiAdmin"')
    if c.fetchone()[0] == 0:
        c.execute('INSERT INTO users (username, password, coins) VALUES ("AbhiAdmin", "29022008", 100000)')
    conn.commit()
    conn.close()

init_db()

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/')
def index():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    user = c.execute('SELECT * FROM users WHERE id = ?', (session['user_id'],)).fetchone()
    if not user:
        session.clear()
        conn.close()
        return redirect(url_for('login'))
        
    matches = c.execute('SELECT * FROM matches').fetchall()
    conn.close()
    
    return render_template_string('''<!DOCTYPE html>
<html lang="hi">
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>CRICXABHI Fantasy</title><script src="https://cdn.tailwindcss.com"></script></head>
<body class="bg-gray-950 text-white font-sans p-4 pb-20">
    <div class="bg-indigo-600 p-4 rounded-2xl flex justify-between items-center shadow-lg mb-4">
        <div><h1 class="font-bold text-base">CRICXABHI Fantasy 🏏</h1><p class="text-xs text-indigo-200">Hi, <b>{{user.username}}</b></p></div>
        <div class="flex gap-2 items-center">
            <span class="bg-indigo-900 px-3 py-1 rounded-full text-xs font-bold">🪙 {{user.coins}}</span>
            <a href="/wallet" class="bg-amber-500 text-black px-2.5 py-1 rounded-xl font-bold text-xs">Share Coin</a>
            <a href="/logout" class="bg-rose-600 px-2.5 py-1 rounded-xl font-bold text-xs">Logout</a>
        </div>
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
                const x = setInterval(function() {
                    const now = new Date().getTime();
                    const dist = matchTime - now;
                    if (dist < 0) {
                        clearInterval(x);
                        timerElem.innerHTML = "🔴 Match Started / Live";
                    } else {
                        const d = Math.floor(dist / (1000 * 60 * 60 * 24));
                        const h = Math.floor((dist % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
                        const mi = Math.floor((dist % (1000 * 60 * 60)) / (1000 * 60));
                        const s = Math.floor((dist % (1000 * 60)) / 1000);
                        timerElem.innerHTML = "⏳ Starts in: " + d + "d " + h + "h " + mi + "m " + s + "s";
                    }
                }, 1000);
            })();
        </script>
        <a href="/match/{{m.id}}" class="block text-center bg-indigo-600 py-2.5 rounded-xl font-bold text-xs shadow">View Contests & Teams</a>
    </div>
    {% endfor %}
</body>
</html>''', user=user, matches=matches)

@app.route('/login', methods=['GET', 'POST'])
def login():
    error = ""
    if request.method == 'POST':
        login_type = request.form.get('login_type')
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        
        if login_type == 'admin':
            if username == 'AbhiAdmin' and password == '29022008':
                session['is_admin'] = True
                conn.close()
                return redirect(url_for('admin'))
            else:
                error = "❌ Invalid Admin Credentials!"
        else:
            user = c.execute('SELECT * FROM users WHERE username = ? AND password = ?', (username, password)).fetchone()
            if user:
                session['user_id'] = user[0]
                session['username'] = user[1]
                conn.close()
                return redirect(url_for('index'))
            else:
                error = "❌ Invalid Username or Password!"
        conn.close()
        
    return render_template_string('''<!DOCTYPE html>
<html lang="hi">
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>Login - CRICXABHI Fantasy</title><script src="https://cdn.tailwindcss.com"></script></head>
<body class="bg-gray-950 text-white font-sans p-6 flex items-center justify-center h-screen">
    <div class="bg-gray-900 border border-gray-800 p-6 rounded-2xl max-w-sm w-full shadow-2xl">
        <h2 class="text-base font-bold text-indigo-400 mb-4 text-center">🏏 CRICXABHI Login</h2>
        {% if error %}<div class="bg-rose-900 text-rose-200 p-2.5 rounded-xl mb-3 text-xs font-bold text-center">{{error}}</div>{% endif %}
        <form method="POST" class="space-y-3">
            <div>
                <label class="text-xs text-gray-400 block mb-1">Select Login Type</label>
                <select name="login_type" id="loginType" onchange="toggleAdmin()" class="w-full bg-gray-800 border border-gray-700 p-2.5 rounded-xl text-xs text-white">
                    <option value="user">User ID Login</option>
                    <option value="admin">Admin ID Login</option>
                </select>
            </div>
            <div>
                <label class="text-xs text-gray-400 block mb-1" id="labelName">Username</label>
                <input type="text" name="username" placeholder="Enter username..." required class="w-full bg-gray-800 border border-gray-700 p-2.5 rounded-xl text-xs text-white">
            </div>
            <div>
                <label class="text-xs text-gray-400 block mb-1">Password</label>
                <input type="password" name="password" placeholder="Enter password..." required class="w-full bg-gray-800 border border-gray-700 p-2.5 rounded-xl text-xs text-white">
            </div>
            <button type="submit" class="w-full bg-indigo-600 py-3 rounded-xl font-bold text-xs shadow">Login</button>
        </form>
        <div class="text-center mt-4 text-xs text-gray-400">Don't have an account? <a href="/register" class="text-emerald-400 font-bold">Register here</a></div>
    </div>
    <script>
        function toggleAdmin() {
            let val = document.getElementById('loginType').value;
            let lbl = document.getElementById('labelName');
            if(val === 'admin') { lbl.innerText = "Admin ID (AbhiAdmin)"; }
            else { lbl.innerText = "Username"; }
        }
    </script>
</body>
</html>''', error=error)

@app.route('/register', methods=['GET', 'POST'])
def register():
    error = ""
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        if username and password:
            conn = sqlite3.connect(DB_NAME)
            c = conn.cursor()
            try:
                c.execute('INSERT INTO users (username, password, coins) VALUES (?, ?, 0)', (username, password))
                conn.commit()
                conn.close()
                return redirect(url_for('login'))
            except sqlite3.IntegrityError:
                error = "❌ Username already exists! Choose another."
            conn.close()
    return render_template_string('''<!DOCTYPE html>
<html lang="hi">
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>Register</title><script src="https://cdn.tailwindcss.com"></script></head>
<body class="bg-gray-950 text-white font-sans p-6 flex items-center justify-center h-screen">
    <div class="bg-gray-900 border border-gray-800 p-6 rounded-2xl max-w-sm w-full shadow-2xl">
        <h2 class="text-base font-bold text-emerald-400 mb-2 text-center">📝 New User Registration</h2>
        <p class="text-[11px] text-gray-400 mb-4 text-center">Signup bonus: <b>0 Coins</b></p>
        {% if error %}<div class="bg-rose-900 text-rose-200 p-2.5 rounded-xl mb-3 text-xs font-bold text-center">{{error}}</div>{% endif %}
        <form method="POST" class="space-y-3">
            <input type="text" name="username" placeholder="Choose unique username..." required class="w-full bg-gray-800 border border-gray-700 p-2.5 rounded-xl text-xs text-white">
            <input type="password" name="password" placeholder="Create secure password..." required class="w-full bg-gray-800 border border-gray-700 p-2.5 rounded-xl text-xs text-white">
            <button type="submit" class="w-full bg-emerald-600 py-3 rounded-xl font-bold text-xs shadow">Register Now</button>
        </form>
        <div class="text-center mt-4 text-xs text-gray-400">Already registered? <a href="/login" class="text-indigo-400 font-bold">Login here</a></div>
    </div>
</body>
</html>''', error=error)

@app.route('/wallet', methods=['GET', 'POST'])
def wallet():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    user = c.execute('SELECT * FROM users WHERE id = ?', (session['user_id'],)).fetchone()
    msg = ""
    if request.method == 'POST':
        target_name = request.form.get('target_username', '').strip()
        amt = int(request.form.get('amount', 0))
        if amt > 0 and user['coins'] >= amt:
            target_user = c.execute('SELECT * FROM users WHERE username = ?', (target_name,)).fetchone()
            if target_user and target_user['id'] != user['id']:
                c.execute('UPDATE users SET coins = coins - ? WHERE id = ?', (amt, user['id']))
                c.execute('UPDATE users SET coins = coins + ? WHERE id = ?', (amt, target_user['id']))
                conn.commit()
                msg = f"Successfully sent {amt} coins to {target_name}!"
            else:
                msg = "❌ Target user not found or invalid!"
        else:
            msg = "❌ Insufficient coins or invalid amount!"
    user = c.execute('SELECT * FROM users WHERE id = ?', (session['user_id'],)).fetchone()
    conn.close()
    return render_template_string('''<!DOCTYPE html>
<html lang="hi">
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>Share Coin</title><script src="https://cdn.tailwindcss.com"></script></head>
<body class="bg-gray-950 text-white font-sans p-4 pb-20">
    <div class="bg-indigo-600 p-3 rounded-xl flex items-center mb-4 shadow"><a href="/" class="mr-3 font-bold bg-indigo-700 px-2.5 py-1 rounded-lg text-xs">←</a><h1 class="text-sm font-bold">🪙 Share Coin (To Users or Admin)</h1></div>
    <div class="bg-gray-900 border border-gray-800 p-4 rounded-2xl mb-4">
        <p class="text-xs text-gray-300 mb-2">My Balance: <b>🪙 {{user.coins}} coins</b></p>
        {% if msg %}<div class="bg-indigo-950 text-indigo-200 p-2.5 rounded-xl mb-3 text-xs font-bold">{{msg}}</div>{% endif %}
        <form method="POST" class="space-y-3">
            <input type="text" name="target_username" placeholder="Recipient Username (e.g. AbhiAdmin or user)..." required class="w-full bg-gray-800 border border-gray-700 p-2.5 rounded-xl text-xs text-white">
            <input type="number" name="amount" placeholder="Coin Amount..." min="1" required class="w-full bg-gray-800 border border-gray-700 p-2.5 rounded-xl text-xs text-white">
            <button type="submit" class="w-full bg-emerald-600 py-3 rounded-xl font-bold text-xs shadow">Transfer Coins</button>
        </form>
    </div>
</body>
</html>''', user=user, msg=msg)

@app.route('/match/<int:match_id>')
def match_detail(match_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    user = c.execute('SELECT * FROM users WHERE id = ?', (session['user_id'],)).fetchone()
    match = c.execute('SELECT * FROM matches WHERE id = ?', (match_id,)).fetchone()
    contests = c.execute('SELECT * FROM contests WHERE match_id = ?', (match_id,)).fetchall()
    my_teams = c.execute('SELECT * FROM teams WHERE match_id = ? AND user_id = ?', (match_id, user['id'])).fetchall()
    
    contest_data = []
    for con in contests:
        participants = c.execute('SELECT users.username, teams.team_name, contest_participants.rank, contest_participants.winnings FROM contest_participants JOIN users ON contest_participants.user_id = users.id JOIN teams ON contest_participants.team_id = teams.id WHERE contest_participants.contest_id = ? ORDER BY contest_participants.rank ASC', (con['id'],)).fetchall()
        contest_data.append({'contest': con, 'participants': participants})

    all_teams = []
    if match['status'] in ['Live', 'Completed']:
        all_teams = c.execute('SELECT teams.*, users.username FROM teams JOIN users ON teams.user_id = users.id WHERE teams.match_id = ? ORDER BY teams.total_points DESC', (match_id,)).fetchall()
    conn.close()
    
    return render_template_string('''<!DOCTYPE html>
<html lang="hi">
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>Match Detail</title><script src="https://cdn.tailwindcss.com"></script></head>
<body class="bg-gray-950 text-white font-sans p-4 pb-20">
    <div class="bg-indigo-600 p-3 rounded-xl flex items-center mb-4 shadow"><a href="/" class="mr-3 font-bold bg-indigo-700 px-2.5 py-1 rounded-lg text-xs">←</a><h1 class="text-sm font-bold">{{match.team1}} vs {{match.team2}}</h1></div>
    
    <div class="bg-gray-900 border border-indigo-500 p-3 rounded-2xl mb-4">
        <h3 class="font-bold text-indigo-300 text-xs mb-2">🔒 My Created Teams</h3>
        {% if not my_teams %}<p class="text-[11px] text-gray-400 mb-2">Pehle apni team banayein!</p>{% endif %}
        {% for t in my_teams %}
        <div class="bg-gray-800 p-2.5 rounded-xl mb-2 text-xs border border-gray-700">
            <div class="flex justify-between font-bold text-emerald-400 mb-1"><span>{{t.team_name}}</span><span>Score: {{t.total_points}} pts</span></div>
            <div class="text-gray-300 text-[11px] mb-1">⭐ C: <b>{{t.captain}} (2x)</b> | 🌟 VC: <b>{{t.vice_captain}} (1.5x)</b></div>
            <div class="text-gray-400 text-[10px] mb-2">Players: {{t.players}}</div>
            {% if match.status == 'Upcoming' %}
            <a href="/create_team/{{match.id}}?edit={{t.id}}" class="bg-amber-500 text-black font-bold px-2.5 py-1 rounded text-[10px]">✏️ Edit Lineup</a>
            {% endif %}
        </div>
        {% endfor %}
        {% if match.status == 'Upcoming' %}
        <a href="/create_team/{{match.id}}" class="block text-center bg-indigo-600 py-2 rounded-xl font-bold text-xs mt-2">+ Create New Team</a>
        {% endif %}
    </div>

    {% if match.status in ['Live', 'Completed'] %}
    <div class="bg-gray-900 border border-amber-500 p-3 rounded-2xl mb-4">
        <h3 class="font-bold text-amber-400 text-xs mb-2">🔓 All Users Public Leaderboard & Teams</h3>
        {% for t in all_teams %}
        <div class="bg-gray-800 p-2.5 rounded-xl mb-2 text-xs border border-gray-700">
            <div class="flex justify-between font-bold mb-1"><span class="text-indigo-300">{{t.team_name}} ({{t.username}})</span><span class="text-amber-400">⚡ {{t.total_points}} Pts</span></div>
            <div class="text-gray-300 text-[11px] mb-1">⭐ C: {{t.captain}} | 🌟 VC: {{t.vice_captain}}</div>
            <div class="text-gray-400 text-[10px]">Players: {{t.players}}</div>
        </div>
        {% endfor %}
    </div>
    {% endif %}

    <h3 class="text-xs font-bold mb-2 text-gray-300">Contests & Prize Breakup</h3>
    {% for item in contest_data %}
    <div class="bg-gray-900 border border-gray-800 p-3 rounded-2xl mb-3">
        <div class="flex justify-between font-bold text-xs mb-1"><span>{{item.contest.name}}</span><span class="text-emerald-400">🪙 Prize: {{item.contest.prize_pool}}</span></div>
        <p class="text-[10px] text-gray-400 mb-1">Entry Fee: 🪙 {{item.contest.entry_fee}} | Spots: {{item.participants|length}}/{{item.contest.spots}}</p>
        <p class="text-[10px] text-amber-300 mb-2">🎁 Prize Breakup: {{item.contest.prize_breakup}}</p>
        
        <div class="bg-gray-950 p-2 rounded-xl mb-2 text-[11px]">
            <span class="text-indigo-400 font-bold">Joined Users & Winnings:</span>
            <ul class="list-disc pl-4 mt-1 text-gray-300">
                {% for p in item.participants %}
                <li><b>{{p.username}}</b> (Team: {{p.team_name}}) {% if p.rank %}➔ Rank: <b>#{{p.rank}}</b> | Won: 🪙 <b>{{p.winnings}}</b>{% endif %}</li>
                {% endfor %}
            </ul>
        </div>

        {% if item.participants|length >= item.contest.spots %}
        <div class="text-center bg-rose-900 text-rose-200 py-1.5 rounded font-bold text-xs">Contest Full ❌</div>
        {% else %}
        <form action="/join_contest/{{item.contest.id}}" method="POST" class="flex gap-2">
            <select name="team_id" required class="bg-gray-800 p-1.5 rounded text-xs w-full text-white border border-gray-700">
                <option value="">Apni Team Select Karein</option>
                {% for t in my_teams %}
                <option value="{{t.id}}">{{t.team_name}}</option>
                {% endfor %}
            </select>
            <button type="submit" class="bg-emerald-600 px-4 py-1.5 rounded font-bold text-xs shrink-0">Join (🪙 {{item.contest.entry_fee}})</button>
        </form>
        {% endif %}
    </div>
    {% endfor %}
</body>
</html>''', match=match, contest_data=contest_data, my_teams=my_teams, all_teams=all_teams, user=user)

@app.route('/create_team/<int:match_id>', methods=['GET', 'POST'])
def create_team(match_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    match = c.execute('SELECT * FROM matches WHERE id = ?', (match_id,)).fetchone()
    if match['status'] != 'Upcoming':
        conn.close()
        return "Error: Match shuru hone ke baad team create ya edit nahi ki ja sakti! <a href='/'>Go Home</a>"
        
    user_id = session['user_id']
    edit_id = request.args.get('edit')
    existing_team = None
    if edit_id:
        existing_team = c.execute('SELECT * FROM teams WHERE id = ? AND user_id = ?', (edit_id, user_id)).fetchone()

    if request.method == 'POST':
        t_name = request.form.get('team_name')
        capt = request.form.get('captain')
        v_capt = request.form.get('vice_captain')
        plrs = request.form.getlist('players')
        if len(plrs) != 11:
            conn.close()
            return "Error: Exact 11 players select karne honge! <a href='javascript:history.back()'>Go Back</a>"
        p_str = ",".join(plrs)
        if edit_id and existing_team:
            c.execute('UPDATE teams SET team_name = ?, captain = ?, vice_captain = ?, players = ? WHERE id = ?', (t_name, capt, v_capt, p_str, edit_id))
        else:
            c.execute('INSERT INTO teams (match_id, user_id, team_name, captain, vice_captain, players) VALUES (?, ?, ?, ?, ?, ?)', (match_id, user_id, t_name, capt, v_capt, p_str))
        conn.commit()
        conn.close()
        return redirect(url_for('match_detail', match_id=match_id))
        
    players = c.execute('SELECT * FROM players WHERE match_id = ?', (match_id,)).fetchall()
    conn.close()
    
    return render_template_string('''<!DOCTYPE html>
<html lang="hi">
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>Create Team</title><script src="https://cdn.tailwindcss.com"></script></head>
<body class="bg-gray-950 text-white font-sans p-4 pb-20">
    <div class="bg-indigo-600 p-3 rounded-xl mb-4"><h1 class="text-sm font-bold">Select Exact 11 Players & C/VC</h1></div>
    <form method="POST">
        <div class="mb-3"><input type="text" name="team_name" value="{% if existing_team %}{{existing_team.team_name}}{% endif %}" placeholder="Team Name" required class="w-full bg-gray-900 border border-gray-700 p-2.5 rounded-xl text-xs text-white"></div>
        <div class="space-y-2 mb-4">
            {% for p in players %}
            <label class="flex justify-between items-center bg-gray-900 border border-gray-800 p-2.5 rounded-xl text-xs">
                <div class="flex items-center gap-2">
                    <input type="checkbox" name="players" value="{{p.name}}" {% if existing_team and p.name in existing_team.players %}checked{% endif %} class="accent-indigo-500">
                    <div><span class="font-bold">{{p.name}}</span><span class="text-[10px] text-gray-400 block">{{p.team}} • {{p.role}}</span></div>
                </div>
                <div class="flex gap-2 text-[11px]">
                    <label><input type="radio" name="captain" value="{{p.name}}" {% if existing_team and existing_team.captain == p.name %}checked{% endif %} required> C (2x)</label>
                    <label><input type="radio" name="vice_captain" value="{{p.name}}" {% if existing_team and existing_team.vice_captain == p.name %}checked{% endif %} required> VC (1.5x)</label>
                </div>
            </label>
            {% endfor %}
        </div>
        <button class="w-full bg-emerald-600 py-3 rounded-xl font-bold text-xs shadow">Save Team</button>
    </form>
</body>
</html>''', players=players, existing_team=existing_team)

@app.route('/join_contest/<int:contest_id>', methods=['POST'])
def join_contest(contest_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    user_id = session['user_id']
    team_id = request.form.get('team_id')
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    contest = c.execute('SELECT * FROM contests WHERE id = ?', (contest_id,)).fetchone()
    user = c.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()
    
    joined_already = c.execute('SELECT * FROM contest_participants WHERE contest_id = ? AND user_id = ?', (contest_id, user_id)).fetchone()
    if joined_already:
        conn.close()
        return "Error: Aap is contest mein pehle hi join kar chuke hain! (Limit: 1 entry per user) <a href='javascript:history.back()'>Go Back</a>"
        
    participants_count = c.execute('SELECT COUNT(*) FROM contest_participants WHERE contest_id = ?', (contest_id,)).fetchone()[0]
    if participants_count >= contest['spots']:
        conn.close()
        return "Error: Contest Full ❌ <a href='javascript:history.back()'>Go Back</a>"
        
    if user['coins'] < contest['entry_fee']:
        conn.close()
        return "Error: Not enough coins! <a href='javascript:history.back()'>Go Back</a>"
        
    # Instant coin deduction on joining
    c.execute('UPDATE users SET coins = coins - ? WHERE id = ?', (contest['entry_fee'], user_id))
    c.execute('INSERT INTO contest_participants (contest_id, user_id, team_id) VALUES (?, ?, ?)', (contest_id, user_id, team_id))
    conn.commit()
    match_id = contest['match_id']
    conn.close()
    return redirect(url_for('match_detail', match_id=match_id))

@app.route('/admin', methods=['GET', 'POST'])
def admin():
    if not session.get('is_admin'):
        return redirect(url_for('login'))
        
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    
    msg = ""
    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'match':
            c.execute('INSERT INTO matches (team1, team2, match_time, status) VALUES (?, ?, ?, "Upcoming")', (request.form.get('t1'), request.form.get('t2'), request.form.get('time')))
            msg = "Match added successfully!"
        elif action == 'player':
            c.execute('INSERT INTO players (match_id, name, team, role) VALUES (?, ?, ?, ?)', (request.form.get('match_id'), request.form.get('p_name'), request.form.get('p_team'), request.form.get('p_role')))
            msg = "Player added successfully!"
        elif action == 'contest':
            # Prize breakup format e.g. "1-5: 100, 6-29: 50"
            c.execute('INSERT INTO contests (match_id, name, prize_pool, entry_fee, spots, prize_breakup) VALUES (?, ?, ?, ?, ?, ?)', (request.form.get('match_id'), request.form.get('c_name'), request.form.get('prize'), request.form.get('fee'), request.form.get('spots'), request.form.get('breakup')))
            msg = "Contest added successfully!"
        elif action == 'add_coins':
            target_uid = request.form.get('target_user_id')
            add_amt = int(request.form.get('add_amount', 0))
            if add_amt != 0:
                c.execute('UPDATE users SET coins = coins + ? WHERE id = ?', (add_amt, target_uid))
                msg = f"Successfully added {add_amt} coins to user!"
        elif action == 'give_points':
            match_id = request.form.get('match_id')
            p_name = request.form.get('player_name')
            pts = float(request.form.get('points', 0))
            c.execute('UPDATE players SET points = ? WHERE match_id = ? AND name = ?', (pts, match_id, p_name))
            
            teams = c.execute('SELECT * FROM teams WHERE match_id = ?', (match_id,)).fetchall()
            for t in teams:
                plr_list = t['players'].split(',')
                t_pts = 0
                for p in plr_list:
                    p_row = c.execute('SELECT points FROM players WHERE match_id = ? AND name = ?', (match_id, p.strip())).fetchone()
                    p_val = p_row['points'] if p_row else 0
                    if p.strip() == t['captain']:
                        t_val = p_val * 2
                    elif p.strip() == t['vice_captain']:
                        t_val = p_val * 1.5
                    else:
                        t_val = p_val
                    t_pts += t_val
                c.execute('UPDATE teams SET total_points = ? WHERE id = ?', (t_pts, t['id']))
            msg = f"Points updated for {p_name} and all team scores recalculated!"
        elif action == 'update_status':
            match_id = request.form.get('match_id')
            new_status = request.form.get('status')
            c.execute('UPDATE matches SET status = ? WHERE id = ?', (new_status, match_id))
            if new_status == 'Completed':
                contests = c.execute('SELECT * FROM contests WHERE match_id = ?', (match_id,)).fetchall()
                for con in contests:
                    participants = c.execute('SELECT contest_participants.*, teams.total_points FROM contest_participants JOIN teams ON contest_participants.team_id = teams.id WHERE contest_participants.contest_id = ? ORDER BY teams.total_points DESC', (con['id'],)).fetchall()
                    
                    # Parse breakup like "1-5: 200, 6-29: 50"
                    breakup_map = {}
                    parts = con['prize_breakup'].split(',')
                    for part in parts:
                        if ':' in part:
                            rng, amt = part.split(':')
                            amt = int(amt.strip())
                            rng = rng.strip()
                            if '-' in rng:
                                start_r, end_r = map(int, rng.split('-'))
                                for r in range(start_r, end_r + 1):
                                    breakup_map[r] = amt
                            else:
                                breakup_map[int(rng)] = amt

                    for idx, p in enumerate(participants):
                        rank = idx + 1
                        winnings = breakup_map.get(rank, 0)
                        
                        c.execute('UPDATE contest_participants SET rank = ?, winnings = ? WHERE id = ?', (rank, winnings, p['id']))
                        if winnings > 0:
                            c.execute('UPDATE users SET coins = coins + ? WHERE id = ?', (winnings, p['user_id']))
            msg = "Match status updated and winnings automatically distributed!"
        conn.commit()
        
    matches = c.execute('SELECT * FROM matches').fetchall()
    users = c.execute('SELECT * FROM users').fetchall()
    players = c.execute('SELECT * FROM players').fetchall()
    conn.close()
    
    return render_template_string('''<!DOCTYPE html>
<html lang="hi">
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>Admin Panel</title><script src="https://cdn.tailwindcss.com"></script></head>
<body class="bg-gray-950 text-white font-sans p-4 pb-20">
    <div class="flex justify-between items-center mb-4"><h1 class="text-sm font-bold text-emerald-400">👑 Admin Panel</h1><div class="flex gap-2"><a href="/" class="text-indigo-400 text-xs bg-indigo-950 px-3 py-1 rounded-lg">Home</a><a href="/logout" class="text-rose-400 text-xs bg-rose-950 px-3 py-1 rounded-lg">Logout</a></div></div>
    {% if msg %}<div class="bg-emerald-900 text-emerald-200 p-2.5 rounded-xl mb-3 text-xs font-bold">{{msg}}</div>{% endif %}
    
    <div class="bg-gray-900 border border-gray-800 p-3 rounded-2xl mb-4">
        <h3 class="font-bold text-indigo-300 text-xs mb-2">👥 Registered Users & Live Coin Balances</h3>
        <div class="space-y-2 max-h-56 overflow-y-auto text-xs">
            {% for u in users %}
            <div class="flex justify-between items-center bg-gray-800 p-2 rounded">
                <div><b>{{u.username}}</b> <span class="text-amber-400 font-bold ml-2">🪙 {{u.coins}}</span></div>
                <form method="POST" class="flex gap-1">
                    <input type="hidden" name="action" value="add_coins">
                    <input type="hidden" name="target_user_id" value="{{u.id}}">
                    <input type="number" name="add_amount" placeholder="+ Coins" required class="bg-gray-900 border border-gray-700 p-1 rounded text-[10px] w-16 text-white">
                    <button type="submit" class="bg-emerald-600 px-2 py-1 rounded font-bold text-[10px]">+</button>
                </form>
            </div>
            {% endfor %}
        </div>
    </div>

    <form method="POST" class="bg-gray-900 border border-gray-800 p-3 rounded-2xl mb-3"><input type="hidden" name="action" value="match">
        <h3 class="font-bold mb-2 text-indigo-300 text-xs">1. Add Match</h3>
        <input type="text" name="t1" placeholder="Team 1" required class="w-full bg-gray-800 p-2.5 rounded-xl mb-2 text-xs text-white">
        <input type="text" name="t2" placeholder="Team 2" required class="w-full bg-gray-800 p-2.5 rounded-xl mb-2 text-xs text-white">
        <input type="datetime-local" name="time" required class="w-full bg-gray-800 p-2.5 rounded-xl mb-2 text-xs text-white">
        <button class="w-full bg-indigo-600 py-2.5 rounded-xl font-bold text-xs">Add Match</button>
    </form>

    <form method="POST" class="bg-gray-900 border border-gray-800 p-3 rounded-2xl mb-3"><input type="hidden" name="action" value="player">
        <h3 class="font-bold mb-2 text-indigo-300 text-xs">2. Add Player</h3>
        <select name="match_id" class="w-full bg-gray-800 p-2.5 rounded-xl mb-2 text-xs text-white">{% for m in matches %}<option value="{{m.id}}">{{m.team1}} vs {{m.team2}}</option>{% endfor %}</select>
        <input type="text" name="p_name" placeholder="Player Name" required class="w-full bg-gray-800 p-2.5 rounded-xl mb-2 text-xs text-white">
        <input type="text" name="p_team" placeholder="Team Code" required class="w-full bg-gray-800 p-2.5 rounded-xl mb-2 text-xs text-white">
        <select name="p_role" class="w-full bg-gray-800 p-2.5 rounded-xl mb-2 text-xs text-white"><option value="Batsman">Batsman</option><option value="Bowler">Bowler</option><option value="All-Rounder">All-Rounder</option><option value="WK">WK</option></select>
        <button class="w-full bg-emerald-600 py-2.5 rounded-xl font-bold text-xs">Add Player</button>
    </form>

    <form method="POST" class="bg-gray-900 border border-gray-800 p-3 rounded-2xl mb-3"><input type="hidden" name="action" value="contest">
        <h3 class="font-bold mb-2 text-indigo-300 text-xs">3. Create Contest & Serial Prize Breakup</h3>
        <select name="match_id" class="w-full bg-gray-800 p-2.5 rounded-xl mb-2 text-xs text-white">{% for m in matches %}<option value="{{m.id}}">{{m.team1}} vs {{m.team2}}</option>{% endfor %}</select>
        <input type="text" name="c_name" placeholder="Contest Name (e.g. Mega Contest)" required class="w-full bg-gray-800 p-2.5 rounded-xl mb-2 text-xs text-white">
        <input type="number" name="prize" placeholder="Total Prize Pool" required class="w-full bg-gray-800 p-2.5 rounded-xl mb-2 text-xs text-white">
        <input type="number" name="fee" placeholder="Entry Fee" required class="w-full bg-gray-800 p-2.5 rounded-xl mb-2 text-xs text-white">
        <input type="number" name="spots" placeholder="Total Spots" required class="w-full bg-gray-800 p-2.5 rounded-xl mb-2 text-xs text-white">
        <input type="text" name="breakup" placeholder="Breakup e.g. 1-5: 200, 6-29: 50" required class="w-full bg-gray-800 p-2.5 rounded-xl mb-2 text-xs text-white">
        <button class="w-full bg-indigo-600 py-2.5 rounded-xl font-bold text-xs">Create Contest</button>
    </form>

    <form method="POST" class="bg-gray-900 border border-gray-800 p-3 rounded-2xl mb-3"><input type="hidden" name="action" value="give_points">
        <h3 class="font-bold mb-2 text-indigo-300 text-xs">4. Give Points to Players (C=2x, VC=1.5x Auto)</h3>
        <select name="match_id" class="w-full bg-gray-800 p-2.5 rounded-xl mb-2 text-xs text-white">{% for m in matches %}<option value="{{m.id}}">{{m.team1}} vs {{m.team2}}</option>{% endfor %}</select>
        <select name="player_name" class="w-full bg-gray-800 p-2.5 rounded-xl mb-2 text-xs text-white">{% for p in players %}<option value="{{p.name}}">{{p.name}} (Match {{p.match_id}})</option>{% endfor %}</select>
        <input type="number" step="0.5" name="points" placeholder="Points to assign" required class="w-full bg-gray-800 p-2.5 rounded-xl mb-2 text-xs text-white">
        <button class="w-full bg-purple-600 py-2.5 rounded-xl font-bold text-xs">Update Points & Recalculate Teams</button>
    </form>

    <form method="POST" class="bg-gray-900 border border-gray-800 p-3 rounded-2xl"><input type="hidden" name="action" value="update_status">
        <h3 class="font-bold mb-2 text-indigo-300 text-xs">5. Match Status Control & Auto-Payout</h3>
        <select name="match_id" class="w-full bg-gray-800 p-2.5 rounded-xl mb-2 text-xs text-white">{% for m in matches %}<option value="{{m.id}}">{{m.team1}} vs {{m.team2}} (Current: {{m.status}})</option>{% endfor %}</select>
        <select name="status" class="w-full bg-gray-800 p-2.5 rounded-xl mb-2 text-xs text-white"><option value="Upcoming">Upcoming</option><option value="Live">Live</option><option value="Completed">Completed (Auto Payout)</option></select>
        <button class="w-full bg-amber-500 text-black py-2.5 rounded-xl font-bold text-xs">Update Status & Distribute Winnings</button>
    </form>
</body>
</html>''', matches=matches, users=users, players=players, msg=msg)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
