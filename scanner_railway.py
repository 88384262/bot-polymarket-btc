#!/usr/bin/env python3
import requests
import json
import time
import os
from datetime import datetime

def log(msg):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[SCANNER][{ts}] {msg}", flush=True)

def get_btc():
    try:
        r = requests.get("https://api.binance.com/api/v3/ticker/price?symbol=BTCUSDT", timeout=5)
        return float(r.json()["price"]), time.time()
    except:
        return None, None

def enviar_sinal_para_api(direcao, preco, confianca):
    try:
        # ENDEREÇO CORRETO: localhost porque está NO MESMO CONTAINER
        url_api = "http://localhost:5000/api/novo_sinal"
        
        sinal = {
            'preco': f"{preco:,.2f}",
            'hora': datetime.now().strftime('%H:%M:%S'),
            'expira': '02:14',
            'confianca': str(round(confianca, 1)),
            'estrategia': 'Momentum Pro',
            'direcao': direcao,
            'ativo': 'BTC/USDT'
        }
        
        response = requests.post(url_api, json=sinal, timeout=3)
        if response.status_code == 201:
            log(f"🚀 SINAL ENVIADO COM SUCESSO PARA API! ({direcao})")
        else:
            log(f"⚠️ API respondeu com erro: {response.status_code}")
            
    except Exception as e:
        log(f"⚠️ Erro ao tentar enviar sinal: {e}")

def main():
    log("Scanner aguardando dados do mercado...")
    hist = []
    while True:
        btc, ts = get_btc()
        if btc:
            hist.append(btc)
            if len(hist) > 10: hist.pop(0)
            if len(hist) >= 2:
                diff = ((hist[-1] - hist[0]) / hist[0]) * 100
                if diff > 0.1:
                    enviar_sinal_para_api("ALTA", btc, 87)
                elif diff < -0.1:
                    enviar_sinal_para_api("BAIXA", btc, 87)
        time.sleep(10)

if __name__ == "__main__":
    main()
