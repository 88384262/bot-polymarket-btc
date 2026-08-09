from flask import Flask, jsonify, make_response
import json, os, time
from flask_cors import CORS

app = Flask(__name__)
# CORS mais permissivo
CORS(app, resources={r"/api/*": {"origins": "*", "methods": ["GET", "OPTIONS"], "allow_headers": "*"}})

ARQ_MERC = os.getenv("ARQ_MERC", "btc_mercados_v21.json")
ARQ_MOD = os.getenv("ARQ_MOD", "btc_modelo_v21.json")
ARQ_ATUAL = os.getenv("ARQ_MERCADO_ATUAL", "btc_mercado_atual.json")

def ler_json(caminho, padrao={}):
    try:
        with open(caminho, 'r') as f:
            return json.load(f)
    except:
        return padrao

@app.route("/api/signals")
def signals():
    atual = ler_json(ARQ_ATUAL, {})
    mercados = ler_json(ARQ_MERC, [])
    modelo = ler_json(ARQ_MOD, {"acertos":0,"erros":0,"bank":0})

    sinal = atual.get("sinal","")
    current = None
    if sinal in ("UP","DOWN"):
        tf = atual.get("timestamp_fechamento",0)
        tr = max(0, tf - time.time())
        current = {
            "type": "up" if sinal=="UP" else "down",
            "confidence": int(atual.get("score",50)),
            "price": round(atual.get("preco_abertura",0),2),
            "expires_in": f"{int(tr//60):02d}:{int(tr%60):02d}",
            "apostou": atual.get("apostou",False),
            "vs_open": round(atual.get("vs_open",0.0),3),
            "rsi": round(atual.get("rsi",50.0),1),
            "mom": round(atual.get("mom",0.0),4)
        }

    history = []
    for m in reversed(mercados):
        s = m.get("sinal","")
        if not s: continue
        a = m.get("apostou",False)
        if not a: continue
        r = m.get("resultado","")
        res = "hit" if s==r else "miss"
        from datetime import datetime
        ta = m.get("timestamp_abertura",0)
        hora = datetime.fromtimestamp(ta).strftime("%H:%M") if ta else "--:--"
        history.append({
            "type": "up" if s=="UP" else "down",
            "confidence": int(m.get("score",50)),
            "time": hora,
            "result": res
        })

    history = history[:10]

    hits = modelo.get("acertos",0)
    misses = modelo.get("erros",0)
    total = hits + misses
    rate = round((hits/total)*100,2) if total else 0

    response = make_response(jsonify({
        "current": current,
        "history": history,
        "stats": {"total":total,"hits":hits,"misses":misses,"rate":rate},
        "server_time": time.time()
    }))
    # Headers CORS explicitos
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "GET, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "*"
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    return response

@app.route("/")
def home():
    return "BTC Signal Pro API - Online"

def run_api():
    import threading
    port = int(os.environ.get("PORT", 5000))
    print(f"[API] Iniciando na porta {port}...")
    def _run():
        try:
            app.run(host="0.0.0.0", port=port, threaded=True, debug=False, use_reloader=False)
        except Exception as e:
            print(f"[API] Erro no servidor: {e}")
    t = threading.Thread(target=_run, daemon=True)
    t.start()
    print(f"[API] Servidor iniciado em http://0.0.0.0:{port}")
