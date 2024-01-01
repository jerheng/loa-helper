import settings
import discord
from discord.ext import commands
from datetime import datetime
import pandas as pd


def run():
    intents = discord.Intents.default()
    intents.message_content = True

    bot = commands.Bot(command_prefix="/", intents=intents)

    @bot.event
    async def on_ready():
        print(bot.user)
        print(bot.user.id)
        print("-" * 8)

    # /schedule
    @bot.command(
        brief="Collating available days for raid attendance",
        description="Bot sends a message into a location where command is called and tags @everyone, asking to react for available days to be scheduled for raids",
    )
    async def schedule(ctx):
        print(
            f"Command /schedule has been called by {ctx.message.author}({ctx.message.author.id}) in {ctx.guild.name}({ctx.guild.id}), channel {ctx.channel}({ctx.channel.id}) at {datetime.now()}"
        )
        await ctx.message.delete()

        emojis = settings.emojis
        msg = await ctx.send("@everyone, please react with your available days!")
        for emoji in emojis:
            await msg.add_reaction(emoji)

    @bot.command(
        brief="Display overall schedule of all members who reacted",
        description="Bot sends an embed with all the members who reacted to the days showing when they're available and not.",
    )
    async def gen(ctx):
        print(
            f"Command /gen has been called by {ctx.message.author}({ctx.message.author.id}) in {ctx.guild.name}({ctx.guild.id}), channel {ctx.channel}({ctx.channel.id}) at {datetime.now()}"
        )
        await ctx.message.delete()

        flag = False  # Flag to keep track of whether the message has been found.

        # Set oldest_first = False so that we only keep track of the latest schedule collated
        async for message in ctx.channel.history(oldest_first=False):
            # print(message)
            if message.author.bot:
                # print(message.content)
                if message.content.startswith(
                    "@everyone, please react with your available days!"
                ):
                    flag = True  # Latest schedule message has been found

                    user_set, react_dict = await collate_table(message)

                    # Convert react_dict into a user that converts the reactions into green squares and non-reactions into red-squares
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
                    # initialize table
                    table = []
                    headers = settings.headers
                    table.append(headers)
                    for item in conv.items():
                        table.append([item[0]] + list(item[1]))

                    # convert into dataframe to easily pickup column data.
                    df = pd.DataFrame(table[1:], columns=table[0])

                    for header in headers:
                        print(header, list(df[header]))

                    server_emojis = list(react_dict.keys())

                    embed = discord.Embed(title="Schedule")
                    embed.add_field(
                        name=headers[0],
                        value="\n\n".join(list(df[headers[0]])),
                        inline=True,
                    )
                    embed.add_field(
                        name="\u1CBC".join(server_emojis),
                        value="\n\n".join("\u1CBC".join(row[1:]) for row in table[1:]),
                        inline=True,
                    )
                    await ctx.send(embed=embed)
                else:
                    pass  # Nothing should happen here
            else:
                pass  # Nothing should happen here
            if (
                flag == True
            ):  # Latest message containing schedule has been found, break from the loop.
                break

    "Helper function to collect reactions from a prior schedule message."

    async def collate_table(msg):
        # There is an edge case that may cause a bug where if the bot's reactions are removed, it will not be able to run due to dimensionality failure
        react_dict = {}
        for reaction in msg.reactions:
            reaction_str = str(reaction)
            if reaction_str in settings.emojis:
                async for user in reaction.users():
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

    bot.run(settings.DISCORD_API_SECRET)


if __name__ == "__main__":
    run()
