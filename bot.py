import discord
from discord import app_commands

from datetime import datetime
import time

def utc2local(utc):
    epoch = time.mktime(utc.timetuple())
    offset = datetime.fromtimestamp(epoch) - datetime.utcfromtimestamp(epoch)
    return utc + offset


intents = discord.Intents.default()
intents.message_content = True

client = discord.Client(intents=intents)

tree = app_commands.CommandTree(client)



@tree.command(name = "say_hello", description = "The bot posts Hello", guild=discord.Object(id=1081651254226325658)) #Add the guild ids in which the slash command will appear. If it should be in all, remove the argument, but note that it will take some time (up to an hour) to register the command if it's for all guilds.
async def first_command(interaction):
    await interaction.response.send_message("Hello!")
	
@tree.command(name = "message_times", description = "Get a message time statistic", guild=discord.Object(id=1081651254226325658))	
async def history(interaction, member: discord.Member):
    counter = 0
    times = [0] * 24
    for channel in interaction.guild.channels:
        if isinstance(channel, discord.TextChannel):
            async for message in channel.history(limit = 100):
                if message.author == member:
                    counter += 1
                    times[utc2local(message.created_at).hour] += 1

    await interaction.response.send_message(f'{member.mention} has sent **{counter}** messages in this server. \n Message_Time_Array: **{times}**')


@client.event
async def on_ready():
    await tree.sync(guild=discord.Object(id=1081651254226325658))
    print("Ready!")

@client.event
async def on_message(message):
    if message.author == client.user:
        return

    if message.content.startswith('$hello'):
        await message.channel.send('Hello!')

client.run('MTA4NDQyMzcwOTg5MDE4NzM5NA.G5mrBm.EU3MQb9z_uHcoyU9B0j5KeJbdWMb_ZsyNoxxBI')

