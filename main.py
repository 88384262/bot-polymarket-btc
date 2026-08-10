import os
import time
import threading
import subprocess
import sys

print("=" * 60)
print("🚀 BTC SIGNAL PRO - INICIADOR ANTI-CONFLITO")
print("=" * 60)

# Verifica se o bot já está rodando para evitar conflitos
def is_bot_running():
    try:
        result = subprocess.run(['pgrep', '-f', 'bot_telegram_railway.py'], capture_output=True, text=True)
        return bool(result.stdout.strip())
    except:
        return False

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
    # CORREÇÃO DEFINITIVA: Executa o bot em um subprocesso isolado
    # Isso impede que o Railway crie "instâncias fantasmas" e evita o Conflict
    print("[BOT] Verificando se o Bot do Telegram já está rodando...")
    
    if is_bot_running():
        print("[BOT] Um processo do bot já está rodando. Pulando inicialização para evitar conflito.")
        while True:
            time.sleep(60) # Monitora eternamente, mas não cria duplicata
    else:
        print("[BOT] Iniciando Bot do Telegram em subprocesso isolado...")
        try:
            subprocess.run([sys.executable, "bot_telegram_railway.py"], check=True)
        except subprocess.CalledProcessError:
            print("[BOT] O Bot fechou inesperadamente. Reiniciando em 5 segundos...")
            time.sleep(5)
            run_bot()

if __name__ == "__main__":
    # 1. API roda em thread (estável)
    api_thread = threading.Thread(target=run_api, daemon=True)
    api_thread.start()
    time.sleep(2)

    # 2. Scanner roda em thread
    scanner_thread = threading.Thread(target=run_scanner, daemon=True)
    scanner_thread.start()

    # 3. BOT AGORA RODA NO PROCESSO PRINCIPAL (Garantia de compatibilidade)
    # Isso impede totalmente o erro de "múltiplas instâncias"
    run_bot()
