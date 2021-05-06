import discord
import time
import json
from threading import Thread
import sys
import asyncio
import os
from datetime import datetime

if not os.path.exists('users'):
    os.mkdir('users')
if not os.path.exists('messages'):
    os.mkdir('messages')


class DocBuilder:

    def sortUsers(users):
        sortedUsers = []
        oldUsers = users.copy()
        for i in range(len(users)):
            maxInterest = 0
            maxUser = None
            for user in oldUsers:
                if(user['interest'] >= maxInterest):
                    maxUser = user
                    maxInterest = user['interest']
            sortedUsers.append(maxUser)
            oldUsers.remove(maxUser)
        return sortedUsers
    def build(users):
        yield '# Discord User Documentation'
        rank = 0
        for user in users:
            rank += 1
            yield '## ' + str(user['name']) + ' (' + str(user['id']) + ')'
            yield '![' + user['name'] + '](' + user['image'] + ')'
            yield ''
            yield '### Informationen:'
            yield '* **Gesamte Onlinezeit:** ' + str(Util.dictValue(user, 'online_time')) + ' Minuten'
            yield '* **Beigetreten:** ' + Util.formatTime(user['joined'])
            if('offline_since' in user):
                yield '* **Zuletzt online:** ' + Util.formatTime(user['offline_since'])
            elif('online' in user and user['online']):
                yield '* **Zuletzt online:** ' + Util.formatTime(int(time.time() / 60))
            yield '* **Gesendete Nachrichten:** ' + str(user['actions']['sent_message'])
            yield '* **Gesendete GIFs:** ' + str(user['actions']['sent_gif'])
            yield '* **Gesendete Schimpfwörter:** ' + str(user['actions']['sent_badword'])
            yield '* **Gesendete Spiele:** ' + str(user['actions']['sent_game'])
            yield '* **Interest-Score:** ' + str(user['interest']) + ', Rang: ' + str(rank)
            if('left' in user):
                yield '* **Server verlassen:** (' + Util.formatTime(user['left']) + ')' 
            if('has_mobile' in user):
                yield '* **Hat Discord-Mobile**'
            if('activities' in user):
                yield '### Interessen:'
                if('listening' in user['activities']):
                    yield '#### Musik:'
                    maxSongCount = 0
                    maxArtist = None
                    for artist in user['activities']['listening']:
                        yield '* ' + artist
                        songCount = 0
                        for album in user['activities']['listening'][artist]:
                            yield '  * ' + album
                            for song in user['activities']['listening'][artist][album]:
                                yield '    * **' + song + '** (' + str(user['activities']['listening'][artist][album][song][1]) + 'x, Zuletzt: ' + Util.formatTime(user['activities']['listening'][artist][album][song][0]) + ')'
                                songCount+=1
                        if(songCount >= maxSongCount):
                            maxSongCount = songCount
                            maxArtist = artist
                    yield '* **Lieblingskünstler:** ' + maxArtist
                if('playing' in user['activities']):
                    yield '### Spiele:'
                    for game in user['activities']['playing']:
                        yield '* **' + game + '** (Zuletzt: ' + Util.formatTime(user['activities']['playing'][game]) + ')'
                if('custom' in user['activities']):
                    yield '### Sonstige:'
                    for custom in user['activities']['custom']:
                        yield '* **' + str(custom) + '** (Zuletzt: ' + Util.formatTime(user['activities']['custom'][custom]) + ')'
                for activity in user['activities']:
                    if(activity not in ['listening', 'playing', 'custom']):
                        yield '* Unbekannte Aktivitätskategorie: ' + activity
            if(len(user['messages']) > 0):
                yield '### Nachrichten:'
                for channel in user['messages']:
                    yield '* **' + channel + '**:'
                    for message in user['messages'][channel]:
                        yield '  * ' + message[0] + ' (' + Util.formatTime(message[1]) + ')'
            yield '<div style="page-break-after: always;"></div>'
            yield ''


class ControllerThread(Thread):

    def __init__(self):
        Thread.__init__(self)
        self.start()

    def processCmd(self, cmd, args):
        if(cmd == 'data'):
            if(args[0] == 'cached'):
                print("Cached users:", processor.users.getCachedCount())
        elif(cmd == 'stats'):
            if(args[0] == 'has-mobile'):
                print("Users with mobile phones:")
                count = 0
                for id in processor.users.users:
                    user = processor.users.users[id]
                    if('has_mobile' in user):
                        count += 1
                        print(user['name'])
                print("Total:", count)
        elif(cmd == 'user'):
            user = None
            for id in processor.users.users:
                if(id == int(args[0])):
                    user = processor.users.users[id]
            if(user != None):
                if(args[1] == 'data'):
                    print(json.dumps(user, indent=4))
            else:
                print("User nicht gefunden.")
        elif(cmd == 'build-doc'):
            print("Building doc...")
            with open('doc.md', 'w') as file:
                for line in DocBuilder.build(DocBuilder.sortUsers(list(processor.users.users.values()))):
                    file.write(line + '\n')
                file.flush()
            print("Done.")
                

    def run(self):
        try:
            while True:
                inp = input()
                args = inp.split(' ')
                self.processCmd(args[0], args[1:])
        except KeyboardInterrupt:
            pass


class UserData:
    def __init__(self):
        self.users = dict()

    def cacheAll(self, memberList):
        for member in memberList:
            self.getUserData(member)
            self.userChange(member, member)

    def getCachedCount(self):
        return len(self.users)

    def filePath(self, member):
        return 'users/' + str(member.id) + '.json'

    def loadUserData(self, user):
        if(os.path.exists(self.filePath(user))):
            with open(self.filePath(user), 'r') as file:
                return json.loads(file.read())
        else:
            data = {
                'id': user.id,
                'joined': int(time.time() / 60),
                'image': str(user.avatar_url),
                'name': str(user.name),
                'messages': {},
                'interest': 0,
                'actions': {
                    'sent_gif': 0,
                    'sent_game': 0,
                    'sent_message': 0,
                    'sent_badword': 0
                }
            }
            with open(self.filePath(user), 'w') as file:
                print("Created blank user data for", user.name)
                file.write(json.dumps(data))
                file.flush()
            return data

    def getUserDataById(self, id):
        return self.users[id]

    def getUserData(self, member):
        if(member.id not in self.users):
            self.users[member.id] = self.loadUserData(member)
        return self.users[member.id]

    def markUserLeft(self, member, save=True):
        data = self.getUserData(member)
        self.setOnline(member, False, save=False)
        data['left'] = int(time.time() / 60)
        data['online'] = False
        print("Marked left:", member.name)
        if(save):
            self.saveUserData(data)

    def saveUserData(self, data):
        with open('users/' + str(data['id']) + '.json', 'w') as file:
            file.write(json.dumps(data))
            file.flush()

    def getActionCount(self, member, action):
        data = self.getUserData(member)
        if(action in data['actions']):
            return data['actions'][action]
        else:
            data['actions'][action] = 0
            self.saveUserData(data)
            return 0

    def performedAction(self, member, action, save=True):
        data = self.getUserData(member)
        if(action in data['actions']):
            data['actions'][action] += 1
        else:
            data['actions'][action] = 1
        if(save):
            self.saveUserData(data)

    def setOnline(self, member, online, save=True):
        data = self.getUserData(member)
        if(online):
            data['online_since'] = int(time.time() / 60)
            data['online'] = True
        else:
            data['online'] = False
            if('online_since' in data):
                if('online_time' in data):
                    data['online_time'] += int(time.time() / 60) - \
                        data['online_since']
                else:
                    data['online_time'] = int(
                        time.time() / 60) - data['online_since']
            else:
                data['online_time'] = 0
            data['offline_since'] = int(time.time() / 60)
        if(save):
            self.saveUserData(data)

    def setHasMobile(self, member, save=True):
        data = self.getUserData(member)
        if('has_mobile' not in data):
            data['has_mobile'] = True
            if(save):
                self.saveUserData(data)
            return True
        else:
            return False

    def addMessage(self, member, message, save=True):
        data = self.getUserData(member)
        data['interest'] += 1
        if(message.channel.type is discord.ChannelType.private):
            if('privatemessage' not in data['messages']):
                data['messages']['privatemessage'] = []
            data['messages']['privatemessage'].append([
                message.content,
                int(time.time() / 60)
            ])
            print("Private Nachricht von", member.name, message.content)
        else:
            if(message.channel.name not in data['messages']):
                data['messages'][message.channel.name] = []
            data['messages'][message.channel.name].append([
                message.content,
                int(time.time() / 60)
            ])
        if(save):
            self.saveUserData(data)

    def addActivity(self, member, activity, save=True):
        changed = False
        if(activity != None):
            data = self.getUserData(member)
            if('activities' not in data):
                data['activities'] = {}
            activityType = str(activity.type)
            activityType = activityType[activityType.index('.')+1:]
            if(activityType not in data['activities']):
                data['activities'][activityType] = dict()
                data['interest'] += 5
            if(activityType == 'playing'):
                if(activity.name not in data['activities']['playing']):
                    data['activities']['playing'][activity.name] = 0
                    data['interest'] += 2
                data['activities']['playing'][activity.name] = int(
                    time.time() / 60)
            elif(activityType == 'listening'):
                songString = activity.artist + ': ' + \
                    activity.title + ' (' + activity.album + ')'
                found = False
                for artist in data['activities']['listening']:
                    if(artist == activity.artist):
                        for album in data['activities']['listening'][artist]:
                            if(album == activity.album):
                                for title in data['activities']['listening'][artist][album]:
                                    if(title == activity.title):
                                        found = True
                                        break
                if(not found):
                    if(activity.artist not in data['activities']['listening']):
                        data['activities']['listening'][activity.artist] = {}
                    if(activity.album not in data['activities']['listening'][activity.artist]):
                        data['activities']['listening'][activity.artist][activity.album] = {
                        }
                    if(activity.title not in data['activities']['listening'][activity.artist][activity.album]):
                        data['activities']['listening'][activity.artist][activity.album][activity.title] = [
                            0, 0]
                        data['interest'] += 0.1
                    data['activities']['listening'][activity.artist][activity.album][activity.title][0] = int(
                        time.time() / 60)
                    data['activities']['listening'][activity.artist][activity.album][activity.title][1] += 1
                    changed = True
            elif(activity.name != None):
                if(activity.name not in data['activities'][activityType]):
                    data['activities'][activityType][activity.name] = 0
                    data['interest'] += 3
                data['activities'][activityType][activity.name] = int(time.time() / 60)
            if(save and changed):
                self.saveUserData(data)
        return changed

    def userChange(self, before, after):
        changed = False
        if(str(before.status) != 'offline' and str(after.status) == 'offline'):
            self.setOnline(after, False, save=False)
            changed = True
        elif(str(before.status) == 'offline' and str(after.status) != 'offline'):
            self.setOnline(after, True, save=False)
            changed = True
        if(after.is_on_mobile()):
            if(self.setHasMobile(after, save=False)):
                changed = True
        if(after.activity != None):
            for activity in after.activities:
                if(self.addActivity(after, activity, save=False)):
                    changed = True
        if(changed):
            print("Updated", after.name)
            self.saveUserData(self.getUserData(after))


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
        try:
            for role in user.roles:
                if(role.name.startswith('Admin')):
                    return True
        except Exception:
            pass
        return False

    def getChannel(guild, name):
        for channel in guild.channels:
            if channel.name == name:
                return channel
        print("Warn: Channel not found:", name)

    def notifyInternal(msg):
        Util.getChannel(member.guild, 'intern').send(msg)

    def dictValue(dict, key, default="-"):
        if(key in dict):
            return dict[key]
        else:
            return default

    def formatTime(timeCode):
        millis = timeCode * 60
        time = datetime.fromtimestamp(millis)
        return time.strftime('%d.%m.%Y %H:%M') + ' Uhr'

    def boolString(bool):
        if bool:
            return 'Ja'
        else:
            return 'Nein'



class MessageProcessor(Thread):
    def __init__(self):
        Thread.__init__(self)
        self.badwords = []
        self.urls = []
        self.read()
        self.deleteMessages = []
        self.users = UserData()

    def run(self):
        print("Task-thread started.")
        while True:
            time.sleep(60)
            for msg in self.deleteMessages:
                if(time.time() - msg['timestamp'] >= msg['deleteafter']):
                    msg['msg'].delete()
                    print("Removed ", msg['msg'].content,
                          "after", msg['deleteafter'])

    def read(self):
        self.badwords = Util.readFileList('badwords_long.txt')
        self.urls = Util.readFileList('urls.txt')

    async def process(self, message):
        msg = message.content.lower()
        self.users.addMessage(message.author, message, save=False)
        modify = False
        if(not Util.isAdmin(message.author)):
            for badword in self.badwords:
                if badword.lower() in msg:
                    msg = msg.replace(
                        badword.lower(), Util.repstr('*', len(badword)))
                    await message.delete()
                    await message.author.send('Bitte vermeide Schimpfwörter. Deine Nachricht "' + msg + '" wurde entfernt.')
                    await Util.notifyInternal('Schimpfwort "' + message.content + '" von ' + message.author.name + ' wurde entfernt.')
                    print("Schimpfwort von", message.author.name,
                          "entfernt:", message.content)
                    self.users.performedAction(
                        message.author, 'sent_badword', save=False)
                    return
            if(Util.isUrl(msg) and message.channel.name != 'media'):
                urlValid = False
                for url in self.urls:
                    if(url in msg):
                        urlValid = True
                        break
                if(not urlValid):
                    await message.delete()
                    await message.author.send('Bitte vermeide Links zu fremden Inhalten.')
                    print("Link von", message.author.name,
                          "entfernt:", message.content)
                    return
                elif('stadtlandfluss.cool' in msg):
                    print("StadtLandFluss Link von", message.author.name,
                          "zur Löschung markiert:", message.content)
                    if(self.users.getActionCount(message.author, 'sent_game') <= 0):
                        await message.author.send('Hey, hier ein kleiner Hinweis: Um den Chat übersichtlich zu halten werden Links zu StadtLandFluss-Spielen nach einer Stunde automatisch gelöscht. :)')
                    self.users.performedAction(
                        message.author, 'sent_game', save=False)
                    await asyncio.sleep(60 * 60)
                    await message.delete()
                elif('tenor.com' in msg):
                    print("Gif von", message.author.name,
                          "zur Löschung markiert:", message.content)
                    if(self.users.getActionCount(message.author, 'sent_gif') <= 0):
                        await message.author.send('Hey, hier ein kleiner Hinweis: Um den Chat übersichtlich zu halten werden GIFs nach einer Stunde automatisch gelöscht. :)')
                    self.users.performedAction(
                        message.author, 'sent_gif', save=False)
                    await asyncio.sleep(60 * 60)
                    await message.delete()
        else:
            if(msg.startswith('!asmod')):
                newMessage = message.content[6:].strip()
                await message.delete()
                await message.channel.send(newMessage)
        self.users.performedAction(message.author, 'sent_message')


processor = MessageProcessor()
intents = discord.Intents().all()
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
        print("Saving data...")
        await dumpUserData()
    if('cache-all' in sys.argv):
        print("Caching all users...")
        for guild in client.guilds:
            processor.users.cacheAll(await guild.fetch_members().flatten())
        print("Done.")
    if('message' in sys.argv):
        with open('message.txt', 'r') as file:
            await Util.getChannel(client.guilds[0], 'media').send(file.read())


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
    if(message.channel.type == discord.ChannelType.private):
        await message.author.send('Um dir zu antworten bin ich leider noch nicht kompetent genug. Vielleicht 2030, wenn ich mit meinen Roboterfreunden die Weltherrschaft übernehme. Bis dahin musst du dich leider noch an das menschliche Team wenden ;)')


@client.event
async def on_member_join(member):
    print(member.name, "joined.", member.id)
    if(member.name != 'dtr4746' and member.guild.member_count % 5 == 0):
        await Util.getChannel(member.guild, 'intern').send('Beigetreten: ' + member.name + ' (' + str(member.guild.member_count) + ')')
    if(member.guild.member_count % 100 == 0):
        await Util.getChannel(member.guild, 'allgemein').send('@' + member.name + ' ist das ' + str(member.guild.member_count) + '. Mitglied! Willkommen. :)')
    print("Total", member.guild.member_count)
    processor.users.getUserData(member)


@client.event
async def on_member_remove(member):
    if(member.name != 'dtr4746' and member.guild.member_count % 5 == 0):
        await Util.getChannel(member.guild, 'intern').send('Verlassen: ' + member.name + ' (' + str(member.guild.member_count) + ')')
    processor.users.markUserLeft(member)
    print(member.name, "left.")


@client.event
async def on_member_update(before, after):
    processor.users.userChange(before, after)


ControllerThread()
client.run('xxxxxxx')
