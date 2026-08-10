from flask import Flask, jsonify, request
from flask_cors import CORS
import json
import os
from datetime import datetime
import requests

# ============================================
# 1. INICIALIZAÇÃO DO FLASK
# ============================================
app = Flask(__name__)
CORS(app)  # Permite que o site consulte a API

# ============================================
# 2. FUNÇÃO PARA BUSCAR OS SINAIS DO SEU SCANNER
# ============================================
def buscar_ultimo_sinal():
    """
    Aqui você vai buscar o sinal mais recente do seu scanner.
    Como você já tem um scanner_railway.py rodando, você pode:
    
    OPÇÃO A: Ler de um arquivo JSON
    OPÇÃO B: Chamar diretamente as funções do scanner
    OPÇÃO C: Ler de um banco de dados
    """
    
    # --- OPÇÃO A: Ler de um arquivo JSON (RECOMENDADO) ---
    try:
        with open('ultimo_sinal.json', 'r') as f:
            dados = json.load(f)
            return dados
    except FileNotFoundError:
        # Se o arquivo não existir, retorna dados vazios
        return None
    
    # --- OPÇÃO B: Chamar diretamente o scanner (se estiver no mesmo arquivo) ---
    # from scanner_railway import obter_sinal
    # return obter_sinal()


def buscar_historico_sinais():
    """
    Busca o histórico de sinais.
    """
    try:
        with open('historico_sinais.json', 'r') as f:
            historico = json.load(f)
            return historico
    except FileNotFoundError:
        return []


def calcular_desempenho(historico):
    """
    Calcula estatísticas com base no histórico.
    """
    total = len(historico)
    acertos = sum(1 for s in historico if s.get('resultado') == 'ACERTO')
    erros = sum(1 for s in historico if s.get('resultado') == 'ERRO')
    
    taxa = round((acertos / total * 100), 2) if total > 0 else 0
    
    return {
        'total': total,
        'acertos': acertos,
        'erros': erros,
        'taxa': taxa
    }


# ============================================
# 3. ENDPOINT PRINCIPAL - /api/sinais
# ============================================
@app.route('/api/sinais', methods=['GET'])
def get_sinais():
    """
    Endpoint que o site vai chamar para pegar os sinais.
    """
    
    # Busca o sinal atual
    sinal_atual = buscar_ultimo_sinal()
    
    # Busca o histórico
    historico = buscar_historico_sinais()
    
    # Calcula o desempenho
    desempenho = calcular_desempenho(historico)
    
    # Se não tiver sinal, retorna dados mockados para teste
    if not sinal_atual:
        return jsonify({
            'sinal_atual': {
                'preco': '67,842.35',
                'hora': datetime.now().strftime('%H:%M:%S'),
                'expira': '02:14',
                'confianca': '87',
                'estrategia': 'Momentum Pro',
                'direcao': 'ALTA',
                'ativo': 'BTC/USDT'
            },
            'ultimos_sinais': [
                {'ativo': 'BTC/USDT', 'direcao': 'ALTA', 'confianca': '87', 'timeframe': '5 min', 'hora': '12:35', 'resultado': 'ACERTO'},
                {'ativo': 'ETH/USDT', 'direcao': 'BAIXA', 'confianca': '81', 'timeframe': '5 min', 'hora': '12:30', 'resultado': 'ACERTO'},
                {'ativo': 'SOL/USDT', 'direcao': 'ALTA', 'confianca': '74', 'timeframe': '5 min', 'hora': '12:25', 'resultado': 'ERRO'},
            ],
            'desempenho': {
                'total': 37,
                'acertos': 31,
                'erros': 6,
                'taxa': 83.78
            }
        })
    
    # Monta a resposta com os dados reais
    return jsonify({
        'sinal_atual': {
            'preco': sinal_atual.get('preco', '--'),
            'hora': sinal_atual.get('hora', datetime.now().strftime('%H:%M:%S')),
            'expira': sinal_atual.get('expira', '--:--'),
            'confianca': sinal_atual.get('confianca', '--'),
            'estrategia': sinal_atual.get('estrategia', 'Momentum Pro'),
            'direcao': sinal_atual.get('direcao', 'ALTA'),  # 'ALTA' ou 'BAIXA'
            'ativo': sinal_atual.get('ativo', 'BTC/USDT')
        },
        'ultimos_sinais': historico[-10:],  # Últimos 10 sinais
        'desempenho': desempenho
    })


# ============================================
# 4. ENDPOINT PARA RECEBER NOVOS SINAIS DO SCANNER
# ============================================
@app.route('/api/novo_sinal', methods=['POST'])
def receber_novo_sinal():
    """
    Endpoint que seu scanner vai chamar quando detectar um novo sinal.
    Assim o site sempre terá os dados mais atualizados.
    """
    dados = request.json
    
    if not dados:
        return jsonify({'erro': 'Nenhum dado enviado'}), 400
    
    # Salva o sinal atual
    with open('ultimo_sinal.json', 'w') as f:
        json.dump(dados, f)
    
    # Adiciona ao histórico
    try:
        with open('historico_sinais.json', 'r') as f:
            historico = json.load(f)
    except FileNotFoundError:
        historico = []
    
    # Adiciona o novo sinal com timestamp
    novo_sinal = {
        **dados,
        'hora_recebido': datetime.now().strftime('%H:%M:%S'),
        'resultado': 'PENDENTE'  # Você pode atualizar depois
    }
    
    historico.append(novo_sinal)
    
    # Mantém apenas os últimos 100 sinais
    if len(historico) > 100:
        historico = historico[-100:]
    
    with open('historico_sinais.json', 'w') as f:
        json.dump(historico, f)
    
    return jsonify({'status': 'Sinal recebido com sucesso!'}), 201


# ============================================
# 5. ENDPOINT DE TESTE
# ============================================
@app.route('/api/status', methods=['GET'])
def status():
    """
    Endpoint para verificar se a API está funcionando.
    """
    return jsonify({
        'status': 'online',
        'timestamp': datetime.now().isoformat(),
        'versao': '1.0'
    })


# ============================================
# 6. INICIALIZAÇÃO DO SERVIDOR
# ============================================
if __name__ == '__main__':
    # Cria arquivos iniciais se não existirem
    if not os.path.exists('ultimo_sinal.json'):
        with open('ultimo_sinal.json', 'w') as f:
            json.dump({}, f)
    
    if not os.path.exists('historico_sinais.json'):
        with open('historico_sinais.json', 'w') as f:
            json.dump([], f)
    
    # Roda o servidor
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
