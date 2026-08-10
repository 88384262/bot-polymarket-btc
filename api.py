from flask import Flask, jsonify, request
from flask_cors import CORS
import os
from datetime import datetime

app = Flask(__name__)
CORS(app)

# ==========================================================
# A CORREÇÃO MÁGICA: A MEMÓRIA DO SISTEMA
# Essas variáveis vivem enquanto o servidor estiver rodando.
# ==========================================================
ULTIMO_SINAL = None
HISTORICO_SINAIS = []

# ==========================================================
# ENDPOINT QUE O SCANNER USA PARA GRITAR
# ==========================================================
@app.route('/api/novo_sinal', methods=['POST'])
def receber_sinal():
    global ULTIMO_SINAL, HISTORICO_SINAIS
    
    dados = request.json
    if not dados:
        return jsonify({'erro': 'Sem dados'}), 400
    
    # Salva o sinal na memória global
    ULTIMO_SINAL = dados
    
    # Guarda no histórico
    HISTORICO_SINAIS.append(dados)
    if len(HISTORICO_SINAIS) > 20: # Mantém só os últimos 20
        HISTORICO_SINAIS = HISTORICO_SINAIS[-20:]
        
    return jsonify({'status': 'sinal recebido com sucesso!'}), 201

# ==========================================================
# ENDPOINT QUE O SEU SITE USA PARA LER
# ==========================================================
@app.route('/api/sinais', methods=['GET'])
def get_sinais():
    # Pega o que está guardado na memória
    sinal_atual = ULTIMO_SINAL
    historico = HISTORICO_SINAIS
    
    desempenho = {
        'total': len(historico),
        'acertos': 0, # Se quiser contabilizar acertos, precisa de lógica extra
        'erros': 0,
        'taxa': 0
    }
    
    if not sinal_atual:
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
        'sinal_atual': sinal_atual,
        'ultimos_sinais': historico,
        'desempenho': desempenho
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
