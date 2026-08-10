from flask import Flask, jsonify, request
from flask_cors import CORS
import os
from datetime import datetime

app = Flask(__name__)
CORS(app)

# MEMÓRIA DO SISTEMA (Onde os dados ficam guardados)
MEMORY_STORAGE = {
    'ultimo_sinal': None,
    'historico': []
}

# ==========================================
# 1. ROTA QUE O SITE USA PARA LER OS DADOS
# ==========================================
@app.route('/api/sinais', methods=['GET'])
def get_sinais():
    sinal = MEMORY_STORAGE.get('ultimo_sinal')
    historico = MEMORY_STORAGE.get('historico', [])[-10:]
    
    if not sinal:
        return jsonify({
            'sinal_atual': {
                'preco': '--',
                'hora': datetime.now().strftime('%H:%M:%S'),
                'expira': '--:--',
                'confianca': '--',
                'estrategia': 'Momentum Pro',
                'direcao': '--',
                'ativo': 'BTC/USDT'
            },
            'ultimos_sinais': [],
            'desempenho': {'total': 0, 'acertos': 0, 'erros': 0, 'taxa': 0}
        })
    
    # Se tiver sinal, devolve ele para o site
    return jsonify({
        'sinal_atual': sinal,
        'ultimos_sinais': historico,
        'desempenho': {'total': len(historico), 'acertos': 0, 'erros': 0, 'taxa': 0}
    })

# ==========================================
# 2. ROTA QUE O SCANNER USA PARA ENVIAR O SINAL
# ==========================================
@app.route('/api/novo_sinal', methods=['POST'])
def receber_sinal():
    dados = request.json
    if not dados:
        return jsonify({'erro': 'Sem dados'}), 400
    
    # Salva o sinal novo na memória
    MEMORY_STORAGE['ultimo_sinal'] = dados
    
    # Adiciona no histórico
    hist = MEMORY_STORAGE.get('historico', [])
    hist.append(dados)
    if len(hist) > 50:
        hist = hist[-50:]
    MEMORY_STORAGE['historico'] = hist
    
    return jsonify({'status': 'ok'}), 201

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
