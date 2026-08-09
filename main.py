import threading, time, sys, os

print("="*60)
print("BTC SIGNAL PRO - Scanner + Bot + API")
print("="*60)

# Evita multiplas instancias do bot
LOCK_FILE = "/tmp/bot.lock"

def check_lock():
    if os.path.exists(LOCK_FILE):
        try:
            with open(LOCK_FILE, 'r') as f:
                pid = int(f.read().strip())
            # Verifica se o processo ainda existe
            os.kill(pid, 0)
            print(f"[!] Outra instancia do bot ja esta rodando (PID {pid})")
            print("[!] Aguardando 30s para tentar novamente...")
            time.sleep(30)
            return check_lock()
        except (OSError, ValueError):
            # Processo nao existe mais, remove lock
            os.remove(LOCK_FILE)
    with open(LOCK_FILE, 'w') as f:
        f.write(str(os.getpid()))
    return True

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

def run_api():
    print("[+] API Web iniciando...")
    try:
        import api
        api.run_api()
    except Exception as e:
        print(f"[!] API erro: {e}")

if __name__ == "__main__":
    check_lock()

    # Scanner em thread
    threading.Thread(target=run_scanner, daemon=True).start()

    # API em thread
    threading.Thread(target=run_api, daemon=True).start()

    # Bot na thread principal
    run_bot()
