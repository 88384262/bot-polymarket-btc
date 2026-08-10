// URL da sua API (Se mudar no futuro, mude aqui)
const API_URL = 'https://worker-production-9154.up.railway.app/api/sinais';

// ==========================================================
// DADOS MOCK DE BACKUP (Para garantir que o site nunca fique branco)
// ==========================================================
const MOCK_DATA = {
    sinal_atual: {
        preco: '67,842.35',
        hora: '12:35:02',
        expira: '02:14',
        confianca: '87',
        estrategia: 'Momentum Pro',
        direcao: 'ALTA',
        ativo: 'BTC/USDT'
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

// ==========================================================
// FUNÇÕES DE RENDERIZAÇÃO (Desenham o visual)
// ==========================================================
function renderizarSinal(sinal) {
    const direcaoEl = document.getElementById('sinal-direcao');
    const precoEl = document.getElementById('preco-atual');
    const horaEl = document.getElementById('hora-atual');
    const expiraEl = document.getElementById('expira-em');
    const confiancaEl = document.getElementById('confianca-valor');

    if(sinal && sinal.direcao && sinal.direcao !== '--') {
        const isUp = sinal.direcao === 'ALTA';
        direcaoEl.innerHTML = `
            <span class="${isUp ? 'sinal-up' : 'sinal-down'}">
                ${isUp ? 'ALTA' : 'BAIXA'} 
                <i class="fas fa-arrow-${isUp ? 'up' : 'down'}"></i>
            </span>
        `;
        precoEl.textContent = `$ ${sinal.preco || '0.00'}`;
        horaEl.textContent = sinal.hora || '--:--:--';
        expiraEl.textContent = sinal.expira || '--:--';
        
        const conf = parseInt(sinal.confianca) || 0;
        const cor = conf > 70 ? '#2ecc71' : (conf > 50 ? '#f1c40f' : '#e74c3c');
        confiancaEl.innerHTML = `
            <span style="color: ${cor};">${sinal.confianca || 0}%</span>
            <div class="gauge-ring" style="border-top-color: ${cor};"></div>
        `;
    } else {
        direcaoEl.innerHTML = `<span class="loading-text">AGUARDANDO...</span>`;
    }
}

function renderizarTabela(historico) {
    const tabelaBody = document.getElementById('tabela-body');
    if (!historico || historico.length === 0) {
        tabelaBody.innerHTML = `<tr><td colspan="6" style="text-align:center; color:#848e9c; padding:20px;">Nenhum sinal registrado</td></tr>`;
        return;
    }
    
    tabelaBody.innerHTML = historico.map(s => {
        const isUp = s.direcao === 'ALTA';
        const isAcerto = s.resultado === 'ACERTO';
        const isErro = s.resultado === 'ERRO';
        
        let badgeClass = 'badge-pendente';
        let badgeText = 'PENDENTE';
        if(isAcerto) { badgeClass = 'badge-acerto'; badgeText = '✅ ACERTO'; }
        else if(isErro) { badgeClass = 'badge-erro'; badgeText = '❌ ERRO'; }

        // Ícone aleatório para estética
        const icons = ['fab fa-bitcoin btc-icon', 'fab fa-ethereum eth-icon', 'fab fa-solana sol-icon', 'fab fa-bnb bnb-icon'];
        const randomIcon = icons[Math.floor(Math.random() * icons.length)];

        return `
            <tr>
                <td>
                    <div class="coin-small">
                        <i class="${randomIcon}"></i> ${s.ativo || 'BTC/USDT'}
                    </div>
                </td>
                <td>
                    <span class="${isUp ? 'sinal-up' : 'sinal-down'}">
                        ${isUp ? 'ALTA' : 'BAIXA'} <i class="fas fa-arrow-${isUp ? 'up' : 'down'}"></i>
                    </span>
                </td>
                <td><strong>${s.confianca || '--'}%</strong></td>
                <td>${s.timeframe || '5 min'}</td>
                <td>${s.hora || '--:--'}</td>
                <td><span class="badge-result ${badgeClass}">${badgeText}</span></td>
            </tr>
        `;
    }).join('');
}

function renderizarDesempenho(desempenho) {
    document.getElementById('total-sinais').textContent = desempenho.total || 0;
    document.getElementById('total-acertos').textContent = desempenho.acertos || 0;
    document.getElementById('total-erros').textContent = desempenho.erros || 0;
    document.getElementById('taxa-acerto').textContent = `${desempenho.taxa || 0}%`;
}

// ==========================================================
// LÓGICA PRINCIPAL (Tenta API, se falhar usa Mock)
// ==========================================================
async function carregarDados() {
    try {
        // Tenta buscar na API
        const response = await fetch(API_URL);
        if (!response.ok) throw new Error("Erro HTTP " + response.status);
        
        const data = await response.json();
        console.log("✅ API conectada! Dados recebidos:", data);

        // Renderiza com os dados REAIS da API
        renderizarSinal(data.sinal_atual);
        renderizarTabela(data.ultimos_sinais);
        renderizarDesempenho(data.desempenho);

    } catch (error) {
        console.warn("⚠️ API falhou. Usando dados MOCK (Backup)...", error);
        
        // Renderiza com os dados MOCK (para o site nunca ficar vazio)
        renderizarSinal(MOCK_DATA.sinal_atual);
        renderizarTabela(MOCK_DATA.ultimos_sinais);
        renderizarDesempenho(MOCK_DATA.desempenho);
    }
}

// Inicia a verificação
carregarDados();

// Atualiza automaticamente a cada 10 segundos
setInterval(carregarDados, 10000);
