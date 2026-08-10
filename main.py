import os
import time
import threading
import sys

print("="*60)
print("🚀 BTC SIGNAL PRO - INICIADOR UNIFICADO")
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
    print("[BOT] Iniciando Telegram...")
    while True:
        try:
            import bot_telegram_railway
            bot_telegram_railway.main()
        except Exception as e:
            print(f"[BOT] Erro fatal (reiniciando em 15s): {e}")
            time.sleep(15)

if __name__ == "__main__":
    # API roda na thread principal (imprescindível para o Waitress)
    api_thread = threading.Thread(target=run_api, daemon=False)
    api_thread.start()

    # Scanner e Bot rodam em threads daemon
    threading.Thread(target=run_scanner, daemon=True).start()
    threading.Thread(target=run_bot, daemon=True).start()

    # Mantém o script principal rodando para sempre
    while True:
        time.sleep(1)
