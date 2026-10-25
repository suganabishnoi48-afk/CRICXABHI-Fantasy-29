from flask import Flask, render_template, request, redirect, url_for, session
import sqlite3

app = Flask(__name__)
app.secret_key = 'cricxabhi_fixed_key_2026'
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
    
    return render_template('match_detail.html', match=match, contest_data=contest_data, my_teams=my_teams, all_teams=all_teams, user=user)

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
    return render_template('create_team.html', players=players, existing_team=existing_team, edit_id=edit_id)

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
        return render_template('admin.html', matches=matches, users=users, msg=msg, total_contests=total_contests)

    error_msg = ""
    if request.method == 'POST':
        pass_input = request.form.get('admin_pass')
        if pass_input == '29022008':
            session['is_admin'] = True
            return redirect(url_for('admin'))
        else:
            error_msg = "❌ गलत पासवर्ड! कृपया सही पासवर्ड दर्ज करें।"

    return render_template('admin_login.html', error_msg=error_msg)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
                
