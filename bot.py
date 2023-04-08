import discord
from discord import app_commands
from discord.ext import tasks, commands

from datetime import datetime
import time

import matplotlib.pyplot as plt

import os

import math


def read_token():
    with open("token.txt", 'r') as f:
        lines = f.readlines()
        return lines[0].strip()

def utc2local(utc):
    epoch = time.mktime(utc.timetuple())
    offset = datetime.fromtimestamp(epoch) - datetime.utcfromtimestamp(epoch)
    return utc + offset

def visualizeMessagesTimes(member):
    times = []
    subdirs = [x[0] for x in os.walk("UserCache")]
    for subdir in subdirs:
        files = os.walk(subdir).__next__()[2]
        if files.count(member+".txt") > 0 :
            file = open(subdir + "/" + member+".txt", "r")
            lines = file.readlines()
            i = 0
            while i < len(lines)-1:
                l = lines[i].split("[")
                l[0] = l[0].rstrip(" ")
                date = datetime.strptime(l[0], "%Y-%m-%d %H:%M:%S")
                times.append(date.time())
                l[1] = l[1].rstrip("]\n")
                i += int(l[1])+1
            file.close()
			
    
    hour_list = [float(t.hour) for t in times]
    minute_list = [math.floor(t.minute/10)/6 for t in times] # magic numbers, die irgendwas machen Vllt weiß ich es morgen noch /6 = 10/60
    hm_list = []
                    
    for h,m in zip(hour_list, minute_list):
        hm_list.append(h+m)
        
    numbers = [x for x in range(0,24)]
    labels = map(lambda x : str(x), numbers)
    plt.xticks(numbers, labels)
    plt.xlim(0, 24)
    plt.hist(hm_list, color="Green", width= 1/6)

    plt.xlabel('times of messages')
    plt.ylabel('frequency of occurrences')
    plt.title(member)
    plt.savefig('graphs/hist.png')
                   
    return


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
        for guild in bot.guilds:
            for channel in guild.channels:
                if isinstance(channel, discord.TextChannel):
                    if not os.path.exists(f'UserCache/{guild.id}/{channel.id}'):
                        os.makedirs(f'UserCache/{guild.id}/{channel.id}')
                    async for message in channel.history(limit = 100, oldest_first = True):
                        
                        file = open(f'UserCache/{guild.id}/{channel.id}/{message.author}.txt', 'a+', encoding="utf-8")
                        file.write(f'{utc2local(message.created_at)}\n')
                        file.write(f'{message.content}\n')
                        file.close()
    
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

    #await interaction.response.send_message(f'{member.mention} has sent **{counter}** messages in this server. \n Message_Time_Array: **{times}**')
    visualizeMessagesTimes(f'{member}')
    await interaction.response.send_message(file=discord.File('graphs/hist.png'))


@bot.event
async def on_ready():
    #await bot.add_cog(background_caching(bot))
    print("Ready!")

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    if message.content.startswith('$hello'):
        await message.channel.send('Hello!')


bot.run(token)

