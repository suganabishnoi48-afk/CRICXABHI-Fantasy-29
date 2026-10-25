from flask import Flask, render_template_string, request, redirect, url_for, session
import sqlite3

app = Flask(__name__)
app.secret_key = 'cricxabhi_absolute_final_key_2026'
DB_NAME = 'fantasy_web.db'

def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT UNIQUE, coins INTEGER DEFAULT 0)')
    c.execute('CREATE TABLE IF NOT EXISTS matches (id INTEGER PRIMARY KEY AUTOINCREMENT, team1 TEXT, team2 TEXT, match_time TEXT, status TEXT DEFAULT "Upcoming")')
    c.execute('CREATE TABLE IF NOT EXISTS players (id INTEGER PRIMARY KEY AUTOINCREMENT, match_id INTEGER, name TEXT, team TEXT, role TEXT, points REAL DEFAULT 0)')
    c.execute('CREATE TABLE IF NOT EXISTS contests (id INTEGER PRIMARY KEY AUTOINCREMENT, match_id INTEGER, name TEXT, prize_pool INTEGER, entry_fee INTEGER, spots INTEGER)')
    c.execute('CREATE TABLE IF NOT EXISTS teams (id INTEGER PRIMARY KEY AUTOINCREMENT, match_id INTEGER, user_id INTEGER, team_name TEXT, captain TEXT, vice_captain TEXT, players TEXT)')
    c.execute('CREATE TABLE IF NOT EXISTS contest_participants (id INTEGER PRIMARY KEY AUTOINCREMENT, contest_id INTEGER, user_id INTEGER, team_id INTEGER)')
    
    c.execute('SELECT COUNT(*) FROM users WHERE username = "AbhiAdmin"')
    if c.fetchone()[0] == 0:
        c.execute('INSERT INTO users (username, coins) VALUES ("AbhiAdmin", 100000)')
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
                session['username'] = user[1]
            else:
                c.execute('INSERT INTO users (username, coins) VALUES (?, 0)', (uname,))
                conn.commit()
                session['user_id'] = c.lastrowid
                session['username'] = uname
            conn.close()
        return redirect(url_for('index'))
    
    if 'user_id' not in session:
        session['user_id'] = 1
        session['username'] = 'AbhiAdmin'

    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    user = c.execute('SELECT * FROM users WHERE id = ?', (session['user_id'],)).fetchone()
    if not user:
        session['user_id'] = 1
        user = c.execute('SELECT * FROM users WHERE id = 1').fetchone()
    matches = c.execute('SELECT * FROM matches').fetchall()
    conn.close()
    
    return render_template_string('''
    <!DOCTYPE html>
    <html lang="hi">
    <head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>CRICXABHI Fantasy</title><script src="https://cdn.tailwindcss.com"></script></head>
    <body class="bg-gray-950 text-white font-sans p-4 pb-20">
        <div class="bg-indigo-600 p-4 rounded-2xl flex justify-between items-center shadow-lg mb-4">
            <div><h1 class="font-bold text-base">CRICXABHI Fantasy 🏏</h1><p class="text-xs text-indigo-200">Hi, <b>{{user.username}}</b></p></div>
            <div class="flex gap-2 items-center">
                <span class="bg-indigo-900 px-3 py-1 rounded-full text-xs font-bold">🪙 {{user.coins}}</span>
                <a href="/admin" class="bg-emerald-500 text-black px-3 py-1 rounded-xl font-bold text-xs shadow">Admin</a>
            </div>
        </div>
        <div class="bg-gray-900 p-4 rounded-2xl mb-4 border border-gray-800">
            <h3 class="text-xs font-semibold text-gray-300 mb-2">Login / Switch Account (0 Coins on signup)</h3>
            <form method="POST" class="flex gap-2"><input type="text" name="username" placeholder="Enter unique name..." required class="bg-gray-800 border border-gray-700 p-2.5 rounded-xl text-xs w-full text-white"><button class="bg-indigo-600 px-4 py-2.5 rounded-xl text-xs font-bold">Go</button></form>
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
    </html>
    ''', user=user, matches=matches)

@app.route('/match/<int:match_id>')
def match_detail(match_id):
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    user = c.execute('SELECT * FROM users WHERE id = ?', (session.get('user_id', 1),)).fetchone()
    match = c.execute('SELECT * FROM matches WHERE id = ?', (match_id,)).fetchone()
    contests = c.execute('SELECT * FROM contests WHERE match_id = ?', (match_id,)).fetchall()
    my_teams = c.execute('SELECT * FROM teams WHERE match_id = ? AND user_id = ?', (match_id, user['id'])).fetchall()
    
    contest_data = []
    for con in contests:
        participants = c.execute('SELECT users.username, teams.team_name FROM contest_participants JOIN users ON contest_participants.user_id = users.id JOIN teams ON contest_participants.team_id = teams.id WHERE contest_participants.contest_id = ?', (con['id'],)).fetchall()
        contest_data.append({'contest': con, 'participants': participants})

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
            {% if not my_teams %}<p class="text-[11px] text-gray-400 mb-2">Pehle apni team banayein!</p>{% endif %}
            {% for t in my_teams %}
            <div class="bg-gray-800 p-2.5 rounded-xl mb-2 text-xs border border-gray-700">
                <div class="font-bold text-emerald-400 mb-1">{{t.team_name}}</div>
                <div class="text-gray-300 text-[11px] mb-1">⭐ C: <b>{{t.captain}}</b> | 🌟 VC: <b>{{t.vice_captain}}</b></div>
                <div class="text-gray-400 text-[10px] mb-2">Players: {{t.players}}</div>
                {% if match.status == 'Upcoming' %}
                <a href="/create_team/{{match.id}}?edit={{t.id}}" class="bg-amber-500 text-black font-bold px-2.5 py-1 rounded text-[10px]">✏️ Edit Lineup</a>
                {% endif %}
            </div>
            {% endfor %}
            <a href="/create_team/{{match.id}}" class="block text-center bg-indigo-600 py-2 rounded-xl font-bold text-xs mt-2">+ Create New Team</a>
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

        <h3 class="text-xs font-bold mb-2 text-gray-300">Contests & Joined Participants</h3>
        {% for item in contest_data %}
        <div class="bg-gray-900 border border-gray-800 p-3 rounded-2xl mb-3">
            <div class="flex justify-between font-bold text-xs mb-1"><span>{{item.contest.name}}</span><span class="text-emerald-400">🪙 Prize: {{item.contest.prize_pool}}</span></div>
            <p class="text-[10px] text-gray-400 mb-2">Entry Fee: 🪙 {{item.contest.entry_fee}} | Spots: {{item.participants|length}}/{{item.contest.spots}}</p>
            
            <div class="bg-gray-950 p-2 rounded-xl mb-2 text-[11px]">
                <span class="text-amber-400 font-bold">Joined Users ({{item.participants|length}}):</span>
                {% if not item.participants %}<span class="text-gray-500"> Abhi koi nahi juda.</span>{% endif %}
                <ul class="list-disc pl-4 mt-1 text-gray-300">
                    {% for p in item.participants %}
                    <li><b>{{p.username}}</b> (Team: {{p.team_name}})</li>
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
    </html>
    ''', match=match, contest_data=contest_data, my_teams=my_teams, all_teams=all_teams, user=user)

@app.route('/create_team/<int:match_id>', methods=['GET', 'POST'])
def create_team(match_id):
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    user_id = session.get('user_id', 1)
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
    
    return render_template_string('''
    <!DOCTYPE html>
    <html lang="hi">
    <head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>Create Team</title><script src="https://cdn.tailwindcss.com"></script></head>
    <body class="bg-gray-950 text-white font-sans p-4 pb-20">
        <div class="bg-indigo-600 p-3 rounded-xl mb-4"><h1 class="text-sm font-bold">{% if edit_id %}Edit Lineup{% else %}Select 11 Players{% endif %}</h1></div>
        <form method="POST">
            <div class="mb-3"><input type="text" name="team_name" value="{% if existing_team %}{{existing_team.team_name}}{% endif %}" placeholder="Team Name" required class="w-full bg-gray-900 border border-gray-700 p-2.5 rounded-xl text-xs text-white"></div>
            <h3 class="text-xs font-bold text-indigo-300 mb-2">Pick 11 Players & Select C/VC:</h3>
            <div class="space-y-2 mb-4">
                {% for p in players %}
                <label class="flex justify-between items-center bg-gray-900 border border-gray-800 p-2.5 rounded-xl text-xs">
                    <div class="flex items-center gap-2"><input type="checkbox" name="players" value="{{p.name}}" {% if existing_team and p.name in existing_team.players %}checked{% endif %} class="accent-indigo-500"><div><span class="font-bold">{{p.name}}</span><span class="text-[10px] text-gray-400 block">{{p.team}} • {{p.role}}</span></div></div>
                    <div class="flex gap-2 text-[11px]"><label><input type="radio" name="captain" value="{{p.name}}" {% if existing_team and existing_team.captain == p.name %}checked{% endif %} required> C</label><label><input type="radio" name="vice_captain" value="{{p.name}}" {% if existing_team and existing_team.vice_captain == p.name %}checked{% endif %} required> VC</label></div>
                </label>
                {% endfor %}
            </div>
            <button class="w-full bg-emerald-600 py-3 rounded-xl font-bold text-xs shadow">{% if edit_id %}Update Lineup{% else %}Save Team{% endif %}</button>
        </form>
    </body>
    </html>
    ''', players=players, existing_team=existing_team, edit_id=edit_id)

@app.route('/join_contest/<int:contest_id>', methods=['POST'])
def join_contest(contest_id):
    user_id = session.get('user_id', 1)
    team_id = request.form.get('team_id')
    if not team_id:
        return "Team select karna zaroori hai! <a href='javascript:history.back()'>Go Back</a>"
    
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    contest = c.execute('SELECT * FROM contests WHERE id = ?', (contest_id,)).fetchone()
    user = c.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()
    
    participants_count = c.execute('SELECT COUNT(*) FROM contest_participants WHERE contest_id = ?', (contest_id,)).fetchone()[0]
    if participants_count >= contest['spots']:
        conn.close()
        return "Error: Yeh contest full ho chuka hai! Ab aur entries allowed nahi hain. <a href='javascript:history.back()'>Go Back</a>"

    if user['coins'] < contest['entry_fee']: 
        conn.close()
        return "Aapke paas contest join karne ke liye sufficient coins nahi hain! <a href='javascript:history.back()'>Go Back</a>"
    
    joined = c.execute('SELECT * FROM contest_participants WHERE contest_id = ? AND user_id = ?', (contest_id, user_id)).fetchone()
    if joined:
        conn.close()
        return "Aap is contest mein pehle hi join kar chuke hain! <a href='javascript:history.back()'>Go Back</a>"
    
    c.execute('UPDATE users SET coins = coins - ? WHERE id = ?', (contest['entry_fee'], user_id))
    c.execute('INSERT INTO contest_participants (contest_id, user_id, team_id) VALUES (?, ?, ?)', (contest_id, user_id, team_id))
    conn.commit()
    match_id = contest['match_id']
    conn.close()
    return redirect(url_for('match_detail', match_id=match_id))

@app.route('/admin', methods=['GET', 'POST'])
def admin():
    if request.method == 'POST':
        pass_input = request.form.get('admin_pass')
        if pass_input == '29022008':
            session['is_admin'] = True
            return redirect(url_for('admin'))
        elif pass_input is not None:
            return render_template_string('''
            <!DOCTYPE html>
            <html>
            <head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>Admin Login</title><script src="https://cdn.tailwindcss.com"></script></head>
            <body class="bg-gray-950 text-white font-sans p-6 flex items-center justify-center h-screen">
                <div class="bg-gray-900 border border-gray-800 p-6 rounded-2xl max-w-sm w-full shadow-2xl text-center">
                    <h2 class="text-base font-bold text-rose-400 mb-2">❌ Wrong Password!</h2>
                    <p class="text-xs text-gray-400 mb-4">Sahi password darj karein.</p>
                    <a href="/admin" class="inline-block bg-indigo-600 px-4 py-2 rounded-xl text-xs font-bold">Try Again</a>
                </div>
            </body>
            </html>
            ''')
    
    if not session.get('is_admin'):
        return render_template_string('''
        <!DOCTYPE html>
        <html>
        <head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>Admin Login</title><script src="https://cdn.tailwindcss.com"></script></head>
        <body class="bg-gray-950 text-white font-sans p-6 flex items-center justify-center h-screen">
            <div class="bg-gray-900 border border-gray-800 p-6 rounded-2xl max-w-sm w-full shadow-2xl">
                <h2 class="text-base font-bold text-emerald-400 mb-4 text-center">🔐 Admin Password Required</h2>
                <form method="POST">
                    <input type="password" name="admin_pass" placeholder="Enter Password..." required class="w-full bg-gray-800 border border-gray-700 p-3 rounded-xl mb-4 text-xs text-white focus:outline-none">
                    <button type="submit" class="w-full bg-emerald-600 py-3 rounded-xl font-bold text-xs shadow">Login to Admin</button>
         
