from flask import Flask, jsonify, request
from flask_cors import CORS
import os
from datetime import datetime

app = Flask(__name__)
CORS(app)

# Armazenamento em memória (para evitar falhas de arquivos no Railway)
MEMORY_STORAGE = {
    'ultimo_sinal': None,
    'historico': []
}

@app.route('/api/sinais', methods=['GET'])
def get_sinais():
    sinal = MEMORY_STORAGE.get('ultimo_sinal')
    historico = MEMORY_STORAGE.get('historico', [])[-10:]
    
    # Desempenho fake para demonstração (ou calcule se quiser salvar resultado)
    total = len(historico)
    desempenho = {
        'total': total,
        'acertos': 0,
        'erros': 0,
        'taxa': 0
    }
    
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
            'desempenho': desempenho
        })
    
    return jsonify({
        'sinal_atual': {
            'preco': sinal.get('preco', '--'),
            'hora': sinal.get('hora', datetime.now().strftime('%H:%M:%S')),
            'expira': sinal.get('expira', '--:--'),
            'confianca': str(sinal.get('confianca', '--')),
            'estrategia': sinal.get('estrategia', 'Momentum Pro'),
            'direcao': sinal.get('sinal', '--'),
            'ativo': sinal.get('ativo', 'BTC/USDT')
        },
        'ultimos_sinais': historico,
        'desempenho': desempenho
    })

@app.route('/api/novo_sinal', methods=['POST'])
def receber_sinal():
    dados = request.json
    if not dados:
        return jsonify({'erro': 'Sem dados'}), 400
    
    # Salva na memória
    MEMORY_STORAGE['ultimo_sinal'] = dados
    
    novo = dados.copy()
    novo['resultado'] = 'PENDENTE'
    novo['data_recebido'] = datetime.now().isoformat()
    
    hist = MEMORY_STORAGE.get('historico', [])
    hist.append(novo)
    if len(hist) > 100:
        hist = hist[-100:]
    MEMORY_STORAGE['historico'] = hist
    
    return jsonify({'status': 'ok'}), 201

@app.route('/api/status', methods=['GET'])
def status():
    return jsonify({'status': 'online', 'versao': '1.0'})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
