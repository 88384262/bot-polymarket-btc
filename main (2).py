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
        time.sleep(10)
        run_bot()

def run_api():
    print("[+] API Web iniciando...")
    try:
        import api
        api.run_api()
    except Exception as e:
        print(f"[!] API erro: {e}")
        time.sleep(10)
        run_api()

if __name__ == "__main__":
    threading.Thread(target=run_scanner, daemon=True).start()
    threading.Thread(target=run_api, daemon=True).start()
    run_bot()
