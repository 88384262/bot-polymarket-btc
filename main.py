import os
import time
import threading

print("="*60)
print("✅ SISTEMA SIMPLIFICADO - APENAS API E SCANNER")
print("="*60)

def run_api():
    print("[API] Iniciando servidor Flask...")
    try:
        from waitress import serve
        import api
        port = int(os.environ.get("PORT", 5000))
        serve(api.app, host="0.0.0.0", port=port, threads=4)
    except Exception as e:
        print(f"[API] Erro: {e}")

def run_scanner():
    print("[SCANNER] Iniciando...")
    while True:
        try:
            import scanner_railway
            scanner_railway.main()
        except Exception as e:
            print(f"[SCANNER] Erro: {e}")
            time.sleep(10)

if __name__ == "__main__":
    # Roda a API (Thread principal)
    threading.Thread(target=run_api, daemon=True).start()
    
    # Roda o Scanner
    run_scanner() # O Scanner vai rodar para sempre
