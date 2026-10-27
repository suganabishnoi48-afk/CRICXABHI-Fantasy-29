from flask import Flask, render_template_string, request, redirect, url_for, session
import os
import psycopg2
import psycopg2.extras
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'cricxabhi_fixed_2026'

def get_db_connection():
    conn = psycopg2.connect(
        dbname="postgres",
        user="postgres.yhbrlylvimbjazdirqiq",
        password="@Abhishek.2929",
        host="aws-0-ap-northeast-1.pooler.supabase.com",
        port="6543",
        cursor_factory=psycopg2.extras.RealDictCursor
    )
    return conn

def init_db():
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (
                    id SERIAL PRIMARY KEY,
                    username TEXT UNIQUE,
                    password TEXT,
                    coins REAL DEFAULT 0
                )''')
    c.execute('''CREATE TABLE IF NOT EXISTS matches (
                    id SERIAL PRIMARY KEY,
                    team1 TEXT,
                    team2 TEXT,
                    match_time TEXT,
                    status TEXT DEFAULT 'Upcoming'
                )''')
    c.execute('''CREATE TABLE IF NOT EXISTS players (
                    id SERIAL PRIMARY KEY,
                    match_id INTEGER,
                    name TEXT,
                    team TEXT,
                    role TEXT,
                    points REAL DEFAULT 0
                )''')
    c.execute('''CREATE TABLE IF NOT EXISTS contests (
                    id SERIAL PRIMARY KEY,
                    match_id INTEGER,
                    name TEXT,
                    prize_pool INTEGER,
                    entry_fee INTEGER,
                    spots INTEGER,
                    prize_breakup TEXT
                )''')
    c.execute('''CREATE TABLE IF NOT EXISTS teams (
                    id SERIAL PRIMARY KEY,
                    match_id INTEGER,
                    user_id INTEGER,
                    team_name TEXT,
                    captain TEXT,
                    vice_captain TEXT,
                    players TEXT,
                    total_points REAL DEFAULT 0
                )''')
    c.execute('''CREATE TABLE IF NOT EXISTS contest_participants (
                    id SERIAL PRIMARY KEY,
                    contest_id INTEGER,
                    user_id INTEGER,
                    team_id INTEGER,
                    rank INTEGER,
                    winnings INTEGER DEFAULT 0
                )''')
    
    c.execute('SELECT COUNT(*) AS count FROM users WHERE username = %s', ('AbhiAdmin',))
    if c.fetchone()['count'] == 0:
        c.execute('INSERT INTO users (username, password, coins) VALUES (%s, %s, %s)', ('AbhiAdmin', '29022008', 100000))
    conn.commit()
    conn.close()

init_db()

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/', methods=['GET', 'POST'])
def index():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('SELECT * FROM users WHERE id = %s', (session['user_id'],))
    user = c.fetchone()
    if not user:
        session.clear()
        conn.close()
        return redirect(url_for('login'))
        
    if session.get('is_admin') and request.method == 'POST':
        action = request.form.get('action')
        if action == 'match':
            t1 = request.form.get('t1')
            t2 = request.form.get('t2')
            time = request.form.get('time')
            c.execute('INSERT INTO matches (team1, team2, match_time, status) VALUES (%s, %s, %s, %s)', (t1, t2, time, 'Upcoming'))
            conn.commit()
        elif action == 'player':
            match_id = request.form.get('match_id')
            p_name = request.form.get('p_name')
            p_team = request.form.get('p_team')
            p_role = request.form.get('p_role')
            c.execute('INSERT INTO players (match_id, name, team, role, points) VALUES (%s, %s, %s, %s, %s)', (match_id, p_name, p_team, p_role, 0.0))
            conn.commit()
        elif action == 'update_player_points':
            player_id = request.form.get('player_id')
            new_points = float(request.form.get('points', 0))
            c.execute('UPDATE players SET points = %s WHERE id = %s', (new_points, player_id))
            conn.commit()
        elif action == 'contest':
            match_id = request.form.get('match_id')
            c_name = request.form.get('c_name')
            prize = request.form.get('prize')
            fee = request.form.get('fee')
            spots = request.form.get('spots')
            breakup = request.form.get('breakup')
            c.execute('INSERT INTO contests (match_id, name, prize_pool, entry_fee, spots, prize_breakup) VALUES (%s, %s, %s, %s, %s, %s)', (match_id, c_name, prize, fee, spots, breakup))
            conn.commit()
        elif action == 'update_status':
            match_id = request.form.get('match_id')
            status = request.form.get('status')
            c.execute('UPDATE matches SET status = %s WHERE id = %s', (status, match_id))
            conn.commit()
            
            if status == 'Completed':
                c.execute('SELECT * FROM players WHERE match_id = %s', (match_id,))
                match_players = {p['name']: p['points'] for p in c.fetchall()}
                
                c.execute('SELECT * FROM teams WHERE match_id = %s', (match_id,))
                match_teams = c.fetchall()
                
                for t in match_teams:
                    plist = t['players'].split(',')
                    t_pts = 0.0
                    for pname in plist:
                        pbase = match_players.get(pname.strip(), 0.0)
                        if pname.strip() == t['captain']:
                            t_pts += pbase * 2
                        elif pname.strip() == t['vice_captain']:
                            t_pts += pbase * 1.5
                        else:
                            t_pts += pbase
                    c.execute('UPDATE teams SET total_points = %s WHERE id = %s', (t_pts, t['id']))
                conn.commit()
                
                c.execute('SELECT * FROM contests WHERE match_id = %s', (match_id,))
                match_contests = c.fetchall()
                for con in match_contests:
                    c.execute('''SELECT cp.*, t.total_points FROM contest_participants cp
                                 JOIN teams t ON cp.team_id = t.id
                                 WHERE cp.contest_id = %s ORDER BY t.total_points DESC''', (con['id'],))
                    participants = c.fetchall()
                    
                    for idx, part in enumerate(participants, 1):
                        rank = idx
                        winnings = 0
                        if rank == 1:
                            winnings = con['prize_pool']
                            c.execute('UPDATE users SET coins = coins + %s WHERE id = %s', (winnings, part['user_id']))
                        
                        c.execute('UPDATE contest_participants SET rank = %s, winnings = %s WHERE id = %s', (rank, winnings, part['id']))
                    conn.commit()

    c.execute('SELECT * FROM matches')
    matches = c.fetchall()
    c.execute('SELECT * FROM players')
    players = c.fetchall()
    conn.close()
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>CRICXABHI Fantasy</title>
        <script src="https://cdn.tailwindcss.com"></script>
    </head>
    <body class="bg-gray-950 text-white font-sans p-4 pb-20">
        <div class="bg-indigo-600 p-4 rounded-2xl flex justify-between items-center shadow-lg mb-4">
            <div>
                <h1 class="font-bold text-base">CRICXABHI Fantasy 🏏</h1>
                <p class="text-xs text-indigo-200">Hi, <b>{user['username']}</b></p>
            </div>
            <div class="flex gap-2 items-center">
                <span class="bg-indigo-900 px-3 py-1 rounded-full text-xs font-bold">🪙 {user['coins']}</span>
                <a href="/wallet" class="bg-amber-500 text-black px-2.5 py-1 rounded-xl font-bold text-xs">Share Coin</a>
                <a href="/logout" class="bg-rose-600 px-2.5 py-1 rounded-xl font-bold text-xs">Logout</a>
            </div>
        </div>
        <h2 class="text-sm font-bold mb-3 text-gray-300">Upcoming & Live Matches</h2>
    """
    for m in matches:
        badge = f'<span class="text-xs bg-emerald-400 text-black px-2.5 py-1 rounded-full uppercase">{m["status"]}</span>'
        if m['status'] == 'Live':
            badge = '<span class="text-xs bg-amber-400 text-black animate-pulse px-2.5 py-1 rounded-full uppercase">Live</span>'
        elif m['status'] == 'Completed':
            badge = '<span class="text-xs bg-rose-500 text-white px-2.5 py-1 rounded-full uppercase">Completed</span>'
            
        html += f"""
        <div class="bg-gray-900 border border-gray-800 p-4 rounded-2xl mb-3 shadow">
            <div class="flex justify-between font-bold text-base mb-1">
                <span>{m['team1']} vs {m['team2']}</span> {badge}
            </div>
            <a href="/match/{m['id']}" class="block text-center bg-indigo-600 py-2.5 rounded-xl font-bold text-xs shadow mt-2">View Contests & Teams</a>
        </div>
        """
    
    if session.get('is_admin'):
        html += """
        <div class="mt-6 border-t border-gray-800 pt-4">
            <h2 class="text-lg font-bold text-amber-400 mb-3">Admin Panel</h2>
            
            <form method="POST" class="bg-gray-900 border border-gray-800 p-3 rounded-2xl mb-3">
                <input type="hidden" name="action" value="match">
                <h3 class="font-bold mb-2 text-indigo-300 text-xs">1. Add Match</h3>
                <input type="text" name="t1" placeholder="Team 1" required class="w-full bg-gray-800 p-2.5 rounded-xl mb-2 text-xs text-white">
                <input type="text" name="t2" placeholder="Team 2" required class="w-full bg-gray-800 p-2.5 rounded-xl mb-2 text-xs text-white">
                <input type="datetime-local" name="time" required class="w-full bg-gray-800 p-2.5 rounded-xl mb-2 text-xs text-white">
                <button class="w-full bg-indigo-600 py-2.5 rounded-xl font-bold text-xs">Add Match</button>
            </form>
            
            <form method="POST" class="bg-gray-900 border border-gray-800 p-3 rounded-2xl mb-3">
                <input type="hidden" name="action" value="player">
                <h3 class="font-bold mb-2 text-indigo-300 text-xs">2. Add Player</h3>
                <select name="match_id" class="w-full bg-gray-800 p-2.5 rounded-xl mb-2 text-xs text-white">
        """
        for m in matches:
            html += f'<option value="{m["id"]}">{m["team1"]} vs {m["team2"]}</option>'
        html += """
                </select>
                <input type="text" name="p_name" placeholder="Player Name" required class="w-full bg-gray-800 p-2.5 rounded-xl mb-2 text-xs text-white">
                <input type="text" name="p_team" placeholder="Team Code" required class="w-full bg-gray-800 p-2.5 rounded-xl mb-2 text-xs text-white">
                <select name="p_role" class="w-full bg-gray-800 p-2.5 rounded-xl mb-2 text-xs text-white">
                    <option value="Batsman">Batsman</option>
                    <option value="Bowler">Bowler</option>
                    <option value="All-Rounder">All-Rounder</option>
                    <option value="WK">WK</option>
                </select>
                <button class="w-full bg-emerald-600 py-2.5 rounded-xl font-bold text-xs">Add Player</button>
            </form>
            
            <form method="POST" class="bg-gray-900 border border-gray-800 p-3 rounded-2xl mb-3">
                <input type="hidden" name="action" value="update_player_points">
                <h3 class="font-bold mb-2 text-indigo-300 text-xs">3. Update Player Points</h3>
                <select name="player_id" class="w-full bg-gray-800 p-2.5 rounded-xl mb-2 text-xs text-white">
        """
        for p in players:
            html += f'<option value="{p["id"]}">{p["name"]} ({p["team"]}) - Current: {p["points"]} pts</option>'
        html += """
                </select>
                <input type="number" step="0.5" name="points" placeholder="New Points..." required class="w-full bg-gray-800 p-2.5 rounded-xl mb-2 text-xs text-white">
                <button class="w-full bg-amber-600 py-2.5 rounded-xl font-bold text-xs">Update Points</button>
            </form>

            <div class="bg-gray-900 border border-gray-800 p-3 rounded-2xl mb-3 flex justify-between items-center">
                <div>
                    <h3 class="font-bold text-indigo-300 text-xs">4. User Data Management</h3>
                    <p class="text-[10px] text-gray-400">View all users and add coins</p>
                </div>
                <a href="/admin/users" class="bg-indigo-600 px-3 py-2 rounded-xl font-bold text-xs shadow">Show More →</a>
            </div>

            <form method="POST" class="bg-gray-900 border border-gray-800 p-3 rounded-2xl mb-3">
                <input type="hidden" name="action" value="contest">
                <h3 class="font-bold mb-2 text-indigo-300 text-xs">5. Create Contest</h3>
                <select name="match_id" class="w-full bg-gray-800 p-2.5 rounded-xl mb-2 text-xs text-white">
        """
        for m in matches:
            html += f'<option value="{m["id"]}">{m["team1"]} vs {m["team2"]}</option>'
        html += """
                </select>
                <input type="text" name="c_name" placeholder="Contest Name" required class="w-full bg-gray-800 p-2.5 rounded-xl mb-2 text-xs text-white">
                <input type="number" name="prize" placeholder="Total Prize Pool" required class="w-full bg-gray-800 p-2.5 rounded-xl mb-2 text-xs text-white">
                <input type="number" name="fee" placeholder="Entry Fee" required class="w-full bg-gray-800 p-2.5 rounded-xl mb-2 text-xs text-white">
                <input type="number" name="spots" placeholder="Total Spots" required class="w-full bg-gray-800 p-2.5 rounded-xl mb-2 text-xs text-white">
                <input type="text" name="breakup" placeholder="Breakup e.g. 1st: 100%" required class="w-full bg-gray-800 p-2.5 rounded-xl mb-2 text-xs text-white">
                <button class="w-full bg-indigo-600 py-2.5 rounded-xl font-bold text-xs">Create Contest</button>
            </form>
            
            <form method="POST" class="bg-gray-900 border border-gray-800 p-3 rounded-2xl">
                <input type="hidden" name="action" value="update_status">
                <h3 class="font-bold mb-2 text-indigo-300 text-xs">6. Match Status Control (Auto Coins Distribution on Complete)</h3>
                <select name="match_id" class="w-full bg-gray-800 p-2.5 rounded-xl mb-2 text-xs text-white">
        """
        for m in matches:
            html += f'<option value="{m["id"]}">{m["team1"]} vs {m["team2"]} (Current: {m["status"]})</option>'
        html += """
                </select>
                <select name="status" class="w-full bg-gray-800 p-2.5 rounded-xl mb-2 text-xs text-white">
                    <option value="Upcoming">Upcoming</option>
                    <option value="Live">Live</option>
                    <option value="Completed">Completed</option>
                </select>
                <button class="w-full bg-amber-500 text-black py-2.5 rounded-xl font-bold text-xs">Update Status</button>
            </form>
        </div>
        """

    html += """
    </body>
    </html>
    """
    return render_template_string(html)

@app.route('/admin/users', methods=['GET', 'POST'])
def admin_users():
    if not session.get('is_admin'):
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    c = conn.cursor()
    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'add_user_coins':
            target_user_id = request.form.get('target_user_id')
            add_amt = float(request.form.get('add_amt', 0))
            if add_amt != 0:
                c.execute('UPDATE users SET coins = coins + %s WHERE id = %s', (add_amt, target_user_id))
                conn.commit()
                
    c.execute('SELECT * FROM users ORDER BY id ASC')
    all_users = c.fetchall()
    conn.close()
    
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>All Users Data</title>
        <script src="https://cdn.tailwindcss.com"></script>
    </head>
    <body class="bg-gray-950 text-white font-sans p-4 pb-20">
        <div class="bg-indigo-600 p-3 rounded-xl flex items-center mb-4 shadow">
            <a href="/" class="mr-3 font-bold bg-indigo-700 px-2.5 py-1 rounded-lg text-xs">←</a>
            <h1 class="text-sm font-bold">👥 User Data & Coin Management</h1>
        </div>
        <div class="bg-gray-900 border border-gray-800 p-4 rounded-2xl space-y-2">
    """
    for u in all_users:
        html += f"""
        <div class="flex items-center justify-between bg-gray-800 p-3 rounded-xl text-xs border border-gray-700">
            <div>
                <span class="font-bold text-emerald-400">{u['username']}</span> 
                <p class="text-gray-300 mt-0.5">Coins: 🪙 {u['coins']}</p>
            </div>
            <form method="POST" class="flex items-center gap-1">
                <input type="hidden" name="action" value="add_user_coins">
                <input type="hidden" name="target_user_id" value="{u['id']}">
                <input type="number" name="add_amt" placeholder="Amt" required class="w-16 bg-gray-700 p-1.5 rounded text-xs text-white text-center">
                <button type="submit" class="bg-emerald-600 px-3 py-1.5 rounded font-bold text-xs" title="Add Coins">➕</button>
            </form>
        </div>
        """
    html += """
        </div>
        <a href="/" class="block text-center bg-gray-800 py-2.5 rounded-xl font-bold text-xs mt-4">Back to Home</a>
    </body>
    </html>
    """
    return render_template_string(html)

@app.route('/login', methods=['GET', 'POST'])
def login():
    error = ""
    if request.method == 'POST':
        login_type = request.form.get('login_type')
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        conn = get_db_connection()
        c = conn.cursor()
        if login_type == 'admin':
            if username == 'AbhiAdmin' and password == '29022008':
                session['is_admin'] = True
                session['user_id'] = 1
                session['username'] = 'AbhiAdmin'
                conn.close()
                return redirect(url_for('index'))
            else:
                error = "❌ Invalid Admin Credentials!"
        else:
            c.execute('SELECT * FROM users WHERE username = %s AND password = %s', (username, password))
            user = c.fetchone()
            if user:
                session['user_id'] = user['id']
                session['username'] = user['username']
                session.pop('is_admin', None)
                conn.close()
                return redirect(url_for('index'))
            else:
                error = "❌ Invalid Username or Password!"
        conn.close()
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Login</title>
        <script src="https://cdn.tailwindcss.com"></script>
    </head>
    <body class="bg-gray-950 text-white font-sans p-6 flex items-center justify-center h-screen">
        <div class="bg-gray-900 border border-gray-800 p-6 rounded-2xl max-w-sm w-full shadow-2xl">
            <h2 class="text-base font-bold text-indigo-400 mb-4 text-center">🏏 CRICXABHI Login</h2>
            {f'<div class="bg-rose-900 text-rose-200 p-2.5 rounded-xl mb-3 text-xs font-bold text-center">{error}</div>' if error else ''}
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
            function toggleAdmin() {{
                let val = document.getElementById("loginType").value;
                let lbl = document.getElementById("labelName");
                if(val === "admin") {{ lbl.innerText = "Admin ID (AbhiAdmin)"; }}
                else {{ lbl.innerText = "Username"; }}
            }}
        </script>
    </body>
    </html>
    """
    return render_template_string(html)

@app.route('/register', methods=['GET', 'POST'])
def register():
    error = ""
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        if username and password:
            conn = get_db_connection()
            c = conn.cursor()
            try:
                c.execute('INSERT INTO users (username, password, coins) VALUES (%s, %s, 0)', (username, password))
                conn.commit()
                conn.close()
                return redirect(url_for('login'))
            except Exception as e:
                error = "❌ Username already exists!"
            conn.close()
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Register</title>
        <script src="https://cdn.tailwindcss.com"></script>
    </head>
    <body class="bg-gray-950 text-white font-sans p-6 flex items-center justify-center h-screen">
        <div class="bg-gray-900 border border-gray-800 p-6 rounded-2xl max-w-sm w-full shadow-2xl">
            <h2 class="text-base font-bold text-emerald-400 mb-2 text-center">📝 New User Registration</h2>
            {f'<div class="bg-rose-900 text-rose-200 p-2.5 rounded-xl mb-3 text-xs font-bold text-center">{error}</div>' if error else ''}
            <form method="POST" class="space-y-3">
                <input type="text" name="username" placeholder="Choose unique username..." required class="w-full bg-gray-800 border border-gray-700 p-2.5 rounded-xl text-xs text-white">
                <input type="password" name="password" placeholder="Create secure password..." required class="w-full bg-gray-800 border border-gray-700 p-2.5 rounded-xl text-xs text-white">
                <button type="submit" class="w-full bg-emerald-600 py-3 rounded-xl font-bold text-xs shadow">Register Now</button>
            </form>
            <div class="text-center mt-4 text-xs text-gray-400">Already registered? <a href="/login" class="text-indigo-400 font-bold">Login here</a></div>
        </div>
    </body>
    </html>
    """
    return render_template_string(html)

@app.route('/wallet', methods=['GET', 'POST'])
def wallet():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('SELECT * FROM users WHERE id = %s', (session['user_id'],))
    user = c.fetchone()
    msg = ""
    if request.method == 'POST':
        target_name = request.form.get('target_username', '').strip()
        amt = int(request.form.get('amount', 0))
        if amt > 0 and user['coins'] >= amt:
            c.execute('SELECT * FROM users WHERE username = %s', (target_name,))
            target_user = c.fetchone()
            if target_user and target_user['id'] != user['id']:
                c.execute('UPDATE users SET coins = coins - %s WHERE id = %s', (amt, user['id']))
                c.execute('UPDATE users SET coins = coins + %s WHERE id = %s', (amt, target_user['id']))
                conn.commit()
                msg = f"Successfully sent {amt} coins to {target_name}!"
            else:
                msg = "❌ Target user not found!"
        else:
            msg = "❌ Insufficient coins!"
    c.execute('SELECT * FROM users WHERE id = %s', (session['user_id'],))
    user = c.fetchone()
    conn.close()
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Share Coin</title>
        <script src="https://cdn.tailwindcss.com"></script>
    </head>
    <body class="bg-gray-950 text-white font-sans p-4 pb-20">
        <div class="bg-indigo-600 p-3 rounded-xl flex items-center mb-4 shadow">
            <a href="/" class="mr-3 font-bold bg-indigo-700 px-2.5 py-1 rounded-lg text-xs">←</a>
            <h1 class="text-sm font-bold">🪙 Share Coin</h1>
        </div>
        <div class="bg-gray-900 border border-gray-800 p-4 rounded-2xl mb-4">
            <p class="text-xs text-gray-300 mb-2">My Balance: <b>🪙 {user['coins']} coins</b></p>
            {f'<div class="bg-indigo-950 text-indigo-200 p-2.5 rounded-xl mb-3 text-xs font-bold">{msg}</div>' if msg else ''}
            <form method="POST" class="space-y-3">
                <input type="text" name="target_username" placeholder="Recipient Username..." required class="w-full bg-gray-800 border border-gray-700 p-2.5 rounded-xl text-xs text-white">
                <input type="number" name="amount" placeholder="Coin Amount..." min="1" required class="w-full bg-gray-800 border border-gray-700 p-2.5 rounded-xl text-xs text-white">
                <button type="submit" class="w-full bg-emerald-600 py-3 rounded-xl font-bold text-xs shadow">Transfer Coins</button>
            </form>
        </div>
    </body>
    </html>
    """
    return render_template_string(html)

@app.route('/match/<int:match_id>')
def match_detail(match_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('SELECT * FROM users WHERE id = %s', (session['user_id'],))
    user = c.fetchone()
    c.execute('SELECT * FROM matches WHERE id = %s', (match_id,))
    match = c.fetchone()
    c.execute('SELECT * FROM contests WHERE match_id = %s', (match_id,))
    contests = c.fetchall()
    c.execute('SELECT * FROM teams WHERE match_id = %s AND user_id = %s', (match_id, user['id']))
    my_teams = c.fetchall()
    conn.close()
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Match Detail</title>
        <script src="https://cdn.tailwindcss.com"></script>
    </head>
    <body class="bg-gray-950 text-white font-sans p-4 pb-20">
        <div class="bg-indigo-600 p-3 rounded-xl flex items-center mb-4 shadow">
            <a href="/" class="mr-3 font-bold bg-indigo-700 px-2.5 py-1 rounded-lg text-xs">←</a>
            <h1 class="text-sm font-bold">{match['team1']} vs {match['team2']} ({match['status']})</h1>
        </div>
    """
    
    if match['status'] == 'Upcoming':
        if not my_teams:
            html += f'''
            <div class="mb-4">
                <a href="/create_team/{match['id']}" class="block text-center bg-emerald-600 py-3 rounded-xl font-bold text-xs shadow">➕ Create Team</a>
            </div>
            '''
        else:
            html += f'''
            <div class="mb-4">
                <a href="/create_team/{match['id']}" class="block text-center bg-amber-600 py-3 rounded-xl font-bold text-xs shadow">✏️ Edit Team</a>
            </div>
            '''

    html += '<div class="bg-gray-900 border border-indigo-500 p-3 rounded-2xl mb-4"><h3 class="font-bold text-indigo-300 text-xs mb-2">🔒 My Created Teams</h3>'
    if not my_teams:
        html += '<p class="text-[11px] text-gray-400 mb-2">Pehle apni team banayein!</p>'
    for t in my_teams:
        if match['status'] == 'Upcoming':
            team_action_btn = f'<a href="/create_team/{match_id}" class="text-[10px] bg-amber-500 text-black px-2 py-1 rounded font-bold">Edit</a>'
        else:
            team_action_btn = f'<a href="/show_team/{t["id"]}" class="text-[10px] bg-emerald-500 text-black px-2.5 py-1 rounded font-bold">Show Your Team</a>'
            
        html += f"""
        <div class="bg-gray-800 p-2.5 rounded-xl mb-2 text-xs border border-gray-700">
            <div class="flex justify-between font-bold text-emerald-400 mb-1">
                <span>{t['team_name']}</span>
                <div class="flex items-center gap-2">
                    <span>Score: {t['total_points']} pts</span>
                    {team_action_btn}
                </div>
            </div>
            <div class="text-gray-300 text-[11px] mb-1">⭐ C (2x): <b>{t['captain']}</b> | 🌟 VC (1.5x): <b>{t['vice_captain']}</b></div>
        </div>
        """
    html += '</div>'
    
    html += '<h3 class="font-bold text-amber-400 text-xs mb-2">🏆 Contests</h3>'
    for contest in contests:
        join_btn = ""
        if match['status'] == 'Upcoming':
            join_btn = f'<a href="/join_contest/{contest["id"]}" class="flex-1 text-center bg-indigo-600 py-2 rounded-xl font-bold text-xs">Join Contest</a>'
        else:
            join_btn = '<span class="flex-1 text-center bg-gray-700 text-gray-400 py-2 rounded-xl font-bold text-xs">Locked (Match Started)</span>'
            
        html += f"""
        <div class="bg-gray-900 border border-gray-800 p-3 rounded-2xl mb-3">
            <div class="flex justify-between font-bold text-xs mb-1">
                <span>{contest['name']}</span><span>Prize: 🪙 {contest['prize_pool']}</span>
            </div>
            <p class="text-[11px] text-gray-400 mb-2">Entry Fee: 🪙 {contest['entry_fee']} | Spots: {contest['spots']}</p>
            <div class="flex gap-2">
                <a href="/contest/{contest['id']}" class="flex-1 text-center bg-gray-800 py-2 rounded-xl font-bold text-xs">Leaderboard</a>
                {join_btn}
            </div>
        </div>
        """
    html += '<a href="/" class="block text-center bg-gray-800 py-2.5 rounded-xl font-bold text-xs mt-4">Back to Home</a></body></html>'
    return render_template_string(html)

@app.route('/create_team/<int:match_id>', methods=['GET', 'POST'])
def create_team(match_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('SELECT * FROM matches WHERE id = %s', (match_id,))
    match = c.fetchone()
    
    if match['status'] != 'Upcoming':
        conn.close()
        return "<script>alert('Match has already started or completed! You cannot edit teams now.'); window.location.href='/match/" + str(match_id) + "';</script>"
        
    c.execute('SELECT * FROM players WHERE match_id = %s', (match_id,))
    players = c.fetchall()
    
    msg = ""
    if request.method == 'POST':
        team_name = request.form.get('team_name', '').strip()
        selected_players = request.form.getlist('players')
        captain = request.form.get('captain')
        vice_captain = request.form.get('vice_captain')
        
        if len(selected_players) != 11:
            msg = "❌ Aapko exact 11 khiladi select karne honge!"
        elif not captain or not vice_captain:
            msg = "❌ Captain aur Vice-Captain select karna zaroori hai!"
        else:
            p_str = ",".join(selected_players)
            c.execute('SELECT * FROM teams WHERE match_id = %s AND user_id = %s', (match_id, session['user_id']))
            existing_team = c.fetchone()
            if existing_team:
                c.execute('UPDATE teams SET team_name = %s, captain = %s, vice_captain = %s, players = %s WHERE id = %s',
                          (team_name, captain, vice_captain, p_str, existing_team['id']))
            else:
                c.execute('INSERT INTO teams (match_id, user_id, team_name, captain, vice_captain, players, total_points) VALUES (%s, %s, %s, %s, %s, %s, %s)',
                          (match_id, session['user_id'], team_name, captain, vice_captain, p_str, 0.0))
            conn.commit()
            conn.close()
            return redirect(url_for('match_detail', match_id=match_id))
    conn.close()
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Create Team</title>
        <script src="https://cdn.tailwindcss.com"></script>
    </head>
    <body class="bg-gray-950 text-white font-sans p-4 pb-20">
        <div class="bg-indigo-600 p-3 rounded-xl flex items-center mb-4 shadow">
            <a href="/match/{match_id}" class="mr-3 font-bold bg-indigo-700 px-2.5 py-1 rounded-lg text-xs">←</a>
            <h1 class="text-sm font-bold">Create Team: {match['team1']} vs {match['team2']}</h1>
        </div>
    """
    if msg:
        html += f'<div class="bg-rose-900 text-rose-200 p-2.5 rounded-xl mb-3 text-xs font-bold text-center">{msg}</div>'
    
    html += f"""
        <form method="POST" class="space-y-4">
            <div>
                <label class="text-xs text-gray-400 block mb-1">Team Name</label>
                <input type="text" name="team_name" placeholder="Enter Team Name..." required class="w-full bg-gray-800 border border-gray-700 p-2.5 rounded-xl text-xs text-white">
            </div>
            <div class="bg-gray-900 border border-gray-800 p-3 rounded-2xl">
                <h3 class="font-bold text-xs text-amber-400 mb-2">Select 11 Players</h3>
    """
    for p in players:
        html += f"""
        <div class="flex items-center justify-between bg-gray-800 p-2 rounded-xl mb-2 text-xs">
            <label class="flex items-center gap-2 cursor-pointer flex-1">
                <input type="checkbox" name="players" value="{p['name']}" class="w-4 h-4 accent-indigo-600">
                <span>{p['name']} ({p['team']}) - <span class="text-gray-400">{p['role']}</span></span>
            </label>
            <div class="flex gap-2">
                <label class="text-[10px] bg-gray-700 px-2 py-1 rounded cursor-pointer"><input type="radio" name="captain" value="{p['name']}"> C</label>
                <label class="text-[10px] bg-gray-700 px-2 py-1 rounded cursor-pointer"><input type="radio" name="vice_captain" value="{p['name']}"> VC</label>
            </div>
        </div>
        """
    html += """
            </div>
            <button type="submit" class="w-full bg-emerald-600 py-3 rounded-xl font-bold text-xs shadow">Save Team</button>
        </form>
    </body>
    </html>
    """
    return render_template_string(html)

@app.route('/show_team/<int:team_id>')
def show_team(team_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('SELECT * FROM teams WHERE id = %s', (team_id,))
    team = c.fetchone()
    c.execute('SELECT * FROM matches WHERE id = %s', (team['match_id'],))
    match = c.fetchone()
    c.execute('SELECT * FROM players WHERE match_id = %s', (team['match_id'],))
    match_players = {p['name']: p for p in c.fetchall()}
    conn.close()
    
    players_list = team['players'].split(',')
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Show Team</title>
        <script src="https://cdn.tailwindcss.com"></script>
    </head>
    <body class="bg-gray-950 text-white font-sans p-4 pb-20">
        <div class="bg-indigo-600 p-3 rounded-xl flex items-center mb-4 shadow">
            <a href="/match/{match['id']}" class="mr-3 font-bold bg-indigo-700 px-2.5 py-1 rounded-lg text-xs">←</a>
            <h1 class="text-sm font-bold">Team: {team['team_name']}</h1>
        </div>
        
        <div class="bg-gray-900 border border-indigo-500 p-3 rounded-2xl mb-4 text-xs">
            <div class="flex justify-between font-bold text-emerald-400 mb-2">
                <span>Match: {match['team1']} vs {match['team2']}</span>
                <span>Total Points: {team['total_points']} pts</span>
            </div>
            <p class="text-gray-300">⭐ Captain (2x): <b>{team['captain']}</b> | 🌟 Vice-Captain (1.5x): <b>{team['vice_captain']}</b></p>
        </div>
        
        <div class="space-y-2">
    """
    for pname in players_list:
        pname = pname.strip()
        p_obj = match_players.get(pname, {'team': '-', 'role': '-', 'points': 0.0})
        base_pts = p_obj['points']
        multiplier = 1.0
        mult_label = ""
        if pname == team['captain']:
            multiplier = 2.0
            mult_label = " (C - 2x)"
        elif pname == team['vice_captain']:
            multiplier = 1.5
            mult_label = " (VC - 1.5x)"
            
        final_p_pts = base_pts * multiplier
        html += f"""
        <div class="bg-gray-900 border border-gray-800 p-3 rounded-xl flex justify-between items-center text-xs">
            <div>
                <span class="font-bold">{pname}</span>{mult_label}
                <p class="text-[10px] text-gray-400">{p_obj['team']} | {p_obj['role']} | Base Pts: {base_pts}</p>
            </div>
            <div class="font-bold text-emerald-400">
                +{final_p_pts} pts
            </div>
        </div>
        """
    html += """
        </div>
        <a href="/match/""" + str(match['id']) + """" class="block text-center bg-gray-800 py-2.5 rounded-xl font-bold text-xs mt-4">Back to Match</a>
    </body>
    </html>
    """
    return render_template_string(html)

@app.route('/join_contest/<int:contest_id>')
def join_contest(contest_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('SELECT * FROM contests WHERE id = %s', (contest_id,))
    contest = c.fetchone()
    c.execute('SELECT * FROM matches WHERE id = %s', (contest['match_id'],))
    match = c.fetchone()
    
    if match['status'] != 'Upcoming':
        conn.close()
        return "<script>alert('Match has started! You cannot join contests now.'); window.location.href='/match/" + str(contest['match_id']) + "';</script>"
        
    c.execute('SELECT * FROM users WHERE id = %s', (session['user_id'],))
    user = c.fetchone()
    c.execute('SELECT * FROM teams WHERE match_id = %s AND user_id = %s', (contest['match_id'], user['id']))
    teams = c.fetchall()
    
    if user['coins'] < contest['entry_fee']:
        conn.close()
        return "<script>alert('Insufficient coins!'); window.location.href='/match/" + str(contest['match_id']) + "';</script>"
    
    if teams:
        team_id = teams[0]['id']
        c.execute('SELECT * FROM contest_participants WHERE contest_id = %s AND user_id = %s', (contest_id, user['id']))
        already = c.fetchone()
        if not already:
            c.execute('UPDATE users SET coins = coins - %s WHERE id = %s', (contest['entry_fee'], user['id']))
            c.execute('INSERT INTO contest_participants (contest_id, user_id, team_id, rank, winnings) VALUES (%s, %s, %s, %s, %s)',
                      (contest_id, user['id'], team_id, 0, 0))
            conn.commit()
    conn.close()
    return redirect(url_for('contest_detail', contest_id=contest_id))

@app.route('/contest/<int:contest_id>')
def contest_detail(contest_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('SELECT * FROM contests WHERE id = %s', (contest_id,))
    contest = c.fetchone()
    c.execute('''SELECT cp.*, u.username, t.team_name, t.total_points FROM contest_participants cp
                 JOIN users u ON cp.user_id = u.id
                 JOIN teams t ON cp.team_id = t.id
                 WHERE cp.contest_id = %s ORDER BY t.total_points DESC''', (contest_id,))
    participants = c.fetchall()
    conn.close()
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Leaderboard</title>
        <script src="https://cdn.tailwindcss.com"></script>
    </head>
    <body class="bg-gray-950 text-white font-sans p-4 pb-20">
        <div class="bg-indigo-600 p-3 rounded-xl flex items-center mb-4 shadow">
            <a href="/" class="mr-3 font-bold bg-indigo-700 px-2.5 py-1 rounded-lg text-xs">←</a>
            <h1 class="text-sm font-bold">{contest['name']} - Leaderboard</h1>
        </div>
        <div class="bg-gray-900 border border-gray-800 p-4 rounded-2xl">
    """
    if not participants:
        html += '<p class="text-xs text-gray-400 text-center py-4">Koi participant nahi hai abhi.</p>'
    for idx, p in enumerate(participants, 1):
        win_text = f" | Winnings: 🪙 {p['winnings']}" if p['winnings'] > 0 else ""
        html += f"""
        <div class="flex justify-between items-center bg-gray-800 p-3 rounded-xl mb-2 text-xs border border-gray-700">
            <div>
                <span class="font-bold text-amber-400">#{idx}</span> <span class="font-bold">{p['username']}</span>
                <p class="text-[10px] text-gray-400">Team: {p['team_name']}{win_text}</p>
            </div>
            <div class="text-right font-bold text-emerald-400">
                {p['total_points']} pts
            </div>
        </div>
        """
    html += """
        </div>
    </body>
    </html>
    """
    return render_template_string(html)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
