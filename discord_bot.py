import discord
import time
import platform
import discord.channel
import datetime
import requests
import sqlite3


from urllib.parse import parse_qs, urlparse
from discord.ext import commands, tasks
from discord.ext.commands import bot
from colorama import Back, Fore, Style
from sentiment_analyzer import sample_analyze_sentiment
from utils import token_py



intents = discord.Intents().all()
client = commands.Bot(description="Bot", command_prefix='>>', intents=intents)

def create_db_tables(conn):
    if conn is not None:
        c = conn.cursor()
        c.execute("""CREATE TABLE IF NOT EXISTS messages ( 
                                    channel_id text NOT NULL, 
                                    sender_id text NOT NULL, 
                                    name text NOT NULL,
                                    sentiment text NOT NULL,
                                    ts text NOT NULL
                                );""")
    else:
        print("Error! cannot create the database connection.")

    return c

conn = sqlite3.connect('database.db', check_same_thread=False)

c = create_db_tables(conn)


@client.event
async def on_ready():
    prfx = (Back.BLACK + Fore.GREEN + time.strftime("%H:%M:%S UTC", time.localtime()) + Back.RESET + Fore.WHITE + Style.BRIGHT)
    print(prfx + " Logged in as " + Fore.YELLOW + client.user.name)
    print(prfx + " Bot ID " + Fore.YELLOW + str(client.user.id))
    print(prfx + " Discord Version " + Fore.YELLOW + discord.__version__)
    print(prfx + " Python Version " + Fore.YELLOW + str(platform.python_version()))
    synced = await client.tree.sync()
    print(prfx + " Slash CMDs Synced " + Fore.YELLOW + str(len(synced)) + " Commands")
    await client.change_presence(activity=discord.Activity(type=discord.ActivityType.listening, name="Slow Office Music"))
    print("Ben hazirim!")
    

@client.event
async def on_member_join(member:discord.Member):
    channel = discord.utils.get(member.guild.text_channels, name="welcome")
    await channel.send(f"<@{member.id}> has joined us. Welcome!")

    
@client.event
async def on_member_remove(member:discord.Member):
    channel = discord.utils.get(member.guild.text_channels, name="goodbye")
    await channel.send(f"<@{member.id}> has left us :(")


@client.tree.command(name="help", description="List of all commands and descriptions")
async def help(interaction: discord.Interaction):
    embed = discord.Embed(title="Commands", description="""Here are all the commands which are being used with the 
                                                            forward slash '/'""", color=discord.Color.green())

    embed.add_field(name = "help", value="Lists all the commands", inline=False)
    embed.add_field(name = "clear", value="Purges the ammount of messages given as an argument", inline=False)
    embed.add_field(name = "userinfo", value="""Retrieves the information of the given user (github information 
                                                can be passed to be seen too""", inline=False)

    embed.add_field(name = "message", value="Sends a Discord Message to the given user", inline=False)
    embed.add_field(name = "dm", value="Creates a DM with the bot which the user can ask for help", inline=False)   
    embed.add_field(name = "sentiment", value="Retrieves the sentiment analysis of a certain given message", inline=False)
    embed.add_field(name = "commits", value="Retrieves the given user's commit count on a given repository", inline=False)
    embed.add_field(name = "dbget", value="""Retrieves the database of entered messages in a chat with the respective 
                                            Channel ID, User ID, message content and the messages sentimental analysis""", inline=False)

    await interaction.response.send_message(embed=embed)


@client.tree.command(name="clear", description="Clears messages")
async def clear(interaction: discord.Interaction, number:int):
    await interaction.response.send_message(content=f"Deleted {(number)} message(s)", ephemeral=True, delete_after=3)
    await interaction.channel.purge(limit=number)

@client.tree.command(name="sentiment", description="Analyzes the sentiment of the message")
async def sentiment(interaction: discord.Interaction, message:str):
    sentiment_response = sample_analyze_sentiment(message)
    await interaction.response.send_message(sentiment_response)

@client.tree.command(name="userinfo", description="Sends the information on a user")
async def userinfo(interaction: discord.Interaction, member:discord.Member=None, owner_name: str=" ", repo_name: str=" "):
    if member == None:
        member = interaction.user
    
    if(owner_name and repo_name != " "):
        roles = [role for role in member.roles]
        embed = discord.Embed(title="User info", description=f"Here's the user info on the user {member.mention}", color = discord.Color.green(), timestamp = datetime.datetime.utcnow())
        embed.set_thumbnail(url=member.avatar)
        embed.add_field(name = "ID", value = member.id)
        embed.add_field(name = "Name", value = f"{member.name}#{member.discriminator}")
        embed.add_field(name = "Nickname", value = member.display_name)
        embed.add_field(name = "Status", value = member.status)
        embed.add_field(name = "Created At", value = member.created_at.strftime("%a, %B %#d, %Y, %I:%M %p "))
        embed.add_field(name = "Joined At", value = member.joined_at.strftime("%a, %B %#d, %Y, %I:%M %p "))
        embed.add_field(name = f"Roles ({len(roles)})", value = " ".join([role.mention for role in roles]))
        embed.add_field(name = "Top Role", value = member.top_role.mention)
        embed.add_field(name = "Messages", value = "0")
        embed.add_field(name = "Bot?", value = member.bot)
        embed.add_field(name = "Commits", value= get_commits_count(owner_name, repo_name))
    else:
        roles = [role for role in member.roles]
        embed = discord.Embed(title="User info", description=f"Here's the user info on the user {member.mention}", color = discord.Color.green(), timestamp = datetime.datetime.utcnow())
        embed.set_thumbnail(url=member.avatar)
        embed.add_field(name = "ID", value = member.id)
        embed.add_field(name = "Name", value = f"{member.name}#{member.discriminator}")
        embed.add_field(name = "Nickname", value = member.display_name)
        embed.add_field(name = "Status", value = member.status)
        embed.add_field(name = "Created At", value = member.created_at.strftime("%a, %B %#d, %Y, %I:%M %p "))
        embed.add_field(name = "Joined At", value = member.joined_at.strftime("%a, %B %#d, %Y, %I:%M %p "))
        embed.add_field(name = f"Roles ({len(roles)})", value = " ".join([role.mention for role in roles]))
        embed.add_field(name = "Top Role", value = member.top_role.mention)
        embed.add_field(name = "Messages", value = "0")
        embed.add_field(name = "Bot?", value = member.bot)
    
    await interaction.response.send_message(embed=embed)


@client.tree.command(name="message", description="Send DM to a user")
async def message(interaction: discord.Interaction ,user: discord.Member, message: str):
    await interaction.response.send_message("Your message to the user has been sent", ephemeral=True, delete_after=3)
    await user.send(message)


@client.tree.command(name="helpme", description="Help me with the bot")
async def helpme(interaction: discord.Interaction):
    await interaction.response.send_message("Please check your DM for help", ephemeral=True, delete_after=5)
    await interaction.user.send("Reply to this message to seek further help from our admins")

    

@client.tree.command(name="commits", description="Gets the number of commit")
async def commits(interaction: discord.Interaction, owner_name1: str, repo_name1: str):
    commit_count = get_commits_count(owner_name1, repo_name1)
    await interaction.response.send_message("The total number of commits is: {}".format(commit_count))


def get_commits_count(owner_name: str, repo_name: str) -> int:
    url = f"https://api.github.com/repos/{owner_name}/{repo_name}/commits?per_page=1"
    r = requests.get(url)
    links = r.links
    rel_last_link_url = urlparse(links["last"]["url"])
    rel_last_link_url_args = parse_qs(rel_last_link_url.query)
    rel_last_link_url_page_arg = rel_last_link_url_args["page"][0]
    commits_count = int(rel_last_link_url_page_arg)
    return commits_count


@client.event
async def on_message(message: discord.Message):
    channelIDsToListen = [ 803386846905761836 ]
    if message.channel.id in channelIDsToListen and message.author.bot is False:
        message_tostring = f'{message.content}'
        sentiment_response = sample_analyze_sentiment(message_tostring)
        message_author = "<@"+str(message.author.id)+">"
        time_message = str(time.strftime("%H:%M:%S UTC", time.localtime()))
        channel_message = "<#"+str(message.channel.id)+">"

        c.execute("""INSERT INTO messages(channel_id, sender_id, name, sentiment, ts) 
               VALUES (?,?,?,?,?);""", (channel_message, message_author, message.content, str(sentiment_response), time_message))
        c.execute("COMMIT")

    if message.author == client.user:
        return
    
    if message.guild is None and not message.author.bot:
        channel2 = client.get_guild(803386846905761833).get_channel(1063721359198392342)
        await channel2.send(f"{message.author} replied: '{message.content}' at " + time.strftime("%H:%M:%S UTC", time.localtime()))


@client.tree.command(name="dbget")
async def dbget(interaction: discord.Interaction):
    c.execute("SELECT * FROM messages")
    rows = c.fetchall()
    string = ""
    for i in rows:
        string_new = convertTuple(i)
        string = string + string_new + "\n"

    await interaction.response.send_message(string, ephemeral=True)


def convertTuple(tup):
    str = ''
    for item in tup:
        str = str + item + " | "
    return str

client.run(token_py)
