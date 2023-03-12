import discord
from discord import app_commands
from discord.ext import tasks, commands

from datetime import datetime
import time

import os

def read_token():
    with open("token.txt", 'r') as f:
        lines = f.readlines()
        return lines[0].strip()

def utc2local(utc):
    epoch = time.mktime(utc.timetuple())
    offset = datetime.fromtimestamp(epoch) - datetime.utcfromtimestamp(epoch)
    return utc + offset

	
intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)


token = read_token()



@bot.tree.command(name = "say_hello", description = "The bot posts Hello", guild=discord.Object(id=1081651254226325658)) #Add the guild ids in which the slash command will appear. If it should be in all, remove the argument, but note that it will take some time (up to an hour) to register the command if it's for all guilds.
async def say_hello(interaction):
    await interaction.response.send_message("Hello!")
	
@bot.tree.command(name = "message_times", description = "Get a message time statistic", guild=discord.Object(id=1081651254226325658))	
async def message_times(interaction, member: discord.Member):
    counter = 0
    times = [0] * 24
    for channel in interaction.guild.channels:
        if isinstance(channel, discord.TextChannel):
            async for message in channel.history(limit = 100):
                if message.author == member:
                    counter += 1
                    times[utc2local(message.created_at).hour] += 1

    await interaction.response.send_message(f'{member.mention} has sent **{counter}** messages in this server. \n Message_Time_Array: **{times}**')


@bot.event
async def on_ready():
    print("Ready!")

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    if message.content.startswith('$hello'):
        await message.channel.send('Hello!')


bot.run(token)



