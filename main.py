import os
import time
import threading
import sys

print("="*60)
print("🚀 BTC SIGNAL PRO - INICIADOR TURBO")
print("="*60)

def run_api():
    print("[API] Iniciando servidor Flask via Waitress...")
    try:
        from waitress import serve
        import api
        port = int(os.environ.get("PORT", 5000))
        serve(api.app, host="0.0.0.0", port=port, threads=4)
    except Exception as e:
        print(f"[API] Erro fatal: {e}")
        time.sleep(10)
        run_api()

def run_scanner():
    print("[SCANNER] Iniciando...")
    while True:
        try:
            import scanner_railway
            scanner_railway.main()
        except Exception as e:
            print(f"[SCANNER] Erro: {e}")
            time.sleep(10)

def run_bot():
    # CORREÇÃO PARA O EVENT LOOP DO TELEGRAM
    # Não usamos thread. Usamos um subprocesso separado.
    import subprocess
    import sys
    print("[BOT] Iniciando Bot do Telegram em processo separado...")
    subprocess.run([sys.executable, "bot_telegram_railway.py"])

if __name__ == "__main__":
    # 1. API roda em uma thread (suporta isso perfeitamente)
    api_thread = threading.Thread(target=run_api, daemon=True)
    api_thread.start()
    time.sleep(2) # Dá um tempo para a API subir

    # 2. Scanner roda em uma thread
    scanner_thread = threading.Thread(target=run_scanner, daemon=True)
    scanner_thread.start()

    # 3. O BOT é executado em um processo separado (NÃO CAUSA ERRO DE EVENT LOOP)
    run_bot()
