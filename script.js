// URL da sua API (a mesma que está no seu vercel.json)
const API_URL = 'https://worker-production-9154.up.railway.app/api/sinais';

async function carregarDados() {
    try {
        const response = await fetch(API_URL);
        const data = await response.json();

        // 1. Atualizar SINAL MAIS RECENTE
        const sinal = data.sinal_atual;
        const direcaoEl = document.getElementById('sinal-direcao');
        const precoEl = document.getElementById('preco-atual');
        const horaEl = document.getElementById('hora-atual');
        const expiraEl = document.getElementById('expira-em');
        const confiancaEl = document.getElementById('confianca-valor');

        if(sinal && sinal.direcao !== '--') {
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

        // 2. Atualizar TABELA
        const tabelaBody = document.getElementById('tabela-body');
        const historico = data.ultimos_sinais || [];
        
        if (historico.length === 0) {
            tabelaBody.innerHTML = `<tr><td colspan="6" style="text-align:center; color:#848e9c;">Nenhum sinal registrado</td></tr>`;
        } else {
            tabelaBody.innerHTML = historico.map(s => {
                const isUp = s.direcao === 'ALTA';
                const isAcerto = s.resultado === 'ACERTO';
                const isErro = s.resultado === 'ERRO';
                
                let badgeClass = 'badge-pendente';
                let badgeText = 'PENDENTE';
                if(isAcerto) { badgeClass = 'badge-acerto'; badgeText = 'ACERTO'; }
                else if(isErro) { badgeClass = 'badge-erro'; badgeText = 'ERRO'; }

                // Ícone aleatório para estética (simulando diferentes moedas)
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

        // 3. Atualizar DESEMPENHO
        const desempenho = data.desempenho || { total: 0, acertos: 0, erros: 0, taxa: 0 };
        document.getElementById('total-sinais').textContent = desempenho.total;
        document.getElementById('total-acertos').textContent = desempenho.acertos;
        document.getElementById('total-erros').textContent = desempenho.erros;
        document.getElementById('taxa-acerto').textContent = `${desempenho.taxa || 0}%`;

    } catch (error) {
        console.error('Erro ao buscar API:', error);
        document.getElementById('sinal-direcao').innerHTML = `<span style="color: #e74c3c; font-size: 14px;">ERRO DE CONEXÃO</span>`;
    }
}

// Executa na carga e atualiza a cada 10 segundos
carregarDados();
setInterval(carregarDados, 10000);
