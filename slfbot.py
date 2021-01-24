import discord
import time
import json
from threading import Thread
import sys
import asyncio

class Util:
    domains = ['de', 'com', 'org', 'net']
    def readFileList(file):
        with open(file, 'r') as file:
            return file.read().split('\n')
    def repstr(string, length):
        return (string * length)[0:length]
    def isUrl(string):
        if('https://' in string or 'http://' in string):
            return True
        for domain in Util.domains:
            if(('.' + domain) in string):
                return True
    def isAdmin(user):
        for role in user.roles:
            if(role.name.startswith('Admin')):
               return True
        return False

class MessageProcessor(Thread):
    def __init__(self):
        Thread.__init__(self)
        self.badwords = []
        self.urls = []
        self.read()
        self.deleteMessages = []

    def run(self):
        print("Task-thread started.")
        while True:
            time.sleep(60)
            for msg in self.deleteMessages:
                if(time.time() - msg['timestamp'] >= msg['deleteafter']):
                    msg['msg'].delete()
                    print("Removed ", msg['msg'].content, "after", msg['deleteafter'])

    def read(self):
        self.badwords = Util.readFileList('badwords_long.txt')
        self.urls = Util.readFileList('urls.txt')

    async def process(self, message):
        msg = message.content.lower()
        modify = False
        if(not Util.isAdmin(message.author)):
            for badword in self.badwords:
                if badword.lower() in msg:
                    msg = msg.replace(badword.lower(), Util.repstr('*', len(badword)))
                    await message.delete()
                    await message.author.send('Bitte vermeide Schimpfwörter. Deine Nachricht "' + msg + '" wurde entfernt.')
                    print("Schimpfwort von", message.author.name, "entfernt:",message.content)
                    return
            if(Util.isUrl(msg)):
                urlValid = False
                for url in self.urls:
                    if(url in msg):
                        urlValid = True
                        break
                if(not urlValid):
                    await message.delete()
                    await message.author.send('Bitte vermeide Links zu fremden Inhalten.')
                    print("Link von", message.author.name, "entfernt:",message.content)
                    return
                elif('stadtlandfluss.cool' in msg or 'tenor.com' in msg):
                    print("Link von", message.author.name, "zur Löschung markiert:", message.content)
                    await asyncio.sleep(60 * 60)
                    await message.delete()
            return (modify, msg)

processor = MessageProcessor()
intents = discord.Intents.default()
intents.members = True
client = discord.Client(intents=intents)

async def dumpUserData():
    for server in client.guilds:
        with open(server.name + '.json', 'w') as file:
            members = await server.fetch_members().flatten()
            memberData = list()
            for member in members:
                memberData.append({
                    'name': member.name,
                    'image': str(member.avatar_url),
                    'activities': member.activities,
                    'joined': str(member.joined_at),
                    'id': member.id
                })
            file.write(json.dumps(memberData))
            file.flush()
@client.event
async def on_ready():
    print('We have logged in as {0.user}'.format(client))
    await client.change_presence(activity=discord.Activity(type=discord.ActivityType.listening, name="dem Chat"))
    if('save-data' in sys.argv):
        await dumpUserData()


def isInvalidLink(msg):
    msg = msg.lower()
    return msg.startswith('http') or msg.startswith('https') and not 'stadtlandfluss.cool' in msg

def getAnswerFor(msg):
    msg = msg.lower()
    if('wie' in msg and 'spieler' in msg and 'viele' in msg):
        return 'Die Spielerzahl an sich ist nicht begrenzt. Mit sehr vielen Spielern wird es höchstens irgendwann unübersichtlich.'
@client.event
async def on_message(message):
    if message.author == client.user:
        return
    await processor.process(message)

@client.event
async def on_member_join(member):
    print(member.name, "joined.")
    if(member.guild.member_count % 100 == 0):
        await member.guild.channels[0].send(member.name + ' ist das ' + member.guild.member_count + '. Mitglied! Wilkommen. :)')
    print(member.name, "Total", member.guild.member_count)

@client.event
async def on_member_remove(member):
    print(member.name, "left.")


client.run('Nzk4NTI2ODc3ODgyOTA4NzEy.X_2UGw.HmOEXhxkGhth2Gbyly2IKRvjj4o')
