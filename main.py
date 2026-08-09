import threading, time, sys, os, multiprocessing

print("="*60)
print("BTC SIGNAL PRO - Scanner + Bot + API")
print("="*60)

def run_scanner():
    print("[+] Scanner iniciando em thread...")
    while True:
        try:
            import scanner_railway
            scanner_railway.main()
        except Exception as e:
            print(f"[!] Scanner erro: {e}")
            time.sleep(10)

def run_bot():
    """Roda em processo separado - cada processo tem sua propria thread principal"""
    print("[+] Bot Telegram iniciando em processo separado...")
    try:
        import bot_telegram_railway
        bot_telegram_railway.main()
    except Exception as e:
        print(f"[!] Bot erro fatal: {e}")
        time.sleep(5)

if __name__ == "__main__":
    # Scanner em thread (no processo principal)
    threading.Thread(target=run_scanner, daemon=True).start()

    # Bot em PROCESSO SEPARADO (assim ele tem thread principal propria para asyncio)
    bot_proc = multiprocessing.Process(target=run_bot)
    bot_proc.start()
    print(f"[+] Bot iniciado em processo PID {bot_proc.pid}")

    # API Flask RODA NO PROCESSO PRINCIPAL (Railway detecta a porta aqui)
    print("[+] API Web iniciando no processo principal...")
    try:
        import api
        port = int(os.environ.get("PORT", 5000))
        print(f"[API] Iniciando na porta {port}...")
        api.app.run(host="0.0.0.0", port=port, threaded=True, debug=False, use_reloader=False)
    except Exception as e:
        print(f"[!] API erro fatal: {e}")
        time.sleep(5)
