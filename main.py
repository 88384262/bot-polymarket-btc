import os
import time
import threading
import sys
import asyncio

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
    try:
        import bot_telegram_railway
        bot_telegram_railway.main()
    except Exception as e:
        print(f"[BOT] Erro fatal: {e}")

if __name__ == "__main__":
    # ⚠️ CORREÇÃO AQUI: A API fica na Thread, o Bot e Scanner ficam no loop principal

    # 1. Inicia a API em uma Thread separada (Waitress funciona bem assim)
    api_thread = threading.Thread(target=run_api, daemon=True)
    api_thread.start()

    # 2. O Scanner roda em uma Thread separada
    threading.Thread(target=run_scanner, daemon=True).start()

    # 3. O Bot do Telegram PRECISA rodar no Event Loop Principal (Main Thread)
    # Isso resolve o erro "There is no current event loop"
    run_bot()
