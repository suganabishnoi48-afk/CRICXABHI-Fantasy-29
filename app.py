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
    
    c.execute('SELECT COUNT(*) FROM users WHERE username = %s', ('AbhiAdmin',))
    if c.fetchone()['count'] == 0:
        c.execute('INSERT INTO users (username, password, coins) VALUES (%s, %s, %s)', ('AbhiAdmin', '29022008', 100000))
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
    
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('SELECT * FROM users WHERE id = %s', (session['user_id'],))
    user = c.fetchone()
    if not user:
        session.clear()
        conn.close()
        return redirect(url_for('login'))
        
    c.execute('SELECT * FROM matches')
    matches = c.fetchall()
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
    page += '<h2 class="text-base font-bold text-emerald-400 mb-2 text-center">📝 New User Registration</h2><p class="text-[11px] text-gray-400 mb-4 text-center">Signup bonus: <b>0 Coins</b></p>'
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
    page += '<form method="POST" class="space-y-3"><input type="text" name="target_username" placeholder="Recipient Username (e.g. AbhiAdmin)..." required class="w-full bg-gray-800 border border-gray-700 p-2.5 rounded-xl text-xs text-white">'
    page += '<input type="number" name="amount" placeholder="Coin Amount..." min="1" required class="w-full bg-gray-800 border border-gray-700 p-2.5 rounded-xl text-xs text-white">'
    page += '<button type="submit" class="w-full bg-emerald-600 py-3 rounded-xl font-bold text-xs shadow">Transfer Coins</button></form></div></body></html>'
    return render_template_string(page)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
    
