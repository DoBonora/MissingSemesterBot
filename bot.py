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

class background_caching(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        if not os.path.exists("UserCache"):
            os.makedirs("UserCache")
        for guild in bot.guilds:
            if not os.path.exists(f'UserCache/{guild.id}'):
                os.makedirs(f'UserCache/{guild.id}')
        self.message_cache.start()
    
    def cog_unload(self):
        message_cache.cancel()
    
    @tasks.loop(seconds=30.0)
    async def message_cache(self):
        print("debug loop")
        for guild in bot.guilds:
            for channel in guild.channels:
                if isinstance(channel, discord.TextChannel):
                    if not os.path.exists(f'UserCache/{guild.id}/{channel.id}'):
                        os.makedirs(f'UserCache/{guild.id}/{channel.id}')
                    #last_message_time
                    lines_to_write = {}
                    if os.path.isfile(f'UserCache/{guild.id}/{channel.id}/time.txt'):
                        with open(f'UserCache/{guild.id}/{channel.id}/time.txt', 'r') as time_file:
                            last_time = datetime.strptime(time_file.readline(), "%Y-%m-%d %H:%M:%S").astimezone()
                    else: 
                        last_time = datetime.strptime("2015-05-13 00:00:01", "%Y-%m-%d %H:%M:%S").astimezone() #startime is discord release date
                    async for message in channel.history(limit = 100, after = last_time, oldest_first = True):
                        if message.author not in lines_to_write:
                            lines_to_write[message.author] = []
                        lines_to_write[message.author].append((f'{message.created_at.astimezone().strftime("%Y-%m-%d %H:%M:%S")}\n{message.content}\n'))
                        if message.created_at.astimezone() > last_time:
                            last_time = message.created_at.astimezone()
                    for author, lines in lines_to_write.items():
                        with open(f'UserCache/{guild.id}/{channel.id}/{author}.txt', 'a+') as file:
                            for line in lines:
                                file.write(f'{line}')
                    with open(f'UserCache/{guild.id}/{channel.id}/time.txt', 'w') as time_file:
                            time_file.write(last_time.strftime("%Y-%m-%d %H:%M:%S"))
                        
    
    @message_cache.before_loop
    async def before_message_cache(self):
        print('waiting...')
        await self.bot.wait_until_ready()



	
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
    await bot.add_cog(background_caching(bot))
    print("Ready!")

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    if message.content.startswith('$hello'):
        await message.channel.send('Hello!')


bot.run(token)

