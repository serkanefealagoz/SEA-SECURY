from flask import Flask, render_template_string, request, redirect, url_for, session, jsonify
import sqlite3

app = Flask(__name__)
app.secret_key = "cok-gizli-guvenlik-anahtari"

def init_db():
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            password TEXT
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sessions (
            session_id TEXT PRIMARY KEY,
            status TEXT
        )
    """)
    # İzin verilen IP'ler tablosu
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS allowed_ips (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT,
            ip_address TEXT
        )
    """)
    conn.commit()
    conn.close()

init_db()

# IP Kontrolü
def check_ip_permission(username, client_ip):
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM allowed_ips WHERE username = ? AND ip_address = ?", (username, client_ip))
    row = cursor.fetchone()
    conn.close()
    # Eğer o kullanıcıya ait kayıtlı IP yoksa veya eşleşiyorsa izin ver
    return row is not None

INDEX_HTML = """
<!DOCTYPE html>
<html lang="tr">
<head><meta charset="UTF-8"><title>Giriş</title>
<style>
    body { font-family: 'Segoe UI', sans-serif; background: #0f172a; color: white; height: 100vh; display: flex; justify-content: center; align-items: center; margin: 0; }
    .card { background: #1e293b; padding: 40px; border-radius: 12px; width: 320px; text-align: center; box-shadow: 0 10px 25px rgba(0,0,0,0.3); }
    input { width: 100%; padding: 12px; margin: 10px 0; border: 1px solid #334155; background: #0f172a; color: white; border-radius: 6px; box-sizing: border-box; }
    button { background: #4f46e5; color: white; border: none; padding: 12px; width: 100%; border-radius: 6px; font-size: 16px; cursor: pointer; font-weight: bold; }
    .link { margin-top: 15px; display: block; color: #38bdf8; text-decoration: none; font-size: 14px; }
</style>
</head>
<body>
    <div class="card">
        <h2>Giriş Yap</h2>
        <form method="POST">
            <input type="text" name="username" placeholder="Kullanıcı Adı" required>
            <input type="password" name="password" placeholder="Şifre" required>
            <button type="submit">Giriş Yap</button>
        </form>
        <a href="/register" class="link">Kayıt ol</a>
    </div>
</body>
</html>
"""

REGISTER_HTML = """
<!DOCTYPE html>
<html lang="tr">
<head><meta charset="UTF-8"><title>Kayıt Ol</title>
<style>
    body { font-family: 'Segoe UI', sans-serif; background: #0f172a; color: white; height: 100vh; display: flex; justify-content: center; align-items: center; margin: 0; }
    .card { background: #1e293b; padding: 40px; border-radius: 12px; width: 320px; text-align: center; box-shadow: 0 10px 25px rgba(0,0,0,0.3); }
    input { width: 100%; padding: 12px; margin: 10px 0; border: 1px solid #334155; background: #0f172a; color: white; border-radius: 6px; box-sizing: border-box; }
    button { background: #10b981; color: white; border: none; padding: 12px; width: 100%; border-radius: 6px; font-size: 16px; cursor: pointer; font-weight: bold; }
    .link { margin-top: 15px; display: block; color: #38bdf8; text-decoration: none; font-size: 14px; }
</style>
</head>
<body>
    <div class="card">
        <h2>Kayıt Ol</h2>
        <form method="POST">
            <input type="text" name="username" placeholder="Kullanıcı Adı" required>
            <input type="password" name="password" placeholder="Şifre" required>
            <button type="submit">Kayıt Ol</button>
        </form>
        <a href="/" class="link">Geri dön</a>
    </div>
</body>
</html>
"""

UNLOCK_PAGE_HTML = """
<!DOCTYPE html>
<html lang="tr">
<head><meta charset="UTF-8"><title>PC Kilidini Aç</title>
<style>
    body { font-family: 'Segoe UI', sans-serif; background: #0f172a; color: white; height: 100vh; display: flex; justify-content: center; align-items: center; margin: 0; }
    .card { background: #1e293b; padding: 40px; border-radius: 16px; width: 320px; text-align: center; box-shadow: 0 10px 25px rgba(0,0,0,0.3); }
    h2 { color: #38bdf8; margin-bottom: 10px; }
    p { color: #94a3b8; font-size: 14px; margin-bottom: 25px; }
    button { background: #10b981; color: white; border: none; padding: 15px; width: 100%; border-radius: 8px; font-size: 16px; cursor: pointer; font-weight: bold; }
</style>
</head>
<body>
    <div class="card">
        <h2>Bilgisayar Kilidi</h2>
        <p>Butona basarak bilgisayarınızın kilidini açın.</p>
        <form method="POST"><button type="submit">Kilidi Aç</button></form>
    </div>
</body>
</html>
"""

UNAUTHORIZED_HTML = """
<!DOCTYPE html>
<html lang="tr">
<head><meta charset="UTF-8"><title>Erişim Engellendi</title></head>
<body style="background:#0f172a; color:#ef4444; font-family:sans-serif; text-align:center; padding-top:100px;">
    <h1>Erişim Engellendi!</h1>
    <p style="color:#94a3b8;">Bu telefonun IP adresi yöneticisi tarafından yetkilendirilmemiş.</p>
</body>
</html>
"""

@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        conn = sqlite3.connect("database.db")
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE username = ? AND password = ?", (username, password))
        user = cursor.fetchone()
        conn.close()
        if user:
            session["user"] = username
            return redirect(url_for("dashboard"))
    return render_template_string(INDEX_HTML)

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        try:
            conn = sqlite3.connect("database.db")
            cursor = conn.cursor()
            cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password))
            conn.commit()
            conn.close()
            return redirect(url_for("login"))
        except:
            return "Bu kullanıcı adı alınmış!"
    return render_template_string(REGISTER_HTML)

@app.route("/dashboard")
def dashboard():
    if "user" not in session: return redirect(url_for("login"))
    return f"<body style='background:#0f172a; color:white; text-align:center; padding-top:100px; font-family:sans-serif;'><h1>Hoş geldin, {session['user']}!</h1><p>Yönetici Paneli üzerinden IP tanımlayabilirsiniz.</p></body>"

# Masaüstü programından IP ekleme API'si
@app.route("/api/add-ip", methods=["POST"])
def add_ip():
    data = request.json
    username = data.get("username")
    password = data.get("password")
    ip_address = data.get("ip_address")

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    # Önce şifreyi doğrula
    cursor.execute("SELECT * FROM users WHERE username = ? AND password = ?", (username, password))
    user = cursor.fetchone()

    if not user:
        conn.close()
        return jsonify({"status": "error", "message": "Geçersiz kullanıcı adı veya şifre!"}), 401

    # IP'yi kaydet (Eğer daha önce eklenmediyse)
    cursor.execute("SELECT * FROM allowed_ips WHERE username = ? AND ip_address = ?", (username, ip_address))
    existing = cursor.fetchone()
    if not existing:
        cursor.execute("INSERT INTO allowed_ips (username, ip_address) VALUES (?, ?)", (username, ip_address))
        conn.commit()
    conn.close()
    return jsonify({"status": "success", "message": "IP başarıyla yetkilendirildi!"})

@app.route("/mobile-unlock", methods=["GET", "POST"])
def mobile_unlock():
    session_id = request.args.get("session")
    username = request.args.get("user") # Hangi kullanıcıya ait oturum
    
    # İstemci IP'sini al
    client_ip = request.headers.get('X-Forwarded-For', request.remote_addr)
    if client_ip: client_ip = client_ip.split(',')[0].strip()

    # Eğer o kullanıcı için hiç IP tanımlanmamışsa veya IP yetkili ise izin ver
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM allowed_ips WHERE username = ?", (username,))
    count = cursor.fetchone()[0]
    conn.close()

    if count > 0 and not check_ip_permission(username, client_ip):
        return render_template_string(UNAUTHORIZED_HTML), 403

    if "user" not in session: return redirect(url_for("login"))
    
    if request.method == "POST":
        conn = sqlite3.connect("database.db")
        cursor = conn.cursor()
        cursor.execute("REPLACE INTO sessions (session_id, status) VALUES (?, ?)", (session_id, "approved"))
        conn.commit()
        conn.close()
        return "<body style='background:#0f172a; color:#10b981; font-family:sans-serif; text-align:center; padding-top:100px;'><h1>Başarılı!</h1><p>Kilidi açılıyor...</p></body>"
        
    return render_template_string(UNLOCK_PAGE_HTML)

@app.route("/api/check-status", methods=["GET"])
def check_status():
    session_id = request.args.get("session")
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    cursor.execute("SELECT status FROM sessions WHERE session_id = ?", (session_id,))
    row = cursor.fetchone()
    conn.close()
    if row and row[0] == "approved": return jsonify({"status": "unlocked"})
    return jsonify({"status": "waiting"})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
