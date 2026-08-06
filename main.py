#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
POLYMARKET BTC - SCANNER + BOT TELEGRAM (NUVEM)
Roda scanner e bot juntos no Railway.
O scanner salva btc_mercado_atual.json e o bot le em tempo real.
"""

import threading
import time
import sys

print("=" * 60)
print("INICIANDO SISTEMA POLYMARKET BTC NA NUVEM")
print("Scanner + Bot Telegram rodando juntos")
print("=" * 60)

# Importa e roda o scanner em thread separada
def run_scanner():
    print("[NUVEM] Iniciando Scanner...")
    try:
        import scanner_railway
        scanner_railway.main()
    except Exception as e:
        print(f"[ERRO SCANNER] {e}")
        time.sleep(10)
        run_scanner()  # Restart

# Importa e roda o bot em thread separada
def run_bot():
    print("[NUVEM] Iniciando Bot Telegram...")
    try:
        import asyncio
        import bot_telegram_railway
        bot_telegram_railway.main()
    except Exception as e:
        print(f"[ERRO BOT] {e}")
        time.sleep(10)
        run_bot()  # Restart

if __name__ == "__main__":
    # Scanner em thread
    t_scanner = threading.Thread(target=run_scanner, daemon=True)
    t_scanner.start()

    # Bot na thread principal
    run_bot()
