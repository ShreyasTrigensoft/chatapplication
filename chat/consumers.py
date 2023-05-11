import json
from channels.generic.websocket import AsyncWebsocketConsumer

from deepgram import Deepgram
from typing import Dict
import os
from gtts import gTTS
import base64
from deep_translator import GoogleTranslator
import codecs
from dotenv import load_dotenv



load_dotenv()


class ChatConsumer(AsyncWebsocketConsumer):
	dg_client = Deepgram(os.getenv('DEEPGRAM_API_KEY'))

	async def get_transcript(self, data: Dict) -> None:
		if 'channel' in data:
			transcript = data['channel']['alternatives'][0]['transcript']
			trans = await self.send_sdp(transcript)
			if trans:
				# await self.send(trans)
				await self.send(text_data = json.dumps({"message":trans ,"username":'username'}))
		
	async def connect_to_deepgram(self):
		try:
			self.socket = await self.dg_client.transcription.live({'punctuate': True, 'interim_results': False})
			self.socket.registerHandler(self.socket.event.CLOSE, lambda c: print(f'Connection closed with code {c}.'))
			self.socket.registerHandler(self.socket.event.TRANSCRIPT_RECEIVED, self.get_transcript)
			print(self.socket.event.TRANSCRIPT_RECEIVED)
		except Exception as e:
			raise Exception(f'Could not open socket: {e}')

	async def connect(self):
		self.roomGroupName = "group_chat_gfg"
		print(self.channel_name)
		await self.channel_layer.group_add(
			self.roomGroupName ,
			self.channel_name
		)
		await self.connect_to_deepgram()
		await self.accept()

	async def disconnect(self , close_code):
		await self.channel_layer.group_discard(
			self.roomGroupName ,
			self.channel_layer
		)
	async def receive(self, bytes_data):
		# print(bytes_data)
		await self.channel_layer.group_send(
			self.roomGroupName,{
				"type" : "sendMessage" ,
				'bytes_data':bytes_data
			})
		
	async def sendMessage(self , event) :
		# print(event['bytes_data'])
		audio_data = event['bytes_data']
		audio_base64 = base64.b64encode(audio_data)
		audio_base64_string = codecs.decode(audio_base64, 'utf-8')
		await self.send(text_data = json.dumps({"message":'message' ,"audio":audio_base64_string}))



	async def send_sdp(self, bytes_data):
		try:
			translate_text =GoogleTranslator(source='auto', target='hi').translate(bytes_data)

			tts = gTTS(translate_text,slow=False)
			
			filename = 'my_gtts_file.mp3'
			tts.save(filename)

			
			# playsound(filename)

			with open(filename, 'rb') as f:
					audio_bytes = f.read()

			audio_base64 = base64.b64encode(audio_bytes)

			audio_base64_string = codecs.decode(audio_base64, 'utf-8')

			# print("base",audio_base64_string)

			return audio_base64_string
		
		except Exception as e:
			pass
