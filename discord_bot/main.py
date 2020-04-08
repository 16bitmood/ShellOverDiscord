# basics
import os,sys,time
import csv,re
from dotenv import load_dotenv

import asyncio
import socketio
import discord

bot_users = []
def load_users():
    with open("../users.csv", newline='') as csvfile:
        reader = csv.DictReader(csvfile)  
        for row in reader:
            bot_users.append((row['USER_ID'],row['DISC_NAME']))
            # print(row['USER_ID'],row['DISC_NAME'])

def authorized(x):
    for user_id,disc_name in bot_users:
        if user_id == str(x):
            return True
    return False

# Docker Client Code
sio = socketio.AsyncClient()
running_shells = {}

@sio.event
async def connect():
    print("Connected to Docker Server!")

@sio.on('info')
async def info(data):
    print("[DOCKER]",data)

@sio.on('shell_output')
async def shell_output(data):
    given_id = int(data[0])
    if given_id in running_shells.keys():
        # TODO: remove ansi escape sequences
        to_send = "```\n" + data[1] + "\n```"
        await running_shells[given_id].send(to_send)
    print("[INFO] Sending shell output of ",given_id)

@sio.on('dispatch_discord_file')
async def dispatch_discord_file(data):
    print("[INFO] Sending file to discord")
    temp_file_name = "./temp/to_send"
    
    with open(temp_file_name,"wb") as f:
        f.write(data["dat"])

    file = discord.File(temp_file_name, filename=data["file_name"])
    await running_shells[int(data["user"])].send(file=file)
    
    os.remove(temp_file_name)

# Discord Bot Code
disc_bot = discord.Client()

@disc_bot.event
async def on_ready():
    print("Connected to discord!")
    print(disc_bot.guilds)

@disc_bot.event
async def on_message(msg):
    if msg.content[0] == ">":
        if authorized(msg.author.id):
            await sio.emit("shell",{'input':msg.content[1:],'id':msg.author.id})
            running_shells[msg.author.id] = msg.channel
        else:
            await msg.channel.send('no')
    elif msg.content[0] == "!":
        if authorized(msg.author.id):
            await sio.emit("shell_reset",{'id':msg.author.id})
            running_shells[msg.author.id] = None
        else:
            await msg.channel.send('no')
        return


async def main():
    # Load Discord bot config
    load_dotenv()
    TOKEN = os.getenv('DISCORD_TOKEN')
    load_users()
    print(bot_users)

    await asyncio.wait([\
    disc_bot.start(TOKEN), \
    sio.connect('http://127.0.0.1:5000')])

loop = asyncio.get_event_loop()
loop.run_until_complete(main())
loop.close()
