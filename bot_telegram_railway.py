#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BOT TELEGRAM - v20.7 COMPATIBLE - COM BLOQUEIO DE CONFLITO
"""

import json
import os
import time
import asyncio
import requests
import threading
from datetime import datetime, timezone, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

# =========================
# CONFIGURAÇÃO
# =========================
TOKEN_BOT = os.getenv("TOKEN_BOT", "SEU_TOKEN_AQUI")
VALOR_PIX = float(os.getenv("VALOR_PIX", "15.00"))
DIAS_ACESSO = int(os.getenv("DIAS_ACESSO", "7"))
ARQ_MERCADO_ATUAL = "btc_mercado_atual.json"
ARQ_USUARIOS = "telegram_usuarios.json"
ARQ_LOCK = "bot_lock.txt"  # Arquivo de bloqueio para evitar conflitos

# =========================
# UTILITÁRIOS
# =========================
def log(msg):
    ts = datetime.now().strftime("%H:%M:%S")
    print(f"[BOT][{ts}] {msg}", flush=True)

def carregar_json(caminho, padrao):
    try:
        with open(caminho, 'r') as f:
            return json.load(f)
    except:
        return padrao

def salvar_json(caminho, dados):
    with open(caminho, 'w') as f:
        json.dump(dados, f, indent=2)

def tem_acesso(user_id):
    usuarios = carregar_json(ARQ_USUARIOS, {})
    user = usuarios.get(str(user_id))
    if not user: return False
    try:
        dt_expira = datetime.fromisoformat(user.get("expira_em", ""))
        return datetime.now(timezone.utc) < dt_expira
    except:
        return False

def liberar_acesso(user_id, dias):
    usuarios = carregar_json(ARQ_USUARIOS, {})
    expira = datetime.now(timezone.utc) + timedelta(days=dias)
    usuarios[str(user_id)] = {"user_id": user_id, "expira_em": expira.isoformat()}
    salvar_json(ARQ_USUARIOS, usuarios)

# =========================
# COMANDOS
# =========================
async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if tem_acesso(user.id):
        await update.message.reply_text(f"👋 Olá {user.first_name}!\n\n✅ Acesso Ativo!\n📊 Você receberá os sinais em tempo real.")
    else:
        keyboard = [[InlineKeyboardButton("💰 Comprar Acesso (Teste)", callback_data='comprar')]]
        await update.message.reply_text(
            f"👋 Olá {user.first_name}!\n\n🤖 Bot de Sinais BTC.\n💳 Plano: R${VALOR_PIX:.2f} por {DIAS_ACESSO} dias.",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.data == 'comprar':
        liberar_acesso(update.effective_user.id, DIAS_ACESSO)
        await query.edit_message_text("✅ Acesso liberado com sucesso! (Simulação para teste)")

# =========================
# MONITOR DE SINAIS
# =========================
async def enviar_sinais(application):
    log("Monitor de sinais iniciado!")
    while True:
        try:
            mercado = carregar_json(ARQ_MERCADO_ATUAL, None)
            if mercado and mercado.get("apostou"):
                sinal = mercado.get("sinal", "")
                direcao = "📈 ALTA" if sinal == "UP" else "📉 BAIXA"
                msg = f"🚨 SINAL DETECTADO!\n\nDireção: {direcao}\nPreço: ${mercado.get('preco_abertura', 0):,.2f}\nConfiança: {mercado.get('score', 0):.1f}%"
                
                usuarios = carregar_json(ARQ_USUARIOS, {})
                for uid in usuarios.keys():
                    try:
                        await application.bot.send_message(chat_id=int(uid), text=msg)
                    except: pass
                await asyncio.sleep(300) # Aguarda 5 min para não floodar
            await asyncio.sleep(5)
        except Exception as e:
            log(f"Erro monitor: {e}")
            await asyncio.sleep(5)

async def post_init(application: Application):
    log("Bot conectado e rodando!")
    asyncio.create_task(enviar_sinais(application))

# =========================
# MAIN (COM BLOQUEIO DE CONFLITO)
# =========================
def main():
    if TOKEN_BOT == "SEU_TOKEN_AQUI":
        print("ERRO: TOKEN_BOT não configurado!")
        return

    # 🔒 BLOQUEIO DE CONFLITO: Se o arquivo de lock existir, não inicia
    if os.path.exists(ARQ_LOCK):
        log("⚠️ Outra instância já está rodando. Saindo para evitar Conflict.")
        return
    
    # Cria o arquivo de bloqueio
    with open(ARQ_LOCK, 'w') as f:
        f.write(str(os.getpid()))
    log("🔒 Instância bloqueada com sucesso.")

    try:
        application = Application.builder().token(TOKEN_BOT).post_init(post_init).build()
        application.add_handler(CommandHandler("start", cmd_start))
        application.add_handler(CallbackQueryHandler(callback_handler))
        
        log("✅ Bot iniciado sem conflitos!")
        application.run_polling(drop_pending_updates=True)
    finally:
        # Remove o bloqueio quando o bot parar
        if os.path.exists(ARQ_LOCK):
            os.remove(ARQ_LOCK)
            log("🔓 Bloqueio removido.")

if __name__ == "__main__":
    main()
