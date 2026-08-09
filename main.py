import threading, time, sys, os, asyncio

print("="*60)
print("BTC SIGNAL PRO - Scanner + Bot + API")
print("="*60)

def run_scanner():
    print("[+] Scanner iniciando...")
    while True:
        try:
            import scanner_railway
            scanner_railway.main()
        except Exception as e:
            print(f"[!] Scanner erro: {e}")
            time.sleep(10)

def run_bot():
    print("[+] Bot Telegram iniciando...")
    while True:
        try:
            import bot_telegram_railway
            bot_telegram_railway.main()
        except Exception as e:
            print(f"[!] Bot erro: {e}")
            time.sleep(15)

if __name__ == "__main__":
    # Scanner em thread
    threading.Thread(target=run_scanner, daemon=True).start()

    # Bot em thread (com event loop proprio para asyncio)
    def bot_thread():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        run_bot()
    threading.Thread(target=bot_thread, daemon=True).start()

    # API Flask com WAITRESS (servidor de producao estavel)
    print("[+] API Web iniciando com Waitress...")
    try:
        import api
        from waitress import serve
        port = int(os.environ.get("PORT", 5000))
        print(f"[API] Iniciando na porta {port}...")
        serve(api.app, host="0.0.0.0", port=port, threads=4)
    except ImportError:
        print("[!] Waitress nao instalado, usando Flask dev server...")
        import api
        port = int(os.environ.get("PORT", 5000))
        api.app.run(host="0.0.0.0", port=port, threaded=True, debug=False, use_reloader=False)
    except Exception as e:
        print(f"[!] API erro fatal: {e}")
        time.sleep(5)
