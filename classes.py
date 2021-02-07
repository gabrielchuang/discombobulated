import discord
import sqlite3
import datetime

meta = open('meta.txt').read().split()
dbname = meta[1]

class Team():
	def __init__(self, message, client): 
		self.message = message
		self.channel = message.channel
		self.client = client

		self.content = message.content.split(' ')

		conn = sqlite3.connect(dbname)
		c = conn.cursor()
		c.execute('''SELECT team_name, channel_ID, vc_ID FROM teams WHERE channel_ID=?''', (self.channel.id,))
		res = c.fetchall()[0]

		self.name, self.channel_ID, self.vc_ID = res[0], res[1], res[2]

		c.close()

		#haha timezones go brr
		self.now = (message.created_at+datetime.timedelta(hours=-4)).isoformat(sep=' ', timespec='seconds')
