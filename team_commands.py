import discord
import re
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
	helptext = open('texts/team_text.txt').read()
	await team.channel.send(helptext)

async def reg_team(message, client):
	if (message.channel.id != meta['team-create-channel']):
		return
	helptext = open('texts/team_help.txt').read()
	team_name = re.findall('`#?(?P<ch>.*?)`', message.content)[0]

	for user in message.mentions:
		if not any([x.id == meta["hacker-role"] for x in user.roles]):
			await message.channel.send("❌At least one user here does not have the Hacker role! Please make sure they have checked in to the server and try again.")
			return

	categ = None
	for cat_id in meta["hacker-channel-category"]:
		if len(client.get_channel(cat_id).channels) < 48:
			categ = client.get_channel(cat_id)
			break
	if categ == None:
		await message.channel.send("❌There isn't enough space in the allotted categories to create new channels. Please make a new category and ping @On-call.")
		return

	nchans = len(client.get_channel(cat_id).channels)
	print(nchans)

	channel = await message.guild.create_text_channel("🐧"+team_name, category=categ)
	vc_channel = await message.guild.create_voice_channel("🛠"+team_name+"-voice", category=categ)

	admin_role = message.guild.get_role(meta["admin-role"])
	mentor_role = message.guild.get_role(meta["mentor-role"])
	await channel.set_permissions(mentor_role, read_messages=True, send_messages=True)
	await vc_channel.set_permissions(mentor_role, connect=True, speak=True, view_channel=True)

	for user in message.mentions:
		await channel.set_permissions(user, read_messages=True, send_messages=True)
		await vc_channel.set_permissions(user, connect=True, speak=True, view_channel=True)

	await channel.set_permissions(message.guild.me, read_messages=True, send_messages=True)
	await channel.set_permissions(message.guild.default_role, read_messages=False, send_messages=False)
	await vc_channel.set_permissions(message.guild.default_role, connect=False, speak=False, view_channel=False)

	conn = sqlite3.connect(dbname)
	c = conn.cursor()
	c.execute(''' INSERT into teams values(?,?,?)''', (team_name,channel.id,vc_channel.id))
	conn.commit()
	c.close()
	conn.close()

	await message.channel.send(f"✅Registered team `{team_name}`, with users " + ", ".join([str(x) for x in message.mentions]) +
		", and private channels have been created. Please check that you successfully pinged every member: if you missed some (either due to a typo or because " +
		"they're not on the server yet), please ping @On-call and they will manually add the missing team members. DO NOT try to register the team again!")

	await channel.send(f"🎉 __**Welcome, Team {team_name}!**__ 🎉\n\nThis is your personal space to talk and " +
	"collaborate amongst your teammates. This text channel, along with the corresponding voice channel, " +
	"are accessible only by the members of this team, as well as organizers for any logistical issues " +
	"and mentors for any help needed. A list of commands you can use that are specific to this channel are:\n\n" +
	helptext +
	"\nIf any members are missing or if there are any logistical issues, please ping @On-call.")

async def process_request(team):
	conn = sqlite3.connect(dbname)
	c = conn.cursor()
	request_text = team.message.content.split('!ask ')[1]

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
