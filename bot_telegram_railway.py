#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BOT TELEGRAM - SINAIS POLYMARKET BTC v5.0 (2 ESTAGIOS: AGUARDE + ULTIMO MINUTO)
- Estagio 1: "AGUARDE UP/DOWN" quando scanner detecta tendencia
- Estagio 2: "APOSTAR AGORA" no ultimo minuto (mais seguro)
- Pagamento via Pix REAL pelo Mercado Pago

INSTALACAO:
    pip install python-telegram-bot requests

CONFIGURACAO:
    1. TOKEN do BotFather (linha 38)
    2. Access Token do Mercado Pago (linha 44)
    3. ADMIN_ID opcional (linha 39)

COMANDOS:
    /start      - Boas-vindas
    /comprar    - Comprar acesso
    /status     - Verificar status
    /pix        - Gerar Pix
"""

import json
import os
import time
import asyncio
import requests
from datetime import datetime, timezone, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

# ============================================================================
# CONFIGURACAO (variaveis de ambiente para nuvem)
# ============================================================================
TOKEN_BOT = os.getenv("TOKEN_BOT", "SEU_TOKEN_AQUI")
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))

# MERCADO PAGO
MP_ACCESS_TOKEN = os.getenv("MP_ACCESS_TOKEN", "SEU_ACCESS_TOKEN_AQUI")

# Dados Pix fallback
CHAVE_PIX = os.getenv("CHAVE_PIX", "44950f23-ede4-4fb5-825b-b531d11daa97")
NOME_PIX = os.getenv("NOME_PIX", "LUCAS")
CIDADE_PIX = os.getenv("CIDADE_PIX", "SAO PAULO")
VALOR_PIX = float(os.getenv("VALOR_PIX", "15.00"))
DIAS_ACESSO = int(os.getenv("DIAS_ACESSO", "7"))

# Arquivos (na nuvem, salvamos na pasta atual)
ARQ_MERCADO_ATUAL = os.getenv("ARQ_MERCADO_ATUAL", "btc_mercado_atual.json")
ARQ_USUARIOS = os.getenv("ARQ_USUARIOS", "telegram_usuarios.json")
ARQ_PAGAMENTOS = os.getenv("ARQ_PAGAMENTOS", "telegram_pagamentos.json")
ARQ_PENDENTES = os.getenv("ARQ_PENDENTES", "telegram_pendentes.json")

# ============================================================================
# CORES
# ============================================================================
C = {
    'reset': '\033[0m', 'bold': '\033[1m',
    'green': '\033[92m', 'red': '\033[91m',
    'yellow': '\033[93m', 'cyan': '\033[96m',
    'blue': '\033[94m', 'dim': '\033[90m',
}

def log(msg, cor='reset'):
    ts = datetime.now().strftime("%H:%M:%S")
    print(f"[{ts}] {C[cor]}{msg}{C['reset']}", flush=True)

def carregar_json(caminho, padrao):
    try:
        with open(caminho, 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return padrao

def salvar_json(caminho, dados):
    with open(caminho, 'w', encoding='utf-8') as f:
        json.dump(dados, f, indent=2, ensure_ascii=False)

# ============================================================================
# SISTEMA DE USUARIOS
# ============================================================================
def carregar_usuarios():
    return carregar_json(ARQ_USUARIOS, {})

def salvar_usuarios(usuarios):
    salvar_json(ARQ_USUARIOS, usuarios)

def carregar_pagamentos():
    return carregar_json(ARQ_PAGAMENTOS, {"historico": []})

def salvar_pagamentos(pagamentos):
    salvar_json(ARQ_PAGAMENTOS, pagamentos)

def carregar_pendentes():
    return carregar_json(ARQ_PENDENTES, {})

def salvar_pendentes(pendentes):
    salvar_json(ARQ_PENDENTES, pendentes)

def tem_acesso(user_id):
    usuarios = carregar_usuarios()
    user = usuarios.get(str(user_id))
    if not user:
        return False
    expira = user.get("expira_em", "")
    if not expira:
        return False
    try:
        dt_expira = datetime.fromisoformat(expira)
        return datetime.now(timezone.utc) < dt_expira
    except:
        return False

def dias_restantes(user_id):
    usuarios = carregar_usuarios()
    user = usuarios.get(str(user_id))
    if not user:
        return 0
    expira = user.get("expira_em", "")
    if not expira:
        return 0
    try:
        dt_expira = datetime.fromisoformat(expira)
        restante = (dt_expira - datetime.now(timezone.utc)).total_seconds() / 86400
        return max(0, int(restante))
    except:
        return 0

def liberar_acesso(user_id, dias=DIAS_ACESSO):
    usuarios = carregar_usuarios()
    expira = datetime.now(timezone.utc) + timedelta(days=dias)
    usuarios[str(user_id)] = {
        "user_id": user_id,
        "liberado_em": datetime.now(timezone.utc).isoformat(),
        "expira_em": expira.isoformat(),
        "dias": dias,
    }
    salvar_usuarios(usuarios)

# ============================================================================
# MERCADO PAGO
# ============================================================================
MP_HEADERS = {
    "Authorization": f"Bearer {MP_ACCESS_TOKEN}",
    "Content-Type": "application/json",
    "X-Idempotency-Key": ""
}

def criar_pagamento_mp(user_id, valor=VALOR_PIX):
    if MP_ACCESS_TOKEN == "SEU_ACCESS_TOKEN_AQUI":
        return None, "Token do Mercado Pago nao configurado!"

    external_ref = f"POLY_{user_id}_{int(time.time())}"
    payload = {
        "transaction_amount": float(valor),
        "description": f"Acesso Bot Sinais - {DIAS_ACESSO} dias",
        "payment_method_id": "pix",
        "payer": {
            "email": f"user{user_id}@bot.com",
            "first_name": "Usuario",
            "last_name": str(user_id),
        },
        "external_reference": external_ref,
    }
    try:
        headers = dict(MP_HEADERS)
        headers["X-Idempotency-Key"] = external_ref
        response = requests.post(
            "https://api.mercadopago.com/v1/payments",
            headers=headers,
            json=payload,
            timeout=30
        )
        data = response.json()
        if response.status_code in (200, 201):
            payment_id = data.get("id")
            pix_qr = data.get("point_of_interaction", {}).get("transaction_data", {}).get("qr_code", "")
            return {
                "payment_id": payment_id,
                "external_ref": external_ref,
                "qr_code": pix_qr,
                "valor": valor,
                "user_id": user_id,
                "status": "pending",
                "criado_em": datetime.now().isoformat(),
            }, None
        else:
            erro = data.get("message", "Erro desconhecido")
            return None, f"Erro MP: {erro}"
    except Exception as e:
        return None, f"Erro conexao: {e}"

def verificar_pagamento_mp(payment_id):
    try:
        response = requests.get(
            f"https://api.mercadopago.com/v1/payments/{payment_id}",
            headers=MP_HEADERS,
            timeout=30
        )
        data = response.json()
        if response.status_code == 200:
            return data.get("status", "unknown"), data
        return "error", None
    except Exception as e:
        return "error", str(e)

# ============================================================================
# PIX MANUAL (fallback)
# ============================================================================
def gerar_pix_manual(txid, valor=VALOR_PIX):
    valor_str = f"{valor:.2f}"
    chave_len = len(CHAVE_PIX)
    pix_key = f"01{chave_len:02d}{CHAVE_PIX}"
    gui = "0014br.gov.bcb.pix"
    merchant_acc = f"26{len(gui + pix_key):02d}{gui}{pix_key}"
    nome = NOME_PIX[:25]
    nome_field = f"59{len(nome):02d}{nome}"
    cidade = CIDADE_PIX[:15]
    cidade_field = f"60{len(cidade):02d}{cidade}"
    valor_field = f"54{len(valor_str):02d}{valor_str}"
    txid_field = f"05{len(txid):02d}{txid}"
    additional = f"62{len(txid_field):02d}{txid_field}"
    payload = (
        "000201" + merchant_acc + "52040000" + "5303986" +
        valor_field + "5802BR" + nome_field + cidade_field + additional
    )
    crc = calcular_crc16(payload + "6304")
    payload += f"6304{crc:04X}"
    return payload

def calcular_crc16(payload):
    crc = 0xFFFF
    polinomio = 0x1021
    for byte in payload.encode('utf-8'):
        crc ^= (byte << 8)
        for _ in range(8):
            if crc & 0x8000:
                crc = (crc << 1) ^ polinomio
            else:
                crc <<= 1
            crc &= 0xFFFF
    return crc

# ============================================================================
# COMANDOS TELEGRAM
# ============================================================================
async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_id = user.id
    if tem_acesso(user_id):
        keyboard = [[InlineKeyboardButton("📊 Meu Status", callback_data='status')]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(
            f"👋 Ola, {user.first_name}!\n\n"
            f"✅ *Acesso Ativo!*\n"
            f"📊 Voce recebera sinais em *2 estagios*:\n"
            f"   1️⃣ *AGUARDE* — quando o scanner detecta tendencia\n"
            f"   2️⃣ *APOSTAR AGORA* — no *ULTIMO MINUTO* (mais seguro)\n\n"
            f"⚠️ A analise pode mudar ate o fechamento!\n"
            f"📈 Fique atento ao chat!",
            reply_markup=reply_markup, parse_mode='Markdown'
        )
    else:
        keyboard = [
            [InlineKeyboardButton("💰 Comprar Acesso - R${:.2f}".format(VALOR_PIX), callback_data='comprar')],
            [InlineKeyboardButton("📊 Ver Status", callback_data='status')],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        texto = (
            f"👋 Ola, {user.first_name}!\n\n"
            f"🤖 *Bot de Sinais Polymarket BTC*\n\n"
            f"📈 Receba sinais em *2 estagios*:\n"
            f"   1️⃣ *AGUARDE UP/DOWN* — tendencia detectada\n"
            f"   2️⃣ *APOSTAR AGORA* — no *ULTIMO MINUTO* (mais seguro)\n\n"
            f"💳 *Plano:* R${VALOR_PIX:.2f} por {DIAS_ACESSO} dias\n"
            f"✅ Pagamento via *PIX* (Mercado Pago)\n"
            f"⚡ Liberacao automatica apos confirmacao\n\n"
            f"Clique em *Comprar Acesso* para comecar!"
        )
        await update.message.reply_text(texto, reply_markup=reply_markup, parse_mode='Markdown')

async def cmd_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if tem_acesso(user_id):
        dias = dias_restantes(user_id)
        await update.message.reply_text(
            f"✅ *Acesso Ativo!*\n\n"
            f"📅 Dias restantes: *{dias}*\n"
            f"📊 Sinais em *2 estagios*:\n"
            f"   1️⃣ *AGUARDE* — tendencia detectada\n"
            f"   2️⃣ *APOSTAR AGORA* — ultimo minuto (mais seguro)\n\n"
            f"⚠️ A analise pode mudar ate o fechamento!\n"
            f"⏰ Fique atento ao chat!",
            parse_mode='Markdown'
        )
    else:
        keyboard = [[InlineKeyboardButton("💰 Comprar Acesso", callback_data='comprar')]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(
            f"❌ *Acesso Inativo*\n\n"
            f"Clique abaixo para comprar:",
            reply_markup=reply_markup, parse_mode='Markdown'
        )

async def cmd_comprar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    pagamento, erro = criar_pagamento_mp(user_id, VALOR_PIX)
    if pagamento:
        pendentes = carregar_pendentes()
        pendentes[str(user_id)] = pagamento
        salvar_pendentes(pendentes)
        pix_code = pagamento["qr_code"]
        payment_id = pagamento["payment_id"]
        texto = (
            f"💳 *Pagamento via PIX (Mercado Pago)*\n\n"
            f"📋 *Codigo Pix (Copia e Cola):*\n"
            f"`{pix_code}`\n\n"
            f"💰 *Valor:* R${VALOR_PIX:.2f}\n"
            f"📅 *Acesso:* {DIAS_ACESSO} dias\n"
            f"⏱ *Validade:* 30 minutos\n\n"
            f"📲 *Como pagar:*\n"
            f"1. Abra seu app bancario\n"
            f"2. Escolha 'Pix Copia e Cola'\n"
            f"3. Cole o codigo acima\n"
            f"4. Confirme o pagamento\n\n"
            f"✅ Assim que confirmar, seu acesso sera liberado *automaticamente*!"
        )
        keyboard = [
            [InlineKeyboardButton("🔍 Verificar Pagamento", callback_data=f'verificar_{payment_id}')],
            [InlineKeyboardButton("📋 Copiar Codigo Pix", callback_data=f'copiar_mp_{payment_id}')],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(texto, reply_markup=reply_markup, parse_mode='Markdown')
    else:
        txid = f"POLY{user_id}{int(time.time())}"
        pix_code = gerar_pix_manual(txid)
        texto = (
            f"⚠️ *Pagamento via PIX Manual*\n\n"
            f"Erro: `{erro}`\n\n"
            f"📋 *Codigo Pix:*\n"
            f"`{pix_code}`\n\n"
            f"💰 *Valor:* R${VALOR_PIX:.2f}\n"
            f"📅 *Acesso:* {DIAS_ACESSO} dias\n\n"
            f"📲 Pague e envie o comprovante para o admin."
        )
        await update.message.reply_text(texto, parse_mode='Markdown')

async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    user_id = update.effective_user.id
    user = update.effective_user

    if data == 'status':
        if tem_acesso(user_id):
            dias = dias_restantes(user_id)
            await query.edit_message_text(
                f"✅ *Acesso Ativo!*\n\n"
                f"📅 Dias restantes: *{dias}*\n"
                f"📊 Sinais em *2 estagios*:\n"
                f"   1️⃣ *AGUARDE* — tendencia detectada\n"
                f"   2️⃣ *APOSTAR AGORA* — ultimo minuto (mais seguro)\n\n"
                f"⚠️ A analise pode mudar ate o fechamento!",
                parse_mode='Markdown'
            )
        else:
            keyboard = [[InlineKeyboardButton("💰 Comprar Acesso", callback_data='comprar')]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(
                f"❌ *Acesso Inativo*\n\n"
                f"Clique abaixo para comprar:",
                reply_markup=reply_markup, parse_mode='Markdown'
            )

    elif data == 'comprar':
        pagamento, erro = criar_pagamento_mp(user_id, VALOR_PIX)
        if pagamento:
            pendentes = carregar_pendentes()
            pendentes[str(user_id)] = pagamento
            salvar_pendentes(pendentes)
            pix_code = pagamento["qr_code"]
            payment_id = pagamento["payment_id"]
            texto = (
                f"💳 *Pagamento via PIX (Mercado Pago)*\n\n"
                f"📋 *Codigo Pix:*\n"
                f"`{pix_code}`\n\n"
                f"💰 *Valor:* R${VALOR_PIX:.2f}\n"
                f"📅 *Acesso:* {DIAS_ACESSO} dias\n\n"
                f"✅ Pagamento confirmado = acesso liberado automaticamente!"
            )
            keyboard = [
                [InlineKeyboardButton("🔍 Verificar Pagamento", callback_data=f'verificar_{payment_id}')],
                [InlineKeyboardButton("📋 Copiar Codigo Pix", callback_data=f'copiar_mp_{payment_id}')],
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(texto, reply_markup=reply_markup, parse_mode='Markdown')
        else:
            await query.edit_message_text(f"⚠️ Erro: `{erro}`", parse_mode='Markdown')

    elif data.startswith('verificar_'):
        payment_id = data[10:]
        status, info = verificar_pagamento_mp(payment_id)
        if status == "approved":
            liberar_acesso(user_id, DIAS_ACESSO)
            pagamentos = carregar_pagamentos()
            pagamentos["historico"].append({
                "user_id": user_id, "username": user.username or user.first_name,
                "payment_id": payment_id, "valor": VALOR_PIX,
                "data": datetime.now().isoformat(), "status": "aprovado_mp", "gateway": "mercado_pago"
            })
            salvar_pagamentos(pagamentos)
            pendentes = carregar_pendentes()
            if str(user_id) in pendentes:
                del pendentes[str(user_id)]
            salvar_pendentes(pendentes)
            await query.edit_message_text(
                f"🎉 *Pagamento Confirmado!*\n\n"
                f"✅ Acesso liberado por *{DIAS_ACESSO} dias*.\n"
                f"📊 Sinais em 2 estagios: AGUARDE + ULTIMO MINUTO\n\n"
                f"⚡ *Fique atento ao chat!*\n\n"
                f"Bons trades! 🚀",
                parse_mode='Markdown'
            )
            if ADMIN_ID and ADMIN_ID != 0:
                try:
                    await context.bot.send_message(
                        chat_id=ADMIN_ID,
                        text=(f"💰 *Nova Venda!*\n\n👤 {user.first_name}\n🆔 `{user_id}`\n💵 R${VALOR_PIX:.2f}\n✅ Liberado auto!"),
                        parse_mode='Markdown'
                    )
                except: pass
            log(f"Acesso liberado para {user_id} - R${VALOR_PIX} [MP]", 'green')
        elif status == "pending":
            await query.answer("⏳ Pagamento pendente. Pague o Pix no app do banco.", show_alert=True)
        elif status == "in_process":
            await query.answer("⏳ Pagamento em processamento. Aguarde...", show_alert=True)
        else:
            await query.answer(f"❌ Status: {status}. Tente novamente.", show_alert=True)

    elif data.startswith('copiar_mp_'):
        payment_id = data[10:]
        pendentes = carregar_pendentes()
        pix_code = ""
        for uid, pag in pendentes.items():
            if str(pag.get("payment_id")) == payment_id:
                pix_code = pag.get("qr_code", "")
                break
        if pix_code:
            await query.answer("Codigo copiado! Cole no app do banco.", show_alert=True)
        else:
            await query.answer("Codigo nao encontrado.", show_alert=True)

# ============================================================================
# ENVIO DE SINAIS EM 2 ESTAGIOS
# ============================================================================
async def enviar_sinais(application):
    """
    Monitora o mercado atual do scanner e envia sinais em 2 estagios:

    ESTAGIO 1 - "AGUARDE UP/DOWN":
      Enviado quando o scanner detecta uma tendencia clara (sinal UP ou DOWN)
      mas ainda nao e o momento ideal de apostar.
      Avisa o usuario para ficar preparado.

    ESTAGIO 2 - "APOSTAR AGORA UP/DOWN":
      Enviado no ULTIMO MINUTO do mercado, quando o scanner decide apostar.
      Este e o momento mais seguro.
    """
    bot = application.bot

    # Controle de envio por mercado
    enviados_aguarde = set()   # Mercados que ja enviaram "AGUARDE"
    enviados_apostar = set()   # Mercados que ja enviaram "APOSTAR AGORA"
    ultimo_sinal = {}          # Ultimo sinal enviado por mercado (para nao repetir)

    log("Monitor de sinais iniciado!", 'cyan')
    log("Modo: 2 ESTAGIOS (AGUARDE + ULTIMO MINUTO)", 'green')

    while True:
        try:
            # Le o mercado atual do scanner (TEMPO REAL)
            mercado = carregar_json(ARQ_MERCADO_ATUAL, None)

            if not mercado or not isinstance(mercado, dict):
                await asyncio.sleep(3)
                continue

            ta = mercado.get("timestamp_abertura", 0)
            tf = mercado.get("timestamp_fechamento", 0)
            sinal = mercado.get("sinal", "")
            apostou = mercado.get("apostou", False)
            score = mercado.get("score", 50.0)
            scans = mercado.get("scans", 0)
            btc = mercado.get("preco_abertura", 0)
            vs = mercado.get("vs_open", 0)
            mom = mercado.get("mom", 0)
            rsi_v = mercado.get("rsi", 50)
            tend_v = mercado.get("tend", "DESCONHECIDO")

            # Tempo restante
            agora = time.time()
            tempo_restante = max(0, tf - agora)
            min_restantes = int(tempo_restante // 60)
            seg_restantes = int(tempo_restante % 60)

            # ID unico do mercado
            mercado_id = f"btc-updown-5m-{ta}"

            # Se nao tem sinal valido, pula
            if sinal not in ("UP", "DOWN"):
                await asyncio.sleep(3)
                continue

            # =====================================================================
            # ESTAGIO 2: APOSTAR AGORA (ultimo minuto ou scanner decidiu apostar)
            # =====================================================================
            if apostou and mercado_id not in enviados_apostar:
                enviados_apostar.add(mercado_id)

                emoji = "🟢" if sinal == "UP" else "🔴"
                cor_texto = "*UP* 📈" if sinal == "UP" else "*DOWN* 📉"

                # Alerta especial para ultimo minuto
                if tempo_restante <= 60:
                    alerta_tempo = (
                        f"⏰ *ULTIMO MINUTO!*\n"
                        f"⚡ *APOSTAR AGORA!*\n\n"
                    )
                else:
                    alerta_tempo = (
                        f"⏰ *Entrada confirmada!*\n"
                        f"📊 {min_restantes}m {seg_restantes}s restantes\n\n"
                    )

                mensagem = (
                    f"{emoji} *SINAL FINAL* {emoji}\n\n"
                    f"{alerta_tempo}"
                    f"📊 Direcao: {cor_texto}\n"
                    f"🎯 Confianca: {score:.1f}%\n"
                    f"📈 BTC: ${btc:,.2f}\n"
                    f"📊 Momentum: {mom:+.4f}%\n"
                    f"📊 RSI: {rsi_v:.1f}\n"
                    f"📊 Tendencia: {tend_v}\n"
                    f"🆔 Mercado: `{mercado_id}`\n\n"
                    f"✅ *Este e o momento mais seguro para apostar!*\n"
                    f"💰 *Boa sorte no trade!*"
                )

                await enviar_para_usuarios(bot, mensagem, mercado_id, "APOSTAR")

                # Limpa sets antigos
                if len(enviados_apostar) > 50:
                    enviados_apostar.clear()
                    enviados_aguarde.clear()
                    ultimo_sinal.clear()

                await asyncio.sleep(3)
                continue

            # =====================================================================
            # ESTAGIO 1: AGUARDE (tendencia detectada, mas ainda nao e hora)
            # =====================================================================
            # So envia "AGUARDE" se:
            # - Ainda nao enviamos para este mercado
            # - O sinal mudou (ex: era UP, agora é DOWN)
            # - Tem pelo menos 3 scans (dados minimos)
            # - Ainda nao estamos no ultimo minuto

            sinal_anterior = ultimo_sinal.get(mercado_id)

            if (mercado_id not in enviados_aguarde or sinal != sinal_anterior) and scans >= 3 and tempo_restante > 60:

                # Se o sinal mudou, atualiza o controle
                if sinal != sinal_anterior:
                    # Remove do set para reenviar com nova direcao
                    enviados_aguarde.discard(mercado_id)

                enviados_aguarde.add(mercado_id)
                ultimo_sinal[mercado_id] = sinal

                emoji = "🟢" if sinal == "UP" else "🔴"
                cor_texto = "*UP* 📈" if sinal == "UP" else "*DOWN* 📉"

                # Se for atualizacao de sinal (mudou de direcao)
                if sinal_anterior and sinal_anterior != sinal:
                    mudanca = f"⚠️ *ATENCAO: Sinal mudou!*\nAntes: {sinal_anterior} | Agora: {sinal}\n\n"
                else:
                    mudanca = ""

                mensagem = (
                    f"{emoji} *AGUARDE* {emoji}\n\n"
                    f"{mudanca}"
                    f"📊 Tendencia detectada: {cor_texto}\n"
                    f"🎯 Confianca: {score:.1f}%\n"
                    f"📈 BTC: ${btc:,.2f}\n"
                    f"📊 Momentum: {mom:+.4f}%\n"
                    f"📊 RSI: {rsi_v:.1f}\n"
                    f"📊 Tendencia: {tend_v}\n"
                    f"⏰ Tempo restante: {min_restantes}m {seg_restantes}s\n\n"
                    f"⚠️ *A analise pode mudar ate o fechamento!*\n"
                    f"⏳ *O minuto mais seguro e o ULTIMO.*\n"
                    f"📵 *NAO APOSTE AINDA — aguarde o sinal final!*\n\n"
                    f"🆔 Mercado: `{mercado_id}`"
                )

                await enviar_para_usuarios(bot, mensagem, mercado_id, "AGUARDE")

            await asyncio.sleep(3)

        except Exception as e:
            log(f"Erro no monitor: {e}", 'red')
            await asyncio.sleep(3)


async def enviar_para_usuarios(bot, mensagem, mercado_id, tipo):
    """Envia mensagem para todos os usuarios com acesso."""
    usuarios = carregar_usuarios()
    enviados_count = 0

    tipo_str = "AGUARDE" if tipo == "AGUARDE" else "APOSTAR"

    for uid_str, user_data in usuarios.items():
        try:
            uid = int(uid_str)
            if tem_acesso(uid):
                await bot.send_message(
                    chat_id=uid,
                    text=mensagem,
                    parse_mode='Markdown'
                )
                enviados_count += 1
                await asyncio.sleep(0.1)
        except Exception as e:
            log(f"Erro ao enviar para {uid_str}: {e}", 'red')

    log(f"[{tipo_str}] {mercado_id} enviado para {enviados_count} usuarios!", 'green')


# ============================================================================
# VERIFICADOR AUTOMATICO DE PAGAMENTOS
# ============================================================================
async def verificador_automatico(application):
    log("Verificador de pagamentos iniciado!", 'cyan')
    while True:
        try:
            pendentes = carregar_pendentes()
            if pendentes:
                for user_id_str, pagamento in list(pendentes.items()):
                    payment_id = pagamento.get("payment_id")
                    if not payment_id:
                        continue
                    status, info = verificar_pagamento_mp(payment_id)
                    if status == "approved":
                        user_id = int(user_id_str)
                        liberar_acesso(user_id, DIAS_ACESSO)
                        pagamentos = carregar_pagamentos()
                        pagamentos["historico"].append({
                            "user_id": user_id, "payment_id": payment_id,
                            "valor": pagamento.get("valor", VALOR_PIX),
                            "data": datetime.now().isoformat(),
                            "status": "aprovado_auto", "gateway": "mercado_pago"
                        })
                        salvar_pagamentos(pagamentos)
                        del pendentes[user_id_str]
                        salvar_pendentes(pendentes)
                        try:
                            await application.bot.send_message(
                                chat_id=user_id,
                                text=(
                                    f"🎉 *Pagamento Confirmado!*\n\n"
                                    f"✅ Acesso liberado por *{DIAS_ACESSO} dias*.\n"
                                    f"📊 Sinais em 2 estagios: AGUARDE + ULTIMO MINUTO\n\n"
                                    f"⚡ *Fique atento ao chat!*\n\n"
                                    f"Bons trades! 🚀"
                                ),
                                parse_mode='Markdown'
                            )
                        except: pass
                        log(f"Pagamento {payment_id} aprovado! User {user_id}", 'green')
            await asyncio.sleep(30)
        except Exception as e:
            log(f"Erro verificador: {e}", 'red')
            await asyncio.sleep(30)

# ============================================================================
# POST_INIT
# ============================================================================
async def post_init(application: Application):
    log("Bot conectado ao Telegram!", 'green')
    application.create_task(verificador_automatico(application))
    application.create_task(enviar_sinais(application))

# ============================================================================
# MAIN
# ============================================================================
def main():
    if TOKEN_BOT == "SEU_TOKEN_AQUI":
        log("ERRO: Configure o TOKEN_BOT!", 'red')
        return

    log("=" * 60, 'cyan')
    log("Bot Telegram Polymarket v5.0...", 'cyan')
    log("=" * 60, 'cyan')
    log(f"Lendo mercado atual de: {ARQ_MERCADO_ATUAL}", 'dim')
    log(f"Valor: R${VALOR_PIX:.2f} | Dias: {DIAS_ACESSO}", 'dim')
    log("Modo: 2 ESTAGIOS (AGUARDE + APOSTAR AGORA)", 'green')
    log("=" * 60, 'cyan')

    application = Application.builder().token(TOKEN_BOT).post_init(post_init).build()

    application.add_handler(CommandHandler("start", cmd_start))
    application.add_handler(CommandHandler("status", cmd_status))
    application.add_handler(CommandHandler("comprar", cmd_comprar))
    application.add_handler(CommandHandler("pix", cmd_comprar))
    application.add_handler(CallbackQueryHandler(callback_handler))

    log("Bot iniciado! Pressione Ctrl+C para parar.", 'green')
    log("=" * 60, 'cyan')

    application.run_polling()

if __name__ == "__main__":
    main()
