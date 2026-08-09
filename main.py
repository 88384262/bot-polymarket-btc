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
        print("[+] API iniciada com sucesso!")
    except Exception as e:
        print(f"[!] API erro (continuando sem API): {e}")
        # Nao reinicia - continua sem API se der erro

if __name__ == "__main__":
    # Scanner em thread
    threading.Thread(target=run_scanner, daemon=True).start()

    # API em thread (se falhar, nao quebra o bot)
    threading.Thread(target=run_api, daemon=True).start()

    # Bot na thread principal
    run_bot()
