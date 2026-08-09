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

def run_bot():
    print("[+] Bot Telegram iniciando...")
    try:
        import bot_telegram_railway
        bot_telegram_railway.main()
    except Exception as e:
        print(f"[!] Bot erro: {e}")
        time.sleep(15)
        run_bot()

if __name__ == "__main__":
    # Scanner em thread
    threading.Thread(target=run_scanner, daemon=True).start()

    # Bot em thread
    threading.Thread(target=run_bot, daemon=True).start()

    # API Flask RODA NO PROCESSO PRINCIPAL
    print("[+] API Web iniciando no processo principal...")
    try:
        import api
        port = int(os.environ.get("PORT", 5000))
        print(f"[API] Iniciando na porta {port}...")
        api.app.run(host="0.0.0.0", port=port, threaded=True, debug=False, use_reloader=False)
    except Exception as e:
        print(f"[!] API erro fatal: {e}")
        time.sleep(5)
