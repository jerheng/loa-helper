import settings
import discord
import typing   
from discord.ext import commands
from discord import app_commands, Interaction
from datetime import datetime
import pandas as pd
from pymongo import MongoClient

# Replace the following with your MongoDB connection string
client = MongoClient(settings.mongo_uri) # Importing mongo_uri from settings, hidden file in dotenv

# Select the database and collection
db = mongo_client["loa-helper"]
collection = db["events"]

def run():
    intents = discord.Intents.default()
    intents.message_content = True
    intents.members = True

    bot = commands.Bot(command_prefix="/", intents=intents)

    @bot.event
    async def on_ready():
        print("-" * 15)
        print(f"Bot is ready!")
        print(bot.user, bot.user.id)
        print(f"Bot is in {len(list(bot.guilds))} guilds!: {list(bot.guilds)}")
        print("-" * 15)

    # /schedule
@bot.command(
    brief="Collating available days for raid attendance",
    description="Bot sends a message into a location where command is called and tags @everyone, asking to react for available days to be scheduled for raids.\nThis is generally recommended to be run in threads to not clog chats and ping people in excess since it uses @everyone.",
)
async def schedule(ctx, arg="@everyone"):
    print(
        f"Command /schedule has been called by {ctx.message.author}({ctx.message.author.id}) in {ctx.guild.name}({ctx.guild.id}), channel {ctx.channel}({ctx.channel.id}) at {datetime.now()}"
    )

    # Check if the argument provided is a valid role, otherwise tag everyone
    roles = await get_roles(ctx)
    if arg.startswith("<@&") and arg.endswith(">"):
        arg_id = arg[3:-1].strip()
        for role in roles:
            if str(role.id) == arg_id:
                break
    else:
        arg = "@everyone"
    await ctx.message.delete()

    # Check if arg is a valid prefix for a role, otherwise make sure it is set to everyone. It has to be a valid role.
    emojis = settings.emojis
    msg = await ctx.send(f"{arg}, please react with your available days!")

    # Update prior scheduling messages to expired
    collection.update_many(
        {"channel_id": ctx.channel.id, "status": "Scheduling"},
        {"$set": {"status": "Expired"}}
    )
    print(f"Prior schedules in channel {ctx.channel.id} set to 'Expired'.")

    # Save new message details to MongoDB
    message_data = {
        "message_id": msg.id,
        "content": msg.content,
        "channel_id": msg.channel.id,
        "channel_name": msg.channel.name,
        "guild_id": msg.guild.id,
        "guild_name": msg.guild.name,
        "author_id": ctx.message.author.id,
        "author_name": ctx.message.author.name,
        "command_user_id": ctx.author.id,
        "command_user_name": ctx.author.name,
        "arguments": arg,
        "timestamp": msg.created_at.isoformat(),
        "status": "Scheduling"  # Possible statuses as ["Scheduling", "Expired"]
    }
    collection.insert_one(message_data)
    print(f"New message saved to MongoDB with ID: {msg.id}")

    for emoji in emojis:
        await msg.add_reaction(emoji)
    await msg.pin(reason=None)

    print(f"Role mentioned is: {arg}")
    # Shadow ping members to add them to the thread
    await add_to_thread(ctx, arg)
    
    @schedule.autocomplete("role")
    async def schedule_autocomplete(ctx, interaction: discord.Interaction, current: str) -> typing.List[app_commands.choice[str]]:
        data = []
        for role in await get_roles(ctx):
            data.append(app_commands.Choice(name=role, value=role))
        return data

    # /gen
    @bot.command(
        brief="Display overall schedule of all members who reacted",
        description="Bot sends an embed with all the members who reacted to the days showing when they're available and not.\nThis command also only generates the latest called schedule in the channel.",
    )
    async def gen(ctx):
        print(
            f"Command /gen has been called by {ctx.message.author}({ctx.message.author.id}) in {ctx.guild.name}({ctx.guild.id}), channel {ctx.channel}({ctx.channel.id}) at {datetime.now()}"
        )

        # Delete command initialization message
        await ctx.message.delete()

        # Get all guild roles
        roles = await get_roles(ctx)
        roles_dict = {}
        rev_roles_dict = {}
        for role in roles:
            roles_dict[str(role.id)] = str(role.name)
            rev_roles_dict[str(role.name)] = str(role.id)

        flag = False  # Flag to keep track of whether the message has been found.

        latest_request = collection.find_one(
            {"channel_id":ctx.channel.id},
            sort = [("timestamp, -1")]
        ) # Status here is irreelvant

        if latest_request:
            print(f"Latest schedule request found with message ID: {latest_request['message_id']}")
            try:
                message = await ctx.channel.fetch_mesasge(latest_request["message_id"])
            except discord.NotFound:
                print("Message not found in the channel")
                return
            mentioned_role = str(latest_request["content"]).strip().split()[0][:-1]
            role_members = await get_members(ctx, mentioned_role)
            
            user_set, react_dict = await collate_table(message)

            #diff check for user_set and role_members
            remind_members = []
            for member in role_members.keys():
                if member not in user_set:
                    if role_members[member] != str(bot.user.id):
                        remind_members.append(role_members[member])
            print(f"Reminding the following members: {remind_members}")

            # Convert react_dict into a user that converts the reactions into green squares and non-reactions into red-squares
            conv = conv_dict(user_set, react_dict)

            #Initialize table
            table = []
            headers = settings.headers
            table.append(headers)
            for item in conv.items():
                table.append([item[0]] + list(item[1]))
    
            # Convert table into dataframe to easily pick up column data.
            df = pd.DataFrame(table[1:], columns=table[0])

            # Print for debugging
            for header in headers:
                print(header, list(df[header]))

            server_emojis = list(react_dict.keys())

            # Building embeds
            embed = discord.Embed(title=f"Schedule {message.jump_url}")

            embed.add_field(
                name=headers[0],
                value="\n".join(list(df[headers[0]])),
                inline=True
            )

            embed.add_field(
                name="\u2800".join(server_emojis),
                value="\n".join("\u2800".join(row[1:]) for row in table[1:]),
                inline=True
            )

            if remind_members:
                remind_members = [f"<@{member}>" for member in remind_members]
                reminder = f"Reminding: {' '.join(remind_members)}"
            else:
                reminder = ""

            if reminder:
                await ctx.send(reminder, embed=embed)  # Reminder + embed
            else:
                await ctx.send(embed=embed)  # Embed only
        else:
            print("No active scheduling found in the channel.")
            await ctx.send("No active scheduling found in this channel.")
            
        # Set oldest_first = False so that we only keep track of the latest schedule collate
        # print("Searching messages now:")
        # async for message in ctx.channel.history(oldest_first=False, limit = 500):
        #     # print(message)
        #     # Delete command initialization message
        #     if message.author.bot:
        #         # print(message.content)
        #         if message.content.endswith("please react with your available days!"):
        #             print("Message found")
        #             mentioned_role = str(message.content).strip().split()[0][:-1]
        #             role_members = await get_members(ctx, mentioned_role)

        #             flag = True  # Latest schedule message has been found

        #             user_set, react_dict = await collate_table(message)

        #             # now do a diff check for user_set and role_members
        #             remind_members = [] # remind_members is initialized here to check if all members in user_set are in the pinged role, otherwise collect members who have yet to react.
        #             for member in role_members.keys():
        #                 if member not in user_set:
        #                     if role_members[member] != str(bot.user.id):
        #                         remind_members.append(role_members[member])
        #             print(f"Reminding the following members: {remind_members}")

        #             # Convert react_dict into a user that converts the reactions into green squares and non-reactions into red-squares
        #             conv = conv_dict(user_set, react_dict)

        #             # initialize table
        #             table = []
        #             headers = settings.headers
        #             table.append(headers)
        #             for item in conv.items():
        #                 table.append([item[0]] + list(item[1]))

        #             # Get count of users who reacted per emote
        #             # tmp = ["Total"] + [str(len(react_dict[key])) for key in react_dict.keys()]
        #             # table.append(tmp)

        #             print(table)

        #             # convert table into dataframe to easily pickup column data.
        #             df = pd.DataFrame(table[1:], columns=table[0])

        #             # print for debugging
        #             for header in headers:
        #                 print(header, list(df[header]))

        #             server_emojis = list(react_dict.keys())

        #             # building embeds
        #             embed = discord.Embed(title=f"Schedule {message.jump_url}")

        #             embed.add_field(
        #                 name=headers[0],
        #                 value="\n".join(list(df[headers[0]])),
        #                 inline=True
        #             )

        #             embed.add_field(
        #                 name="\u2800".join(server_emojis),
        #                 value="\n".join("\u2800".join(row[1:]) for row in table[1:]),
        #                 inline=True
        #             )

        #             if remind_members != []:
        #                 for i in range(len(remind_members)):
        #                     remind_members[i] = f"<@{remind_members[i]}>"
        #                 reminder = f"Reminding: {' '.join(remind_members)}"
        #             else:
        #                 reminder = ""

        #             if reminder == "":
        #                 await ctx.send(embed=embed) # no members to remind, embed only
        #             else:
        #                 # await ctx.send(reminder, embed=embed) # reminder + embed
        #                 await ctx.send(reminder, embed=embed)
        #         else:
        #             pass  # Nothing should happen here
        #     else:
        #         pass  # Nothing should happen here
        #     if (
        #         flag == True
        #     ):  # Latest message containing schedule has been found, break from the loop.
        #         break


    "Bunch of helper functions below.............."


    "Helper function to collect reactions from a prior schedule message."
    async def collate_table(msg):
        # There is an edge case that may cause a bug where if the bot's reactions are removed, it will not be able to run due to dimensionality failure
        user_ids = []
        react_dict = {}
        for reaction in msg.reactions:
            reaction_str = str(reaction)
            if reaction_str in settings.emojis:
                async for user in reaction.users():
                    if user.id not in user_ids:
                        user_ids.append(user.id)
                    if user == bot.user:
                        if reaction_str not in react_dict:
                            react_dict[reaction_str] = []
                    else:
                        if reaction_str not in react_dict:
                            react_dict[reaction_str] = [user.name]
                        else:
                            react_dict[reaction_str].append(user.name)
        total_users = []  # Get unique set of users who reacted
        for val in react_dict.values():
            total_users += val
        total_users = set(total_users)
        print(total_users, react_dict)
        return (total_users, react_dict)
        # react_dict should have the structure of {emoji_id1:[list of usernames], emoji_id2:[list of usernames]}

    "Helper function to get all members belonging to role in the mentioned channel"
    async def get_members(ctx, mentioned_role):
        roles = await get_roles(ctx)
        roles_dict = {}
        rev_roles_dict = {}
        for role in roles:
            roles_dict[str(role.id)] = str(role.name)
            rev_roles_dict[str(role.name)] = str(role.id)
        if mentioned_role == "@everyone":
            mentioned_role = rev_roles_dict[mentioned_role]
        else:
            mentioned_role = mentioned_role[3:-1]
        print(f"Getting members from role: {roles_dict[mentioned_role]}!")

        role_members = {}
        if roles_dict[mentioned_role] == "@everyone":
            for member in ctx.channel.parent.members:
                role_members[str(member.name)] = str(member.id)
        else:
            for role in roles:
                if str(role.id) == mentioned_role:
                    for member in role.members:
                        role_members[str(member.name)] = str(member.id)
        return role_members
    
    "Helper function to shadow ping all members mentioned in the role to the thread"
    async def add_to_thread(ctx, arg):
        role_members = await get_members(ctx, arg)
        remind_members = []
        for member in role_members.keys():
            if role_members[member] != str(bot.user.id):
                remind_members.append(f"<@{role_members[member]}>")
        print(f"Adding members to thread: {' '.join(remind_members)}")
        add_msg = f"Adding to thread: {' '.join(remind_members)}"
        await ctx.send(add_msg, delete_after=1)

    "Helper function to get a list of role objects in a guild"
    async def get_roles(ctx):
        # Has to be used before the context is deleted
        roles = list(ctx.guild.roles)
        # roles = {role.id:role.name for role in roles}
        return roles

    "Helper function to convert react_dict into {usernames:[red/green square]}"
    def conv_dict(user_set, react_dict):
        conv = {}
        for user in user_set:
            for key in react_dict.keys():
                if user not in conv:
                    if user not in react_dict[key]:
                        conv[user] = ["🟥"]
                    else:
                        conv[user] = ["🟩"]
                else:
                    if user not in react_dict[key]:
                        conv[user].append("🟥")
                    else:
                        conv[user].append("🟩")
        return conv

    bot.run(settings.DISCORD_API_SECRET)
    bot.on_disconnect(bot.connect(reconnect=True))

if __name__ == "__main__":
    run()