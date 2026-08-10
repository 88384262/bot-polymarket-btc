from flask import Flask, jsonify, request
from flask_cors import CORS
import json
import os
from datetime import datetime

app = Flask(__name__)
CORS(app)

# ============================================
# FUNÇÕES PARA LER OS SINAIS SALVOS
# ============================================
def buscar_ultimo_sinal():
    try:
        with open('ultimo_sinal.json', 'r') as f:
            return json.load(f)
    except:
        return None

def buscar_historico():
    try:
        with open('historico_sinais.json', 'r') as f:
            return json.load(f)
    except:
        return []

def calcular_desempenho(historico):
    total = len(historico)
    if total == 0:
        return {'total': 0, 'acertos': 0, 'erros': 0, 'taxa': 0}
    
    sinais_com_resultado = [s for s in historico[-100:] if s.get('resultado') in ['ACERTO', 'ERRO']]
    acertos = sum(1 for s in sinais_com_resultado if s.get('resultado') == 'ACERTO')
    erros = sum(1 for s in sinais_com_resultado if s.get('resultado') == 'ERRO')
    taxa = round((acertos / (acertos + erros) * 100), 2) if (acertos + erros) > 0 else 0
    
    return {
        'total': len(sinais_com_resultado),
        'acertos': acertos,
        'erros': erros,
        'taxa': taxa
    }

# ============================================
# ENDPOINTS
# ============================================
@app.route('/api/sinais', methods=['GET'])
def get_sinais():
    sinal = buscar_ultimo_sinal()
    historico = buscar_historico()
    desempenho = calcular_desempenho(historico)
    
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
            'ativo': sinal.get('ativo', 'BTC/USDT'),
            'score': sinal.get('score', 0),
            'tendencia': sinal.get('tendencia', '--'),
            'rsi': sinal.get('rsi', 0),
            'mom': sinal.get('mom', 0)
        },
        'ultimos_sinais': historico[-10:],
        'desempenho': desempenho
    })

@app.route('/api/novo_sinal', methods=['POST'])
def receber_sinal():
    dados = request.json
    if not dados:
        return jsonify({'erro': 'Sem dados'}), 400
    
    with open('ultimo_sinal.json', 'w') as f:
        json.dump(dados, f, indent=2)
    
    try:
        with open('historico_sinais.json', 'r') as f:
            historico = json.load(f)
    except:
        historico = []
    
    novo = dados.copy()
    novo['resultado'] = 'PENDENTE'
    novo['data_recebido'] = datetime.now().isoformat()
    historico.append(novo)
    
    if len(historico) > 100:
        historico = historico[-100:]
    
    with open('historico_sinais.json', 'w') as f:
        json.dump(historico, f, indent=2)
    
    return jsonify({'status': 'ok'}), 201

@app.route('/api/status', methods=['GET'])
def status():
    return jsonify({'status': 'online', 'versao': '1.0'})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
