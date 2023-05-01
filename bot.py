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
import cv2
import shutil
from deepdiff import DeepDiff

def read_token():
    with open("token.txt", 'r', encoding="utf-8") as f:
        lines = f.readlines()
        return lines[0].strip()

def utc2local(utc):
    epoch = time.mktime(utc.timetuple())
    offset = datetime.fromtimestamp(epoch) - datetime.utcfromtimestamp(epoch)
    return utc + offset

def visualizeMessagesTimes(member, image = True):
    plt.clf()
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
    #TODO: Helena pls fix comment
    minute_list = [math.floor(t.minute/10)/6 for t in times] # magic numbers, die irgendwas machen Vllt weiß ich es morgen noch /6 = 10/60
    hm_list = []
                    
    for h,m in zip(hour_list, minute_list):
        hm_list.append(h+m)
        
    if image: 
        numbers = [x for x in range(0,24)]
        labels = map(lambda x : str(x), numbers)
        plt.xticks(numbers, labels)
        plt.xlim(0, 24)
        plt.hist(hm_list, color="Green", width= 1/6)

        plt.xlabel('times of messages')
        plt.ylabel('frequency of occurrences')
        plt.title(member)
        plt.savefig('graphs/hist.png')
             
    return hm_list


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
    avatar = member.display_avatar.replace(format='png', size=2048).url
    
    #discord uses greyscale pngs colored by some 'magic' which breaks the algorithm
    #therefore we just hardcoded all the 6 possible default avatars with pictures we manually saved
    if avatar.count('embed') > 0 : 
        if avatar.count('0.png') > 0 :
            shutil.copy('ressources/0.png', 'graphs/avatar.png')
        elif avatar.count('1.png') > 0 :
            shutil.copy('ressources/1.png', 'graphs/avatar.png')   
        elif avatar.count('2.png') > 0 : 
            shutil.copy('ressources/2.png', 'graphs/avatar.png')       
        elif avatar.count('3.png') > 0 :
            shutil.copy('ressources/3.png', 'graphs/avatar.png')        
        elif avatar.count('4.png') > 0 :
            shutil.copy('ressources/4.png', 'graphs/avatar.png')    
        elif avatar.count('5.png') > 0 :
            shutil.copy('ressources/5.png', 'graphs/avatar.png')        
    else:     
        img_data = requests.get(avatar).content
        with open('graphs/avatar.png', 'wb') as handler:
            handler.write(img_data)
    
    avatar_coloring = np.array(Image.open('graphs/avatar.png'))
    avatar_mask = cv2.cvtColor(avatar_coloring, cv2.COLOR_BGR2GRAY)
    edges = cv2.Canny(avatar_mask, threshold1=100, threshold2=200)
    wc = WordCloud(max_words=2000, mask=edges, relative_scaling=0.1, background_color="rgba(255, 255, 255, 0)", mode="RGBA")
    wc.generate_from_frequencies(dict)

    # create coloring from image
    image_colors = ImageColorGenerator(avatar_coloring)
    wc.recolor(color_func=image_colors)
    
    wc.to_file('graphs/wc.png')
    return

def averageHours(hour_list):
    #average time of a list of times
    for idx, x in enumerate(hour_list):
        if (idx == 0): avg = x
        else :
            #calculate difference with hour wraparound
            dif = x-avg
            if (abs(dif) > 12): dif=x+(24-avg)
            avg += (dif / (idx+1)) #rolling average
            if (avg > 24): avg-=24
    return avg

def calculateLovescore(member1, member2):
    hm_list1 = visualizeMessagesTimes(f'{member1}', image = False)
    hm_list2 = visualizeMessagesTimes(f'{member2}', image = False)
    plt.clf()


    avg1 = averageHours(hm_list1)
    avg2 = averageHours(hm_list2)

    #same calculation for difference
    timeDifference = avg1-avg2
    if (abs(timeDifference) > 12): timeDifference=avg1+(24-avg2)
    
    #percentage the times differ by
    timeScore = 100 - 100*abs(timeDifference)/24

    dict1 = getFrequencyDictForText(f'{member1}')
    dict2 = getFrequencyDictForText(f'{member2}')

    #we compare the top 10 of both users
    #for this we compare the occurance of both these top10 in both users
    dict_Top10_1 = sorted(dict1, key=dict1.get, reverse=True)[:10]
    dict_Top10_2 = sorted(dict2, key=dict2.get, reverse=True)[:10]

    occ1 = 0
    occ1_1 = 0
    for key in dict_Top10_1:
        occ1 += dict2.get(key, 0)
        occ1_1 += dict1.get(key, 0)
    dictDiff1 = occ1/sum(dict2.values())
    owndictDiff1 = occ1_1/sum(dict1.values())
    dictDiff1 = 100 * dictDiff1/owndictDiff1
    
    occ2 = 0
    occ2_2 = 0
    for key in dict_Top10_2:
        occ2 += dict1.get(key, 0)
        occ2_2 += dict2.get(key,0)
    dictDiff2 = occ2/sum(dict1.values())
    owndictDiff2 = occ2_2/sum(dict2.values())
    dictDiff2 = 100 * dictDiff2/owndictDiff2

    #final lovescore is the average difference of all these scores
    dictScore = (dictDiff1+dictDiff2)/2
    lovescore = int((timeScore+dictScore)/2)



    generateWordcloud(dict1, member1)
    wc1 = plt.imread('graphs/wc.png')
    generateWordcloud(dict2, member2)
    wc2 = plt.imread('graphs/wc.png')
    heart = plt.imread('ressources/heart.png')

    fig, axes = plt.subplots(1, 3)
    plt.text(0.5, 0.5, f'{lovescore}%', ha ='center', va ='center', size=25, transform = axes[1].transAxes)

    axes[0].imshow(wc1, interpolation="bilinear")
    axes[1].imshow(heart, interpolation="bilinear")
    axes[2].imshow(wc2, interpolation="bilinear")
    for ax in axes:
        ax.set_axis_off()
    plt.savefig('graphs/lovescore.png', transparent=True, bbox_inches='tight')
    return  

#we cant just poll discord for 50000 messages with every command
#therefore we poll it in the background and save it into a local cash in chunks    
class background_caching(commands.Cog):
    #on init create the folder structure if it does not exist yet
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
        self.message_cache.cancel()
    
    #every 30 seconds we poll new messages to cache more, or to add new messages once our cache is up to date
    @tasks.loop(seconds=30.0)
    async def message_cache(self):
        #print("debug loop")
        #for every server and every channel on those servers we make a cache folder
        for guild in bot.guilds:
            for channel in guild.channels:
                if isinstance(channel, discord.TextChannel):
                    if not os.path.exists(f'UserCache/{guild.id}/{channel.id}'):
                        os.makedirs(f'UserCache/{guild.id}/{channel.id}')
                    lines_to_write = {}
                    #we save the timestamp of the last message we cached, so we can continue from that point the next time
                    if os.path.isfile(f'UserCache/{guild.id}/{channel.id}/time.txt'):
                        with open(f'UserCache/{guild.id}/{channel.id}/time.txt', 'r') as time_file:
                            last_time = datetime.strptime(time_file.readline(), "%Y-%m-%d %H:%M:%S").astimezone() #if checkpoint exists continue
                    else: 
                        last_time = datetime.strptime("2015-05-13 00:00:01", "%Y-%m-%d %H:%M:%S").astimezone() #fallback startime is discord release date
                    #limit of 100 messages was chosen arbitrarily, it works for our purposes, for larger servers the bot needs some time to be up to date
                    async for message in channel.history(limit = 100, after = last_time, oldest_first = True):
                        if message.author not in lines_to_write:
                            lines_to_write[message.author] = []
                        line_count = message.content.count("\n") + 1 #count message length to more easily parse it when reading
                        #write time followed by content length and content
                        lines_to_write[message.author].append((f'{message.created_at.astimezone().strftime("%Y-%m-%d %H:%M:%S")} [{line_count}]\n{message.content}\n'))
                        if message.created_at.astimezone() > last_time: #find oldest message in list
                            last_time = message.created_at.astimezone()
                    for author, lines in lines_to_write.items():
                        #write the timestamp and all lines in a fspecific file for every user
                        with open(f'UserCache/{guild.id}/{channel.id}/{author}.txt', 'a+', encoding="utf-8") as file:
                            for line in lines:
                                file.write(f'{line}')
                    with open(f'UserCache/{guild.id}/{channel.id}/time.txt', 'w', encoding="utf-8") as time_file:
                            time_file.write(last_time.strftime("%Y-%m-%d %H:%M:%S")) #write time of last parsed message to continue later
                        
    #debug message before the caching starts to show bot is ready
    @message_cache.before_loop
    async def before_message_cache(self):
        print('waiting...')
        await self.bot.wait_until_ready()



#discord bots use intends to set up what they can and cannot do (as well als giving them rights on a server)	
intents = discord.Intents.default()
intents.message_content = True

#command prefix only used for old way of doing commands
bot = commands.Bot(command_prefix="!", intents=intents)


token = read_token()


#Discord commands need to be registered on the  tree to be able to be used as slash commands
#Registering them on a specific guild (i.e. Server) makes them available faster but limits them
@bot.tree.command(name = "say_hello", description = "The bot posts Hello", guild=discord.Object(id=1081651254226325658)) 
async def say_hello(interaction):
    await interaction.response.send_message("Hello!")
	
@bot.tree.command(name = "message_times", description = "Get a message time statistic", guild=discord.Object(id=1081651254226325658))	
async def message_times(interaction, member: discord.Member):
    #if the message is not responded in time it times out, so we need to defer it
    await interaction.response.defer()
    visualizeMessagesTimes(f'{member}')
    #the followup can be used to answer a defered question after the fact i.e. once the image is created
    await interaction.followup.send(file=discord.File('graphs/hist.png'))

@bot.tree.command(name = "wordcloud", description = "Get an user wordcloud", guild=discord.Object(id=1081651254226325658))	
async def wordcloud(interaction, member: discord.Member):
    await interaction.response.defer()
    generateWordcloud(getFrequencyDictForText(f'{member}'), member)
    await interaction.followup.send(file=discord.File('graphs/wc.png'))

@bot.tree.command(name = "lovescore", description = "Get a lovescore between two users", guild=discord.Object(id=1081651254226325658))	
async def lovescore(interaction, member1: discord.Member, member2: discord.Member):
    await interaction.response.defer()
    calculateLovescore(member1, member2)
    await interaction.followup.send(file=discord.File('graphs/lovescore.png'))

#cogs are needed to do background tasks, like our caching
@bot.event
async def on_ready():
    await bot.add_cog(background_caching(bot))
    await bot.tree.sync(guild=discord.Object(id=1081651254226325658))
    print("Ready!")

#legacy/debug Command to test if bot really is running
@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    if message.content.startswith('$hello'):
        await message.channel.send('Hello!')

#run the bot using an external token (not shared on git but saved in a local file)
bot.run(token)