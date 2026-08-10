// URL da sua API
const API_URL = 'https://worker-production-9154.up.railway.app/api/sinais';

// ==========================================================
// ESTADO DO SISTEMA (Controla o cronômetro real)
// ==========================================================
let segundosRestantes = 0;
let contadorAtivo = false;

// ==========================================================
// FUNÇÕES DE RENDERIZAÇÃO
// ==========================================================
function renderizarSinal(sinal) {
    const direcaoEl = document.getElementById('sinal-direcao');
    const precoEl = document.getElementById('preco-atual');
    const confiancaEl = document.getElementById('confianca-valor');
    const horaEl = document.getElementById('hora-atual');
    const expiraEl = document.getElementById('expira-em');

    if(sinal && sinal.direcao && sinal.direcao !== '--') {
        const isUp = sinal.direcao === 'ALTA';
        direcaoEl.innerHTML = `
            <span class="${isUp ? 'sinal-up' : 'sinal-down'}">
                ${isUp ? 'ALTA' : 'BAIXA'} 
                <i class="fas fa-arrow-${isUp ? 'up' : 'down'}"></i>
            </span>
        `;
        precoEl.textContent = `$ ${sinal.preco || '0.00'}`;
        
        const conf = parseInt(sinal.confianca) || 0;
        const cor = conf > 70 ? '#2ecc71' : (conf > 50 ? '#f1c40f' : '#e74c3c');
        confiancaEl.innerHTML = `
            <span style="color: ${cor};">${sinal.confianca || 0}%</span>
            <div class="gauge-ring" style="border-top-color: ${cor};"></div>
        `;

        // ==========================================================
        // 100% VINDO DO SCANNER (Nenhuma invenção)
        // ==========================================================
        
        // 1. Exibe a hora EXATA que o scanner enviou
        horaEl.textContent = sinal.hora || '--:--:--';

        // 2. Ativa o cronômetro baseado no valor enviado pelo scanner
        if (sinal.expira && sinal.expira !== '--:--') {
            const partes = sinal.expira.split(':');
            const mins = parseInt(partes[0]) || 0;
            const segs = parseInt(partes[1]) || 0;
            segundosRestantes = (mins * 60) + segs;
            contadorAtivo = true; 
        } else {
            contadorAtivo = false;
            expiraEl.textContent = '--:--';
        }

    } else {
        direcaoEl.innerHTML = `<span class="loading-text" style="color: #848e9c;">AGUARDANDO...</span>`;
        precoEl.textContent = '$ --';
        confiancaEl.innerHTML = `<span style="color: #848e9c;">--%</span><div class="gauge-ring" style="border-top-color: #848e9c;"></div>`;
        document.getElementById('hora-atual').textContent = '--:--:--';
        document.getElementById('expira-em').textContent = '--:--';
        contadorAtivo = false;
    }
}

function renderizarTabela(historico) {
    const tabelaBody = document.getElementById('tabela-body');
    if (!historico || historico.length === 0) {
        tabelaBody.innerHTML = `<tr><td colspan="6" style="text-align:center; color:#848e9c; padding:20px;">Aguardando primeiro sinal real do scanner...</td></tr>`;
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

        return `
            <tr>
                <td>
                    <div class="coin-small">
                        <i class="fab fa-bitcoin btc-icon" style="color: #f7931a;"></i> BTC/USDT
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
// CRONÔMETRO DO SCANNER (Apenas conta o tempo enviado)
// ==========================================================
function atualizarCronometro() {
    if (contadorAtivo && segundosRestantes > 0) {
        segundosRestantes--;
        
        const mins = String(Math.floor(segundosRestantes / 60)).padStart(2, '0');
        const segs = String(segundosRestantes % 60).padStart(2, '0');
        document.getElementById('expira-em').textContent = `${mins}:${segs}`;
        
        if (segundosRestantes === 0) {
            contadorAtivo = false;
            document.getElementById('expira-em').textContent = '00:00';
        }
    }
}
// Atualiza o cronômetro a cada 1 segundo
setInterval(atualizarCronometro, 1000);

// ==========================================================
// LÓGICA PRINCIPAL (Busca API)
// ==========================================================
async function carregarDados() {
    try {
        const response = await fetch(API_URL);
        if (!response.ok) throw new Error("Erro HTTP");
        
        const data = await response.json();
        console.log("✅ Dados reais recebidos do scanner:", data);

        // Atualiza o painel com os dados do scanner
        renderizarSinal(data.sinal_atual);
        renderizarTabela(data.ultimos_sinais);
        renderizarDesempenho(data.desempenho);

    } catch (error) {
        console.warn("⚠️ API falhou. Aguardando scanner reconectar...");
    }
}

// Inicia a verificação da API (a cada 10 segundos)
carregarDados();
setInterval(carregarDados, 10000);
