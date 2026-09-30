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
            password TEXT,
            auth_code TEXT
        )
    """)
    conn.commit()
    conn.close()

init_db()

# HTML Arayüzleri (Tek dosya içinde modern şık tasarım)
INDEX_HTML = """
<!DOCTYPE html>
<html lang="tr">
<head>
    <meta charset="UTF-8">
    <title>Güvenli Kilit Paneli</title>
    <style>
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%); height: 100vh; display: flex; justify-content: center; align-items: center; margin: 0; }
        .card { background: white; padding: 40px; border-radius: 12px; box-shadow: 0 10px 25px rgba(0,0,0,0.1); width: 350px; text-align: center; }
        h2 { color: #333; margin-bottom: 20px; }
        input { width: 100%; padding: 12px; margin: 10px 0; border: 1px solid #ddd; border-radius: 6px; box-sizing: border-box; font-size: 14px; }
        button { background: #4f46e5; color: white; border: none; padding: 12px; width: 100%; border-radius: 6px; font-size: 16px; cursor: pointer; transition: background 0.3s; }
        button:hover { background: #4338ca; }
        .error { color: #ef4444; font-size: 13px; margin-top: 10px; }
        .link { margin-top: 15px; display: block; color: #4f46e5; text-decoration: none; font-size: 14px; }
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
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%); height: 100vh; display: flex; justify-content: center; align-items: center; margin: 0; }
        .card { background: white; padding: 40px; border-radius: 12px; box-shadow: 0 10px 25px rgba(0,0,0,0.1); width: 350px; text-align: center; }
        h2 { color: #333; margin-bottom: 20px; }
        input { width: 100%; padding: 12px; margin: 10px 0; border: 1px solid #ddd; border-radius: 6px; box-sizing: border-box; font-size: 14px; }
        button { background: #10b981; color: white; border: none; padding: 12px; width: 100%; border-radius: 6px; font-size: 16px; cursor: pointer; transition: background 0.3s; }
        button:hover { background: #059669; }
        .link { margin-top: 15px; display: block; color: #4f46e5; text-decoration: none; font-size: 14px; }
    </style>
</head>
<body>
    <div class="card">
        <h2>Hesap Oluştur</h2>
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

PANEL_HTML = """
<!DOCTYPE html>
<html lang="tr">
<head>
    <meta charset="UTF-8">
    <title>Mobil Kilit Kontrolü</title>
    <style>
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: #0f172a; color: white; height: 100vh; display: flex; justify-content: center; align-items: center; margin: 0; }
        .card { background: #1e293b; padding: 40px; border-radius: 16px; box-shadow: 0 10px 25px rgba(0,0,0,0.3); width: 320px; text-align: center; }
        h2 { margin-bottom: 10px; color: #38bdf8; }
        .code-box { background: #0f172a; border: 2px dashed #38bdf8; padding: 15px; font-size: 28px; font-weight: bold; letter-spacing: 5px; color: #f43f5e; margin: 20px 0; border-radius: 8px; }
        button { background: #ef4444; color: white; border: none; padding: 12px; width: 100%; border-radius: 8px; font-size: 16px; cursor: pointer; font-weight: bold; transition: background 0.3s; }
        button:hover { background: #dc2626; }
        p { color: #94a3b8; font-size: 13px; }
    </style>
</head>
<body>
    <div class="card">
        <h2>Mobil Kumanda</h2>
        <p>Bilgisayarın kilidini açmak için aşağıdaki aktif kodu kullanabilir veya kilitle butonuna basabilirsin:</p>
        <div class="code-box">{{ code }}</div>
        <form action="/lock-pc" method="POST">
            <button type="submit">Bilgisayarı Uzaktan Kilitle</button>
        </form>
    </div>
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
            return redirect(url_for("panel"))
        else:
            error = "Hatalı kullanıcı adı veya şifre!"
            
    return render_template_string(INDEX_HTML, error=error)

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        initial_code = "".join(random.choices(string.digits, k=6))
        
        try:
            conn = sqlite3.connect("database.db")
            cursor = conn.cursor()
            cursor.execute("INSERT INTO users (username, password, auth_code) VALUES (?, ?, ?)", (username, password, initial_code))
            conn.commit()
            conn.close()
            return redirect(url_for("login"))
        except:
            return "Bu kullanıcı adı zaten alınmış!"
            
    return render_template_string(REGISTER_HTML)

@app.route("/panel")
def panel():
    if "user" not in session:
        return redirect(url_for("login"))
    
    username = session["user"]
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    cursor.execute("SELECT auth_code FROM users WHERE username = ?", (username,))
    row = cursor.fetchone()
    conn.close()
    
    return render_template_string(PANEL_HTML, code=row[0] if row else "000000")

@app.route("/lock-pc", methods=["POST"])
def lock_pc():
    # Bilgisayar tarafındaki script bu endpoint'i kontrol edip kilitlenebilir
    return "Komut gönderildi."

# Bilgisayarın kilidi açmak için sorguladığı API
@app.route("/api/verify", methods=["POST"])
def verify():
    data = request.json
    username = data.get("username")
    code = data.get("code")
    
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE username = ? AND auth_code = ?", (username, code))
    user = cursor.fetchone()
    
    if user:
        # Kod kullanıldıktan sonra güvenlik için hemen yeni bir kod üretelim
        new_code = "".join(random.choices(string.digits, k=6))
        cursor.execute("UPDATE users SET auth_code = ? WHERE username = ?", (new_code, username))
        conn.commit()
        conn.close()
        return jsonify({"status": "success"})
    
    conn.close()
    return jsonify({"status": "error"})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)