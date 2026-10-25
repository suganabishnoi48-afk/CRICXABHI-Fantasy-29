from flask import Flask, render_template_string, request, redirect, url_for, session
import sqlite3

app = Flask(__name__)
app.secret_key = 'cricxabhi_edit_team_secret'
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
        username = request.form.get('username').strip()
        if username:
            conn = sqlite3.connect(DB_NAME)
            c = conn.cursor()
            c.execute('SELECT * FROM users WHERE username = ?', (username,))
            user = c.fetchone()
            if user:
                session['user_id'] = user[0]
            else:
                c.execute('INSERT INTO users (username, coins) VALUES (?, 1000)', (username,))
                conn.commit()
                session['user_id'] = c.lastrowid
            conn.close()
        return redirect(url_for('index'))

    if 'user_id' not in session:
        session['user_id'] = 1

    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    user = c.execute('SELECT * FROM users WHERE id = ?', (session['user_id'],)).fetchone()
    matches = c.execute('SELECT * FROM matches').fetchall()
    conn.close()

    return render_template_string('''
    <!DOCTYPE html>
    <html lang="hi">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
        <title>CRICXABHI Fantasy</title>
        <script src="https://cdn.tailwindcss.com"></script>
    </head>
    <body class="bg-gray-950 text-white font-sans antialiased pb-20">
        <div class="bg-indigo-600 p-4 sticky top-0 z-50 flex justify-between items-center shadow-lg">
            <div>
                <h1 class="font-extrabold text-lg tracking-wide">CRICXABHI Fantasy 🏏</h1>
                <p class="text-xs text-indigo-200">Hi, <b class="text-white">{{user.username}}</b></p>
            </div>
            <div class="flex gap-2 items-center">
                <span class="bg-indigo-900 px-3 py-1.5 rounded-full text-sm font-bold shadow-inner">🪙 {{user.coins}}</span>
                <a href="/admin" class="bg-emerald-500 hover:bg-emerald-600 px-3 py-1.5 rounded-xl font-bold text-xs text-black shadow">Admin</a>
            </div>
        </div>

        <div class="p-4 max-w-md mx-auto">
            <div class="bg-gray-900 border border-gray-800 p-4 rounded-2xl mb-5 shadow-xl">
                <h2 class="text-sm font-semibold text-gray-300 mb-2">Apna Naam Badlo / Login Karo</h2>
                <form method="POST" class="flex gap-2">
                    <input type="text" name="username" placeholder="Enter your name..." required class="bg-gray-800 border border-gray-700 p-3 rounded-xl text-sm w-full text-white focus:outline-none focus:border-indigo-500">
                    <button type="submit" class="bg-indigo-600 hover:bg-indigo-700 px-4 py-3 rounded-xl text-sm font-bold shrink-0 shadow">Login</button>
                </form>
            </div>

            <h2 class="text-base font-bold mb-3 text-gray-200">Upcoming & Live Matches</h2>
            {% if not matches %}
            <div class="text-center py-10 text-gray-500 text-sm">Koi match available nahi hai. Admin panel se add karein!</div>
            {% endif %}
            
            {% for m in matches %}
            <div class="bg-gray-900 border border-gray-800 p-4 rounded-2xl mb-4 shadow-xl">
                <div class="flex justify-between items-center mb-2">
                    <span class="font-bold text-base text-white">{{m.team1}} vs {{m.team2}}</span>
                    <span class="text-xs {% if m.status=='Live' %}bg-amber-400 text-black animate-pulse{% elif m.status=='Completed' %}bg-rose-500 text-white{% else %}bg-emerald-400 text-black{% endif %} px-2.5 py-1 rounded-full font-extrabold uppercase tracking-wider">{{m.status}}</span>
                </div>
                
                <div class="text-xs text-amber-300 mb-4 font-mono font-medium" id="timer-{{m.id}}">🕒 Loading Timer...</div>
                <script>
                    (function() {
                        const matchTime = new Date("{{m.match_time}}").getTime();
                        const timerElem = document.getElementById("timer-{{m.id}}");
                        const status = "{{m.status}}";
                        if(status === 'Completed') {
                            timerElem.innerHTML = "🏁 Match Completed";
                            return;
                        }
                        if(status === 'Live') {
                            timerElem.innerHTML = "🔴 Match is LIVE NOW!";
                            return;
                        }
                        const x = setInterval(function() {
                            const now = new Date().getTime();
                            const distance = matchTime - now;
                            if (distance < 0) {
                                clearInterval(x);
                                timerElem.innerHTML = "🔴 Match Started / Live";
                            } else {
                                const days = Math.floor(distance / (1000 * 60 * 60 * 24));
                                const hours = Math.floor((distance % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
                                const minutes = Math.floor((distance % (1000 * 60 * 60)) / (1000 * 60));
                                const seconds = Math.floor((distance % (1000 * 60)) / 1000);
                                timerElem.innerHTML = "⏳ Starts in: " + days + "d " + hours + "h " + minutes + "m " + seconds + "s";
                            }
                        }, 1000);
                    })();
                </script>
                
                <a href="/match/{{m.id}}" class="block text-center bg-indigo-600 hover:bg-indigo-700 py-3 rounded-xl font-bold text-sm shadow-lg transition">Enter Match & Contests</a>
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
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
        <title>Match Details</title>
        <script src="https://cdn.tailwindcss.com"></script>
    </head>
    <body class="bg-gray-950 text-white font-sans antialiased pb-20">
        <div class="bg-indigo-600 p-4 sticky top-0 z-50 flex items-center shadow-lg">
            <a href="/" class="mr-3 text-lg font-bold bg-indigo-700 p-2 rounded-xl">←</a>
            <h1 class="text-base font-bold">{{match.team1}} vs {{match.team2}}</h1>
        </div>
        
        <div class="p-4 max-w-md mx-auto">
            <!-- My Teams -->
            <div class="bg-gray-900 border border-indigo-500 p-4 rounded-2xl mb-5 shadow-xl">
                <h3 class="font-bold text-indigo-300 text-sm mb-3">🔒 My Created Teams</h3>
                {% if not my_teams %}
                <p class="text-xs text-gray-400 mb-3">Aapne abhi tak is match mein koi team nahi banayi hai.</p>
                {% endif %}
                {% for t in my_teams %}
                <div class="bg-gray-800 border border-gray-700 p-3 rounded-xl mb-3 text-xs">
                    <div class="font-extrabold text-emerald-400 text-sm mb-1">{{t.team_name}}</div>
                    <div class="text-gray-300 mb-1">⭐ C: <b>{{t.captain}}</b> | 🌟 VC: <b>{{t.vice_captain}}</b></div>
                    <div class="text-gray-400 mb-2">Players: {{t.players}}</div>
                    
                    {% if match.status == 'Upcoming' %}
                    <a href="/create_team/{{match.id}}/0?edit={{t.id}}" class="inline-block bg-amber-500 hover:bg-amber-600 text-black font-extrabold px-3 py-1.5 rounded-lg text-xs">✏️ Edit Lineup</a>
                    {% endif %}
                </div>
                {% endfor %}
            </div>

            <!-- Public Teams if Live/Completed -->
            {% if match.status in ['Live', 'Completed'] %}
            <div class="bg-gray-900 border border-amber-500 p-4 rounded-2xl mb-5 shadow-xl">
                <h3 class="font-bold text-amber-400 text-sm mb-3">🔓 All Users Public Teams</h3>
                {% for t in all_teams %}
                <div class="bg-gray-800 border border-gray-700 p-3 rounded-xl mb-2 text-xs">
                    <div class="flex justify-between font-bold text-sm mb-1">
                        <span class="text-indigo-300">{{t.team_name}}</span>
                        <span class="text-gray-400 font-normal">By: {{t.username}}</span>
                    </div>
                    <div class="text-gray-300 mb-1">⭐ C: {{t.captain}} | 🌟 VC: {{t.vice_captain}}</div>
                    <div class="text-gray-400">Players: {{t.players}}</div>
                </div>
                {% endfor %}
            </div>
            {% endif %}

            <h3 class="text-sm font-bold mb-3 text-gray-300">Contests</h3>
            {% for con in contests %}
            <div class="bg-gray-900 border border-gray-800 p-4 rounded-2xl mb-3 shadow-xl">
                <div class="flex justify-between font-bold text-sm mb-1">
                    <span>{{con.name}}</span>
                    <span class="text-emerald-400">🪙 {{con.prize_pool}}</span>
                </div>
                <p class="text-xs text-gray-400 mb-3">Entry Fee: 🪙 {{con.entry_fee}} | Spots: {{con.spots}}</p>
                <a href="/create_team/{{match.id}}/{{con.id}}" class="block text-center bg-emerald-600 hover:bg-emerald-700 py-2.5 rounded-xl font-bold text-xs shadow">Join Contest / Create Team</a>
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
    c = conn.cursor()
    
    edit_id = request.args.get('edit')
    existing_team = None
    if edit_id:
        existing_team = c.execute('SELECT * FROM teams WHERE id = ? AND user_id = ?', (edit_id, session.get('user_id', 1))).fetchone()

    if request.method == 'POST':
        team_name = request.form.get('team_name')
        captain = request.form.get('captain')
        vice_captain = request.form.get('vice_captain')
        players = request.form.getlist('players')
        
        if len(players) != 11: 
            return "Error: Exact 11 players select karne honge! <a href='javascript:history.back()' class='text-indigo-400 underline'>Go Back</a>"
        
        players_str = ",".join(players)
        if edit_id and existing_team:
            c.execute('UPDATE teams SET team_name = ?, captain = ?, vice_captain = ?, players = ? WHERE id = ?',
                      (team_name, captain, vice_captain, players_str, edit_id))
        else:
            c.execute('INSERT INTO teams (match_id, user_id, team_name, captain, vice_captain, players) VALUES (?, ?, ?, ?, ?, ?)',
                      (match_id, session.get('user_id', 1), team_name, captain, vice_captain, players_str))
        conn.commit()
        conn.close()
        return redirect(url_for('match_detail', match_id=match_id))
        
    players = c.execute('SELECT * FROM players WHERE match_id = ?', (match_id,)).fetchall()
    conn.close()
    return render_template_string('''
    <!DOCTYPE html>
    <html lang="hi">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
        <title>Create / Edit Team</title>
        <script src="https://cdn.tailwindcss.com"></script>
    </head>
    <body class="bg-gray-950 text-white font-sans antialiased pb-20">
        <div class="bg-indigo-600 p-4 sticky top-0 z-50 shadow-lg">
            <h1 class="text-base font-bold">{% if edit_id %}Edit Your Lineup{% else %}Select 11 Players for your Team{% endif %}</h1>
        </div>
        <div class="p-4 max-w-md mx-auto">
            <form method="POST">
                <div class="mb-4">
                    <label class="block text-xs font-semibold text-gray-300 mb-1">Team Name</label>
                    <input type="text" name="team_name" value="{% if existing_team %}{{existing_team.team_name}}{% endif %}" placeholder="e.g. CricXabhi XI" required class="w-full bg-gray-900 border border-gray-700 p-3 rounded-xl text-sm text-white focus:outline-none focus:border-indigo-500">
                </div>
                
                <h3 class="text-sm font-bold text-indigo-300 mb-3">Pick 11 Players & Select C / VC:</h3>
                <div class="space-y-2 mb-6">
                    {% for p in players %}
                    <label class="flex justify-between items-center bg-gray-900 border border-gray-800 p-3 rounded-2xl shadow">
                        <div class="flex items-center gap-3">
                            <input type="checkbox" name="players" value="{{p.name}}" {% if existing_team and p.name in existing_team.players %}checked{% endif %} class="w-5 h-5 accent-indigo-500 rounded">
                            <div>
                                <span class="font-bold text-sm block text-white">{{p.name}}</span>
                                <span class="text-xs text-gray-400">{{p.team}} • {{p.role}}</span>
                            </div>
                        </div>
                        <div class="flex gap-3 text-xs font-semibold">
                            <label class="flex items-center gap-1 cursor-pointer"><input type="radio" name="captain" value="{{p.name}}" {% if existing_team and existing_team.captain == p.name %}checked{% endif %} required class="accent-indigo-500"> C</label>
                            <label class="flex items-center gap-1 cursor-pointer"><input type="radio" name="vice_captain" value="{{p.name}}" {% if existing_team and existing_team.vice_captain == p.name %}checked{% endif %} required class="accent-indigo-500"> VC</label>
                        </div>
                    </label>
                    {% endfor %}
                </div>
                <button type="submit" class="w-full bg-emerald-600 hover:bg-emerald-700 py-3.5 rounded-2xl font-extrabold text-sm shadow-xl sticky bottom-4">{% if edit_id %}Update Lineup{% else %}Save Team & Join Contest{% endif %}</button>
            </form>
        </div>
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
            t1 = request.form.get('t1')
            t2 = request.form.get('t2')
            time_val = request.form.get('time')
            c.execute('INSERT INTO matches (team1, team2, match_time, status) VALUES (?, ?, ?, "Upcoming")', (t1, t2, time_val))
            msg = "Match added successfully!"
        elif action == 'status':
            c.execute('UPDATE matches SET status = ? WHERE id = ?', (request.form.get('status'), request.form.get('match_id')))
            msg = "Match status updated!"
        elif action == 'player':
            c.execute('INSERT INTO players (match_id, name, team, role) VALUES (?, ?, ?, ?)', (request.form.get('match_id'), request.form.get('p_name'), request.form.get('p_team'), request.form.get('p_role')))
            msg = "Player added successfully!"
        elif action == 'coins':
            u_id = request.form.get('user_id')
            coins = request.form.get('coins')
            c.execute('UPDATE users SET coins = coins + ? WHERE id = ?', (coins, u_id))
            msg = "Coins sent to user successfully!"
        elif action == 'contest':
            c.execute('INSERT INTO contests (match_id, name, prize_pool, entry_fee, spots) VALUES (?, ?, ?, ?, ?)', (request.form.get('match_id'), request.form.get('c_name'), request.form.get('prize'), request.form.get('fee'), request.form.get('spots')))
            msg = "Contest added successfully!"
        conn.commit()
    matches = c.execute('SELECT * FROM matches').fetchall()
    users = c.execute('SELECT * FROM users').fetchall()
    conn.close()
    return render_template_string('''
    <!DOCTYPE html>
    <html lang="hi">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
        <title>Admin Panel</title>
        <script src="https://cdn.tailwindcss.com"></script>
    </head>
    <body class="bg-gray-950 text-white font-sans antialiased p-4 pb-24">
        <div class="max-w-md mx-auto">
            <div class="flex justify-between items-center mb-5">
                <h1 class="text-lg font-extrabold text-emerald-400">👑 Admin Panel</h1>
                <a href="/" class="text-indigo-400 font-bold text-sm bg-indigo-950 px-3 py-1.5 rounded-xl border border-indigo-800">Home</a>
            </div>
            
            {% if msg %}
            <div class="bg-emerald-900 border border-emerald-600 text-emerald-200 p-3 rounded-2xl mb-4 text-xs font-bold shadow">{{msg}}</div>
            {% endif %}
            
            <form method="POST" class="bg-gray-900 border border-gray-800 p-4 rounded-2xl mb-4 shadow-xl">
                <input type="hidden" name="action" value="match">
                <h3 class="font-bold mb-3 text-indigo-300 text-sm">1. Add Match & Real Time</h3>
                <input type="text" name="t1" placeholder="Team 1 (e.g. IND)" required class="w-full bg-gray-800 border border-gray-700 p-3 rounded-xl mb-3 text-sm text-white">
                <input type="text" name="t2" placeholder="Team 2 (e.g. AUS)" required class="w-full bg-gray-800 border border-gray-700 p-3 rounded-xl mb-3 text-sm text-white">
                <label cl
