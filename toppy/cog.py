from __future__ import annotations

import importlib
from typing import TYPE_CHECKING, Union, Any
import inspect

lib = inspect.getouterframes(inspect.currentframe())[4].filename.split('\\')[-4]
discord = importlib.import_module(lib)
commands: Any = importlib.import_module(f'{lib}.ext.commands')

from . import Client, TopGGClient, DBLClient

if TYPE_CHECKING:
    import aiohttp
    

class NoTokenSet(Exception):
    def __init__(self):
        message = 'Create a bot var named "topgg_token" or "dbl_token" to use this cog'
        super().__init__(message)


class ToppyCog(commands.Cog):    
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.client: Union[Client, DBLClient, TopGGClient]
        
        if hasattr(bot, 'dbl_token') and hasattr(bot, 'topgg_token'):
            self.client = Client(bot, dbl_token=bot.dbl_token, topgg_token=bot.topgg_token)  # type: ignore
        elif hasattr(bot, 'dbl_token'):
            self.client = DBLClient(bot, token=bot.dbl_token)  # type: ignore
        elif hasattr(bot, 'topgg_token'):
            self.client = TopGGClient(bot, token=bot.topgg_token)
        else:
            raise NoTokenSet()
    
    @commands.Cog.listener('on_topgg_post_error')
    @commands.Cog.listener('on_dbl_post_error')
    async def post_error(self, error: aiohttp.ClientResponseError):
        print(f'{__name__}: An error occured when posting stats | Status code: {error.status}.'
              f' Enable logging for more information.')
    
    async def cog_command_error(self, ctx: commands.Context, error: commands.CommandError):
        if isinstance(error, commands.NotOwner):
            return
        raise error
    
    @commands.command()
    @commands.is_owner()
    async def post(self, ctx: commands.Context, site: str = None):
        if site is None or not isinstance(self.client, Client):
            await self.client.post_stats()
        elif site.lower() in ('dbl', 'd', 'discordbotlist') and isinstance(self.client, Client):
            await self.client.dbl.post_stats()
        elif site.lower() in ('topgg', 't', 'top.gg') and isinstance(self.client, Client):
            await self.client.topgg.post_stats()
        else:
            await self.client.post_stats()
        
        await ctx.send('Stats sucessfully posted.')
    
    @commands.command()
    @commands.is_owner()
    async def interval(self, ctx: commands.Context, interval: float):
        if isinstance(self.client, Client):
            self.client.intervals = interval  # type: ignore
        else:
            self.client.interval = interval
            
        await ctx.send(f'Interval changed to {interval}')
            
          
if inspect.iscoroutinefunction(commands.Bot.add_cog):  # discord.py uses async setup but some forks don't
    async def setup(bot: commands.Bot) -> None:
        await bot.add_cog(ToppyCog(bot))
else:
    def setup(bot: commands.Bot) -> None:  # type: ignore
        bot.add_cog(ToppyCog(bot))