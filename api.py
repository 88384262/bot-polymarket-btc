from flask import Flask, jsonify, make_response, request, send_from_directory
import json
import os
import time

app = Flask(__name__)

ARQ_MERC = os.getenv("ARQ_MERC", "btc_mercados_v21.json")
ARQ_MOD = os.getenv("ARQ_MOD", "btc_modelo_v21.json")
ARQ_ATUAL = os.getenv("ARQ_MERCADO_ATUAL", "btc_mercado_atual.json")

def ler_json(caminho, padrao={}):
    try:
        with open(caminho, 'r') as f:
            return json.load(f)
    except:
        return padrao

def add_cors(response):
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type,Authorization"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
    response.headers["Cache-Control"] = "no-cache"
    return response

@app.route("/api/signals", methods=["GET", "OPTIONS"])
def signals():
    if request.method == "OPTIONS":
        response = make_response("", 204)
        return add_cors(response)

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
            "apostou": atual.get("apostou",False)
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
        "stats": {"total":total,"hits":hits,"misses":misses,"rate":rate}
    }))
    return add_cors(response)

@app.route("/api/health", methods=["GET"])
def health():
    atual = ler_json(ARQ_ATUAL, {})
    tem_dados = bool(atual.get("sinal"))
    ts = atual.get("timestamp_abertura", 0)
    idade = int(time.time() - ts) if ts else 9999
    return add_cors(make_response(jsonify({
        "status": "ok",
        "scanner_online": tem_dados and idade < 600,
        "last_update": idade
    })))

@app.route("/", methods=["GET"])
def home():
    try:
        return send_from_directory(".", "index.html")
    except:
        return add_cors(make_response("BTC Signal Pro API - Online"))

@app.route("/health", methods=["GET"])
def health_simple():
    return add_cors(make_response(jsonify({"status":"ok"})))

def run_api():
    import threading
    port = int(os.environ.get("PORT", 5000))
    print(f"[API] Iniciando na porta {port}...")
    def _run():
        app.run(host="0.0.0.0", port=port, threaded=True, debug=False, use_reloader=False)
    t = threading.Thread(target=_run, daemon=True)
    t.start()
    print(f"[API] Servidor iniciado em http://0.0.0.0:{port}")
