import os
import time
import subprocess
import sys
import threading

print("="*60)
print("✅ SISTEMA SIMPLIFICADO - RODANDO EM PROCESSOS")
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
    # Roda a API em uma thread separada para não travar
    api_thread = threading.Thread(target=run_api, daemon=True)
    api_thread.start()
    
    # Dá 3 segundos para a API subir (Isso é crucial)
    print("Aguardando 3 segundos para API inicializar...")
    time.sleep(3)

    # Roda o Scanner na Thread Principal
    run_scanner()
