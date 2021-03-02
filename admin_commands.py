import discord
import sqlite3
import re
from classes import *
import json
import requests

with open('meta-TH.json') as f:
	meta = json.load(f)
with open('token.json') as tk:
	token = json.load(tk)

dbname = meta["dbname"]

# --------------

async def admin_help(message, client):
	helptext = open('texts/helptext.txt').read().split('--------')
	await message.channel.send(helptext[1])

async def sudo(message, client):
	query = re.findall('```(?P<ch>.*?)```', message.content)[0]
	conn = sqlite3.connect(dbname)
	c = conn.cursor()
	c.execute(query)
	conn.commit()
	c.close()
	conn.close()

async def check(message, client):
	email = message.content.split('!check ')[1]
	url = 'https://thd-api.herokuapp.com/participants/get'
	dash_token = token['dashboard-token']
	headers = {'Token': dash_token}
	data = {'email': email}

	response = requests.post(url, headers=headers, data=data)

	if (response.status_code == 200):
		participant = response.json()[0]
		name = participant['name']
		team = participant['team_id']
		await message.channel.send(f"✅ Found! This participant's name is {name} with team {team}")
	if (response.status_code == 401):
		await message.channel.send("❌ The dashboard access token has expired!")
	elif (response.status_code == 404):
		await message.channel.send("❌ Could not find the participant.")
	elif (response.status_code == 500):
		await message.channel.send("❌ Some internal server error code. Try again later or contact the tech team.")

async def reg_team(message, client):
	helptext = open('texts/helptext.txt').read().split('--------')
	team_name = re.findall('`#?(?P<ch>.*?)`', message.content)[0]

	categ = None
	for cat_id in meta["hacker-channel-category"]:
		if len(client.get_channel(cat_id).channels) < 48:
			categ = client.get_channel(cat_id)
			break
	if categ == None:
		await message.channel.send("There isn't enough space in the allotted categories to create new channels. Please make a new category and ping Keiffer.")
		return

	nchans = len(client.get_channel(cat_id).channels)
	print(nchans)

	channel = await message.guild.create_text_channel(team_name, category=categ)
	vc_channel = await message.guild.create_voice_channel(team_name+"-voice", category=categ)

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
		"and connect and speak (in the voice channels). Please ping Keiffer for any details on this.")

	await channel.send(f"🎉 __**Welcome, Team {team_name}!**__ 🎉\n\nThis is your personal space to talk and " +
	"collaborate amongst your teammates. This text channel, along with the corresponding voice channel, " +
	"are accessible only by the members of this team, as well as organizers for any logistical issues " +
	"and mentors for any help needed. A list commands you can use specific to this channel are:\n\n" +
	helptext[0] +
	"\nIf any members are missing or if there are any logistical issues, please ping the Organizers.")


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
