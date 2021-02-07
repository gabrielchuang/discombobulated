import discord
import sqlite3
import datetime
import re
from classes import *
import random
import json

hintchannel_ID = int(meta[2])


with open('meta.json') as f:
	meta = json.load(f)
dbname = meta["dbname"]


client = discord.Client()
cc = '!' # command character

auth_admins = [int(x) for x in admin_IDs.split(',')]

async def send_help(team):
	helptext = open('helptext.txt').read().split('--------')
	await team.channel.send(helptext[0])

async def admin_help(message, client):
	helptext = open('helptext.txt').read().split('--------')
	await message.channel.send(helptext[1])

async def process_request(team):
	conn = sqlite3.connect(dbname)
	c = conn.cursor()
	request_text = team.message.content 

	hint_channel = team.client.get_channel(meta["mentors-channel"])

	c.execute(''' SELECT MAX(number) from requests ''')
	lastreqnum = c.fetchall()[0][0]
	if lastreqnum == None:
		lastreqnum = 0

	await team.channel.send(f"Your question has been added to the queue. A TA will be along shortly!")

	request = f"**Question #{lastreqnum+1}**\n**Team**: {team.name}\n**Link**: {team.message.jump_url}\n```{request_text}```" + 
		"Please react ✅ to this message to indicate that you will be taking this question! "
	help_message = await hint_channel.send(request)

	c.execute(''' INSERT INTO requests VALUES(?,?,?,?,?,?)''', (team.name, team.now, request_text, lastreqnum+1, 0, help_message.id))
	conn.commit()
	c.close()
	conn.close()

async def sudo(message, client): 
	query = re.findall('```(?P<ch>.*?)```', message.content)[0]
	conn = sqlite3.connect(dbname)
	c = conn.cursor()
	c.execute(query)
	conn.commit()
	c.close()
	conn.close()

async def reg_team(message, client):
	team_name = re.findall('`#?(?P<ch>.*?)`', message.content)[0]
	channel = await message.guild.create_text_channel(team_name, category=message.channel.category)
	vc_channel = await message.guild.create_voice_channel(team_name+"-voice", category=message.channel.category)

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

	await message.channel.send(f"Registered team `{team_name}`, with users " + ", ".join([str(x) for x in message.mentions]) + 
		". Please check that you successfully pinged every member: if you missed some (either due to a typo or because " +
		"they're not on the server yet), you will have to manually give them permissions to read and send messages (in the text channels) " +
		"and connect and speak (in the voice channels).")


async def reset(message, client):
	conn = sqlite3.connect(dbname)
	c = conn.cursor()
	c.execute(''' DELETE FROM teams''')
	conn.commit()
	c.execute(''' DELETE FROM requests''')
	conn.commit()
	c.close()
	conn.close()

async def announce(message, client):
	conn = sqlite3.connect(dbname)
	c = conn.cursor()
	c.execute(''' SELECT channel_ID, team_name from teams''')
	f = c.fetchall()

	announcement = re.findall('```#?(?P<ch>.*?)```', message.content)[0]

	for team in f:
		print(team)
		try:
			this_channel = client.get_channel(team[0])
			await this_channel.send(announcement)
		except:
			await message.channel.send("Failed to send announcement to team " + team[1] + ", likely because their team channel no longer exists.")
	await message.channel.send("The announcement has been sent to all teams.")

	c.close()
	conn.close()

general_commands = {'help':send_help, 'ask':process_request}
admin_commands = {'sudo':sudo, 'register_team':reg_team, 'rt':reg_team, 'reset':reset, 'adminhelp':admin_help, 'announce':announce}


async def on_raw_reaction_add(payload):
	pass

@client.event
async def on_message(message):
	if message.author != message.guild.me and message.content[0] == cc:
		for cmd in general_commands.keys():
			if cc+cmd in message.content:
				team = Team(message, client)
				await general_commands[cmd](team)
				break 
		for cmd in admin_commands.keys():
			if cc+cmd in message.content and message.author.id in auth_admins and message.channel.id==hintchannel_ID:
				await admin_commands[cmd](message, client)
				break 


@client.event
async def on_ready():
	print('Logged in as')
	print(client.user.name)
	print(client.user.id)

client.run(meta["token"])
