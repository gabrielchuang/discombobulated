import discord
import sqlite3
import re
from classes import *
import json
import requests

with open('meta-TH.json') as f:
	meta = json.load(f)
with open('token.json') as tk:
	tokens = json.load(tk)

dbname = meta['dbname']
token = tokens['token']
dash_token = tokens['dashboard-token']

async def help(message, client):
	generalhelp = open('texts/general_help.txt').read()
	await message.channel.send("Here's a list of commands that I can do:\n\n" + generalhelp)

async def about(message, client):
	abouttext = open('texts/about.txt').read()
	await message.channel.send(abouttext)

async def links(message, client):
	linkstext = open('texts/links.txt').read()
	await message.channel.send(linkstext)

async def checkin(message, client):
	# This command is specific to the welcome channel.
	if (message.channel.id != meta['welcome-channel']):
		return

	await message.delete()
	user = message.author
	registered_role = discord.utils.get(message.guild.roles, name="Registered")
	hacker_role = discord.utils.get(message.guild.roles, name="Hacker")

	email = message.content.split('!checkin ')[1]
	url = 'https://thd-api.herokuapp.com/participants/get'
	headers = {'Token': dash_token}
	data = {'email': email}

	response = requests.post(url, headers=headers, data=data)

	if (response.status_code == 200):
		await user.add_roles(registered_role)
		await user.add_roles(hacker_role)
		await message.channel.send("✅ Checked in! You now have access to the rest of the server.")
	else:
		await message.channel.send("❌ We weren't able to find you! Make sure that you've been registered, otherwise ping the @On-call if there is an issue.")
