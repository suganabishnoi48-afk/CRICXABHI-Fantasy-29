from flask import Flask, render_template_string, request, redirect, url_for, session
import sqlite3

app = Flask(__name__)
app.secret_key = 'cricxabhi_perfect_app_2026'
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

@app.route('/')
def index():
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
    
    contest_data = []
    for con in contests:
        participants = c.execute('SELECT users.username, teams.team_name FROM contest_participants JOIN users ON contest_participants.user_id = users.id JOIN teams ON contest_participants.team_id = teams.id WHERE contest_participants.contest_id = ?', (con['id'],)).fetchall()
        contest_data.append({'contest': con, 'participants': participants})
    conn.close()
    
    page = '<!DOCTYPE html><html><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>Match Detail</title><script src="https://cdn.tailwindcss.com"></script></head>'
    page += '<body class="bg-gray-950 text-white font-sans p-4 pb-20"><div class="bg-indigo-600 p-3 rounded-xl flex items-center mb-4 shadow"><a href="/" class="mr-3 font-bold bg-indigo-700 px-2.5 py-1 rounded-lg text-xs">←</a><h1 class="text-sm font-bold">' + match['team1'] + ' vs ' + match['team2'] + '</h1></div>'
    page += '<a href="/create_team/' + str(match['id']) + '" class="block text-center bg-indigo-600 py-2 rounded-xl font-bold text-xs mb-4">+ Create New Team</a>'
    
    for item in contest_data:
        con = item['contest']
        parts = item['participants']
        page += '<div class="bg-gray-900 border border-gray-800 p-3 rounded-2xl mb-3"><div class="flex justify-between font-bold text-xs mb-1"><span>' + con['name'] + '</span><span class="text-emerald-400">🪙 Prize: ' + str(con['prize_pool']) + '</span></div>'
        page += '<p class="text-[10px] text-gray-400 mb-2">Entry Fee: 🪙 ' + str(con['entry_fee']) + ' | Spots: ' + str(len(parts)) + '/' + str(con['spots']) + '</p>'
        page += '<form action="/join_contest/' + str(con['id']) + '" method="POST" class="flex gap-2"><select name="team_id" required class="bg-gray-800 p-1.5 rounded text-xs w-full text-white border border-gray-700"><option value="">Apni Team Select Karein</option>'
        for t in my_teams:
            page += '<option value="' + str(t['id']) + '">' + t['team_name'] + '</option>'
        page += '</select><button type="submit" class="bg-emerald-600 px-4 py-1.5 rounded font-bold text-xs shrink-0">Join</button></form></div>'
    page += '</body></html>'
    return render_template_string(page)

@app.route('/create_team/<int:match_id>', methods=['GET', 'POST'])
def create_team(match_id):
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    user_id = session.get('user_id', 1)
    if request.method == 'POST':
        t_name = request.form.get('team_name')
        capt = request.form.get('captain')
        v_capt = request.form.get('vice_captain')
        plrs = request.form.getlist('players')
        if len(plrs) != 11:
            conn.close()
            return "Error: Exact 11 players select karne honge! <a href='javascript:history.back()'>Go Back</a>"
        p_str = ",".join(plrs)
        c.execute('INSERT INTO teams (match_id, user_id, team_name, captain, vice_captain, players) VALUES (?, ?, ?, ?, ?, ?)', (match_id, user_id, t_name, capt, v_capt, p_str))
        conn.commit()
        conn.close()
        return redirect(url_for('match_detail', match_id=match_id))
    players = c.execute('SELECT * FROM players WHERE match_id = ?', (match_id,)).fetchall()
    conn.close()
    
    page = '<!DOCTYPE html><html><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>Create Team</title><script src="https://cdn.tailwindcss.com"></script></head>'
    page += '<body class="bg-gray-950 text-white font-sans p-4 pb-20"><div class="bg-indigo-600 p-3 rounded-xl mb-4"><h1 class="text-sm font-bold">Select 11 Players</h1></div>'
    page += '<form method="POST"><div class="mb-3"><input type="text" name="team_name" placeholder="Team Name" required class="w-full bg-gray-900 border border-gray-700 p-2.5 rounded-xl text-xs text-white"></div><div class="space-y-2 mb-4">'
    for p in players:
        page += '<label class="flex justify-between items-center bg-gray-900 border border-gray-800 p-2.5 rounded-xl text-xs"><div class="flex items-center gap-2"><input type="checkbox" name="players" value="' + p['name'] + '" class="accent-indigo-500"><span>' + p['name'] + ' (' + p['role'] + ')</span></div><div class="flex gap-2 text-[11px]"><label><input type="radio" name="captain" value="' + p['name'] + '" required> C</label><label><input type="radio" name="vice_captain" value="' + p['name'] + '" required> VC</label></div></label>'
    page += '</div><button class="w-full bg-emerald-600 py-3 rounded-xl font-bold text-xs shadow">Save Team</button></form></body></html>'
    return render_template_string(page)

@app.route('/join_contest/<int:contest_id>', methods=['POST'])
def join_contest(contest_id):
    user_id = session.get('user_id', 1)
    team_id = request.form.get('team_id')
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    contest = c.execute('SELECT * FROM contests WHERE id = ?', (contest_id,)).fetchone()
    user = c.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()
    if user['coins'] < contest['entry_fee']:
        conn.close()
        return "Not enough coins! <a href='javascript:history.back()'>Go Back</a>"
    c.execute('UPDATE users SET coins = coins - ? WHERE id = ?', (contest['entry_fee'], user_id))
    c.execute('INSERT INTO contest_participants (contest_id, user_id, team_id) VALUES (?, ?, ?)', (contest_id, user_id, team_id))
    conn.commit()
    match_id = contest['match_id']
    conn.close()
    return redirect(url_for('match_detail', match_id=match_id))

@app.route('/admin', methods=['GET', 'POST'])
def admin():
    if request.args.get('logout') == 'true':
        session.pop('is_admin', None)
        return redirect(url_for('index'))
        
    if session.get('is_admin'):
        conn = sqlite3.connect(DB_NAME)
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        if request.method == 'POST':
            action = request.form.get('action')
            if action == 'match':
                c.execute('INSERT INTO matches (team1, team2, match_time, status) VALUES (?, ?, ?, "Upcoming")', (request.form.get('t1'), request.form.get('t2'), request.form.get('time')))
            elif action == 'player':
                c.execute('INSERT INTO players (match_id, name, team, role) VALUES (?, ?, ?, ?)', (request.form.get('match_id'), request.form.get('p_name'), request.form.get('p_team'), request.form.get('p_role')))
            elif action == 'contest':
                c.execute('SELECT * FROM matches WHERE id = ?', (request.form.get('match_id'),))
                m_row = c.fetchone()
                c.execute('INSERT INTO contests (match_id, name, prize_pool, entry_fee, spots) VALUES (?, ?, ?, ?, ?)', (request.form.get('match_id'), request.form.get('c_name'), request.form.get('prize'), request.form.get('fee'), request.form.get('spots')))
            conn.commit()
        matches = c.execute('SELECT * FROM matches').fetchall()
        conn.close()
        
        page = '<!DOCTYPE html><html><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>Admin Panel</title><script src="https://cdn.tailwindcss.com"></script></head>'
        page += '<body class="bg-gray-950 text-white font-sans p-4 pb-20"><div class="flex justify-between items-center mb-4"><h1 class="text-sm font-bold text-emerald-400">👑 Admin Panel</h1><div class="flex gap-2"><a href="/" class="text-indigo-400 text-xs bg-indigo-950 px-3 py-1 rounded-lg">Home</a><a href="/admin?logout=true" class="text-rose-400 text-xs bg-rose-950 px-3 py-1 rounded-lg">Logout</a></div></div>'
        page += '<form method="POST" class="bg-gray-900 border border-gray-800 p-3 rounded-2xl mb-3"><input type="hidden" name="action" value="match"><h3 class="font-bold mb-2 text-indigo-300 text-xs">1. Add Match</h3><input type="text" name="t1" placeholder="Team 1" required class="w-full bg-gray-800 p-2.5 rounded-xl mb-2 text-xs text-white"><input type="text" name="t2" placeholder="Team 2" required class="w-full bg-gray-800 p-2.5 rounded-xl mb-2 text-xs text-white"><input type="text" name="time" placeholder="Time" required class="w-full bg-gray-800 p-2.5 rounded-xl mb-2 text-xs text-white"><button class="w-full bg-indigo-600 py-2.5 rounded-xl font-bold text-xs">Add Match</button></form>'
        
        page += '<form method="POST" class="bg-gray-900 border border-gray-800 p-3 rounded-2xl mb-3"><input type="hidden" name="action" value="player"><h3 class="font-bold mb-2 text-indigo-300 text-xs">2. Add Player</h3><select name="match_id" class="w-full bg-gray-800 p-2.5 rounded-xl mb-2 text-xs text-white">'
        for m in matches:
            page += '<option value="' + str(m['id']) + '">' + m['team1'] + ' vs ' + m['team2'] + '</option>'
        page += '</select><input type="text" name="p_name" placeholder="Player Name" required class="w-full bg-gray-800 p-2.5 rounded-xl mb-2 text-xs text-white"><input type="text" name="p_team" placeholder="Team Code" required class="w-full bg-gray-800 p-2.5 rounded-xl mb-2 text-xs text-white"><select name="p_role" class="w-full bg-gray-800 p-2.5 rounded-xl mb-2 text-xs text-white"><option value="Batsman">Batsman</option><option value="Bowler">Bowler</option><option value="All-Rounder">All-Rounder</option><option value="WK">WK</option></select><button class="w-full bg-emerald-600 py-2.5 rounded-xl font-bold text-xs">Add Player</button></form>'

        page += '<form method="POST" class="bg-gray-900 border border-gray-800 p-3 rounded-2xl mb-3"><input type="hidden" name="action" value="contest"><h3 class="font-bold mb-2 text-indigo-300 text-xs">3. Add Contest</h3><select name="match_id" class="w-full bg-gray-800 p-2.5 rounded-xl mb-2 text-xs text-white">'
        for m in matches:
            page += '<option value="' + str(m['id']) + '">' + m['team1'] + ' vs ' + m['team2'] + '</option>'
        page += '</select><input type="text" name="c_name" placeholder="Contest Name" required class="w-full bg-gray-800 p-2.5 rounded-xl mb-2 text-xs text-white"><input type="number" name="prize" placeholder="Prize Pool" required class="w-full bg-gray-800 p-2.5 rounded-xl mb-2 text-xs text-white"><input type="number" name="fee" placeholder="Entry Fee" required class="w-full bg-gray-800 p-2.5 rounded-xl mb-2 text-xs text-white"><input type="number" name="spots" placeholder="Spots" required class="w-full bg-gray-800 p-2.5 rounded-xl mb-2 text-xs text-white"><button class="w-full bg-indigo-600 py-2.5 rounded-xl font-bold text-xs">Create Contest</button></form>'
        page += '</body></html>'
        return render_template_string(page)

    if request.method == 'POST':
        if request.form.get('admin_pass') == '29022008':
            session['is_admin'] = True
            return redirect(url_for('admin'))

    return render_template_string('<!DOCTYPE html><html><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>Admin Login</title><script src="https://cdn.tailwindcss.com"></script></head><body class="bg-gray-950 text-white font-sans p-6 flex items-center justify-center h-screen"><div class="bg-gray-900 border border-gray-800 p-6 rounded-2xl max-w-sm w-full shadow-2xl"><h2 class="text-base font-bold text-emerald-400 mb-4 text-center">🔐 Admin Password Required</h2><form method="POST"><input type="password" name="admin_pass" placeholder="Enter Password..." required class="w-full bg-gray-800 border border-gray-700 p-3 rounded-xl mb-4 text-xs text-white focus:outline-none"><button type="submit" class="w-full bg-emerald-600 py-3 rounded-xl font-bold text-xs shadow">Login</button></form><div class="text-center mt-3"><a href="/" class="text-indigo-400 text-xs">← Back to Home</a></div></div></body></html>')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
                                 
