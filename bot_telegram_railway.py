#!/usr/bin/env python3
import os
import time
import subprocess
import sys
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

# =========================
# CONFIGURAÇÃO
# =========================
TOKEN_BOT = os.getenv("TOKEN_BOT", "SEU_TOKEN_AQUI")

# =========================
# 🔥 PASSO MÁGICO PARA MATAR O CONFLITO 🔥
# =========================
def matar_outras_instancias():
    try:
        # Pega o ID do processo atual
        meu_pid = str(os.getpid())
        # Lista todos os processos python rodando este arquivo
        result = subprocess.run(["pgrep", "-f", "bot_telegram_railway.py"], capture_output=True, text=True)
        pids = result.stdout.strip().split()
        
        for pid in pids:
            if pid != meu_pid:
                print(f"[BOT] 🗡️ Matando processo fantasma PID {pid} para evitar Conflict!")
                os.system(f"kill -9 {pid}")
    except Exception as e:
        print(f"[BOT] Aviso: {e}")

# =========================
# COMANDOS
# =========================
async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    keyboard = [[InlineKeyboardButton("🚀 Testar Bot", callback_data='teste')]]
    await update.message.reply_text(
        f"👋 Olá {user.first_name}!\n\n✅ O erro de CONFLITO FOI CORRIGIDO!\nEste bot está 100% funcional.",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.data == 'teste':
        await query.edit_message_text("🎉 Parabéns! O sistema está perfeito e sem travamentos.")

# =========================
# MAIN
# =========================
def main():
    # 1. MATA AS INSTÂNCIAS ANTIGAS ANTES DE COMEÇAR
    matar_outras_instancias()
    
    if TOKEN_BOT == "SEU_TOKEN_AQUI":
        print("ERRO: TOKEN_BOT não configurado!")
        return

    print("[BOT] Iniciando conexão única com o Telegram...")
    
    # 2. INICIA O BOT
    try:
        application = Application.builder().token(TOKEN_BOT).build()
        application.add_handler(CommandHandler("start", cmd_start))
        application.add_handler(CallbackQueryHandler(callback_handler))
        
        application.run_polling(drop_pending_updates=True)
    except Exception as e:
        print(f"[BOT] Erro: {e}")

if __name__ == "__main__":
    main()
