from flask import Flask, render_template_string, request, redirect, url_for, session
import sqlite3
import os
import shutil
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'cricxabhi_permanent_data_2026'
DB_NAME = 'fantasy_master.db'
BACKUP_DB = 'backup_fantasy_master.db'

def init_db():
    # Agar main db gayab ho gaya hai par backup pada hai, toh backup se restore kar lo
    if not os.path.exists(DB_NAME) and os.path.exists(BACKUP_DB):
        shutil.copyfile(BACKUP_DB, DB_NAME)
        
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
    
    # Har baar start hone par backup save kar lo
    if os.path.exists(DB_NAME):
        shutil.copyfile(DB_NAME, BACKUP_DB)

init_db()

def save_backup():
    if os.path.exists(DB_NAME):
        shutil.copyfile(DB_NAME, BACKUP_DB)

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
            conn = sqlite3.connect(DB_NAME)
            c = conn.cursor()
            try:
                c.execute('INSERT INTO users (username, password, coins) VALUES (?, ?, 0)', (username, password))
                conn.commit()
                conn.close()
                save_backup()
                return redirect(url_for('login'))
            except sqlite3.IntegrityError:
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
                save_backup()
                msg = f"Successfully sent {amt} coins to {target_name}!"
            else:
                msg = "❌ Target user not found!"
        else:
            msg = "❌ Insufficient coins!"
    user = c.execute('SELECT * FROM users WHERE id = ?', (session['user_id'],)).fetchone()
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
    
    is_live = (match['status'] != 'Upcoming')
    if match['status'] == 'Upcoming':
        try:
            m_time = datetime.strptime(match['match_time'], '%Y-%m-%dT%H:%M')
            if datetime.now() >= m_time:
                is_live = True
        except:
            pass

    contest_data = []
    for con in contests:
        participants = c.execute('SELECT users.username, teams.team_name, contest_participants.rank, contest_participants.winnings FROM contest_participants JOIN users ON contest_participants.user_id = users.id JOIN teams ON contest_participants.team_id = teams.id WHERE contest_participants.contest_id = ? ORDER BY contest_participants.rank ASC', (con['id'],)).fetchall()
        contest_data.append({'contest': con, 'participants': participants})

    all_teams = []
    if is_live:
        all_teams = c.execute('SELECT teams.*, users.username FROM teams JOIN users ON teams.user_id = users.id WHERE teams.match_id = ? ORDER BY teams.total_points DESC', (match_id,)).fetchall()
    conn.close()
    
    page = '<!DOCTYPE html><html><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>Match Detail</title><script src="https://cdn.tailwindcss.com"></script></head>'
    page += '<body class="bg-gray-950 text-white font-sans p-4 pb-20"><div class="bg-indigo-600 p-3 rounded-xl flex items-center mb-4 shadow"><a href="/" class="mr-3 font-bold bg-indigo-700 px-2.5 py-1 rounded-lg text-xs">←</a><h1 class="text-sm font-bold">' + match['team1'] + ' vs ' + match['team2'] + '</h1></div>'
    page += '<div class="bg-gray-900 border border-indigo-500 p-3 rounded-2xl mb-4"><h3 class="font-bold text-indigo-300 text-xs mb-2">🔒 My Created Teams</h3>'
    if not my_teams:
        page += '<p class="text-[11px] text-gray-400 mb-2">Pehle apni team banayein!</p>'
    for t in my_teams:
        page += '<div class="bg-gray-800 p-2.5 rounded-xl mb-2 text-xs border border-gray-700"><div class="flex justify-between font-bold text-emerald-400 mb-1"><span>' + t['team_name'] + '</span><span>Score: ' + str(t['total_points']) + ' pts</span></div>'
        page += '<div class="text-gray-300 text-[11px] mb-1">⭐ C: <b>' + t['captain'] + ' (2x)</b> | 🌟 VC: <b>' + t['vice_captain'] + ' (1.5x)</b></div><div class="text-gray-400 text-[10px] mb-2">Players: ' + t['players'] + '</div>'
        page += '<div class="flex gap-2 mt-2">'
        if not is_live:
            page += '<a href="/create_team/' + str(match['id']) + '?edit=' + str(t['id']) + '" class="bg-amber-500 text-black font-bold px-2.5 py-1 rounded text-[10px]">✏️ Edit Lineup</a>'
        else:
            page += '<a href="/show_team/' + str(t['id']) + '" class="bg-cyan-500 text-black font-bold px-2.5 py-1 rounded text-[10px]">👁️ Show Your Team</a>'
        page += '</div></div>'
    if not is_live:
        page += '<a href="/create_team/' + str(match['id']) + '" class="block text-center bg-indigo-600 py-2 rounded-xl font-bold text-xs mt-2">+ Create New Team</a>'
    page += '</div>'

    if is_live:
        page += '<div class="bg-gray-900 border border-amber-500 p-3 rounded-2xl mb-4"><h3 class="font-bold text-amber-400 text-xs mb-2">🔓 Live Leaderboard & Public Teams</h3>'
        for idx, t in enumerate(all_teams):
            page += '<div class="bg-gray-800 p-2.5 rounded-xl mb-2 text-xs border border-gray-700"><div class="flex justify-between font-bold mb-1"><span class="text-indigo-300">Rank #' + str(idx+1) + ' - ' + t['team_name'] + ' (' + t['username'] + ')</span><span class="text-amber-400">⚡ ' + str(t['total_points']) + ' Pts</span></div>'
            page += '<div class="text-gray-300 text-[11px] mb-1">⭐ C: ' + t['captain'] + ' | 🌟 VC: ' + t['vice_captain'] + '</div><div class="text-gray-400 text-[10px]">Players: ' + t['players'] + '</div></div>'
        page += '</div>'

    page += '<h3 class="text-xs font-bold mb-2 text-gray-300">Contests & Prize Breakup</h3>'
    for item in contest_data:
        con = item['contest']
        parts = item['participants']
        page += '<div class="bg-gray-900 border border-gray-800 p-3 rounded-2xl mb-3"><div class="flex justify-between font-bold text-xs mb-1"><span>' + con['name'] + '</span><span class="text-emerald-400">🪙 Prize: ' + str(con['prize_pool']) + '</span></div>'
        page += '<p class="text-[10px] text-gray-400 mb-1">Entry Fee: 🪙 ' + str(con['entry_fee']) + ' | Spots: ' + str(len(parts)) + '/' + str(con['spots']) + '</p>'
        page += '<p class="text-[10px] text-amber-300 mb-2">🎁 Prize Breakup: ' + con['prize_breakup'] + '</p>'
        page += '<div class="bg-gray-950 p-2 rounded-xl mb-2 text-[11px]"><span class="text-indigo-400 font-bold">Joined Users Live Ranks & Winnings:</span><ul class="list-disc pl-4 mt-1 text-gray-300">'
        for idx, p in enumerate(parts):
            win_str = ' | Won: 🪙 <b>' + str(p['winnings']) + '</b>' if p['winnings'] else ''
            page += '<li><b>' + p['username'] + '</b> (Team: ' + p['team_name'] + ') ➔ Rank: <b>#' + str(idx+1) + '</b>' + win_str + '</li>'
        page += '</ul></div>'

        if len(parts) >= con['spots']:
            page += '<div class="text-center bg-rose-900 text-rose-200 py-1.5 rounded font-bold text-xs">Contest Full ❌</div>'
        elif not is_live:
            page += '<form action="/join_contest/' + str(con['id']) + '" method="POST" class="flex gap-2"><select name="team_id" required class
