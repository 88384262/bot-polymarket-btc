// URL da sua API (ajuste para o endpoint real)
const API_URL = 'https://bot-polymarket-btc.vercel.app/api/sinais'; // ou seu endpoint

// Referências dos elementos
const precoEl = document.getElementById('preco');
const horaEl = document.getElementById('hora');
const expiraEl = document.getElementById('expira');
const confiancaEl = document.querySelector('.valor-confianca');
const tabelaBody = document.getElementById('tabela-sinais');
const totalSinais = document.getElementById('total-sinais');
const totalAcertos = document.getElementById('total-acertos');
const totalErros = document.getElementById('total-erros');
const taxaAcerto = document.getElementById('taxa-acerto');
const cardsContainer = document.getElementById('cards-container');

// Busca sinais da API
async function buscarSinais() {
    try {
        const response = await fetch(API_URL);
        const data = await response.json();
        
        // Seus dados devem vir no formato:
        // { sinal_atual: { ativo, preco, hora, expira, confianca, estrategia, direcao },
        //   ultimos_sinais: [...],
        //   desempenho: { total, acertos, erros, taxa } }
        
        atualizarSinalAtual(data.sinal_atual);
        atualizarTabela(data.ultimos_sinais);
        atualizarDesempenho(data.desempenho);
        atualizarCards(data.ultimos_sinais);
    } catch (error) {
        console.error('Erro ao buscar sinais:', error);
        // Dados mockados para teste (remova depois)
        usarMock();
    }
}

function atualizarSinalAtual(sinal) {
    if (!sinal) return;
    precoEl.textContent = `$${sinal.preco || '--'}`;
    horaEl.textContent = sinal.hora || '--:--:--';
    expiraEl.textContent = sinal.expira || '--:--';
    confiancaEl.textContent = `${sinal.confianca || '--'}%`;
    
    // Cor da confiança
    const conf = parseInt(sinal.confianca) || 0;
    if (conf > 70) confiancaEl.style.color = '#0ecb81';
    else if (conf > 50) confiancaEl.style.color = '#f0b90b';
    else confiancaEl.style.color = '#ea3943';
}

function atualizarTabela(sinais) {
    if (!sinais || sinais.length === 0) {
        tabelaBody.innerHTML = '<tr><td colspan="6">Nenhum sinal disponível</td></tr>';
        return;
    }
    
    tabelaBody.innerHTML = sinais.map(s => `
        <tr>
            <td><strong>${s.ativo || 'BTC/USDT'}</strong></td>
            <td class="${s.direcao === 'ALTA' ? 'sinal-up' : 'sinal-down'}">${s.direcao === 'ALTA' ? '↑ ALTA' : '↓ BAIXA'}</td>
            <td class="confianca-alta">${s.confianca || '--'}%</td>
            <td>${s.timeframe || '5 min'}</td>
            <td>${s.hora || '--:--'}</td>
            <td class="${s.resultado === 'ACERTO' ? 'resultado-acerto' : s.resultado === 'ERRO' ? 'resultado-erro' : ''}">${s.resultado || '--'}</td>
        </tr>
    `).join('');
}

function atualizarDesempenho(dados) {
    if (!dados) return;
    totalSinais.textContent = dados.total || 0;
    totalAcertos.textContent = dados.acertos || 0;
    totalErros.textContent = dados.erros || 0;
    taxaAcerto.textContent = dados.taxa ? `${dados.taxa}%` : '0%';
}

function atualizarCards(sinais) {
    if (!sinais || sinais.length === 0) {
        cardsContainer.innerHTML = '<p>Nenhum sinal disponível</p>';
        return;
    }
    
    // Mostra os 6 primeiros ou menos
    const exibir = sinais.slice(0, 6);
    cardsContainer.innerHTML = exibir.map(s => `
        <div class="card-ativo">
            <div class="ativo">${s.ativo || 'BTC/USDT'}</div>
            <div class="sinal ${s.direcao === 'ALTA' ? 'sinal-up' : 'sinal-down'}">${s.direcao === 'ALTA' ? '↑' : '↓'}</div>
            <div class="conf">${s.confianca || '--'}%</div>
        </div>
    `).join('');
}

// Dados mockados para teste (remova quando a API estiver pronta)
function usarMock() {
    const mock = {
        sinal_atual: {
            preco: '67,842.35',
            hora: '12:35:02',
            expira: '02:14',
            confianca: '87',
            estrategia: 'Momentum Pro'
        },
        ultimos_sinais: [
            { ativo: 'BTC/USDT', direcao: 'ALTA', confianca: '87', timeframe: '5 min', hora: '12:35', resultado: 'ACERTO' },
            { ativo: 'ETH/USDT', direcao: 'BAIXA', confianca: '81', timeframe: '5 min', hora: '12:30', resultado: 'ACERTO' },
            { ativo: 'SOL/USDT', direcao: 'ALTA', confianca: '74', timeframe: '5 min', hora: '12:25', resultado: 'ERRO' },
            { ativo: 'BNB/USDT', direcao: 'ALTA', confianca: '68', timeframe: '5 min', hora: '12:20', resultado: 'ACERTO' },
            { ativo: 'XRP/USDT', direcao: 'BAIXA', confianca: '72', timeframe: '5 min', hora: '12:15', resultado: 'ACERTO' },
            { ativo: 'ADA/USDT', direcao: 'ALTA', confianca: '83', timeframe: '5 min', hora: '12:10', resultado: 'ACERTO' }
        ],
        desempenho: {
            total: 37,
            acertos: 31,
            erros: 6,
            taxa: 83.78
        }
    };
    
    atualizarSinalAtual(mock.sinal_atual);
    atualizarTabela(mock.ultimos_sinais);
    atualizarDesempenho(mock.desempenho);
    atualizarCards(mock.ultimos_sinais);
}

// Executa a cada 60 segundos
buscarSinais();
setInterval(buscarSinais, 60000);
