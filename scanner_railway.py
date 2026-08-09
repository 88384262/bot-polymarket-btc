#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Scanner Polymarket BTC v21.1 - VERSAO NUVEM (Railway)
- Sem limpar tela (nao tem terminal na nuvem)
- Logs com timestamp
- Salva btc_mercado_atual.json para o bot ler
- Multiplas fontes de preco com retry e backoff
"""

import requests
import json
import time
import os
import sys
from datetime import datetime, timezone

# ============================================================================
# CONFIG
# ============================================================================
PAPER = True
STAKE = 5.0
MIN_SCANS = 2

MOM_FORTE = 0.08
MOM_NORMAL = 0.03
MOM_ULTIMA = 0.015
PROX_PEN = 0.02
ATR_MIN = 0.008
PRECO_TRAV_LIM = 8

RSI_P = 14
EMA_P = 20
BB_P = 20
BB_D = 2.0
MOM_C = 3
TEND_C = 8

URL_CL = "https://data.chain.link/api/v1/feeds/1/0xF4030086522a5bEEa4988F8cA5B36dbC97BeE88c/rounds?limit=1"
URL_CG = "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd"
URL_CC = "https://min-api.cryptocompare.com/data/price?fsym=BTC&tsyms=USD"

ARQ_MOD = "btc_modelo_v21.json"
ARQ_MERC = "btc_mercados_v21.json"
ARQ_MERCADO_ATUAL = "btc_mercado_atual.json"

# ============================================================================
# LOGS NA NUVEM
# ============================================================================
def log(msg):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[SCANNER][{ts}] {msg}", flush=True)

def carregar_json(caminho, padrao):
    try:
        with open(caminho, 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return padrao

def salvar_json(caminho, dados):
    try:
        with open(caminho + ".tmp", 'w', encoding='utf-8') as f:
            json.dump(dados, f, indent=2)
        os.replace(caminho + ".tmp", caminho)
    except Exception as e:
        log(f"Erro ao salvar {caminho}: {e}")

# ============================================================================
# ESTADO
# ============================================================================
hist_btc = []
merc_atual = None
merc_fechados = []
acertos = 0
erros = 0
bank = 0.0
ult_fonte = "-"
last_scan_ts = 0

# ============================================================================
# PRECO BTC - MULTIPLAS FONTES COM RETRY
# ============================================================================
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}

def get_btc_chainlink():
    try:
        r = requests.get(URL_CL, timeout=5, headers=HEADERS)
        r.raise_for_status()
        data = r.json()
        rounds = data.get("rounds", [])
        if rounds:
            price_raw = float(rounds[0].get("answer", 0))
            return price_raw / 1e8, time.time()
    except Exception:
        pass
    return None

def get_btc_binance():
    try:
        r = requests.get("https://api.binance.com/api/v3/ticker/price?symbol=BTCUSDT", timeout=5, headers=HEADERS)
        r.raise_for_status()
        preco = float(r.json()["price"])
        return preco, time.time()
    except Exception:
        pass
    return None

def get_btc_coinbase():
    try:
        r = requests.get("https://api.coinbase.com/v2/exchange-rates?currency=BTC", timeout=5, headers=HEADERS)
        r.raise_for_status()
        preco = float(r.json()["data"]["rates"]["USD"])
        return preco, time.time()
    except Exception:
        pass
    return None

def get_btc_kraken():
    try:
        r = requests.get("https://api.kraken.com/0/public/Ticker?pair=XBTUSD", timeout=5, headers=HEADERS)
        r.raise_for_status()
        data = r.json()["result"]["XXBTZUSD"]
        preco = float(data["c"][0])
        return preco, time.time()
    except Exception:
        pass
    return None

def get_btc_coingecko():
    try:
        r = requests.get(URL_CG, timeout=10, headers=HEADERS)
        r.raise_for_status()
        preco = float(r.json()["bitcoin"]["usd"])
        return preco, time.time()
    except Exception:
        pass
    return None

def get_btc_cryptocompare():
    try:
        r = requests.get(URL_CC, timeout=10, headers=HEADERS)
        r.raise_for_status()
        preco = float(r.json()["USD"])
        return preco, time.time()
    except Exception:
        pass
    return None

def get_btc():
    global ult_fonte
    fontes = [
        (get_btc_binance, "Binance"),
        (get_btc_coinbase, "Coinbase"),
        (get_btc_kraken, "Kraken"),
        (get_btc_chainlink, "Chainlink"),
        (get_btc_coingecko, "CoinGecko"),
        (get_btc_cryptocompare, "CryptoCompare"),
    ]
    for fn, nome in fontes:
        result = fn()
        if result:
            ult_fonte = nome
            return result
    if hist_btc:
        ult_fonte = "Cache"
        return hist_btc[-1], time.time()
    raise Exception("Todas fontes falharam")

# ============================================================================
# INDICADORES
# ============================================================================
def rsi(dados, p=RSI_P):
    n = len(dados)
    if n < 2:
        return 50.0
    j = min(p, n - 1)
    g, pe = [], []
    for i in range(1, j + 1):
        diff = dados[-i] - dados[-i - 1]
        (g if diff > 0 else pe).append(abs(diff))
    if not g and not pe:
        return 50.0
    ag = sum(g) / j if g else 0.0
    al = sum(pe) / j if pe else 0.0
    if al == 0:
        return 100.0 if ag > 0 else 50.0
    return 100.0 - (100.0 / (1.0 + ag / al))

def ema(dados, p=EMA_P):
    n = len(dados)
    if n == 0:
        return 0.0
    if n < p:
        return sum(dados) / n
    s = sum(dados[:p]) / p
    k = 2.0 / (p + 1)
    e = s
    for pr in dados[p:]:
        e = pr * k + e * (1 - k)
    return e

def bb(dados, p=BB_P, d=BB_D):
    n = len(dados)
    if n < p:
        m = sum(dados) / n if n else 0.0
        return m, m, m
    j = dados[-p:]
    m = sum(j) / p
    v = sum((x - m) ** 2 for x in j) / p
    sd = v ** 0.5
    return m + d * sd, m, m - d * sd

def atr(dados):
    n = len(dados)
    if n < 2:
        return 0.0
    j = dados[-min(14, n):]
    m = sum(j) / len(j)
    v = sum((x - m) ** 2 for x in j) / len(j)
    return v ** 0.5

def mom(dados, c=MOM_C):
    n = len(dados)
    if n < c + 1:
        return 0.0
    return ((dados[-1] - dados[-(c + 1)]) / dados[-(c + 1)]) * 100.0

def tend(dados, c=TEND_C):
    n = len(dados)
    if n < c + 1:
        return "DESCONHECIDO"
    v = ((dados[-1] - dados[-(c + 1)]) / dados[-(c + 1)]) * 100.0
    return "ALTA" if v > 0.03 else ("BAIXA" if v < -0.03 else "LATERAL")

def travado(dados, lim=PRECO_TRAV_LIM):
    return len(dados) >= lim and all(x == dados[-lim] for x in dados[-lim:])

# ============================================================================
# MODELO
# ============================================================================
def carrega_mod():
    if os.path.exists(ARQ_MOD):
        try:
            with open(ARQ_MOD, "r") as f:
                d = json.load(f)
            return d.get("acertos", 0), d.get("erros", 0), d.get("bank", 0.0)
        except:
            pass
    return 0, 0, 0.0

def salva_mod():
    try:
        with open(ARQ_MOD, "w") as f:
            json.dump({"acertos": acertos, "erros": erros, "bank": bank}, f)
    except:
        pass

# ============================================================================
# DECISAO
# ============================================================================
def score_sinal(btc, vs, rsi_v, ema_v, bb_s, bb_i, mom_v, tend_v):
    sc = 50.0
    rz = []
    if rsi_v > 70:
        sc -= 4.0; rz.append(f"RSI alto ({rsi_v:.0f})")
    elif rsi_v < 30:
        sc += 4.0; rz.append(f"RSI baixo ({rsi_v:.0f})")
    if mom_v > MOM_FORTE:
        sc += 6.0; rz.append("Mom forte UP")
    elif mom_v < -MOM_FORTE:
        sc -= 6.0; rz.append("Mom forte DOWN")
    elif mom_v > MOM_NORMAL:
        sc += 3.0; rz.append("Mom UP")
    elif mom_v < -MOM_NORMAL:
        sc -= 3.0; rz.append("Mom DOWN")
    if tend_v == "ALTA":
        sc += 4.0; rz.append("Tend ALTA")
    elif tend_v == "BAIXA":
        sc -= 4.0; rz.append("Tend BAIXA")
    if btc > bb_s:
        sc -= 3.0; rz.append("Acima BB")
    elif btc < bb_i:
        sc += 3.0; rz.append("Abaixo BB")
    if btc > ema_v:
        sc += 2.0; rz.append("Acima EMA")
    elif btc < ema_v:
        sc -= 2.0; rz.append("Abaixo EMA")
    if vs > 0.01:
        sc += 5.0; rz.append(f"Subiu {vs:.3f}%")
    elif vs < -0.01:
        sc -= 5.0; rz.append(f"Caiu {vs:.3f}%")
    if abs(vs) < PROX_PEN:
        sc -= 3.0; rz.append(f"Prox abert ({vs:.3f}%)")
    sc = max(5.0, min(95.0, sc))
    if sc >= 53:
        s = "UP"
    elif sc <= 47:
        s = "DOWN"
    else:
        s = "AGUARDAR"
    return sc, s, rz

def pode_apostar(m, sc, s, mom_v, atr_p, tempo_r):
    n = m.get("scans", 0)
    if tempo_r > 285:
        return False, "coleta (15s)"
    if n < MIN_SCANS:
        return False, f"dados ({n}/{MIN_SCANS})"
    if travado(hist_btc):
        return False, "preco travado"
    if atr_p < ATR_MIN:
        return False, f"volatilidade baixa"
    if abs(sc - 50.0) < 3.0:
        return False, f"edge baixo ({abs(sc-50):.1f})"
    if s == "AGUARDAR":
        if tempo_r <= 60 and abs(mom_v) >= MOM_ULTIMA:
            return True, "ultima chance"
        return False, "sem sinal"
    return True, "ok"

# ============================================================================
# SALVA MERCADO ATUAL PARA O BOT
# ============================================================================
def salva_mercado_atual():
    if merc_atual is None:
        return
    try:
        with open(ARQ_MERCADO_ATUAL + ".tmp", "w") as f:
            json.dump(merc_atual, f, indent=2)
        os.replace(ARQ_MERCADO_ATUAL + ".tmp", ARQ_MERCADO_ATUAL)
    except Exception as e:
        log(f"Erro ao salvar mercado atual: {e}")

# ============================================================================
# PERSISTENCIA
# ============================================================================
def carrega_merc():
    global merc_fechados
    if os.path.exists(ARQ_MERC):
        try:
            with open(ARQ_MERC, "r") as f:
                merc_fechados = json.load(f)
        except:
            pass

def salva_merc():
    try:
        with open(ARQ_MERC + ".tmp", "w") as f:
            json.dump(merc_fechados, f, indent=2)
        os.replace(ARQ_MERC + ".tmp", ARQ_MERC)
    except:
        pass

# ============================================================================
# LOOP
# ============================================================================
def detecta(btc, ts):
    global merc_atual
    ta = int(ts)
    ti = (ta // 300) * 300
    tf = ti + 300
    if merc_atual is None or ti != merc_atual.get("timestamp_abertura", 0):
        if merc_atual is not None:
            fecha(merc_atual, btc, ts)
        merc_atual = {
            "timestamp_abertura": ti,
            "timestamp_fechamento": tf,
            "preco_abertura": btc,
            "scans": 0,
            "sinal": None,
            "score": 50.0,
            "stake": 0.0,
            "apostou": False,
            "timestamp_aposta": None,
            "resultado": None,
            "rsi": 50.0,
            "mom": 0.0,
            "tend": "DESCONHECIDO",
            "vs_open": 0.0,
        }
        hist_btc.clear()
    return merc_atual

def fecha(m, btc, ts):
    global acertos, erros, bank
    pf = hist_btc[-1] if hist_btc else btc
    pa = m.get("preco_abertura", pf)
    res = "UP" if pf >= pa else "DOWN"
    m["preco_fechamento"] = pf
    m["resultado"] = res
    m["timestamp_fechamento_real"] = ts
    si = m.get("sinal")
    st = m.get("stake", 0.0)
    ap = m.get("apostou", False)
    if ap and si:
        if si == res:
            acertos += 1
            bank += st
        else:
            erros += 1
            bank -= st
    merc_fechados.append(m)
    salva_merc()
    salva_mod()

def do_scan():
    global merc_atual, acertos, erros, bank, last_scan_ts
    btc = None
    ts = None
    for tentativa in range(3):
        try:
            btc, ts = get_btc()
            break
        except Exception as e:
            log(f"Tentativa {tentativa+1}/3 falhou: {e}")
            time.sleep(2 ** tentativa)
    else:
        log("Erro no scan: Todas fontes falharam apos 3 tentativas")
        return
    try:
        detecta(btc, ts)
        if merc_atual is None:
            return
        if not hist_btc or btc != hist_btc[-1]:
            hist_btc.append(btc)
        merc_atual["scans"] = merc_atual.get("scans", 0) + 1
        tr = merc_atual["timestamp_fechamento"] - ts
        merc_atual["tempo_restante"] = tr
        pa = merc_atual["preco_abertura"]
        vs = ((btc - pa) / pa) * 100.0 if pa else 0.0
        rsi_v = rsi(hist_btc)
        ema_v = ema(hist_btc)
        bb_s, _, bb_i = bb(hist_btc)
        at = atr(hist_btc)
        atr_p = (at / btc) * 100.0 if btc else 0.0
        mom_v = mom(hist_btc)
        tend_v = tend(hist_btc)
        sc, si, rz = score_sinal(btc, vs, rsi_v, ema_v, bb_s, bb_i, mom_v, tend_v)
        merc_atual["score"] = sc
        pd, blk = pode_apostar(merc_atual, sc, si, mom_v, atr_p, tr)
        if pd and not merc_atual.get("apostou", False):
            merc_atual["sinal"] = si
            merc_atual["stake"] = STAKE
            merc_atual["apostou"] = True
            merc_atual["timestamp_aposta"] = ts
            merc_atual["rsi"] = rsi_v
            merc_atual["mom"] = mom_v
            merc_atual["tend"] = tend_v
            merc_atual["vs_open"] = vs
            log(f"APOSTA: {si} | Score: {sc:.1f} | BTC: ${btc:,.2f} | Tempo restante: {int(tr)}s | Fonte: {ult_fonte}")
        elif not pd and not merc_atual.get("apostou", False):
            merc_atual["sinal"] = si
            merc_atual["vs_open"] = vs
            merc_atual["rsi"] = rsi_v
            merc_atual["mom"] = mom_v
            merc_atual["tend"] = tend_v
            merc_atual["atr_p"] = atr_p
        salva_mercado_atual()
    except Exception as e:
        log(f"Erro no scan: {e}")

# ============================================================================
# MAIN
# ============================================================================
def main():
    global acertos, erros, bank, last_scan_ts
    acertos, erros, bank = carrega_mod()
    carrega_merc()
    log("=" * 50)
    log("SCANNER POLYMARKET BTC v21.1 - MODO NUVEM")
    log(f"Stake: ${STAKE} | PAPER: {PAPER}")
    log("=" * 50)
    do_scan()
    last_scan_ts = time.time()
    try:
        while True:
            now = time.time()
            if now - last_scan_ts >= 10:
                do_scan()
                last_scan_ts = now
            time.sleep(1)
    except KeyboardInterrupt:
        log("Scanner parado.")
        salva_merc()
        salva_mod()

if __name__ == "__main__":
    main()
