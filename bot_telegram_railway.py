#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BOT TELEGRAM - SINAIS POLYMARKET BTC v5.1 (2 ESTAGIOS: AGUARDE + ULTIMO MINUTO)
- CORRIGIDO COMPLETAMENTE PARA COMPATIBILIDADE COM NOVA BIBLIOTECA
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
# CONFIGURACAO (VARIAVEIS DE AMBIENTE)
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

# ============================================================================
# UTILITÁRIOS
# ============================================================================
C = {'reset': '\033[0m', 'green': '\033[92m', 'red': '\033[91m', 'cyan': '\033[96m'}

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
MP_HEADERS = {"Authorization": f"Bearer {MP_ACCESS_TOKEN}", "Content-Type": "application/json"}

def criar_pagamento_mp(user_id, valor=VALOR_PIX):
    if MP_ACCESS_TOKEN == "SEU_ACCESS_TOKEN_AQUI":
        return None, "Token do Mercado Pago nao configurado!"
    external_ref = f"POLY_{user_id}_{int(time.time())}"
    payload = {
        "transaction_amount": float(valor),
        "description": f"Acesso Bot Sinais - {DIAS_ACESSO} dias",
        "payment_method_id": "pix",
        "payer": {"email": f"user{user_id}@bot.com", "first_name": "Usuario", "last_name": str(user_id)},
        "external_reference": external_ref,
    }
    try:
        headers = dict(MP_HEADERS)
        headers["X-Idempotency-Key"] = external_ref
        response = requests.post("https://api.mercadopago.com/v1/payments", headers=headers, json=payload, timeout=30)
        data = response.json()
        if response.status_code in (200, 201):
            return {
                "payment_id": data.get("id"),
                "external_ref": external_ref,
                "qr_code": data.get("point_of_interaction", {}).get("transaction_data", {}).get("qr_code", ""),
                "valor": valor,
                "user_id": user_id,
                "status": "pending",
                "criado_em": datetime.now().isoformat(),
            }, None
        else:
            return None, data.get("message", "Erro desconhecido")
    except Exception as e:
        return None, f"Erro conexao: {e}"

def verificar_pagamento_mp(payment_id):
    try:
        response = requests.get(f"https://api.mercadopago.com/v1/payments/{payment_id}", headers=MP_HEADERS, timeout=30)
        if response.status_code == 200:
            return response.json().get("status", "unknown"), None
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
            f"👋 Ola, {user.first_name}!\n\n✅ *Acesso Ativo!*\n📊 Voce recebera sinais em *2 estagios*:\n    1️⃣ *AGUARDE* — quando o scanner detecta tendencia\n    2️⃣ *APOSTAR AGORA* — no *ULTIMO MINUTO* (mais seguro)",
            reply_markup=reply_markup, parse_mode='Markdown'
        )
    else:
        keyboard = [
            [InlineKeyboardButton("💰 Comprar Acesso - R${:.2f}".format(VALOR_PIX), callback_data='comprar')],
            [InlineKeyboardButton("📊 Ver Status", callback_data='status')],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(
            f"👋 Ola, {user.first_name}!\n\n🤖 *Bot de Sinais Polymarket BTC*\n\n💳 *Plano:* R${VALOR_PIX:.2f} por {DIAS_ACESSO} dias\n✅ Pagamento via *PIX*\n\nClique em *Comprar Acesso* para comecar!",
            reply_markup=reply_markup, parse_mode='Markdown'
        )

async def cmd_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if tem_acesso(user_id):
        dias = dias_restantes(user_id)
        await update.message.reply_text(f"✅ *Acesso Ativo!*\n\n📅 Dias restantes: *{dias}*", parse_mode='Markdown')
    else:
        keyboard = [[InlineKeyboardButton("💰 Comprar Acesso", callback_data='comprar')]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(f"❌ *Acesso Inativo*\n\nClique abaixo para comprar:", reply_markup=reply_markup, parse_mode='Markdown')

async def cmd_comprar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    pagamento, erro = criar_pagamento_mp(user_id, VALOR_PIX)
    if pagamento:
        pendentes = carregar_pendentes()
        pendentes[str(user_id)] = pagamento
        salvar_pendentes(pendentes)
        pix_code = pagamento["qr_code"]
        payment_id = pagamento["payment_id"]
        
        texto = f"💳 *Pagamento via PIX (Mercado Pago)*\n\n📋 *Codigo Pix:*\n`{pix_code}`\n\n💰 *Valor:* R${VALOR_PIX:.2f}\n📅 *Acesso:* {DIAS_ACESSO} dias\n\n✅ Pagamento confirmado = acesso liberado automaticamente!"
        keyboard = [
            [InlineKeyboardButton("🔍 Verificar Pagamento", callback_data=f'verificar_{payment_id}')],
            [InlineKeyboardButton("📋 Copiar Codigo Pix", callback_data=f'copiar_mp_{payment_id}')],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(texto, reply_markup=reply_markup, parse_mode='Markdown')
    else:
        await update.message.reply_text(f"⚠️ Erro: `{erro}`", parse_mode='Markdown')

async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    user_id = update.effective_user.id
    user = update.effective_user

    if data == 'status':
        if tem_acesso(user_id):
            dias = dias_restantes(user_id)
            await query.edit_message_text(f"✅ *Acesso Ativo!*\n\n📅 Dias restantes: *{dias}*", parse_mode='Markdown')
        else:
            keyboard = [[InlineKeyboardButton("💰 Comprar Acesso", callback_data='comprar')]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(f"❌ *Acesso Inativo*\n\nClique abaixo para comprar:", reply_markup=reply_markup, parse_mode='Markdown')

    elif data == 'comprar':
        pagamento, erro = criar_pagamento_mp(user_id, VALOR_PIX)
        if pagamento:
            pendentes = carregar_pendentes()
            pendentes[str(user_id)] = pagamento
            salvar_pendentes(pendentes)
            pix_code = pagamento["qr_code"]
            payment_id = pagamento["payment_id"]
            
            texto = f"💳 *Pagamento via PIX (Mercado Pago)*\n\n📋 *Codigo Pix:*\n`{pix_code}`\n\n💰 *Valor:* R${VALOR_PIX:.2f}\n📅 *Acesso:* {DIAS_ACESSO} dias\n\n✅ Pagamento confirmado = acesso liberado automaticamente!"
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
            await query.edit_message_text(f"🎉 *Pagamento Confirmado!*\n\n✅ Acesso liberado por *{DIAS_ACESSO} dias*.\n\nBons trades! 🚀", parse_mode='Markdown')
        elif status == "pending":
            await query.answer("⏳ Pagamento pendente. Pague o Pix no app do banco.", show_alert=True)
        else:
            await query.answer(f"❌ Status: {status}. Tente novamente.", show_alert=True)

    elif data.startswith('copiar_mp_'):
        await query.answer("Codigo copiado! Cole no app do banco.", show_alert=True)

# ============================================================================
# MONITOR DE SINAIS (2 ESTAGIOS)
# ============================================================================
async def enviar_sinais(application):
    bot = application.bot
    enviados_aguarde = set()
    enviados_apostar = set()
    ultimo_sinal = {}
    
    log("Monitor de sinais iniciado!", 'cyan')
    while True:
        try:
            mercado = carregar_json(ARQ_MERCADO_ATUAL, None)
            if not mercado: 
                await asyncio.sleep(3)
                continue

            ta = mercado.get("timestamp_abertura", 0)
            tf = mercado.get("timestamp_fechamento", 0)
            sinal = mercado.get("sinal", "")
            apostou = mercado.get("apostou", False)
            score = mercado.get("score", 50.0)
            btc = mercado.get("preco_abertura", 0)
            mom = mercado.get("mom", 0)
            rsi_v = mercado.get("rsi", 50)
            tend_v = mercado.get("tend", "DESCONHECIDO")

            agora = time.time()
            tempo_restante = max(0, tf - agora)
            min_restantes = int(tempo_restante // 60)
            seg_restantes = int(tempo_restante % 60)
            mercado_id = f"btc-updown-5m-{ta}"

            if sinal not in ("UP", "DOWN"):
                await asyncio.sleep(3)
                continue

            # ESTAGIO 2: APOSTAR AGORA
            if apostou and mercado_id not in enviados_apostar:
                enviados_apostar.add(mercado_id)
                emoji = "🟢" if sinal == "UP" else "🔴"
                cor_texto = "*UP* 📈" if sinal == "UP" else "*DOWN* 📉"
                alerta_tempo = f"⏰ *ULTIMO MINUTO!*\n⚡ *APOSTAR AGORA!*\n\n" if tempo_restante <= 60 else f"⏰ *Entrada confirmada!*\n📊 {min_restantes}m {seg_restantes}s restantes\n\n"
                
                mensagem = (
                    f"{emoji} *SINAL FINAL* {emoji}\n\n{alerta_tempo}"
                    f"📊 Direcao: {cor_texto}\n🎯 Confianca: {score:.1f}%\n📈 BTC: ${btc:,.2f}\n"
                    f"🆔 Mercado: `{mercado_id}`\n\n✅ *Este e o momento mais seguro para apostar!*"
                )
                await enviar_para_usuarios(bot, mensagem, mercado_id, "APOSTAR")
                await asyncio.sleep(3)
                continue

            # ESTAGIO 1: AGUARDE
            sinal_anterior = ultimo_sinal.get(mercado_id)
            if (mercado_id not in enviados_aguarde or sinal != sinal_anterior) and mercado.get("scans", 0) >= 3 and tempo_restante > 60:
                if sinal != sinal_anterior: enviados_aguarde.discard(mercado_id)
                enviados_aguarde.add(mercado_id)
                ultimo_sinal[mercado_id] = sinal
                
                emoji = "🟢" if sinal == "UP" else "🔴"
                cor_texto = "*UP* 📈" if sinal == "UP" else "*DOWN* 📉"
                mudanca = f"⚠️ *ATENCAO: Sinal mudou!*\nAntes: {sinal_anterior} | Agora: {sinal}\n\n" if sinal_anterior and sinal_anterior != sinal else ""
                
                mensagem = (
                    f"{emoji} *AGUARDE* {emoji}\n\n{mudanca}"
                    f"📊 Tendencia detectada: {cor_texto}\n🎯 Confianca: {score:.1f}%\n📈 BTC: ${btc:,.2f}\n"
                    f"⏰ Tempo restante: {min_restantes}m {seg_restantes}s\n\n"
                    f"⚠️ *A analise pode mudar ate o fechamento!*\n📵 *NAO APOSTE AINDA — aguarde o sinal final!*"
                )
                await enviar_para_usuarios(bot, mensagem, mercado_id, "AGUARDE")
                
            await asyncio.sleep(3)
        except Exception as e:
            log(f"Erro no monitor: {e}", 'red')
            await asyncio.sleep(3)

async def enviar_para_usuarios(bot, mensagem, mercado_id, tipo):
    usuarios = carregar_usuarios()
    enviados_count = 0
    for uid_str, user_data in usuarios.items():
        try:
            uid = int(uid_str)
            if tem_acesso(uid):
                await bot.send_message(chat_id=uid, text=mensagem, parse_mode='Markdown')
                enviados_count += 1
                await asyncio.sleep(0.05)
        except Exception as e:
            log(f"Erro ao enviar para {uid_str}: {e}", 'red')
    log(f"[{tipo}] {mercado_id} enviado para {enviados_count} usuarios!", 'green')

# ============================================================================
# VERIFICADOR DE PAGAMENTOS
# ============================================================================
async def verificador_automatico(application):
    log("Verificador de pagamentos iniciado!", 'cyan')
    while True:
        try:
            pendentes = carregar_pendentes()
            for user_id_str, pagamento in list(pendentes.items()):
                payment_id = pagamento.get("payment_id")
                if not payment_id: continue
                status, info = verificar_pagamento_mp(payment_id)
                if status == "approved":
                    user_id = int(user_id_str)
                    liberar_acesso(user_id, DIAS_ACESSO)
                    pagamentos = carregar_pagamentos()
                    pagamentos["historico"].append({"user_id": user_id, "payment_id": payment_id, "valor": pagamento.get("valor", VALOR_PIX), "data": datetime.now().isoformat(), "status": "aprovado_auto", "gateway": "mercado_pago"})
                    salvar_pagamentos(pagamentos)
                    del pendentes[user_id_str]
                    salvar_pendentes(pendentes)
                    try:
                        await application.bot.send_message(chat_id=user_id, text=f"🎉 *Pagamento Confirmado!*\n\n✅ Acesso liberado por *{DIAS_ACESSO} dias*.\n\nBons trades! 🚀", parse_mode='Markdown')
                    except: pass
                    log(f"Pagamento {payment_id} aprovado! User {user_id}", 'green')
            await asyncio.sleep(30)
        except Exception as e:
            log(f"Erro verificador: {e}", 'red')
            await asyncio.sleep(30)

# ============================================================================
# POST_INIT (NOVO MÉTODO CORRETO)
# ============================================================================
async def post_init(application: Application):
    log("Bot conectado ao Telegram!", 'green')
    # Cria as tarefas assíncronas
    asyncio.create_task(verificador_automatico(application))
    asyncio.create_task(enviar_sinais(application))

# ============================================================================
# MAIN
# ============================================================================
def main():
    if TOKEN_BOT == "SEU_TOKEN_AQUI":
        log("ERRO: Configure o TOKEN_BOT nas variáveis de ambiente!", 'red')
        return

    log("=" * 60, 'cyan')
    log("Bot Telegram Polymarket v5.1 - CORRIGIDO", 'cyan')
    log("=" * 60, 'cyan')

    # Inicialização correta com Application (sem Updater antigo)
    application = Application.builder().token(TOKEN_BOT).post_init(post_init).build()

    application.add_handler(CommandHandler("start", cmd_start))
    application.add_handler(CommandHandler("status", cmd_status))
    application.add_handler(CommandHandler("comprar", cmd_comprar))
    application.add_handler(CallbackQueryHandler(callback_handler))

    log("Bot iniciado! Pressione Ctrl+C para parar.", 'green')
    application.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
