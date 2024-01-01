import settings
import discord
from discord.ext import commands


def run():
    intents = discord.Intents.default()
    intents.message_content = True
    
    bot = commands.Bot(command_prefix="/", intents=intents)

    @bot.event
    async def on_ready():
        print(bot.user)
        print(bot.user.id)
        print("-"*8)


    #/schedule
    @bot.command(brief="Collating available days for raid attendance", description="Bot sends a message into a location where command is called and tags @everyone, asking to react for available days to be scheduled for raids")
    async def schedule(ctx):
        print("Command /schedule has been called")
        await ctx.message.delete()

        emojis = settings.emojis
        msg = await ctx.send("@everyone, please react with your available days!")     
        for emoji in emojis:
            await msg.add_reaction(emoji)

    @bot.command(brief="Display overall schedule of all members who reacted", description="Bot sends an embed with all the members who reacted to the days showing when they're available and not.")
    async def gen(ctx):
        print("Command /gen has been called")
        await ctx.message.delete()

        async for message in ctx.channel.history(oldest_first=True):
            # print(message)
            if message.author.bot:
                # print(message.content)
                if message.content.startswith("@everyone"):
                    user_set, react_dict = await collate_table(message)
                    #start building the 2d array from react table using user_set
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
                    del conv[bot.user.name]

                    #init table
                    table = []

                    headers = settings.headers
                    table.append(headers)

                    for item in conv.items():
                        table.append([item[0]]+list(item[1]))
                    
                    import pandas as pd
                    df = pd.DataFrame(table[1:], columns = table[0])

                    for header in headers:
                        print(header, list(df[header]))
                    server_emojis = list(settings.emoji_dict.keys())
                    embed = discord.Embed(title = "Schedule")
                    embed.add_field(name = headers[0], value="\n\n".join(list(df[headers[0]])), inline=True)
                    embed.add_field(name = "\u1CBC".join(server_emojis), value="\n\n".join("\u1CBC".join(row[1:]) for row in table[1:]), inline=True)
                    await ctx.send(embed=embed)
                else:
                    pass
            else:
                pass


        #check if there is a schedule already called, if not, ignore and delete 
    async def collate_table(msg):
        emoji_dict = settings.emoji_dict
        react_dict = {}
        for reaction in msg.reactions:
            # print(reaction)
            reaction_str = str(reaction)
            async for user in reaction.users():
                # if user != bot.user:
                # print(user)
                if emoji_dict[reaction_str] not in react_dict:
                    react_dict[emoji_dict[reaction_str]] = [str(user.name)]
                else:
                    react_dict[emoji_dict[reaction_str]].append(str(user.name))
        # print(user_list)
        # print('-'*10)
        # Get total unique set of users who will be available for that reset
        total_users = []
        for val in react_dict.values():
            total_users += val
        user_set = set(total_users)
        # print(user_set, react_dict)
        return (user_set, react_dict)



    bot.run(settings.DISCORD_API_SECRET)

if __name__ == "__main__":
    run()