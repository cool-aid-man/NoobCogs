import discord

from typing import Union

def is_have_avatar(thing: Union[discord.Member, discord.Guild] = None):
    if not thing:
        return ""
    if isinstance(thing, discord.Member):
        try:
            return thing.avatar.url
        except AttributeError:
            return thing.display_avatar.url
    if isinstance(thing, discord.Guild):
        try:
            return thing.icon.url
        except AttributeError:
            return ""