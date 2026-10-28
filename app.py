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
                    points REAL DEFAULT 0,
                    is_lineup INTEGER DEFAULT 0
                )''')
    c.execute('''CREATE TABLE IF NOT EXISTS contests (
                    id SERIAL PRIMARY KEY,
                    match_id INTEGER,
                    name TEXT,
                    prize_pool INTEGER,
                    entry_fee INTEGER,
                    spots INTEGER,
                    team_limit INTEGER DEFAULT 1,
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
                    winnings REAL DEFAULT 0
                )''')
    
    try:
        c.execute('ALTER TABLE players ADD COLUMN IF NOT EXISTS is_lineup INTEGER DEFAULT 0;')
        c.execute('ALTER TABLE contest_participants ALTER COLUMN winnings TYPE REAL;')
        c.execute('ALTER TABLE contests ADD COLUMN IF NOT EXISTS team_limit INTEGER DEFAULT 1;')
    except Exception:
        conn.rollback()

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

@app.route('/terms')
def terms():
    tc_text = """
    CRICXABHI FANTASY - TERMS & CONDITIONS AND DISCLAIMER
    
    Welcome to CRICXABHI Fantasy. By accessing, registering, or participating in any contests, matches, or activities hosted on this platform, you agree to comply with and be bound by the following comprehensive Terms and Conditions. Please read them carefully before using our services.
    
    1. Nature of the Platform & Entertainment Purpose
    CRICXABHI Fantasy is strictly designed and operated as a free-to-play or simulated social entertainment platform intended purely for recreation, skill testing, and entertainment purposes related to cricket statistics and analytics. This platform does not constitute a real-money gambling, betting, or lotteries website.
    
    2. Simulated Coins and Virtual Economy
    All coins, tokens, and rewards utilized within CRICXABHI Fantasy are entirely virtual currency ("Coins"). These coins hold no real-world monetary value, cannot be exchanged for fiat currency, cash, or any physical assets, and are restricted solely to internal gameplay mechanics, creating teams, and joining friendly contests within the application ecosystem.
    
    3. Limitation of Liability & Disclaimer of Financial Responsibility
    The creators, administrators, developers, and owners of CRICXABHI Fantasy (collectively referred to as the "Platform Owner") hold absolutely no responsibility, legal liability, or obligation whatsoever regarding any external financial transactions, private agreements, offline wagers, or informal money exchanges conducted between users or third parties. 
    
    4. User Sole Responsibility
    Users acknowledge and agree that any participation, coin transfers, or competitive engagement is done entirely at their own discretion and risk. The Platform Owner shall not be held liable for any direct, indirect, incidental, or consequential losses, disputes, or claims arising out of user interactions, unauthorized account access, or misuse of the platform. Users bear sole and absolute responsibility for their actions, and the platform owner assumes zero liability for any external monetary exchanges or claims.
    
    5. Fair Play, Code of Conduct, and Account Termination
    Users must maintain fair play standards. Creating multiple fraudulent accounts, exploiting software bugs, attempting unauthorized database manipulation, or engaging in abusive behavior will result in immediate permanent account termination, forfeiture of virtual coins, and revocation of access privileges without prior notice.
    
    6. Modifications and Governing Policies
    The Platform Owner reserves the right to modify, update, suspend, or terminate any feature, contest, database record, or these Terms and Conditions at any time without prior notice. Continued use of the platform signifies your acceptance of any updated guidelines.
    """
    return render_template_string("""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Terms & Conditions</title>
        <script src="https://cdn.tailwindcss.com"></script>
    </head>
    <body class="bg-gray-950 text-white font-sans p-4 pb-20">
        <div class="bg-indigo-600 p-3 rounded-xl flex items-center mb-4 shadow">
            <a href="/" class="mr-3 font-bold bg-indigo-700 px-2.5 py-1 rounded-lg text-xs">←</a>
            <h1 class="text-sm font-bold">Terms & Conditions</h1>
        </div>
        <div class="bg-gray-900 border border-gray-800 p-4 rounded-2xl text-xs space-y-3 leading-relaxed whitespace-pre-line text-gray-300">
            {{ tc }}
        </div>
    </body>
    </html>
    """, tc=tc_text)

@app.route('/delete_account', methods=['GET', 'POST'])
def delete_account():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    error = ""
    if request.method == 'POST':
        uname = request.form.get('username', '').strip()
        pwd = request.form.get('password', '').strip()
        conn = get_db_connection()
        c = conn.cursor()
        c.execute('SELECT * FROM users WHERE id = %s', (session['user_id'],))
        u = c.fetchone()
        
        if u and u['username'] == uname and u['password'] == pwd:
            uid = session['user_id']
            c.execute('DELETE FROM contest_participants WHERE user_id = %s', (uid,))
            c.execute('DELETE FROM teams WHERE user_id = %s', (uid,))
            c.execute('DELETE FROM users WHERE id = %s', (uid,))
            conn.commit()
            conn.close()
            session.clear()
            return "<script>alert('Account permanently deleted successfully!'); window.location.href='/login';</script>"
        else:
            error = "❌ Invalid Username or Password!"
        conn.close()

    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Delete Account</title>
        <script src="https://cdn.tailwindcss.com"></script>
    </head>
    <body class="bg-gray-950 text-white font-sans p-6 flex items-center justify-center h-screen">
        <div class="bg-gray-900 border border-rose-800 p-6 rounded-2xl max-w-sm w-full shadow-2xl">
            <h2 class="text-base font-bold text-rose-500 mb-2 text-center">⚠️ Permanent Account Deletion</h2>
            <p class="text-[11px] text-gray-400 mb-4 text-center">Once deleted, your account, all created teams, match statistics, and total coin balance will be permanently erased and cannot be recovered.</p>
            {f'<div class="bg-rose-900 text-rose-200 p-2.5 rounded-xl mb-3 text-xs font-bold text-center">{error}</div>' if error else ''}
            <form method="POST" class="space-y-3">
                <input type="text" name="username" placeholder="Confirm Username..." required class="w-full bg-gray-800 border border-gray-700 p-2.5 rounded-xl text-xs text-white">
                <input type="password" name="password" placeholder="Confirm Password..." required class="w-full bg-gray-800 border border-gray-700 p-2.5 rounded-xl text-xs text-white">
                <button type="submit" class="w-full bg-rose-600 py-3 rounded-xl font-bold text-xs shadow">Delete Account Permanently</button>
            </form>
            <a href="/" class="block text-center mt-4 text-xs text-indigo-400 font-bold">Cancel & Back to Home</a>
        </div>
    </body>
    </html>
    """
    return render_template_string(html)

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
        elif action == 'contest':
            match_id = request.form.get('match_id')
            c_name = request.form.get('c_name')
            prize = request.form.get('prize')
            fee = request.form.get('fee')
            spots = request.form.get('spots')
            t_limit = int(request.form.get('team_limit', 1))
            
            ranks = request.form.getlist('breakup_rank')
            amounts = request.form.getlist('breakup_amount')
            breakup_parts = []
            for r, a in zip(ranks, amounts):
                if r.strip() and a.strip():
                    breakup_parts.append(f"{r.strip()}:{a.strip()}")
            breakup_str = ", ".join(breakup_parts) if breakup_parts else "1: 100"
            
            c.execute('INSERT INTO contests (match_id, name, prize_pool, entry_fee, spots, team_limit, prize_breakup) VALUES (%s, %s, %s, %s, %s, %s, %s)', 
                      (match_id, c_name, prize, fee, spots, t_limit, breakup_str))
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
                    
                    breakup_dict = {}
                    parts = con['prize_breakup'].split(',')
                    for p_str in parts:
                        if ':' in p_str:
                            r_range, amt = p_str.split(':')
                            r_range = r_range.strip()
                            try:
                                amt_val = float(amt.strip())
                            except:
                                amt_val = 0.0
                            
                            if '-' in r_range:
                                start_r, end_r = r_range.split('-')
                                for r_num in range(int(start_r.strip()), int(end_r.strip()) + 1):
                                    breakup_dict[r_num] = amt_val
                            else:
                                breakup_dict[int(r_range)] = amt_val

                    i = 0
                    n = len(participants)
                    current_rank = 1
                    
                    while i < n:
                        j = i
                        while j < n and participants[j]['total_points'] == participants[i]['total_points']:
                            j += 1
                        
                        group_size = j - i
                        total_group_prize = 0.0
                        for r_offset in range(group_size):
                            r_to_check = current_rank + r_offset
                            total_group_prize += breakup_dict.get(r_to_check, 0.0)
                        
                        share_prize = total_group_prize / group_size if group_size > 0 else 0.0
                        
                        for k in range(i, j):
                            part = participants[k]
                            winnings = share_prize
                            rank = current_rank
                            if winnings > 0:
                                c.execute('UPDATE users SET coins = coins + %s WHERE id = %s', (winnings, part['user_id']))
                            c.execute('UPDATE contest_participants SET rank = %s, winnings = %s WHERE id = %s', (rank, winnings, part['id']))
                        
                        current_rank += group_size
                        i = j
                    conn.commit()

    c.execute('SELECT * FROM matches')
    matches = c.fetchall()
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
                <a href="/terms" class="bg-gray-800 px-2.5 py-1 rounded-xl font-bold text-xs">T&C</a>
                <a href="/delete_account" class="bg-rose-900 text-rose-200 px-2 py-1 rounded-xl font-bold text-xs border border-rose-600" title="Delete Account">D</a>
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
        live_matches = [m for m in matches if m['status'] == 'Live']
        upcoming_matches = [m for m in matches if m['status'] == 'Upcoming']
        completed_matches = [m for m in matches if m['status'] == 'Completed']

        breakup_table_rows = ""
        for r_label in ["1", "2", "3", "4", "5", "6", "7 - 106"]:
            breakup_table_rows += f"""
            <tr class="border-b border-gray-800 text-xs">
                <td class="p-2"><input type="text" name="breakup_rank" value="{r_label}" class="w-full bg-gray-800 p-1 rounded text-white text-center"></td>
                <td class="p-2"><input type="number" name="breakup_amount" placeholder="Coins / Prize" class="w-full bg-gray-800 p-1 rounded text-white"></td>
            </tr>
            """

        html += f"""
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
            
            <div class="bg-gray-900 border border-gray-800 p-3 rounded-2xl mb-3">
                <h3 class="font-bold mb-2 text-amber-300 text-xs">2. Matches Management (Live / Upcoming / Completed)</h3>
                
                <div class="mb-3 bg-gray-800 p-2.5 rounded-xl">
                    <h4 class="text-xs font-bold text-emerald-400 mb-1">🟢 Upcoming Matches</h4>
        """
        if not upcoming_matches:
            html += '<p class="text-[10px] text-gray-400">No upcoming matches.</p>'
        for m in upcoming_matches:
            html += f'''
            <div class="flex justify-between items-center py-1 border-b border-gray-700 text-xs">
                <a href="/admin/match/{m['id']}" class="text-indigo-300 font-bold hover:underline">{m['team1']} vs {m['team2']}</a>
                <form action="/admin/delete_match_permanently" method="POST" onsubmit="return prompt('Enter Admin Password to Delete:') === '1234567890';">
                    <input type="hidden" name="match_id" value="{m['id']}">
                    <button type="submit" class="bg-rose-600 px-2 py-0.5 rounded text-[10px] font-bold">Delete</button>
                </form>
            </div>
            '''
        html += """
                </div>

                <div class="mb-3 bg-gray-800 p-2.5 rounded-xl">
                    <h4 class="text-xs font-bold text-amber-400 mb-1">🔴 Live Matches</h4>
        """
        if not live_matches:
            html += '<p class="text-[10px] text-gray-400">No live matches.</p>'
        for m in live_matches:
            html += f'''
            <div class="flex justify-between items-center py-1 border-b border-gray-700 text-xs">
                <a href="/admin/match/{m['id']}" class="text-indigo-300 font-bold hover:underline">{m['team1']} vs {m['team2']}</a>
                <form action="/admin/delete_match_permanently" method="POST" onsubmit="return prompt('Enter Admin Password to Delete:') === '1234567890';">
                    <input type="hidden" name="match_id" value="{m['id']}">
                    <button type="submit" class="bg-rose-600 px-2 py-0.5 rounded text-[10px] font-bold">Delete</button>
                </form>
            </div>
            '''
        html += """
                </div>

                <div class="bg-gray-800 p-2.5 rounded-xl">
                    <h4 class="text-xs font-bold text-gray-400 mb-1">🏁 Completed Matches</h4>
        """
        if not completed_matches:
            html += '<p class="text-[10px] text-gray-400">No completed matches.</p>'
        for m in completed_matches:
            html += f'''
            <div class="flex justify-between items-center py-1 border-b border-gray-700 text-xs">
                <a href="/admin/match/{m['id']}" class="text-indigo-300 font-bold hover:underline">{m['team1']} vs {m['team2']}</a>
                <form action="/admin/delete_match_permanently" method="POST" onsubmit="return prompt('Enter Admin Password to Delete:') === '1234567890';">
                    <input type="hidden" name="match_id" value="{m['id']}">
                    <button type="submit" class="bg-rose-600 px-2 py-0.5 rounded text-[10px] font-bold">Delete</button>
                </form>
            </div>
            '''
        html += """
                </div>
            </div>

            <div class="bg-gray-900 border border-gray-800 p-3 rounded-2xl mb-3 flex justify-between items-center">
                <div>
                    <h3 class="font-bold text-indigo-300 text-xs">3. User Data Management</h3>
                    <p class="text-[10px] text-gray-400">View all users and add coins</p>
                </div>
                <a href="/admin/users" class="bg-indigo-600 px-3 py-2 rounded-xl font-bold text-xs shadow">Show More →</a>
            </div>

            <form method="POST" class="bg-gray-900 border border-gray-800 p-3 rounded-2xl mb-3">
                <input type="hidden" name="action" value="contest">
                <h3 class="font-bold mb-2 text-indigo-300 text-xs">4. Create Contest (with Prize Breakup Table)</h3>
                <select name="match_id" class="w-full bg-gray-800 p-2.5 rounded-xl mb-2 text-xs text-white">
        """
        for m in matches:
            html += f'<option value="{m["id"]}">{m["team1"]} vs {m["team2"]}</option>'
        html += f"""
                </select>
                <input type="text" name="c_name" placeholder="Contest Name" required class="w-full bg-gray-800 p-2.5 rounded-xl mb-2 text-xs text-white">
                <input type="number" name="prize" placeholder="Total Prize Pool" required class="w-full bg-gray-800 p-2.5 rounded-xl mb-2 text-xs text-white">
                <input type="number" name="fee" placeholder="Entry Fee" required class="w-full bg-gray-800 p-2.5 rounded-xl mb-2 text-xs text-white">
                <input type="number" name="spots" placeholder="Total Spots" required class="w-full bg-gray-800 p-2.5 rounded-xl mb-2 text-xs text-white">
                <div class="mb-2">
                    <label class="text-[11px] text-gray-400 block mb-1">Team Limit per User (e.g. 1, 2, 4)</label>
                    <input type="number" name="team_limit" value="1" min="1" max="10" required class="w-full bg-gray-800 p-2.5 rounded-xl text-xs text-white">
                </div>
                
                <label class="text-[11px] text-gray-400 block mb-1">Winning Breakup Table (Rank & Prize)</label>
                <div class="bg-gray-800 p-2 rounded-xl mb-2">
                    <table class="w-full">
                        <thead>
                            <tr class="text-[10px] text-indigo-300 border-b border-gray-700">
                                <th class="p-1">Rank / Range</th>
                                <th class="p-1">Prize (Coins)</th>
                            </tr>
                        </thead>
                        <tbody>
                            {breakup_table_rows}
                        </tbody>
                    </table>
                </div>

                <button class="w-full bg-indigo-600 py-2.5 rounded-xl font-bold text-xs">Create Contest</button>
            </form>
            
            <form method="POST" class="bg-gray-900 border border-gray-800 p-3 rounded-2xl">
                <input type="hidden" name="action" value="update_status">
                <h3 class="font-bold mb-2 text-indigo-300 text-xs">5. Match Status Control (Auto Coins Distribution on Complete)</h3>
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

@app.route('/admin/match/<int:match_id>', methods=['GET', 'POST'])
def admin_match_detail(match_id):
    if not session.get('is_admin'):
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    c = conn.cursor()
    
    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'add_players_bulk':
            names = request.form.getlist('name')
            teams = request.form.getlist('team')
            roles = request.form.getlist('role')
            lineups = request.form.getlist('lineup')
            
            for i in range(len(names)):
                p_name = names[i].strip()
                if p_name:
                    p_team = teams[i].strip()
                    p_role = roles[i]
                    is_lin = 1 if str(i) in lineups else 0
                    c.execute('INSERT INTO players (match_id, name, team, role, points, is_lineup) VALUES (%s, %s, %s, %s, 0, %s)',
                              (match_id, p_name, p_team, p_role, is_lin))
            conn.commit()
        elif action == 'edit_all_players':
            p_ids = request.form.getlist('player_id')
            names = request.form.getlist('name')
            teams = request.form.getlist('team')
            roles = request.form.getlist('role')
            points = request.form.getlist('points')
            lineups = request.form.getlist('lineup')
            
            for i in range(len(p_ids)):
                pid = p_ids[i]
                p_name = names[i].strip()
                p_team = teams[i].strip()
                p_role = roles[i]
                p_pts = float(points[i] if points[i] else 0)
                is_lin = 1 if str(i) in lineups else 0
                c.execute('UPDATE players SET name = %s, team = %s, role = %s, points = %s, is_lineup = %s WHERE id = %s',
                          (p_name, p_team, p_role, p_pts, is_lin, pid))
            conn.commit()
            
    c.execute('SELECT * FROM matches WHERE id = %s', (match_id,))
    match = c.fetchone()
    c.execute('SELECT * FROM contests WHERE match_id = %s', (match_id,))
    contests = c.fetchall()
    c.execute('SELECT * FROM players WHERE match_id = %s ORDER BY id ASC', (match_id,))
    players = c.fetchall()
    conn.close()
    
    start_serial = len(players) + 1
    add_rows_html = ""
    for i in range(start_serial, start_serial + 15):
        add_rows_html += f"""
        <tr class="border-b border-gray-800 text-xs">
            <td class="p-2 text-center font-bold text-amber-400">{i}</td>
            <td class="p-2"><input type="text" name="name" placeholder="Player Name" class="w-full bg-gray-800 p-1.5 rounded text-white"></td>
            <td class="p-2"><input type="text" name="team" placeholder="Team Code" class="w-full bg-gray-800 p-1.5 rounded text-white"></td>
            <td class="p-2">
                <select name="role" class="w-full bg-gray-800 p-1.5 rounded text-white">
                    <option value="Batsman">Bat</option>
                    <option value="Bowler">Bowl</option>
                    <option value="All-Rounder">All-R</option>
                    <option value="WK">WK</option>
                </select>
            </td>
            <td class="p-2 text-center"><input type="checkbox" name="lineup" value="{i - start_serial}" class="w-4 h-4 accent-emerald-500"></td>
        </tr>
        """

    edit_rows_html = ""
    for idx, p in enumerate(players, 1):
        dot_color = "bg-emerald-500" if p['is_lineup'] == 1 else "bg-rose-500"
        checked_lineup = "checked" if p['is_lineup'] == 1 else ""
        edit_rows_html += f"""
        <tr class="border-b border-gray-800 text-xs">
            <input type="hidden" name="player_id" value="{p['id']}">
            <td class="p-2 text-center"><span class="inline-block w-2.5 h-2.5 rounded-full {dot_color}"></span></td>
            <td class="p-2 font-bold text-amber-400">#{idx}</td>
            <td class="p-2"><input type="text" name="name" value="{p['name']}" required class="w-full bg-gray-800 p-1 rounded text-white"></td>
            <td class="p-2"><input type="text" name="team" value="{p['team']}" required class="w-16 bg-gray-800 p-1 rounded text-white text-center"></td>
            <td class="p-2">
                <select name="role" class="bg-gray-800 p-1 rounded text-white text-xs">
                    <option value="Batsman" {"selected" if p['role']=='Batsman' else ""}>Bat</option>
                    <option value="Bowler" {"selected" if p['role']=='Bowler' else ""}>Bowl</option>
                    <option value="All-Rounder" {"selected" if p['role']=='All-Rounder' else ""}>All-R</option>
                    <option value="WK" {"selected" if p['role']=='WK' else ""}>WK</option>
                </select>
            </td>
            <td class="p-2"><input type="number" step="0.5" name="points" value="{p['points']}" class="w-16 bg-gray-800 p-1 rounded text-white text-center font-bold"></td>
            <td class="p-2 text-center"><input type="checkbox" name="lineup" value="{idx-1}" {checked_lineup} class="w-4 h-4 accent-emerald-500"></td>
        </tr>
        """
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Admin Match Details</title>
        <script src="https://cdn.tailwindcss.com"></script>
    </head>
    <body class="bg-gray-950 text-white font-sans p-4 pb-20">
        <div class="bg-indigo-600 p-3 rounded-xl flex items-center justify-between mb-4 shadow">
            <div class="flex items-center">
                <a href="/" class="mr-3 font-bold bg-indigo-700 px-2.5 py-1 rounded-lg text-xs">←</a>
                <h1 class="text-sm font-bold">{match['team1']} vs {match['team2']} ({match['status']})</h1>
            </div>
            <form action="/admin/delete_match_permanently" method="POST" onsubmit="return prompt('Enter Admin Password to Delete Match:') === '1234567890';">
                <input type="hidden" name="match_id" value="{match['id']}">
                <button type="submit" class="bg-rose-600 px-3 py-1 rounded font-bold text-xs">Delete Match</button>
            </form>
        </div>

        <h3 class="font-bold text-amber-400 text-xs mb-2">🏆 Contests in this Match</h3>
    """
    for contest in contests:
        html += f"""
        <div class="bg-gray-900 border border-gray-800 p-3 rounded-2xl mb-3 flex justify-between items-center text-xs">
            <div>
                <span class="font-bold">{contest['name']}</span>
                <p class="text-[11px] text-gray-400">Prize Pool: 🪙 {contest['prize_pool']} | Fee: 🪙 {contest['entry_fee']} | Limit: {contest.get('team_limit', 1)}</p>
            </div>
            <div class="flex items-center gap-2">
                <a href="/contest/{contest['id']}" class="bg-gray-800 px-3 py-1.5 rounded font-bold">Leaderboard</a>
                <form action="/admin/delete_contest_permanently" method="POST" onsubmit="return prompt('Enter Admin Password to Delete Contest:') === '1234567890';">
                    <input type="hidden" name="contest_id" value="{contest['id']}">
                    <input type="hidden" name="match_id" value="{match['id']}">
                    <button type="submit" class="bg-rose-600 px-2.5 py-1.5 rounded font-bold">Delete</button>
                </form>
            </div>
        </div>
        """
    
    html += f"""
        <h3 class="font-bold text-indigo-300 text-xs mt-4 mb-2">➕ Add More Players (Table Format)</h3>
        <form method="POST" class="bg-gray-900 border border-gray-800 p-3 rounded-2xl mb-6">
            <input type="hidden" name="action" value="add_players_bulk">
            <div class="overflow-x-auto mb-3">
                <table class="w-full text-left border-collapse">
                    <thead>
                        <tr class="bg-gray-800 text-[11px] text-indigo-300">
                            <th class="p-2 text-center">#</th>
                            <th class="p-2">Player Name</th>
                            <th class="p-2">Team Code</th>
                            <th class="p-2">Role</th>
                            <th class="p-2 text-center">Lineup?</th>
                        </tr>
                    </thead>
                    <tbody>
                        {add_rows_html}
                    </tbody>
                </table>
            </div>
            <button type="submit" class="w-full bg-emerald-600 py-2.5 rounded-xl font-bold text-xs shadow">Save Added Players</button>
        </form>

        <h3 class="font-bold text-indigo-300 text-xs mb-2">👥 Saved Players List (Single Bulk Edit & Save)</h3>
        <form method="POST">
            <input type="hidden" name="action" value="edit_all_players">
            <div class="bg-gray-900 border border-gray-800 rounded-2xl overflow-x-auto mb-4">
                <table class="w-full text-left border-collapse">
                    <thead>
                        <tr class="bg-gray-800 text-[11px] text-amber-300">
                            <th class="p-2 text-center">Status</th>
                            <th class="p-2">#</th>
                            <th class="p-2">Name</th>
                            <th class="p-2">Team</th>
                            <th class="p-2">Role</th>
                            <th class="p-2">Pts</th>
                            <th class="p-2 text-center">Lineup</th>
                        </tr>
                    </thead>
                    <tbody>
                        {edit_rows_html}
                    </tbody>
                </table>
            </div>
            <button type="submit" class="w-full bg-amber-600 py-3 rounded-xl font-bold text-xs shadow">Update All Players & Points</button>
        </form>

        <a href="/" class="block text-center bg-gray-800 py-2.5 rounded-xl font-bold text-xs mt-4">Back to Home</a>
    </body>
    </html>
    """
    return render_template_string(html)

@app.route('/admin/delete_match_permanently', methods=['POST'])
def delete_match_permanently():
    if not session.get('is_admin'):
        return redirect(url_for('login'))
    match_id = request.form.get('match_id')
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('DELETE FROM contest_participants WHERE contest_id IN (SELECT id FROM contests WHERE match_id = %s)', (match_id,))
    c.execute('DELETE FROM contests WHERE match_id = %s', (match_id,))
    c.execute('DELETE FROM teams WHERE match_id = %s', (match_id,))
    c.execute('DELETE FROM players WHERE match_id = %s', (match_id,))
    c.execute('DELETE FROM matches WHERE id = %s', (match_id,))
    conn.commit()
    conn.close()
    return redirect(url_for('index'))

@app.route('/admin/delete_contest_permanently', methods=['POST'])
def delete_contest_permanently():
    if not session.get('is_admin'):
        return redirect(url_for('login'))
    contest_id = request.form.get('contest_id')
    match_id = request.form.get('match_id')
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('DELETE FROM contest_participants WHERE contest_id = %s', (contest_id,))
    c.execute('DELETE FROM contests WHERE id = %s', (contest_id,))
    conn.commit()
    conn.close()
    return redirect(url_for('admin_match_detail', match_id=match_id))

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
            <h2 class="text-base font-bold text-indigo-400 mb-2 text-center">🏏 CRICXABHI Login</h2>
            <div class="text-center mb-4"><a href="/terms" class="text-[11px] text-amber-400 underline font-bold">Read Terms & Conditions</a></div>
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
        html += f'''
        <div class="mb-4">
            <a href="/create_team/{match['id']}" class="block text-center bg-emerald-600 py-3 rounded-xl font-bold text-xs shadow">➕ Create / Edit Team (Max Limit Supported)</a>
        </div>
        '''

    html += '<div class="bg-gray-900 border border-indigo-500 p-3 rounded-2xl mb-4"><h3 class="font-bold text-indigo-300 text-xs mb-2">🔒 My Created Teams</h3>'
    if not my_teams:
        html += '<p class="text-[11px] text-gray-400 mb-2">Pehle apni team banayein!</p>'
    for t in my_teams:
        if match['status'] == 'Upcoming':
            team_action_btn = f'<a href="/create_team/{match_id}" class="text-[10px] bg-amber-500 text-black px-2 py-1 rounded font-bold">Edit</a>'
        else:
            team_action_btn = f'<a href="/show_team/{t["id"]}" class="text-[10px] bg-emerald-500 text-black px-2.5 py-1 rounded font-bold">Show Team</a>'
            
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
                <a href="/contest/{contest['id']}" class="text-indigo-400 hover:underline"><span>{contest['name']}</span></a>
                <span>Prize: 🪙 {contest['prize_pool']}</span>
            </div>
            <p class="text-[11px] text-gray-400 mb-2">Entry: 🪙 {contest['entry_fee']} | Spots: {contest['spots']} | Limit: {contest.get('team_limit', 1)} Team(s)</p>
            <div class="flex gap-2">
                <a href="/contest/{contest['id']}" class="flex-1 text-center bg-gray-800 py-2 rounded-xl font-bold text-xs">View Contest</a>
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
    c.execute('SELECT * FROM teams WHERE match_id = %s AND user_id = %s ORDER BY id ASC', (match_id, session['user_id']))
    user_teams = c.fetchall()
    conn.close()
    
    msg = ""
    if request.method == 'POST':
        team_name = request.form.get('team_name', '').strip()
        selected_players = request.form.getlist('players')
        captain = request.form.get('captain')
        vice_captain = request.form.get('vice_captain')
        team_slot = int(request.form.get('team_slot', 1))
        
        if len(selected_players) != 11:
            msg = "❌ Aapko exact 11 khiladi select karne honge!"
        elif not captain or not vice_captain:
            msg = "❌ Captain aur Vice-Captain select karna zaroori hai!"
        elif captain == vice_captain:
            msg = "❌ Error: Captain and Vice-Captain cannot be the same player! Please choose different players like Dream11."
        else:
            p_str = ",".join(selected_players)
            conn = get_db_connection()
            c = conn.cursor()
            
            # Check if team slot already exists
            if len(user_teams) >= team_slot:
                # Update existing team slot
                t_id = user_teams[team_slot - 1]['id']
                c.execute('UPDATE teams SET team_name = %s, captain = %s, vice_captain = %s, players = %s WHERE id = %s',
                          (f"{team_name} (T{team_slot})", captain, vice_captain, p_str, t_id))
            else:
                # Insert new team slot
                c.execute('INSERT INTO teams (match_id, user_id, team_name, captain, vice_captain, players, total_points) VALUES (%s, %s, %s, %s, %s, %s, %s)',
                          (match_id, session['user_id'], f"{team_name} (T{team_slot})", captain, vice_captain, p_str, 0.0))
            conn.commit()
            conn.close()
            return redirect(url_for('match_detail', match_id=match_id))
    
    # Pre-fill for slot 1 if exists
    default_tname = user_teams[0]['team_name'].split(' (T')[0] if user_teams else ""
    
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
            <h1 class="text-sm font-bold">Create Teams: {match['team1']} vs {match['team2']}</h1>
        </div>
    """
    if msg:
        html += f'<div class="bg-rose-900 text-rose-200 p-2.5 rounded-xl mb-3 text-xs font-bold text-center">{msg}</div>'
    
    html += f"""
        <form method="POST" class="space-y-4">
            <div class="grid grid-cols-2 gap-2">
                <div>
                    <label class="text-xs text-gray-400 block mb-1">Team Base Name</label>
                    <input type="text" name="team_name" value="{default_tname}" placeholder="Enter Team Name..." required class="w-full bg-gray-800 border border-gray-700 p-2.5 rounded-xl text-xs text-white">
                </div>
                <div>
                    <label class="text-xs text-gray-400 block mb-1">Select Team Slot</label>
                    <select name="team_slot" class="w-full bg-gray-800 border border-gray-700 p-2.5 rounded-xl text-xs text-white font-bold">
                        <option value="1">Team 1</option>
                        <option value="2">Team 2</option>
                        <option value="3">Team 3</option>
                        <option value="4">Team 4</option>
                    </select>
                </div>
            </div>
            <div class="bg-gray-900 border border-gray-800 p-3 rounded-2xl">
                <h3 class="font-bold text-xs text-amber-400 mb-2">Select 11 Players (🟢 = Playing Lineup) - C & VC must be different!</h3>
    """
    for p in players:
        dot_color = "bg-emerald-500" if p['is_lineup'] == 1 else "bg-rose-500"
        html += f"""
        <div class="flex items-center justify-between bg-gray-800 p-2 rounded-xl mb-2 text-xs">
            <label class="flex items-center gap-2 cursor-pointer flex-1">
                <span class="inline-block w-2.5 h-2.5 rounded-full {dot_color}"></span>
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
            <button type="submit" class="w-full bg-emerald-600 py-3 rounded-xl font-bold text-xs shadow">Save This Team Slot</button>
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
            <a href="javascript:history.back()" class="mr-3 font-bold bg-indigo-700 px-2.5 py-1 rounded-lg text-xs">←</a>
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
        p_obj = match_players.get(pname, {'team': '-', 'role': '-', 'points': 0.0, 'is_lineup': 0})
        base_pts = p_obj['points']
        dot_color = "bg-emerald-500" if p_obj['is_lineup'] == 1 else "bg-rose-500"
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
            <div class="flex items-center gap-2">
                <span class="inline-block w-2.5 h-2.5 rounded-full {dot_color}"></span>
                <div>
                    <span class="font-bold">{pname}</span>{mult_label}
                    <p class="text-[10px] text-gray-400">{p_obj['team']} | {p_obj['role']} | Base Pts: {base_pts}</p>
                </div>
            </div>
            <div class="font-bold text-emerald-400">
                +{final_p_pts} pts
            </div>
        </div>
        """
    html += """
        </div>
        <a href="javascript:history.back()" class="block text-center bg-gray-800 py-2.5 rounded-xl font-bold text-xs mt-4">Go Back</a>
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
    
    if not teams:
        conn.close()
        return "<script>alert('Pehle apni team banayein!'); window.location.href='/match/" + str(contest['match_id']) + "';</script>"

    # Check how many teams user already joined in this contest vs team_limit
    c.execute('SELECT COUNT(*) as cnt FROM contest_participants WHERE contest_id = %s AND user_id = %s', (contest_id, user['id']))
    joined_count = c.fetchone()['cnt']
    t_limit = contest.get('team_limit', 1)

    if joined_count >= t_limit:
        conn.close()
        return f"<script>alert('Team limit reached! You can only join up to {t_limit} team(s) in this contest.'); window.location.href='/match/{contest['match_id']}';</script>"

    # Join with the next available team slot of the user
    if joined_count < len(teams):
        team_to_join = teams[joined_count]
        c.execute('UPDATE users SET coins = coins - %s WHERE id = %s', (contest['entry_fee'], user['id']))
        c.execute('INSERT INTO contest_participants (contest_id, user_id, team_id, rank, winnings) VALUES (%s, %s, %s, %s, %s)',
                  (contest_id, user['id'], team_to_join['id'], 0, 0))
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
    c.execute('SELECT * FROM matches WHERE id = %s', (contest['match_id'],))
    match = c.fetchone()
    
    c.execute('''SELECT cp.*, u.username, t.team_name, t.total_points, t.id as team_id FROM contest_participants cp
                 JOIN users u ON cp.user_id = u.id
                 JOIN teams t ON cp.team_id = t.id
                 WHERE cp.contest_id = %s ORDER BY t.total_points DESC''', (contest_id,))
    participants = c.fetchall()
    conn.close()
    
    breakup_rows = ""
    parts = contest['prize_breakup'].split(',')
    for p_str in parts:
        if ':' in p_str:
            r_rng, amt = p_str.split(':')
            breakup_rows += f"""
            <div class="flex justify-between items-center bg-gray-800 p-3 rounded-xl mb-2 text-xs border border-gray-700">
                <span class="font-bold text-amber-400">Rank {r_rng.strip()}</span>
                <span class="font-bold text-emerald-400">🪙 {amt.strip()} Coins</span>
            </div>
            """
    if not breakup_rows:
        breakup_rows = '<p class="text-xs text-gray-400 text-center py-4">No prize breakup available.</p>'

    leaderboard_rows = ""
    if not participants:
        leaderboard_rows = '<p class="text-xs text-gray-400 text-center py-4">Koi participant nahi hai abhi.</p>'
    else:
        for idx, p in enumerate(participants, 1):
            win_text = f" | Winnings: 🪙 {p['winnings']}" if p['winnings'] > 0 else ""
            
            if match['status'] in ['Live', 'Completed']:
                team_link_open = f'<a href="/show_team/{p["team_id"]}" class="text-indigo-300 font-bold hover:underline">'
                team_link_close = '</a>'
            else:
                team_link_open = '<span class="text-gray-300 font-bold">'
                team_link_close = '</span>'

            leaderboard_rows += f"""
            <div class="flex justify-between items-center bg-gray-800 p-3 rounded-xl mb-2 text-xs border border-gray-700">
                <div>
                    <span class="font-bold text-amber-400">#{p['rank'] if p['rank'] > 0 else idx}</span> 
                    <span class="font-bold text-white">{p['username']}</span>
                    <p class="text-[10px] text-gray-400">Team: {team_link_open}{p['team_name']}{team_link_close}{win_text}</p>
                </div>
                <div class="text-right font-bold text-emerald-400">
                    {p['total_points']} pts
                </div>
            </div>
            """

    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>{contest['name']}</title>
        <script src="https://cdn.tailwindcss.com"></script>
    </head>
    <body class="bg-gray-950 text-white font-sans p-4 pb-20">
        <div class="bg-indigo-600 p-3 rounded-xl flex items-center mb-4 shadow">
            <a href="/match/{contest['match_id']}" class="mr-3 font-bold bg-indigo-700 px-2.5 py-1 rounded-lg text-xs">←</a>
            <h1 class="text-sm font-bold">{contest['name']}</h1>
        </div>

        <div class="flex border-b border-gray-800 mb-4">
            <button onclick="switchTab('prizes')" id="btnPrizes" class="flex-1 pb-2 text-center font-bold text-xs border-b-2 border-rose-500 text-white">PRIZES</button>
            <button onclick="switchTab('leaderboard')" id="btnLeaderboard" class="flex-1 pb-2 text-center font-bold text-xs border-b-2 border-transparent text-gray-400">LEADERBOARD</button>
        </div>

        <div id="tabPrizes" class="space-y-2">
            <div class="bg-gray-900 border border-gray-800 p-3 rounded-2xl mb-3 text-xs flex justify-between">
                <span>Prize Pool: <b>🪙 {contest['prize_pool']}</b></span>
                <span>Spots: <b>{contest['spots']}</b> | Limit: <b>{contest.get('team_limit', 1)}</b></span>
            </div>
            {breakup_rows}
        </div>

        <div id="tabLeaderboard" class="space-y-2 hidden">
            {leaderboard_rows}
        </div>

        <script>
            function switchTab(tab) {{
                let pTab = document.getElementById('tabPrizes');
                let lTab = document.getElementById('tabLeaderboard');
                let bPrizes = document.getElementById('btnPrizes');
                let bLeader = document.getElementById('btnLeaderboard');

                if(tab === 'prizes') {{
                    pTab.classList.remove('hidden');
                    lTab.classList.add('hidden');
                    bPrizes.classList.add('border-rose-500', 'text-white');
                    bPrizes.classList.remove('border-transparent', 'text-gray-400');
                    bLeader.classList.add('border-transparent', 'text-gray-400');
                    bLeader.classList.remove('border-rose-500', 'text-white');
                }} else {{
                    lTab.classList.remove('hidden');
                    pTab.classList.add('hidden');
                    bLeader.classList.add('border-rose-500', 'text-white');
                    bLeader.classList.remove('border-transparent', 'text-gray-400');
                    bPrizes.classList.add('border-transparent', 'text-gray-400');
                    bPrizes.classList.remove('border-rose-500', 'text-white');
                }}
            }}
        </script>
    </body>
    </html>
    """
    return render_template_string(html)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
