import discord
from discord import app_commands
from discord.ext import tasks, commands
from wordcloud import WordCloud, ImageColorGenerator
import multidict as multidict
from datetime import datetime
import time
import matplotlib.pyplot as plt
import os
import re
import math
import requests
import numpy as np
from PIL import Image
from scipy.ndimage import gaussian_gradient_magnitude
import cv2
import shutil

def read_token():
    with open("token.txt", 'r', encoding="utf-8") as f:
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


def getFrequencyDictForText(member):
    text = ""
    subdirs = [x[0] for x in os.walk("UserCache")]
    for subdir in subdirs:
        files = os.walk(subdir).__next__()[2]
        if files.count(member+".txt") > 0 :
            file = open(subdir + "/" + member+".txt", "r", encoding="utf-8")
            lines = file.readlines()
            i = 0
            while i < len(lines)-1:
                l = lines[i].split("[")
                l[0] = l[0].rstrip(" ")
                l[1] = l[1].rstrip("]\n")
                for x in range(i+1, int(l[1])+i+1):
                    text += lines[x]
                i += int(l[1])+1
            file.close()
    fullTermsDict = multidict.MultiDict()
    tmpDict = {}
    end = ('.', '!', '?', ':', ';', ',')
    for sentence in re.split(' |\n',text):
        if sentence.endswith(end):
            sentence = sentence[:-1]
        if re.match("this|not|it|the|to|in|for|of|if|and|is|that|a|be|on|from|by|der|die|und|in|zu|den|das|nicht|von|sie|ist|ja|nein|des|sich|mit|dem|dass|er|es|ein|ich|auf|so|eine|auch|als|an|nach|wie|im|für", sentence):
            continue
        tmpDict[sentence.lower()] = tmpDict.get(sentence.lower(), 0) + 1
    for key in tmpDict:
        fullTermsDict.add(key, tmpDict[key])
    fullTermsDict.pop('', None)
    return fullTermsDict

def generateWordcloud(dict, member):
    avatar = member.display_avatar.url
    if(avatar.count('embed') > 0): 
        if avatar.count('0.png') > 0 :
            shutil.copy('discord_avatars/0.png', 'graphs/avatar.png')
        elif avatar.count('1.png') > 0 :
            shutil.copy('discord_avatars/1.png', 'graphs/avatar.png')   
        elif avatar.count('2.png') > 0 :
            shutil.copy('discord_avatars/2.png', 'graphs/avatar.png')       
        elif avatar.count('3.png') > 0 :
            shutil.copy('discord_avatars/3.png', 'graphs/avatar.png')        
        elif avatar.count('4.png') > 0 :
            shutil.copy('discord_avatars/4.png', 'graphs/avatar.png')    
        elif avatar.count('5.png') > 0 :
            shutil.copy('discord_avatars/5.png', 'graphs/avatar.png')        
    else:     
        img_data = requests.get(avatar).content
        with open('graphs/avatar.png', 'wb') as handler:
            handler.write(img_data)

    avatar_coloring = np.array(Image.open('graphs/avatar.png'))
    
    avatar_mask = cv2.cvtColor(avatar_coloring, cv2.COLOR_BGR2GRAY)
    edges = cv2.Canny(avatar_mask, threshold1=100, threshold2=200)
    wc = WordCloud(max_words=2000, mask=edges, max_font_size=	25, relative_scaling=0.3, background_color="rgba(255, 255, 255, 0)", mode="RGBA")
    wc.generate_from_frequencies(dict)

    # create coloring from image
    image_colors = ImageColorGenerator(avatar_coloring)
    wc.recolor(color_func=image_colors)
    
    wc.to_file('graphs/wc.png')
    return

class background_caching(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        if not os.path.exists("UserCache"):
            os.makedirs("UserCache")
        if not os.path.exists("graphs"):
            os.makedirs("graphs")    
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
                    lines_to_write = {}
                    if os.path.isfile(f'UserCache/{guild.id}/{channel.id}/time.txt'):
                        with open(f'UserCache/{guild.id}/{channel.id}/time.txt', 'r') as time_file:
                            last_time = datetime.strptime(time_file.readline(), "%Y-%m-%d %H:%M:%S").astimezone() #if checkpoint exists continue
                    else: 
                        last_time = datetime.strptime("2015-05-13 00:00:01", "%Y-%m-%d %H:%M:%S").astimezone() #fallback startime is discord release date
                    async for message in channel.history(limit = 100, after = last_time, oldest_first = True):
                        if message.author not in lines_to_write:
                            lines_to_write[message.author] = []
                        line_count = message.content.count("\n") + 1 #count message length to more easily parse it when reading
                        lines_to_write[message.author].append((f'{message.created_at.astimezone().strftime("%Y-%m-%d %H:%M:%S")} [{line_count}]\n{message.content}\n')) #write time followed by content length and content
                        if message.created_at.astimezone() > last_time: #find oldest message in list
                            last_time = message.created_at.astimezone()
                    for author, lines in lines_to_write.items():
                        with open(f'UserCache/{guild.id}/{channel.id}/{author}.txt', 'a+', encoding="utf-8") as file:
                            for line in lines:
                                file.write(f'{line}')
                    with open(f'UserCache/{guild.id}/{channel.id}/time.txt', 'w', encoding="utf-8") as time_file:
                            time_file.write(last_time.strftime("%Y-%m-%d %H:%M:%S")) #write last parsed message to continue later
                        
    
    @message_cache.before_loop
    async def before_message_cache(self):
        print('waiting...')
        await self.bot.wait_until_ready()



	
intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)


token = read_token()



@bot.tree.command(name = "say_hello", description = "The bot posts Hello", guild=discord.Object(id=1081651254226325658)) 
async def say_hello(interaction):
    await interaction.response.send_message("Hello!")
	
@bot.tree.command(name = "message_times", description = "Get a message time statistic", guild=discord.Object(id=1081651254226325658))	
async def message_times(interaction, member: discord.Member):
    visualizeMessagesTimes(f'{member}')
    await interaction.response.send_message(file=discord.File('graphs/hist.png'))

@bot.tree.command(name = "wordcloud", description = "Get a user wordcloud", guild=discord.Object(id=1081651254226325658))	
async def word_cloud(interaction, member: discord.Member):
    generateWordcloud(getFrequencyDictForText(f'{member}'), member)
    await interaction.response.send_message(file=discord.File('graphs/wc.png'))


@bot.event
async def on_ready():
    await bot.add_cog(background_caching(bot))
    await bot.tree.sync(guild=discord.Object(id=1081651254226325658))
    print("Ready!")


@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    if message.content.startswith('$hello'):
        await message.channel.send('Hello!')


bot.run(token)

