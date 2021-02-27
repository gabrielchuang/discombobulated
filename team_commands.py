import discord
import sqlite3
from classes import *
import json

# --------------

with open('meta-TH.json') as f:
	meta = json.load(f)
with open('token.json') as tk:
	token = json.load(tk)

dbname = meta["dbname"]

client = discord.Client()

async def send_help(team):
	helptext = open('helptext.txt').read().split('--------')
	await team.channel.send(helptext[0])


async def process_request(team):
	conn = sqlite3.connect(dbname)
	c = conn.cursor()
	request_text = team.message.content

	hint_channel = team.client.get_channel(meta["mentors-channel"])

	c.execute(''' SELECT MAX(number) from requests ''')
	lastreqnum = c.fetchall()[0][0]
	if lastreqnum == None:
		lastreqnum = 0


	request = f"**Question #{lastreqnum+1}**\n**Team**: {team.name}\n**Link**: {team.message.jump_url}\n```{request_text}```" + \
		"Question unclaimed. Please react ✅ to this message to indicate that you will be taking this question! "
	help_message = await hint_channel.send(request)

	c.execute('''SELECT count(*) from requests where complete = 0''')
	num_in_queue =c.fetchall()[0][0]
	await team.channel.send(f"Your question has been added to the queue. A mentor will be along shortly! You are currently #{num_in_queue+1} on the queue. Your question number is {lastreqnum+1}.\nYou can see where you are on the queue at any time by typing `!whereami {lastreqnum+1}`.")

	c.execute(''' INSERT INTO requests VALUES(?,?,?,?,?,?,?)''', (team.name, team.now, request_text, lastreqnum+1, 0, help_message.id, team.message.jump_url))

	conn.commit()
	c.close()
	conn.close()

	await help_message.add_reaction("✅")

async def whereami(team):
	try:
		q_num = int(team.message.content.split()[-1])
		conn = sqlite3.connect(dbname)
		c = conn.cursor()

		c.execute(''' select complete from requests where number=?''', (q_num,))
		if (c.fetchall()[0][0] == 1):
			await team.channel.send(f"This question has already been answered. If you're still waiting, a mentor should be along soon! Otherwise, feel free to add yourself back onto the queue to ask again. ")
			return

		c.execute(''' SELECT count(*) from requests where complete=0''')
		queue_length = c.fetchall()[0][0]

		c.execute('''SELECT count(*) from requests where complete=0 and number<=?''', (q_num,))
		posn = c.fetchall()[0][0]

		await team.channel.send(f"You are position {posn}/{queue_length} on the queue.")
	except:
		await team.channel.send("Sorry, that didn't work. Be sure to type a command of the form `!whereami 1234`, replacing `1234` with your question number.")

@client.event
async def on_reaction_add(reaction, user):
	if str(reaction.emoji) == "✅" and user != user.guild.me:
		conn = sqlite3.connect(dbname)
		c = conn.cursor()
		c.execute(''' SELECT * FROM requests WHERE message_ID=?''', (reaction.message.id,))
		f = c.fetchall()
		if len(f) == 1:
			f = f[0]
			c.execute('''delete from requests where message_ID=?''', (reaction.message.id,))
			c.execute(''' INSERT INTO requests VALUES(?,?,?,?,?,?,?)''', (f[0], f[1], f[2], f[3], 1, f[5],f[6]))
			conn.commit()
			c.close()
			conn.close()

			msg = f"~~**Question #{f[3]}**\n**Team**: {f[0]}\n**Link**: <{f[6]}>~~```{f[2]}```" + \
				f"✅ question taken by {str(user)}! "
			await reaction.message.edit(content=msg, embeds=[])
