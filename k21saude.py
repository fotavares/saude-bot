# -*- coding: utf-8 -*-
import requests
import json
import amanobot
from amanobot.loop import MessageLoop
import constants
import time
import sqlite3
from datetime import datetime
from pytz import timezone
import sys

TOKEN = ''

BASE_NAME = 'banco.saude.db'
def insertResposta(user_id, chat_id,message_id,timestamp,response):
	with sqlite3.connect(BASE_NAME) as con:
		cursor = con.cursor()
		sql = 'INSERT INTO resposta values (?,?,?,?,?)'
		cursor.execute(sql,[(chat_id),(user_id),(message_id),(timestamp),(response)])
		con.commit()

def insertQuestion(id,perg,timestamp, chat_id):
	with sqlite3.connect(BASE_NAME) as con:
		cursor = con.cursor()
		sql = 'INSERT INTO pergunta values (?,?,?,?,?)'
		cursor.execute(sql,[(0),(id),(perg),(timestamp),(chat_id)])
		con.commit()

def getTimes(chat_id):
	with sqlite3.connect(BASE_NAME) as con:
		cursor = con.cursor()
		sql = 'SELECT distinct timestamp FROM pergunta where chat_id=' + str(chat_id) + ' ORDER BY timestamp DESC'
		cursor.execute(sql)
		data = cursor.fetchmany(7)
		return data

def getChats():
	with sqlite3.connect(BASE_NAME) as con:
		cursor = con.cursor()
		sql = 'SELECT distinct chat_id FROM pergunta '
		cursor.execute(sql)
		data = cursor.fetchall()
		#print(data)
		return data

def isPerguntaValida(chat_id,message_id):
	with sqlite3.connect(BASE_NAME) as con:
		cursor = con.cursor()
		sql = 'SELECT 1 FROM pergunta where chat_id=' + str(chat_id) + ' and message_id = '+ str(message_id) +' ORDER BY timestamp DESC'
		cursor.execute(sql)
		data = cursor.fetchone()
		return (data[0] == 1)

def getResult(timestamp, chat_id):
	with sqlite3.connect(BASE_NAME) as con:
		cursor = con.cursor()
		sql = '''
		select resposta.user_id,resposta.message_id, pergunta.question, response , resposta."timestamp" from resposta
		inner join pergunta on resposta."timestamp" == pergunta."timestamp" and resposta.message_id == pergunta.message_id
		and resposta.chat_id == pergunta.chat_id
		where resposta."timestamp" = '''  + timestamp + ''' and resposta.chat_id = ''' + str(chat_id) + ''' 
		order by resposta.user_id,resposta.message_id'''
		cursor.execute(sql)
		data = cursor.fetchall()
		return data
		
def handle(msg):
	content_type, chat_type, chat_id = amanobot.glance(msg)
	#print(msg)

	data = datetime.now(timezone('Brazil/East')).strftime('%Y%m%d')

	if content_type == 'text':
		if '/saude' in msg['text']:
			EnviaPergunta(chat_id, data)

		if '/resultado' in msg['text'] :
			CarregaResultado(chat_id)
			#	bot.sendMessage(chat_id, "Escolha a data para o resultado:",reply_markup=keybResult)

		if 'reply_to_message' in msg:
			id_pergunta = msg['reply_to_message']['message_id']
			from_pergunta = msg['reply_to_message']['from']['username']
			user_id = msg['from']['id']
			resposta = msg['text']

			me = bot.getMe()
			if from_pergunta == me['username']:
				#é uma pergunta feita pelo bot?
				if isPerguntaValida(chat_id,id_pergunta):
					#grava a resposta
					insertResposta(user_id, chat_id,id_pergunta,data,resposta)

def EnviaPergunta(chat_id, data):
    stamps = getTimes(chat_id)
    send_question = True if (len(stamps) == 0) else True if (str(data) not in stamps[0]) else False
    if (send_question):
        enviada = bot.sendMessage(chat_id,"Quantos dias você trabalhou após as 21h essa semana?")
        insertQuestion(enviada['message_id'],enviada['text'],data,chat_id)
    else:
        bot.sendMessage(chat_id,"Já foi enviada uma enquete hoje")

def CarregaResultado(chat_id):
    stamps = getTimes(chat_id)
    if(len(stamps) == 0):
            bot.sendMessage(chat_id,"Nenhuma pergunta foi feita ainda. Envie /saude antes")
    else:
            dataRecuperada = datetime.strptime(stamps[0][0], "%Y%m%d")

            resultados = getResult(stamps[0][0],chat_id)
            if(len(resultados) == 0):
                    bot.sendMessage(chat_id,"Sem respostas até o momento!")
            else:
                    print(resultados)
                    id_usuario_anterior = 0
                    msg_result = ''
                    flPrintPergunta = False
                    for result in resultados:
                            user_id = result[0]
                            text = result[2]
                            resp = result[3]
                            user = bot.getChatMember(chat_id,user_id)

                            if not flPrintPergunta:
                                    msg_result = msg_result + dataRecuperada.strftime("%d/%m/%Y") + '\n\n'
                                    msg_result = msg_result + text + ' \n'
                                    flPrintPergunta = True

                            if(id_usuario_anterior != user_id):
                                    msg_result = msg_result + '\n' + user['user']['first_name'] + ' ('+user['user']['username']+') :  ' + resp 
                            id_usuario_anterior = user_id

                    bot.sendMessage(chat_id,msg_result)
	


bot = amanobot.Bot(TOKEN)
if len(sys.argv) > 1:
	data = datetime.now(timezone('Brazil/East')).strftime('%Y%m%d')
	if(sys.argv[1]) == 'Pergunta':
		for chat_id in getChats():
			try:
				#print(chat_id[0])
				bot.sendChatAction(chat_id[0],'typing')
			except:
				print(chat_id[0] + " indisponível")
				pass
			else:
				EnviaPergunta(chat_id[0], data)
				print("Mensagem Enviada via Cron")
	elif (sys.argv[1]) == 'Resposta':
		for chat_id in getChats():
			try:
				#print(chat_id[0])
				bot.sendChatAction(chat_id[0],'typing')
			except:
				print(chat_id[0] + " indisponível")
				pass
			else:
				CarregaResultado(chat_id[0])
else:
	MessageLoop(bot, {'chat':handle}).run_as_thread()
	print ('Executando Saude Magrathea...')
	while 1:
		time.sleep(10)


