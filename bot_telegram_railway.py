#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BOT TELEGRAM - SINAIS POLYMARKET BTC v5.1 (2 ESTAGIOS: AGUARDE + ULTIMO MINUTO)
- CORRIGIDO PARA COMPATIBILIDADE COM NOVA BIBLIOTECA
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
# CONFIGURACAO
# ============================================================================
TOKEN_BOT = os.getenv("TOKEN_BOT", "SEU_TOKEN_AQUI")
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))
MP_ACCESS_TOKEN = os.getenv("MP_ACCESS_TOKEN", "SEU_ACCESS_TOKEN_AQUI")

CHAVE_PIX = os.getenv("CHAVE_PIX", "44950f23-ede4-4fb5-825b-b531d11daa97")
NOME_PIX = os.getenv("NOME_PIX", "LUCAS")
CIDADE_PIX = os.getenv("CIDADE_PIX", "SAO PAULO")
VALOR_PIX = float(os.getenv("VALOR_PIX", "15.00"))
DIAS_ACESSO = int(os.getenv("DIAS_ACESSO", "7"))

ARQ_MERCADO_ATUAL = os.getenv("ARQ_MERCADO_ATUAL", "btc_mercado_atual.json")
ARQ_USUARIOS = os.getenv("ARQ_USUARIOS", "telegram_usuarios.json")
ARQ_PAGAMENTOS = os.getenv("ARQ_PAGAMENTOS", "telegram_pagamentos.json")
ARQ_PENDENTES = os.getenv("ARQ_PENDENTES", "telegram_pendentes.json")

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
    if not user: return False
    expira = user.get("expira_em", "")
    if not expira: return False
    try:
        dt_expira = datetime.fromisoformat(expira)
        return datetime.now(timezone.utc) < dt_expira
    except:
        return False

def dias_restantes(user_id):
    usuarios = carregar_usuarios()
    user = usuarios.get(str(user_id))
    if not user: return 0
    expira = user.get("expira_em", "")
    if not expira: return 0
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
# COMANDOS TELEGRAM
# ============================================================================
async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_id = user.id
    if tem_acesso(user_id):
        keyboard = [[InlineKeyboardButton("📊 Meu Status", callback_data='status')]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(
            f"👋 Ola, {user.first_name}!\n\n✅ *Acesso Ativo!*\n📊 Voce recebera sinais em *2 estagios*:\n    1️⃣ *AGUARDE* — quando o scanner detecta tendencia\n    2️⃣ *APOSTAR AGORA* — no *ULTIMO MINUTO* (mais seguro)\n\n⚠️ A analise pode mudar ate o fechamento!\n📈 Fique atento ao chat!",
            reply_markup=reply_markup, parse_mode='Markdown'
        )
    else:
        keyboard = [
            [InlineKeyboardButton("💰 Comprar Acesso - R${:.2f}".format(VALOR_PIX), callback_data='comprar')],
            [InlineKeyboardButton("📊 Ver Status", callback_data='status')],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(
            f"👋 Ola, {user.first_name}!\n\n🤖 *Bot de Sinais Polymarket BTC*\n\n📈 Receba sinais em *2 estagios*:\n    1️⃣ *AGUARDE UP/DOWN* — tendencia detectada\n    2️⃣ *APOSTAR AGORA* — no *ULTIMO MINUTO* (mais seguro)\n\n💳 *Plano:* R${VALOR_PIX:.2f} por {DIAS_ACESSO} dias\n✅ Pagamento via *PIX* (Mercado Pago)\n⚡ Liberacao automatica apos confirmacao\n\nClique em *Comprar Acesso* para comecar!",
            reply_markup=reply_markup, parse_mode='Markdown'
        )

async def cmd_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if tem_acesso(user_id):
        dias = dias_restantes(user_id)
        await update.message.reply_text(
            f"✅ *Acesso Ativo!*\n\n📅 Dias restantes: *{dias}*\n📊 Sinais em *2 estagios*:\n    1️⃣ *AGUARDE* — tendencia detectada\n    2️⃣ *APOSTAR AGORA* — ultimo minuto (mais seguro)\n\n⚠️ A analise pode mudar ate o fechamento!\n⏰ Fique atento ao chat!",
            parse_mode='Markdown'
        )
    else:
        keyboard = [[InlineKeyboardButton("💰 Comprar Acesso", callback_data='comprar')]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(
            f"❌ *Acesso Inativo*\n\nClique abaixo para comprar:",
            reply_markup=reply_markup, parse_mode='Markdown'
        )

async def cmd_comprar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    pagamento, erro = criar_pagamento_mp(user_id, VALOR_PIX)
    if pagamento:
        pendentes = carregar_pendentes()
        pendentes[str(user_id)] =
