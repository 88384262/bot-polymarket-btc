import threading, time, sys, os

print("="*60)
print("BTC SIGNAL PRO - Scanner + Bot + API")
print("="*60)

def run_scanner():
    print("[+] Scanner iniciando...")
    try:
        import scanner_railway
        scanner_railway.main()
    except Exception as e:
        print(f"[!] Scanner erro: {e}")
        time.sleep(10)
        run_scanner()

def run_api():
    print("[+] API Web iniciando...")
    try:
        import api
        port = int(os.environ.get("PORT", 5000))
        print(f"[API] Iniciando na porta {port}...")
        api.app.run(host="0.0.0.0", port=port, threaded=True, debug=False, use_reloader=False)
    except Exception as e:
        print(f"[!] API erro: {e}")
        time.sleep(10)
        run_api()

if __name__ == "__main__":
    # Scanner em thread
    threading.Thread(target=run_scanner, daemon=True).start()

    # API em thread (Flask funciona bem em thread)
    threading.Thread(target=run_api, daemon=True).start()

    # Bot Telegram RODA NA THREAD PRINCIPAL (precisa de asyncio)
    print("[+] Bot Telegram iniciando na thread principal...")
    try:
        import bot_telegram_railway
        bot_telegram_railway.main()
    except Exception as e:
        print(f"[!] Bot erro fatal: {e}")
        time.sleep(5)
