import amari
import discord
import noobutils as nu
import random

from redbot.core.bot import app_commands, commands, Red
from redbot.core.utils import chat_formatting as cf

from typing import List, Literal, Optional

from .converters import ModifiedFuzzyRole


DEFAULT_GLOBAL = {"tick_emoji": None}


class NoobTools(nu.Cog):
    """
    NoobInDahause's personal tools.

    Too lazy to think of a description, feel free to make a pr on my repo to change this.
    """

    def __init__(self, bot: Red, *args, **kwargs):
        super().__init__(
            bot=bot,
            cog_name=self.__class__.__name__,
            version="1.2.0",
            authors=["NoobInDaHause"],
            use_config=True,
            force_registration=True,
            *args,
            **kwargs
        )
        self.config.register_global(**DEFAULT_GLOBAL)

    async def red_delete_data_for_user(
        self,
        *,
        requester: Literal["discord_deleted_user", "owner", "user", "user_strict"],
        user_id: int,
    ):
        """
        This cog does not store any end user data whatsoever.
        """
        return await super().red_delete_data_for_user(
            requester=requester, user_id=user_id
        )

    async def cog_load(self) -> None:
        if t := await self.config.tick_emoji():
            commands.context.TICK = t

    async def cog_unload(self) -> None:
        commands.context.TICK = "✅"

    @commands.hybrid_command(name="amarilevel", aliases=["alvl", "alevel", "amari"])
    @commands.guild_only()
    @commands.cooldown(1, 5, commands.BucketType.user)
    @commands.bot_has_permissions(embed_links=True)
    @app_commands.guild_only()
    @app_commands.describe(member="The member that you want to level check.")
    async def amarilevel(
        self, context: commands.Context, member: discord.Member = None
    ):
        """
        Check your or someone else's amari level.

        Requires amari api token.
        If you are the bot owner apply for one in their support server [here](https://discord.gg/kqefESMzQj).
        If you already have an amari api token set it with:
        `[p]set api amari auth,<your_api_key>`
        """
        api_dict: dict = await self.bot.get_shared_api_tokens("amari")

        if not api_dict:
            return await context.send(
                content="No amari api token found. Ask the bot owner to set one."
            )

        token = api_dict.get("auth")
        member = member or context.author

        if member.bot:
            return await context.send(content="Bots do not have amari levels.")

        async with context.typing():
            try:
                _amari = amari.AmariClient(token)
                lb = await _amari.fetch_full_leaderboard(context.guild.id)
                memb = await _amari.fetch_user(context.guild.id, member.id)
                rank = lb.get_user(member.id)
                embed = discord.Embed(
                    title="Amari Rank",
                    description=(
                        f"- **Rank**: {cf.humanize_number(rank.position + 1)}\n"
                        f"- **Level**: {cf.humanize_number(memb.level)}\n"
                        f"- **EXP**: {cf.humanize_number(memb.exp)}\n"
                        f"- **Weekly EXP**: {cf.humanize_number(memb.weeklyexp)}"
                    ),
                    colour=member.colour,
                    timestamp=discord.utils.utcnow(),
                )
                embed.set_thumbnail(url=nu.is_have_avatar(member))
                embed.set_footer(text=member, icon_url=nu.is_have_avatar(context.guild))
                await context.send(embed=embed)
            except amari.InvalidToken:
                await context.send(
                    content="The amari api token is invalid please report this to the bot owner."
                )
            except amari.NotFound:
                await context.send(content="This guild has no amari data..")
            except amari.HTTPException:
                await context.send(
                    content="Amari API took too long to respond. Perhaps it is down check back later."
                )
            except Exception as e:
                self.log.exception(str(e), exc_info=e)
                await context.send(
                    content="An error has occurred.\nPlease report this to the bot owner.\n"
                    f"Here is the traceback: {cf.box(e, 'py')}"
                )
            await _amari.close()

    @commands.hybrid_command(name="reach")
    @commands.guild_only()
    @commands.cooldown(1, 10, commands.BucketType.user)
    @commands.bot_has_permissions(embed_links=True, manage_roles=True)
    @app_commands.guild_only()
    @app_commands.describe(
        channel="The channel that you want to reach roles.",
        roles="The roles that you want to reach. (separate roles with spaces)",
    )
    async def reach(
        self,
        context: commands.Context,
        channel: Optional[discord.TextChannel] = None,
        roles: commands.Greedy[ModifiedFuzzyRole] = None,
    ):  # sourcery skip: low-code-quality
        """
        Reach channel and see how many members who can view the channel.

        Separate roles with a space if multiple. (ID's accepted)
        Role searching may or may not be 100% accurate.
        You can pass `everyone` or `here` to check `@everyone` or `@here` reach.
        """
        if not roles:
            return await context.send_help()

        channel = channel or context.channel
        roles = list(dict.fromkeys(roles).keys())

        if len(roles) > 15:
            return await context.send(
                "Easy there you can only reach up to 15 roles at a time."
            )

        final_members: List[discord.Member] = []
        final_str: List[str] = []
        all_members = []

        async with context.typing():
            for role in roles:
                if isinstance(role, str):
                    if role.lower() == "everyone":
                        everyone = [
                            member
                            for member in context.guild.members
                            if not member.bot
                            and channel.permissions_for(member).view_channel
                        ]
                        final_members.extend(everyone)
                        am = [m for m in context.guild.members if not m.bot]
                        mems = len(am)
                        ev = len(everyone)
                        all_members.extend(am)
                        try:
                            div = round((ev / mems * 100), 2)
                        except ZeroDivisionError:
                            div = 0
                        final_str.append(
                            f"` #{len(final_str) + 1} ` @{role}: {cf.humanize_number(ev)} out of "
                            f"{cf.humanize_number(mems)} members - **{div}%**"
                        )
                    elif role.lower() == "here":
                        here = [
                            member
                            for member in context.guild.members
                            if not member.bot
                            and channel.permissions_for(member).view_channel
                            and member.status != discord.Status.offline
                        ]
                        final_members.extend(here)
                        am = [
                            m
                            for m in context.guild.members
                            if not m.bot and m.status != discord.Status.offline
                        ]
                        mems = len(am)
                        her = len(here)
                        all_members.extend(am)
                        try:
                            div = round((her / mems * 100), 2)
                        except ZeroDivisionError:
                            div = 0
                        final_str.append(
                            f"` #{len(final_str) + 1} ` @{role}: {cf.humanize_number(her)} out of "
                            f"{cf.humanize_number(mems)} members - **{div}%**"
                        )
                else:
                    reached = [
                        member
                        for member in role.members
                        if not member.bot
                        and channel.permissions_for(member).view_channel
                    ]
                    final_members.extend(reached)
                    am = [i for i in role.members if not i.bot]
                    mems = len(am)
                    rol = len(reached)
                    all_members.extend(am)
                    try:
                        div = round((rol / mems * 100), 2)
                    except ZeroDivisionError:
                        div = 0
                    final_str.append(
                        f"` #{len(final_str) + 1} ` {role.mention} (`{role.id}`): {cf.humanize_number(rol)}"
                        f" out of {cf.humanize_number(mems)} members - **{div}%**"
                    )

            overall_reach = len(list(set(final_members)))
            overall_members = len(list(set(all_members)))
            try:
                divov = overall_reach / overall_members * 100
            except ZeroDivisionError:
                divov = 0
            okay = "\n".join(final_str)
            embed = (
                discord.Embed(
                    title="Role Reach",
                    description=f"Channel: {channel.mention} (`{channel.id}`)\n\n{okay}\n",
                    colour=await context.embed_colour(),
                    timestamp=discord.utils.utcnow(),
                )
                .set_footer(
                    text=context.guild.name, icon_url=nu.is_have_avatar(context.guild)
                )
                .add_field(
                    name="__**Overall Results:**__",
                    value=(
                        f"> ` - ` Overall Reach: **{cf.humanize_number(overall_reach)}**\n"
                        f"> ` - ` Overall Members: **{cf.humanize_number(overall_members)}**\n"
                        f"> ` - ` Overall Percentage: **{round(divov, 2)}%**"
                    ),
                    inline=False,
                )
            )

            await context.send(embed=embed)

    @commands.hybrid_command(name="membercount", aliases=["mcount"])
    @commands.bot_has_permissions(embed_links=True)
    @commands.guild_only()
    @app_commands.guild_only()
    async def membercount(self, context: commands.Context):
        """
        See the total members in this guild.
        """
        all_members = [mem for mem in context.guild.members if not mem.bot]
        all_bots = [mbot for mbot in context.guild.members if mbot.bot]
        embed = discord.Embed(
            title=f"Membercount for [{context.guild.name}]",
            timestamp=discord.utils.utcnow(),
            colour=await context.embed_colour(),
        )
        embed.set_thumbnail(url=nu.is_have_avatar(context.guild))
        embed.add_field(
            name="Members:", value=cf.humanize_number(len(all_members)), inline=True
        )
        embed.add_field(
            name="Bots:", value=cf.humanize_number(len(all_bots)), inline=True
        )
        embed.add_field(
            name="All:",
            value=cf.humanize_number(context.guild.member_count),
            inline=True,
        )
        await context.send(embed=embed)

    @commands.command(name="randomcolour", aliases=["randomcolor"])
    @commands.bot_has_permissions(embed_links=True)
    async def randomcolour(self, context: commands.Context):
        """
        Generate a random colour.
        """
        colour = discord.Colour(random.randint(0, 0xFFFFFF))
        url = f"https://singlecolorimage.com/get/{str(colour)[1:]}/400x100"
        embed = discord.Embed(
            title="Here is your random colour.",
            description=f"`Hex:` {str(colour)}\n`Value:` {colour.value}\n`RGB:` {colour.to_rgb()}",
            colour=colour,
            timestamp=discord.utils.utcnow(),
        )
        embed.set_image(url=url)
        await context.send(embed=embed)

    @commands.command(name="changetickemoji")
    @commands.is_owner()
    async def changetickemoji(
        self, context: commands.Context, emoji: nu.NoobEmojiConverter = None
    ):
        """
        Change [botname]'s tick emoji.

        Leave emoji parameter as blank to check current tick emoji.
        """
        if not emoji:
            tick = commands.context.TICK
            await context.tick()
            return await context.send(
                content=f"My current tick emoji is set to: {tick}"
            )
        commands.context.TICK = str(emoji)
        if str(emoji) != "✅":
            await self.config.tick_emoji.set(str(emoji))
        else:
            await self.config.tick_emoji.clear()
        await context.tick()
        await context.send(content=f"Successfully set {str(emoji)} as my tick emoji.")

