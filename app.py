from flask import Flask, render_template_string, request, redirect, url_for, session
import sqlite3

app = Flask(__name__)
app.secret_key = 'cricxabhi_safe_key_2026'
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
    
    page = '<!DOCTYPE html><html><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>CRICXABHI Fantasy</title><script src="https://cdn.tailwindcss.com"></script></head>'
    page += '<body class="bg-gray-950 text-white font-sans p-4 pb-20">'
    page += '<div class="bg-indigo-600 p-4 rounded-2xl flex justify-between items-center shadow-lg mb-4"><div><h1 class="font-bold text-base">CRICXABHI Fantasy 🏏</h1><p class="text-xs text-indigo-200">Hi, <b>' + user['username'] + '</b></p></div><div class="flex gap-2 items-center"><span class="bg-indigo-900 px-3 py-1 rounded-full text-xs font-bold">🪙 ' + str(user['coins']) + '</span><a href="/admin" class="bg-emerald-500 text-black px-3 py-1 rounded-xl font-bold text-xs shadow">Admin</a></div></div>'
    page += '<div class="bg-gray-900 p-4 rounded-2xl mb-4 border border-gray-800"><h3 class="text-xs font-semibold text-gray-300 mb-2">Login / Switch Account</h3><form method="POST" class="flex gap-2"><input type="text" name="username" placeholder="Enter name..." required class="bg-gray-800 border border-gray-700 p-2.5 rounded-xl text-xs w-full text-white"><button class="bg-indigo-600 px-4 py-2.5 rounded-xl text-xs font-bold">Go</button></form></div>'
    page += '<h2 class="text-sm font-bold mb-3 text-gray-300">Upcoming & Live Matches</h2>'
    for m in matches:
        page += '<div class="bg-gray-900 border border-gray-800 p-4 rounded-2xl mb-3 shadow"><div class="flex justify-between font-bold text-base mb-1"><span>' + m['team1'] + ' vs ' + m['team2'] + '</span><span class="text-xs bg-emerald-400 text-black px-2.5 py-1 rounded-full uppercase">' + m['status'] + '</span></div>'
        page += '<a href="/match/' + str(m['id']) + '" class="block text-center bg-indigo-600 py-2.5 rounded-xl font-bold text-xs shadow mt-2">View Contests & Teams</a></div>'
    page += '</body></html>'
    return render_template_string(page)

@app.route('/match/<int:match_id>')
def match_detail(match_id):
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    user_id = session.get('user_id', 1)
    user = c.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()
    match = c.execute('SELECT * FROM matches WHERE id = ?', (match_id,)).fetchone()
    contests = c.execute('SELECT * FROM contests WHERE match_id = ?', (match_id,)).fetchall()
    my_teams = c.execute('SELECT * FROM teams WHERE match_id = ? AND user_id = ?', (match_id, user['id'])).fetchall()
    conn.close()
    
    page = '<!DOCTYPE html><html><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>Match Detail</title><script src="https://cdn.tailwindcss.com"></script></head>'
    page += '<body class="bg-gray-950 text-white font-sans p-4 pb-20"><div class="bg-indigo-600 p-3 rounded-xl flex items-center mb-4 shadow"><a href="/" class="mr-3 font-bold bg-indigo-700 px-2.5 py-1 rounded-lg text-xs">←</a><h1 class="text-sm font-bold">' + match['team1'] + ' vs ' + match['team2'] + '</h1></div>'
    page += '<a href="/create_team/' + str(match['id']) + '" class="block text-center bg-indigo-600 py-2 rounded-xl font-bold text-xs mb-4">+ Create New Team</a></body></html>'
    return render_template_string(page)

@app.route('/admin', methods=['GET', 'POST'])
def admin():
    if session.get('is_admin'):
        conn = sqlite3.connect(DB_NAME)
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        if request.method == 'POST':
            c.execute('INSERT INTO matches (team1, team2, match_time, status) VALUES (?, ?, ?, "Upcoming")', (request.form.get('t1'), request.form.get('t2'), request.form.get('time')))
            conn.commit()
        matches = c.execute('SELECT * FROM matches').fetchall()
        conn.close()
        
        page = '<!DOCTYPE html><html><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>Admin Panel</title><script src="https://cdn.tailwindcss.com"></script></head>'
        page += '<body class="bg-gray-950 text-white font-sans p-4 pb-20"><h1 class="text-sm font-bold text-emerald-400 mb-4">👑 Admin Panel</h1><a href="/" class="text-indigo-400 text-xs bg-indigo-950 px-3 py-1 rounded-lg mb-4 inline-block">Home</a>'
        page += '<form method="POST" class="bg-gray-900 border border-gray-800 p-3 rounded-2xl mb-3"><h3 class="font-bold mb-2 text-indigo-300 text-xs">Add Match</h3>'
        page += '<input type="text" name="t1" placeholder="Team 1" required class="w-full bg-gray-800 p-2.5 rounded-xl mb-2 text-xs text-white">'
        page += '<input type="text" name="t2" placeholder="Team 2" required class="w-full bg-gray-800 p-2.5 rounded-xl mb-2 text-xs text-white">'
        page += '<input type="text" name="time" placeholder="Time" required class="w-full bg-gray-800 p-2.5 rounded-xl mb-2 text-xs text-white">'
        page += '<button class="w-full bg-indigo-600 py-2.5 rounded-xl font-bold text-xs">Add Match</button></form></body></html>'
        return render_template_string(page)

    if request.method == 'POST':
        if request.form.get('admin_pass') == '29022008':
            session['is_admin'] = True
            return redirect(url_for('admin'))

    return render_template_string('<!DOCTYPE html><html><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>Admin Login</title><script src="https://cdn.tailwindcss.com"></script></head><body class="bg-gray-950 text-white font-sans p-6 flex items-center justify-center h-screen"><div class="bg-gray-900 border border-gray-800 p-6 rounded-2xl max-w-sm w-full shadow-2xl"><h2 class="text-base font-bold text-emerald-400 mb-4 text-center">🔐 Admin Password Required</h2><form method="POST"><input type="password" name="admin_pass" placeholder="Enter Password..." required class="w-full bg-gray-800 border border-gray-700 p-3 rounded-xl mb-4 text-xs text-white focus:outline-none"><button type="submit" class="w-full bg-emerald-600 py-3 rounded-xl font-bold text-xs shadow">Login</button></form></div></body></html>')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
    
