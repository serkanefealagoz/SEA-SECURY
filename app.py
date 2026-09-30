from flask import Flask, render_template_string, request, redirect, url_for, session, jsonify
import sqlite3
import random
import string

app = Flask(__name__)
app.secret_key = "cok-gizli-guvenlik-anahtari"

# Veritabanı Kurulumu
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
    # QR Oturum Tablosu
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sessions (
            session_id TEXT PRIMARY KEY,
            status TEXT
        )
    """)
    conn.commit()
    conn.close()

init_db()

INDEX_HTML = """
<!DOCTYPE html>
<html lang="tr">
<head>
    <meta charset="UTF-8">
    <title>Giriş Yap</title>
    <style>
        body { font-family: 'Segoe UI', sans-serif; background: #0f172a; color: white; height: 100vh; display: flex; justify-content: center; align-items: center; margin: 0; }
        .card { background: #1e293b; padding: 40px; border-radius: 12px; width: 320px; text-align: center; box-shadow: 0 10px 25px rgba(0,0,0,0.3); }
        input { width: 100%; padding: 12px; margin: 10px 0; border: 1px solid #334155; background: #0f172a; color: white; border-radius: 6px; box-sizing: border-box; }
        button { background: #4f46e5; color: white; border: none; padding: 12px; width: 100%; border-radius: 6px; font-size: 16px; cursor: pointer; font-weight: bold; }
        button:hover { background: #4338ca; }
        .error { color: #ef4444; font-size: 13px; margin-top: 10px; }
        .link { margin-top: 15px; display: block; color: #38bdf8; text-decoration: none; font-size: 14px; }
    </style>
</head>
<body>
    <div class="card">
        <h2>Giriş Yap</h2>
        {% if error %}<div class="error">{{ error }}</div>{% endif %}
        <form method="POST">
            <input type="text" name="username" placeholder="Kullanıcı Adı" required>
            <input type="password" name="password" placeholder="Şifre" required>
            <button type="submit">Giriş Yap</button>
        </form>
        <a href="/register" class="link">Hesabın yok mu? Kayıt ol</a>
    </div>
</body>
</html>
"""

REGISTER_HTML = """
<!DOCTYPE html>
<html lang="tr">
<head>
    <meta charset="UTF-8">
    <title>Kayıt Ol</title>
    <style>
        body { font-family: 'Segoe UI', sans-serif; background: #0f172a; color: white; height: 100vh; display: flex; justify-content: center; align-items: center; margin: 0; }
        .card { background: #1e293b; padding: 40px; border-radius: 12px; width: 320px; text-align: center; box-shadow: 0 10px 25px rgba(0,0,0,0.3); }
        input { width: 100%; padding: 12px; margin: 10px 0; border: 1px solid #334155; background: #0f172a; color: white; border-radius: 6px; box-sizing: border-box; }
        button { background: #10b981; color: white; border: none; padding: 12px; width: 100%; border-radius: 6px; font-size: 16px; cursor: pointer; font-weight: bold; }
        button:hover { background: #059669; }
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
        <a href="/" class="link">Giriş sayfasına dön</a>
    </div>
</body>
</html>
"""

UNLOCK_PAGE_HTML = """
<!DOCTYPE html>
<html lang="tr">
<head>
    <meta charset="UTF-8">
    <title>PC Kilidini Aç</title>
    <style>
        body { font-family: 'Segoe UI', sans-serif; background: #0f172a; color: white; height: 100vh; display: flex; justify-content: center; align-items: center; margin: 0; }
        .card { background: #1e293b; padding: 40px; border-radius: 16px; width: 320px; text-align: center; box-shadow: 0 10px 25px rgba(0,0,0,0.3); }
        h2 { color: #38bdf8; margin-bottom: 10px; }
        p { color: #94a3b8; font-size: 14px; margin-bottom: 25px; }
        button { background: #10b981; color: white; border: none; padding: 15px; width: 100%; border-radius: 8px; font-size: 16px; cursor: pointer; font-weight: bold; transition: background 0.3s; }
        button:hover { background: #059669; }
    </style>
</head>
<body>
    <div class="card">
        <h2>Bilgisayar Kilidi</h2>
        <p>Aşağıdaki butona basarak bilgisayarınızın kilidini anında açabilirsiniz.</p>
        <form method="POST">
            <button type="submit">Kilidi Aç</button>
        </form>
    </div>
</body>
</html>
"""

SUCCESS_HTML = """
<!DOCTYPE html>
<html lang="tr">
<head><meta charset="UTF-8"><title>Başarılı</title></head>
<body style="background:#0f172a; color:white; font-family:sans-serif; text-align:center; padding-top:100px;">
    <h1 style="color:#10b981;">Komut Gönderildi!</h1>
    <p>Bilgisayarınızın kilidi açılıyor...</p>
</body>
</html>
"""

@app.route("/", methods=["GET", "POST"])
def login():
    error = None
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
        else:
            error = "Hatalı kullanıcı adı veya şifre!"
    return render_template_string(INDEX_HTML, error=error)

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
            return "Bu kullanıcı adı zaten alınmış!"
    return render_template_string(REGISTER_HTML)

@app.route("/dashboard")
def dashboard():
    if "user" not in session:
        return redirect(url_for("login"))
    return f"<body style='background:#0f172a; color:white; text-align:center; padding-top:100px; font-family:sans-serif;'><h1>Hoş geldin, {session['user']}!</h1><p>Bilgisayarını kilitlemek veya açmak için QR kodu okutman yeterlidir.</p></body>"

# QR Okutulduğunda açılacak sayfa
@app.route("/mobile-unlock", methods=["GET", "POST"])
def mobile_unlock():
    if "user" not in session:
        return redirect(url_for("login", next=request.url))
    
    session_id = request.args.get("session")
    if not session_id:
        return "Geçersiz oturum!"
        
    if request.method == "POST":
        conn = sqlite3.connect("database.db")
        cursor = conn.cursor()
        cursor.execute("REPLACE INTO sessions (session_id, status) VALUES (?, ?)", (session_id, "approved"))
        conn.commit()
        conn.close()
        return render_template_string(SUCCESS_HTML)
        
    return render_template_string(UNLOCK_PAGE_HTML)

# Bilgisayarın onay durumunu kontrol ettiği API
@app.route("/api/check-status", methods=["GET"])
def check_status():
    session_id = request.args.get("session")
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    cursor.execute("SELECT status FROM sessions WHERE session_id = ?", (session_id,))
    row = cursor.fetchone()
    conn.close()
    
    if row and row[0] == "approved":
        return jsonify({"status": "unlocked"})
    return jsonify({"status": "waiting"})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
