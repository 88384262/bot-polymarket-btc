import os, time, multiprocessing

print("="*60)
print("BTC SIGNAL PRO - Scanner + Bot + API")
print("="*60)

def run_api():
    """API roda em processo separado - thread principal propria"""
    print("[API] Iniciando servidor...")
    try:
        import api
        from waitress import serve
        port = int(os.environ.get("PORT", 5000))
        serve(api.app, host="0.0.0.0", port=port, threads=4)
    except ImportError:
        print("[API] Waitress nao encontrado, usando Flask dev...")
        import api
        port = int(os.environ.get("PORT", 5000))
        api.app.run(host="0.0.0.0", port=port, threaded=True, debug=False, use_reloader=False)
    except Exception as e:
        print(f"[API] Erro: {e}")
        time.sleep(5)

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
    # API em PROCESSO SEPARADO (thread principal propria)
    api_proc = multiprocessing.Process(target=run_api)
    api_proc.start()
    print(f"[+] API iniciada em processo PID {api_proc.pid}")

    # Scanner em thread (dentro do processo principal)
    import threading
    threading.Thread(target=run_scanner, daemon=True).start()

    # Bot Telegram no PROCESSO PRINCIPAL (thread principal - asyncio precisa disso)
    print("[+] Bot no processo principal...")
    run_bot()
