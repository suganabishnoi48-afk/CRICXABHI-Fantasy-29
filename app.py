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
        user="postgres",
        password="@Abhishek.2929",
        host="db.yhbrlylvimbjazdirqiq.supabase.co",
        port="5432",
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
        
    # Admin actions handling
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

    c.execute('SELECT * FROM matches')
    matches = c.fetchall()
    c.execute('SELECT * FROM players')
    players = c.fetchall()
    conn.close()
    
    page = '<!DOCTYPE html><html><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>CRICXABHI Fantasy</title><script src="https://cdn.tailwindcss.com"></script></head>'
    page += '<body class="bg-gray-950 text-white font-sans p-4 pb-20">'
    page += '<div class="bg-indigo-600 p-4 rounded-2xl flex justify-between items-center shadow-lg mb-4"><div><h1 class="font-bold text-base">CRICXABHI Fantasy 🏏</h1><p class="text-xs text-indigo-200">Hi, <b>' + user['username'] + '</b></p></div>'
    page += '<div class="flex gap-2 items-center"><span class="bg-indigo-900 px-3 py-1 rounded-full text-xs font-bold">🪙 ' + str(user['coins']) + '</span><a href="/wallet" class="bg-amber-500 text-black px-2.5 py-1 rounded-xl font-bold text-xs">Share Coin</a><a href="/logout" class="bg-rose-600 px-2.5 py-1 rounded-xl font-bold text-xs">Logout</a></div></div>'
    page += '<h2 class="text-sm font-bold mb-3 text-gray-300">Upcoming & Live Matches</h2>'
    
    for m in matches:
        badge = '<span class="text-xs bg-emerald-400 text-black px-2.5 py-1 rounded-full uppercase">' + m['status'] + '</span>'
        if m['status'] == 'Live':
            badge = '<span class="text-xs bg-amber-400 text-black animate-pulse px-2.5 py-1 rounded-full uppercase">Live</span>'
        elif m['status'] == 'Completed':
            badge = '<span class="text-xs bg-rose-500 text-white px-2.5 py-1 rounded-full uppercase">Completed</span>'
            
        page += '<div class="bg-gray-900 border border-gray-800 p-4 rounded-2xl mb-3 shadow"><div class="flex justify-between font-bold text-base mb-1"><span>' + m['team1'] + ' vs ' + m['team2'] + '</span>' + badge + '</div>'
        page += '<div class="text-xs text-amber-300 mb-3 font-mono" id="timer-' + str(m['id']) + '">🕒 Timer Loading...</div>'
        page += '<script>(function() { const matchTime = new Date("' + str(m['match_time']) + '").getTime(); const timerElem = document.getElementById("timer-' + str(m['id']) + '"); const status = "' + m['status'] + '"; if(status === "Completed") { timerElem.innerHTML = "🏁 Match Completed"; return; } if(status === "Live") { timerElem.innerHTML = "🔴 Match is LIVE NOW!"; return; } const x = setInterval(function() { const now = new Date().getTime(); const dist = matchTime - now; if (dist < 0) { clearInterval(x); timerElem.innerHTML = "🔴 Match Started / Live"; } else { const d = Math.floor(dist / (1000 * 60 * 60 * 24)); const h = Math.floor((dist % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60)); const mi = Math.floor((dist % (1000 * 60 * 60)) / (1000 * 60)); const s = Math.floor((dist % (1000 * 60)) / 1000); timerElem.innerHTML = "⏳ Starts in: " + d + "d " + h + "h " + mi + "m " + s + "s"; } }, 1000); })();</script>'
        page += '<a href="/match/' + str(m['id']) + '" class="block text-center bg-indigo-600 py-2.5 rounded-xl font-bold text-xs shadow">View Contests & Teams</a></div>'
    
    if session.get('is_admin'):
        page += '<div class="mt-6 border-t border-gray-800 pt-4">'
        page += '<h2 class="text-lg font-bold text-amber-400 mb-3">Admin Panel</h2>'
        
        # 1. Add Match
        page += '<form method="POST" class="bg-gray-900 border border-gray-800 p-3 rounded-2xl mb-3"><input type="hidden" name="action" value="match"><h3 class="font-bold mb-2 text-indigo-300 text-xs">1. Add Match</h3><input type="text" name="t1" placeholder="Team 1" required class="w-full bg-gray-800 p-2.5 rounded-xl mb-2 text-xs text-white"><input type="text" name="t2" placeholder="Team 2" required class="w-full bg-gray-800 p-2.5 rounded-xl mb-2 text-xs text-white"><input type="datetime-local" name="time" required class="w-full bg-gray-800 p-2.5 rounded-xl mb-2 text-xs text-white"><button class="w-full bg-indigo-600 py-2.5 rounded-xl font-bold text-xs">Add Match</button></form>'
        
        # 2. Add Player
        page += '<form method="POST" class="bg-gray-900 border border-gray-800 p-3 rounded-2xl mb-3"><input type="hidden" name="action" value="player"><h3 class="font-bold mb-2 text-indigo-300 text-xs">2. Add Player</h3><select name="match_id" class="w-full bg-gray-800 p-2.5 rounded-xl mb-2 text-xs text-white">'
        for m in matches:
            page += '<option value="' + str(m['id']) + '">' + m['team1'] + ' vs ' + m['team2'] + '</option>'
        page += '</select><input type="text" name="p_name" placeholder="Player Name" required class="w-full bg-gray-800 p-2.5 rounded-xl mb-2 text-xs text-white"><input type="text" name="p_team" placeholder="Team Code" required class="w-full bg-gray-800 p-2.5 rounded-xl mb-2 text-xs text-white"><select name="p_role" class="w-full bg-gray-800 p-2.5 rounded-xl mb-2 text-xs text-white"><option value="Batsman">Batsman</option><option value="Bowler">Bowler</option><option value="All-Rounder">All-Rounder</option><option value="WK">WK</option></select><button class="w-full bg-emerald-600 py-2.5 rounded-xl font-bold text-xs">Add Player</button></form>'
        
        # 3. Create Contest
        page += '<form method="POST" class="bg-gray-900 border border-gray-800 p-3 rounded-2xl mb-3"><input type="hidden" name="action" value="contest"><h3 class="font-bold mb-2 text-indigo-300 text-xs">3. Create Contest</h3><select name="match_id" class="w-full bg-gray-800 p-2.5 rounded-xl mb-2 text-xs text-white">'
        for m in matches:
            page += '<option value="' + str(m['id']) + '">' + m['team1'] + ' vs ' + m['team2'] + '</option>'
        page += '</select><input type="text" name="c_name" placeholder="Contest Name" required class="w-full bg-gray-800 p-2.5 rounded-xl mb-2 text-xs text-white"><input type="number" name="prize" placeholder="Total Prize Pool" required class="w-full bg-gray-800 p-2.5 rounded-xl mb-2 text-xs text-white"><input type="number" name="fee" placeholder="Entry Fee" required class="w-full bg-gray-800 p-2.5 rounded-xl mb-2 text-xs text-white"><input type="number" name="spots" placeholder="Total Spots" required class="w-full bg-gray-800 p-2.5 rounded-xl mb-2 text-xs text-white"><input type="text" name="breakup" placeholder="Breakup e.g. 1-5: 200" required class="w-full bg-gray-800 p-2.5 rounded-xl mb-2 text-xs text-white"><button class="w-full bg-indigo-600 py-2.5 rounded-xl font-bold text-xs">Create Contest</button></form>'
        
        # 5. Status Control
        page += '<form method="POST" class="bg-gray-900 border border-gray-800 p-3 rounded-2xl"><input type="hidden" name="action" value="update_status"><h3 class="font-bold mb-2 text-indigo-300 text-xs">5. Match Status Control</h3><select name="match_id" class="w-full bg-gray-800 p-2.5 rounded-xl mb-2 text-xs text-white">'
        for m in matches:
            page += '<option value="' + str(m['id']) + '">' + m['team1'] + ' vs ' + m['team2'] + ' (Current: ' + m['status'] + ')</option>'
        page += '</select><select name="status" class="w-full bg-gray-800 p-2.5 rounded-xl mb-2 text-xs text-white"><option value="Upcoming">Upcoming</option><option value="Live">Live</option><option value="Completed">Completed</option></select><button class="w-full bg-amber-500 text-black py-2.5 rounded-xl font-bold text-xs">Update Status</button></form>'
        page += '</div>'

    page += '</body></html>'
    return render_template_string(page)

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
    
    page = '<!DOCTYPE html><html><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>Login</title><script src="https://cdn.tailwindcss.com"></script></head>'
    page += '<body class="bg-gray-950 text-white font-sans p-6 flex items-center justify-center h-screen"><div class="bg-gray-900 border border-gray-800 p-6 rounded-2xl max-w-sm w-full shadow-2xl">'
    page += '<h2 class="text-base font-bold text-indigo-400 mb-4 text-center">🏏 CRICXABHI Login</h2>'
    if error:
        page += '<div class="bg-rose-900 text-rose-200 p-2.5 rounded-xl mb-3 text-xs font-bold text-center">' + error + '</div>'
    page += '<form method="POST" class="space-y-3"><div><label class="text-xs text-gray-400 block mb-1">Select Login Type</label><select name="login_type" id="loginType" onchange="toggleAdmin()" class="w-full bg-gray-800 border border-gray-700 p-2.5 rounded-xl text-xs text-white"><option value="user">User ID Login</option><option value="admin">Admin ID Login</option></select></div>'
    page += '<div><label class="text-xs text-gray-400 block mb-1" id="labelName">Username</label><input type="text" name="username" placeholder="Enter username..." required class="w-full bg-gray-800 border border-gray-700 p-2.5 rounded-xl text-xs text-white"></div>'
    page += '<div><label class="text-xs text-gray-400 block mb-1">Password</label><input type="password" name="password" placeholder="Enter password..." required class="w-full bg-gray-800 border border-gray-700 p-2.5 rounded-xl text-xs text-white"></div>'
    page += '<button type="submit" class="w-full bg-indigo-600 py-3 rounded-xl font-bold text-xs shadow">Login</button></form>'
    page += '<div class="text-center mt-4 text-xs text-gray-400">Don\'t have an account? <a href="/register" class="text-emerald-400 font-bold">Register here</a></div></div>'
    page += '<script>function toggleAdmin() { let val = document.getElementById("loginType").value; let lbl = document.getElementById("labelName"); if(val === "admin") { lbl.innerText = "Admin ID (AbhiAdmin)"; } else { lbl.innerText = "Username"; } }</script></body></html>'
    return render_template_string(page)

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
    
    page = '<!DOCTYPE html><html><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>Register</title><script src="https://cdn.tailwindcss.com"></script></head>'
    page += '<body class="bg-gray-950 text-white font-sans p-6 flex items-center justify-center h-screen"><div class="bg-gray-900 border border-gray-800 p-6 rounded-2xl max-w-sm w-full shadow-2xl">'
    page += '<h2 class="text-base font-bold text-emerald-400 mb-2 text-center">📝 New User Registration</h2>'
    if error:
        page += '<div class="bg-rose-900 text-rose-200 p-2.5 rounded-xl mb-3 text-xs font-bold text-center">' + error + '</div>'
    page += '<form method="POST" class="space-y-3"><input type="text" name="username" placeholder="Choose unique username..." required class="w-full bg-gray-800 border border-gray-700 p-2.5 rounded-xl text-xs text-white">'
    page += '<input type="password" name="password" placeholder="Create secure password..." required class="w-full bg-gray-800 border border-gray-700 p-2.5 rounded-xl text-xs text-white">'
    page += '<button type="submit" class="w-full bg-emerald-600 py-3 rounded-xl font-bold text-xs shadow">Register Now</button></form>'
    page += '<div class="text-center mt-4 text-xs text-gray-400">Already registered? <a href="/login" class="text-indigo-400 font-bold">Login here</a></div></div></body></html>'
    return render_template_string(page)

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
    
    page = '<!DOCTYPE html><html><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>Share Coin</title><script src="https://cdn.tailwindcss.com"></script></head>'
    page += '<body class="bg-gray-950 text-white font-sans p-4 pb-20"><div class="bg-indigo-600 p-3 rounded-xl flex items-center mb-4 shadow"><a href="/" class="mr-3 font-bold bg-indigo-700 px-2.5 py-1 rounded-lg text-xs">←</a><h1 class="text-sm font-bold">🪙 Share Coin</h1></div>'
    page += '<div class="bg-gray-900 border border-gray-800 p-4 rounded-2xl mb-4"><p class="text-xs text-gray-300 mb-2">My Balance: <b>🪙 ' + str(user['coins']) + ' coins</b></p>'
    if msg:
        page += '<div class="bg-indigo-950 text-indigo-200 p-2.5 rounded-xl mb-3 text-xs font-bold">' + msg + '</div>'
    page += '<form method="POST" class="space-y-3"><input type="text" name="target_username" placeholder="Rec
