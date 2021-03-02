import discord
import sqlite3
import re
import json
from general_commands import *
from team_commands import *
from admin_commands import *
from classes import *

with open('meta-TH.json') as f:
	meta = json.load(f)
with open('token.json') as tk:
	token = json.load(tk)

dbname = meta["dbname"]

cc = '!' # command character

superadmins = meta['superadmins']

# --------------

#to add commands anyone can use, add it here
general_commands = {}

#to add commands specific to a team: write a function, and add it here.
team_commands = {'help':send_help, 'ask':process_request, 'whereami':whereami}

#to add admin or super-admin commands, add it here
admin_commands = {'register_team':reg_team, 'rt':reg_team, 'adminhelp':admin_help, 'announce':announce, 'check':check, 'refresh':refresh}
superadmin_commands = {'sudo':sudo, 'reset':reset}

@client.event
async def on_message(message):
	if message.author != message.guild.me and message.content[0] == cc:
		for cmd in team_commands.keys():
			if cc+cmd in message.content:
				team = Team(message, client)
				await team_commands[cmd](team)
				break
		for cmd in admin_commands.keys():
			if cc+cmd in message.content and any([x.id == meta["admin-role"] for x in message.author.roles]) and message.channel.id==meta["admin-channel"]:
				await admin_commands[cmd](message, client)
				break
		for cmd in superadmin_commands.keys():
			if cc+cmd in message.content and message.author.id in superadmins and message.channel.id==meta["admin-channel"]:
				await superadmin_commands[cmd](message, client)
				break


@client.event
async def on_ready():
	print('Logged in as')
	print(client.user.name)
	print(client.user.id)

client.run(token["token"])
