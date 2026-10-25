from flask import Flask, render_template, request, redirect, url_for, session
import sqlite3

app = Flask(__name__)
app.secret_key = 'cricxabhi_clean_app_key_2026'
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
    
    return render_template('index.html', user=user, matches=matches)

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

    all_teams = []
    if match['status'] in ['Live', 'Completed']:
        all_teams = c.execute('SELECT teams.*, users.username FROM teams JOIN users ON teams.user_id = users.id WHERE teams.match_id = ?', (match_id,)).fetchall()
    conn.close()
    
    # Inline HTML for match detail to prevent template separation issues
    page = '<!DOCTYPE html><html lang="hi"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>Match Detail</title><script src="https://cdn.tailwindcss.com"></script></head>'
    page += '<body class="bg-gray-950 text-white font-sans p-4 pb-20">'
    page += '<div class="bg-indigo-600 p-3 rounded-xl flex items-center mb-4 shadow"><a href="/" class="mr-3 font-bold bg-indigo-700 px-2.5 py-1 rounded-lg text-xs">←</a><h1 class="text-sm font-bold">' + match['team1'] + ' vs ' + match['team2'] + '</h1></div>'
    
    page += '<div class="bg-gray-900 border border-indigo-500 p-3 rounded-2xl mb-4"><h3 class="font-bold text-indigo-300 text-xs mb-2">🔒 My Created Teams</h3>'
    if not my_teams:
        page += '<p class="text-[11px] text-gray-400 mb-2">Pehle apni team banayein!</p>'
    for t in my_teams:
        page += '<div class="bg-gray-800 p-2.5 rounded-xl mb-2 text-xs border border-gray-700"><div class="font-bold text-emerald-400 mb-1">' + t['team_name'] + '</div>'
        page += '<div class="text-gray-300 text-[11px] mb-1">⭐ C: <b>' + t['captain'] + '</b> | 🌟 VC: <b>' + t['vice_captain'] + '</b></div>'
        page += '<div class="text-gray-400 text-[10px] mb-2">Players: ' + t['players'] + '</div>'
        if match['status'] == 'Upcoming':
            page += '<a href="/create_team/' + str(match['id']) + '?edit=' + str(t['id']) + '" class="bg-amber-500 text-black font-bold px-2.5 py-1 rounded text-[10px]">✏️ Edit Lineup</a>'
        page += '</div>'
    page += '<a href="/create_team/' + str(match['id']) + '" class="block text-center bg-indigo-600 py-2 rounded-xl font-bold text-xs mt-2">+ Create New Team</a></div>'

    if match['status'] in ['Live', 'Completed']:
        page += '<div class="bg-gray-900 border border-amber-500 p-3 rounded-2xl mb-4"><h3 class="font-bold text-amber-400 text-xs mb-2">🔓 All Users Public Teams</h3>'
        for t in all_teams:
            page += '<div class="bg-gray-800 p-2.5 rounded-xl mb-2 text-xs border border-gray-700"><div class="flex justify-between font-bold mb-1"><span class="text-indigo-300">' + t['team_name'] + '</span><span class="text-gray-400 text-[10px]">By: ' + t['username'] + '</span></div>'
            page += '<div class="text-gray-300 text-[11px] mb-1">⭐ C: ' + t['captain'] + ' | 🌟 VC: ' + t['vice_captain'] + '</div>'
            page += '<div class="text-gray-400 text-[10px]">Players: ' + t['players'] + '</div></div>'
        page += '</div>'

    page += '<h3 class="text-xs font-bold mb-2 text-gray-300">Contests & Joined Participants</h3>'
    for item in contest_data:
        con = item['contest']
        parts = item['participants']
        page += '<div class="bg-gray-900 border border-gray-800 p-3 rounded-2xl mb-3"><div class="flex justify-between font-bold text-xs mb-1"><span>' + con['name'] + '</span><span class="text-emerald-400">🪙 Prize: ' + str(con['prize_pool']) + '</span></div>'
        page += '<p class="text-[10px] text-gray-400 mb-2">Entry Fee: 🪙 ' + str(con['entry_fee']) + ' | Spots: ' + str(len(parts)) + '/' + str(con['spots']) + '</p>'
        page += '<div class="bg-gray-950 p-2 rounded-xl mb-2 text-[11px]"><span class="text-amber-400 font-bold">Joined Users (' + str(len(parts)) + '):</span>'
        if not parts:
            page += '<span class="text-gray-500"> Abhi koi nahi juda.</span>'
        else:
            page += '<ul class="list-disc pl-4 mt-1 text-gray-300">'
            for p in parts:
                page += '<li><b>' + p['username'] + '</b> (Team: ' + p['team_name'] + ')</li>'
            page += '</ul>'
        page += '</div>'

        if len(parts) >= con['spots']:
            page += '<div class="text-center bg-rose-900 text-rose-200 py-1.5 rounded font-bold text-xs">Contest Full ❌</div>'
        else:
            page += '<form action="/join_contest/' + str(con['id']) + '" method="POST" class="flex gap-2"><select name="team_id" required class="bg-gray-800 p-1.5 rounded text-xs w-full text-white border border-gray-700"><option value="">Apni Team Select Karein</option>'
            for t in my_teams:
                page += '<option value="' + str(t['id']) + '">' + t['team_name'] + '</option>'
            page += '</select><button type="submit" class="bg-emerald-600 px-4 py-1.5 rounded font-bold text-xs shrink-0">Join (🪙 ' + str(con['entry_fee']) + ')</button></form>'
        page += '</div>'
    page += '</body></html>'
    return render_template_string(page)

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
    
    t_val = existing_team['team_name'] if existing_team else ''
    page = '<!DOCTYPE html><html lang="hi"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>Create Team</title><script src="https://cdn.tailwindcss.com"></script></head>'
    page += '<body class="bg-gray-950 text-white font-sans p-4 pb-20">'
    page += '<div class="bg-indigo-600 p-3 rounded-xl mb-4"><h1 class="text-sm font-bold">' + ('Edit Lineup' if edit_id else 'Select 11 Players') + '</h1></div>'
    page += '<form method="POST"><div class="mb-3"><input type="text" name="team_name" value="' + t_val + '" placeholder="Team Name" required class="w-full bg-gray-900 border border-gray-700 p-2.5 rounded-xl text-xs text-white"></div>'
    page += '<h3 class="text-xs font-bold text-indigo-300 mb-2">Pick 11 Players & Select C/VC:</h3><div class="space-y-2 mb-4">'
    for p in players:
        checked_box = 'checked' if existing_team and p['name'] in existing_team['players'] else ''
        checked_c = 'checked' if existing_team and existing_team['captain'] == p['name'] else ''
        checked_vc = 'checked' if existing_team and existing_team['vice_captain'] == p['name'] else ''
        page += '<label class="flex justify-between items-center bg-gray-900 border border-gray-800 p-2.5 rounded-xl text-xs">'
        page += '<div class="flex items-center gap-2"><input type="checkbox" name="players" value="' + p['name'] + '" ' + checked_box + ' class="accent-indigo-500"><div><span class="font-bold">' + p['name'] + '</span><span class="text-[10px] text-gray-400 block">' + p['team'] + ' • ' + p['role'] + '</span></div></div>'
        page += '<div class="flex gap-2 text-[11px]"><label><input type="radio" name="captain" value="' + p['name'] + '" ' + checked_c + ' required> C</label><label><input type="radio" name="vice_captain" value="' + p['name'] + '" ' + checked_vc + ' required> VC</label></div>'
        page += '</label>'
    page += '</div><button class="w-full bg-emerald-600 py-3 rounded-xl font-bold text-xs shadow">' + ('Update Lineup' if edit_id else 'Save Team') + '</button></form></body></html>'
    return render_template_string(page)

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
    if session.get('is_admin'):
        conn = sqlite3.connect(DB_NAME)
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        
        msg = ""
        if request.method == 'POST':
            action = request.form.get('action')
            if action == 'match':
                c.execute('INSERT INTO matches (team1, team2, match_time, status) VALUES (?, ?, ?, "Upcoming")', (request.form.get('t1'), request.form.get('t2'), request.form.get('time')))
                msg = "Match added successfully!"
            elif action == 'status':
                c.execute('UPDATE matches SET status = ? WHERE id = ?', (request.form.get('status'), request.form.get('match_id')))
                msg = "Match status updated!"
            elif action == 'player':
                c.execute('INSERT INTO players (match_id, name, team, role) VALUES (?, ?, ?, ?)', (request.form.get('match_id'), request.form.get('p_name'), request.form.get('p_team'), request.form.get('p_role')))
                msg = "Player added successfully!"
            elif action == 'coins':
                target_user_id = request.form.get('user_id')
                coin_amt = request.form.get('coins')
                c.execute('UPDATE users SET coins = coins + ? WHERE id = ?', (coin_amt, target_user_id))
                msg = "Coins sent successfully to user!"
            elif action == 'contest':
                c.execute('INSERT INTO contests (match_id, name, prize_pool, entry_fee, spots) VALUES (?, ?, ?, ?, ?)', (request.form.get('match_id'), request.form.get('c_name'), request.form.get('prize'), request.form.get('fee'), request.form.get('spots')))
                msg = "Contest added successfully!"
            conn.commit()
        
        matches = c.execute('SELECT * FROM matches').fetchall()
        users = c.execute('SELECT * FROM users').fetchall()
        total_contests = c.execute('SELECT COUNT(*) FROM contests').fetchone()[0]
        conn.close()
        
        page = '<!DOCTYPE html><html lang="hi"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>Admin Panel</title><script src="https://cdn.tailwindcss.com"></script></head>'
        page += '<body class="bg-gray-950 text-white font-sans p-4 pb-20">'
        page += '<div class="flex justify-between items-center mb-4"><h1 class="text-sm font-bold text-emerald-400">👑 Admin Panel (Contests: ' + str(total_contests) + ')</h1><a href="/" class="text-indigo-400 text-xs bg-indigo-950 px-3 py-1 rounded-lg">Home</a></div>'
        if msg:
            page += '<div class="bg-emerald-900 text-emerald-200 p-2.5 rounded-xl mb-3 text-xs font-bold">' + msg + '</div>'
        
        page += '<form method="POST" class="bg-gray-900 border border-gray-800 p-3 rounded-2xl mb-3"><input type="hidden" name="action" value="match"><h3 class="font-bold mb-2 text-indigo-300 text-xs">1. Add Match</h3>'
        page += '<input type="text" name="t1" placeholder="Team 1" required class="w-full bg-gray-800 p-2.5 rounded-xl mb-2 text-xs text-white">'
        page += '<input type="text" name="t2" placeholder="Team 2" required class="w-full bg-gray-800 p-2.5 rounded-xl mb-2 text-xs text-white">'
        page += '<input type="datetime-local" name="time" required class="w-full bg-gray-800 p-2.5 rounded-xl mb-2 text-xs text-white">'
        page += '<button class="w-full bg-indigo-600 py-2.5 rounded-xl font-bold text-xs">Add Match</button></form>'

        page += '<form method="POST" class="bg-gray-900 border border-gray-800 p-3 rounded-2xl mb-3"><input type="hidden" name="action" value="status"><h3 class="font-bold mb-2 text-indigo-300 text-xs">2. Match Status</h3>'
        page += '<select name="match_id" class="w-full bg-gray-800 p-2.5 rounded-xl mb-2 text-xs text-white">'
        for m in matches:
            page += '<option value="' + str(m['id']) + '">' + m['team1'] + ' vs ' + m['team2'] + ' (' + m['status'] + ')</option>'
        page += '</select><select name="status" class="w-full bg-gray-800 p-2.5 rounded-xl mb-2 text-xs text-white"><option value="Upcoming">Upcoming</option><option value="Live">Live</option><option value="Completed">Completed</option></select>'
        page += '<button class="w-full bg-amber-500 text-black py-2.5 rounded-xl font-bold text-xs">Update Status</button></form>'

        page += '<form method="POST" class="bg-gray-900 border border-gray-800 p-3 rounded-2xl mb-3"><input type="hidden" name="action" value="player"><h3 class="font-bold mb-2 text-indigo-300 text-xs">3. Add Player</h3>'
        page += '<select name="match_id" class="w-full bg-gray-800 p-2.5 rounded-xl mb-2 text-xs text-white">'
        for m in matches:
            page += '<option value="' + str(m['id']) + '">' + m['team1'] + ' vs ' + m['team2'] + '</option>'
        page += '</select><input type="text" name="p_name" placeholder="Player Name" required class="w-full bg-gray-800 p-2.5 rounded-xl mb-2 text-xs text-white">'
        page += '<input type="text" name="p_team" placeholder="Team Code" required class="w-full bg-gray-800 p-2.5 rounded-xl mb-2 text-xs text-white">'
        page += '<select name="p_role" class="w-full bg-gray-800 p-2.5 rounded-xl mb-2 text-xs text-white"><option value="Batsman">Batsman</option><option value="Bowler">Bowler</option><option value="All-Rounder">All-Rounder</option><option value="WK">WK</option></select>'
        page += '<button class="w-full bg-emerald-600 py-2.5 rounded-xl font-bold text-xs">Add Player</button></form>'

        page += '<form method="POST" class="bg-gray-900 border border-gray-800 p-3 rounded-2xl mb-3"><input type="hidden" name="action" value="contest"><h3 class="font-bold mb-2 text-indigo-300 text-xs">4. Add Contest</h3>'
        page += '<select name="match_id" class="w-full bg-gray-800 p-2.5 rounded-xl mb-2 text-xs text-white">'
        for m in matches:
            page += '<option value="' + str(m['id']) + '">' + m['team1'
