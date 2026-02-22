from flask import Flask, render_template, request, redirect, jsonify, session
import os, sqlite3, time, requests, random, hashlib, secrets

# =====================================
# CONFIG
# =====================================
WAQI_TOKEN = "ccdbd0d75316aa1f899022e6166c16f24a3346c3"
DB = "city.db"

# Optional ML
USE_ML = True
try:
    import numpy as np
    from sklearn.linear_model import LinearRegression
except Exception:
    USE_ML = False

app = Flask(__name__)
app.secret_key = secrets.token_hex(32)

# =====================================
# GENERATE REALISTIC BASE VALUES
# =====================================
def generate_base(city_type="medium"):
    base = {
        "traffic": random.randint(4,8),
        "pollution": random.randint(4,8),
        "cost": random.randint(5,8),
        "safety": random.randint(5,8),
        "water": random.randint(5,8),
        "healthcare": random.randint(5,9),
        "heat": random.randint(4,8),
        "responseTime": random.randint(4,7),
        "complaints": random.randint(3,7)
    }

    if city_type == "metro":
        base["traffic"] = random.randint(7,9)
        base["cost"] = random.randint(7,9)

    if city_type == "coastal":
        base["water"] = random.randint(7,9)
        base["heat"] = random.randint(6,8)

    if city_type == "north":
        base["heat"] = random.randint(7,9)
        base["water"] = random.randint(4,6)

    return base

# =====================================
# ALL 31 DISTRICT HQs
# =====================================
cities = {
    "Bengaluru": {"lat": 12.9716, "lon": 77.5946, "base": generate_base("metro")},
    "Mysuru": {"lat": 12.2958, "lon": 76.6394, "base": generate_base()},
    "Hubballi": {"lat": 15.3647, "lon": 75.1240, "base": generate_base()},
    "Belagavi": {"lat": 15.8497, "lon": 74.4977, "base": generate_base("north")},
    "Kalaburagi": {"lat": 17.3297, "lon": 76.8343, "base": generate_base("north")},
    "Ballari": {"lat": 15.1394, "lon": 76.9214, "base": generate_base("north")},
    "Vijayapura": {"lat": 16.8302, "lon": 75.7100, "base": generate_base("north")},
    "Raichur": {"lat": 16.2076, "lon": 77.3463, "base": generate_base("north")},
    "Shivamogga": {"lat": 13.9299, "lon": 75.5681, "base": generate_base()},
    "Davangere": {"lat": 14.4644, "lon": 75.9218, "base": generate_base()},
    "Tumakuru": {"lat": 13.3379, "lon": 77.1022, "base": generate_base()},
    "Hassan": {"lat": 13.0072, "lon": 76.0963, "base": generate_base()},
    "Mandya": {"lat": 12.5218, "lon": 76.8951, "base": generate_base()},
    "Chitradurga": {"lat": 14.2250, "lon": 76.3980, "base": generate_base()},
    "Chikkamagaluru": {"lat": 13.3161, "lon": 75.7720, "base": generate_base()},
    "Kolar": {"lat": 13.1367, "lon": 78.1290, "base": generate_base()},
    "Bidar": {"lat": 17.9133, "lon": 77.5301, "base": generate_base("north")},
    "Bagalkot": {"lat": 16.1850, "lon": 75.6969, "base": generate_base("north")},
    "Gadag": {"lat": 15.4290, "lon": 75.6340, "base": generate_base()},
    "Haveri": {"lat": 14.7950, "lon": 75.3990, "base": generate_base()},
    "Koppal": {"lat": 15.3500, "lon": 76.1500, "base": generate_base("north")},
    "Udupi": {"lat": 13.3409, "lon": 74.7421, "base": generate_base("coastal")},
    "Mangaluru": {"lat": 12.9141, "lon": 74.8560, "base": generate_base("coastal")},
    "Karwar": {"lat": 14.8000, "lon": 74.1300, "base": generate_base("coastal")},
    "Kodagu": {"lat": 12.3375, "lon": 75.8069, "base": generate_base()},
    "Chamarajanagar": {"lat": 11.9261, "lon": 76.9400, "base": generate_base()},
    "Ramanagara": {"lat": 12.7200, "lon": 77.2800, "base": generate_base()},
    "Yadgir": {"lat": 16.7700, "lon": 77.1300, "base": generate_base("north")},
    "Vijayanagara": {"lat": 15.3300, "lon": 76.4600, "base": generate_base("north")},
    "Chikkaballapur": {"lat": 13.4350, "lon": 77.7270, "base": generate_base()},
    "Bengaluru Rural": {"lat": 13.2850, "lon": 77.6000, "base": generate_base()}
}

# =====================================
# DATABASE
# =====================================
def db():
    return sqlite3.connect(DB)

def init_db():
    con = db()
    cur = con.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            created_at INTEGER,
            last_login INTEGER
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS feedback (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            city TEXT,
            traffic INTEGER,
            pollution INTEGER,
            cost INTEGER,
            safety INTEGER,
            water INTEGER,
            healthcare INTEGER,
            heat INTEGER,
            responseTime INTEGER,
            complaints INTEGER,
            created_at INTEGER
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS pollution_cache (
            city TEXT PRIMARY KEY,
            aqi INTEGER,
            pm25 REAL,
            ts INTEGER
        )
    """)
    con.commit()
    con.close()

init_db()

# =====================================
# USER AUTHENTICATION
# =====================================
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(password, hash_val):
    return hash_password(password) == hash_val

def create_user(email, username, password):
    try:
        con = db()
        cur = con.cursor()
        cur.execute("""
            INSERT INTO users(email, username, password, created_at)
            VALUES(?, ?, ?, ?)
        """, (email, username, hash_password(password), int(time.time())))
        con.commit()
        con.close()
        return True
    except:
        return False

def get_user(username):
    con = db()
    cur = con.cursor()
    cur.execute("SELECT id, username, email, password FROM users WHERE username=?", (username,))
    user = cur.fetchone()
    con.close()
    return user

# =====================================
# POLLUTION FETCH WITH CACHE
# =====================================
def fetch_waqi_by_geo(lat, lon):
    if not WAQI_TOKEN:
        return None
    url = f"https://api.waqi.info/feed/geo:{lat};{lon}/?token={WAQI_TOKEN}"
    try:
        r = requests.get(url, timeout=5)
        js = r.json()
        if js["status"] == "ok":
            return js["data"]["aqi"]
    except:
        pass
    return None

def get_pollution(city):
    con = db()
    cur = con.cursor()
    cur.execute("SELECT aqi, ts FROM pollution_cache WHERE city=?", (city,))
    row = cur.fetchone()
    now = int(time.time())

    if row and now - row[1] < 1800:
        con.close()
        return row[0]

    lat, lon = cities[city]["lat"], cities[city]["lon"]
    aqi = fetch_waqi_by_geo(lat, lon)
    if aqi:
        cur.execute("INSERT OR REPLACE INTO pollution_cache(city,aqi,ts) VALUES(?,?,?)",
                    (city, aqi, now))
        con.commit()
    con.close()
    return aqi

# =====================================
# AI SCORE
# =====================================
def norm_high(v): return v/10
def norm_low(v): return (10-v)/10

def compute_score(f, aqi):
    score = 0
    score += 0.18 * norm_high(f["safety"])
    score += 0.15 * norm_high(f["healthcare"])
    score += 0.12 * norm_high(f["water"])
    score += 0.15 * norm_low(f["traffic"])
    score += 0.12 * norm_low(f["pollution"])
    score += 0.08 * norm_low(f["cost"])
    score += 0.08 * norm_low(f["heat"])
    score += 0.07 * norm_low(f["responseTime"])
    score += 0.05 * norm_low(f["complaints"])
    if aqi:
        score -= min(aqi/500,1)*0.1
    return round(score*100,2)

# =====================================
# ROUTES
# =====================================
@app.route("/")
def home():
    return render_template("index.html", cities=cities)

@app.route("/auth", methods=["GET", "POST"])
def auth():
    if request.method == "POST":
        action = request.form.get("action", "login")
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()
        email = request.form.get("email", "").strip()
        
        if action == "signup":
            # Sign up
            if not username or not password or not email:
                return render_template("auth.html", error="All fields required")
            if len(password) < 6:
                return render_template("auth.html", error="Password must be at least 6 characters")
            if create_user(email, username, password):
                session['user_id'] = username
                session['username'] = username
                return redirect("/dashboard")
            else:
                return render_template("auth.html", error="Email or username already exists")
        
        elif action == "login":
            # Login
            if not username or not password:
                return render_template("auth.html", error="Username and password required")
            
            user = get_user(username)
            if user and verify_password(password, user[3]):
                session['user_id'] = user[1]
                session['username'] = user[1]
                con = db()
                cur = con.cursor()
                cur.execute("UPDATE users SET last_login=? WHERE username=?", (int(time.time()), username))
                con.commit()
                con.close()
                return redirect("/dashboard")
            else:
                return render_template("auth.html", error="Invalid username or password")
    
    return render_template("auth.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/auth")

@app.route("/dashboard")
def dashboard():
    if 'username' not in session:
        return redirect("/auth")
    return render_template("dashboard.html", username=session['username'])

@app.route("/view/<city>")
def view_city(city):
    if city not in cities:
        return "City not found", 404

    f = cities[city]["base"]
    aqi = get_pollution(city)

    # Create pol dictionary like before
    pol = {
        "aqi": aqi,
        "source": "waqi" if aqi else "none",
        "stale": False
    }

    score = compute_score(f, aqi)

    return render_template("view.html",
                           city=city,
                           features=f,
                           score=score,
                           pol=pol)
@app.route("/feedback/<city>", methods=["GET", "POST"])
def feedback(city):
    if city not in cities:
        return "City not found", 404

    if request.method == "POST":
        fields = ["traffic","pollution","cost","safety","water","healthcare","heat","responseTime","complaints"]
        vals = []
        for f in fields:
            v = int(request.form.get(f, 5))
            v = max(1, min(10, v))
            vals.append(v)

        con = db()
        cur = con.cursor()
        cur.execute("""
            INSERT INTO feedback(city,traffic,pollution,cost,safety,water,healthcare,
                                 heat,responseTime,complaints,created_at)
            VALUES(?,?,?,?,?,?,?,?,?,?,?)
        """, (city, *vals, int(time.time())))
        con.commit()
        con.close()

        return redirect(f"/view/{city}")

    return render_template("feedback.html", city=city)

@app.route("/admin")
def admin():
    con = db()
    cur = con.cursor()
    cur.execute("SELECT * FROM feedback ORDER BY created_at DESC LIMIT 100")
    rows = cur.fetchall()
    con.close()
    return render_template("admin.html", feedback=rows)

@app.route("/api/heat")
def heat():
    pts=[]
    ranked=[]
    for city in cities:
        f = cities[city]["base"]
        aqi = get_pollution(city)
        score = compute_score(f, aqi)
        pts.append([cities[city]["lat"], cities[city]["lon"], score/100])
        ranked.append({"city":city,"score":score,"aqi":aqi})
    ranked.sort(key=lambda x:x["score"], reverse=True)
    return jsonify({"points":pts,"ranked":ranked})

if __name__ == "__main__":
    app.run(debug=True)
