from __future__ import annotations

from typing import Any, Type, TypeVar, Awaitable, Generic, TYPE_CHECKING, Optional

from aiohttp import web

if TYPE_CHECKING:
    from .webhook import SQLDatabase


__all__ = (
    'AsyncContextManager',
    'MISSING',
    'run_webhook_server'
)


T = TypeVar('T')


class _MissingSentinel:
    def __eq__(self, other):
        return False

    def __bool__(self):
        return False

    def __hash__(self):
        return 0

    def __repr__(self):
        return '...'

    def __getattr__(self, item):
        pass


MISSING: Any = _MissingSentinel()
    
    
class AsyncContextManager(Generic[T]):
    def __init__(self, awaitable: Awaitable[T]):
        self.awaitable = awaitable
        self.ret: T = MISSING

    def __await__(self) -> T:
        return self.awaitable.__await__()

    async def __aenter__(self):
        self.ret = await self

        try:
            return await self.ret.__aenter__()
        except AttributeError:
            return self.ret

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        try:
            return await self.ret.__aexit__(exc_type, exc_val, exc_tb)
        except AttributeError:
            pass


async def run_webhook_server(application: web.Application, site_class: Type[web.BaseSite] = web.TCPSite,
                             connect_db: Optional[SQLDatabase] = None, **kwargs) -> web.BaseSite:
    """
    Run the webhook server created in `create_webhook_server`

    Parameters
    -----------
    application: :class:`aiohttp.web.Application`
        The application to run.
    site_class: :class:`aiohttp.web.BaseSite`
        The site for the application. Must have all methods from :class:`aiohttp.web.BaseSite`.
        Defaults to :class:`web.TCPSite`
    connect_db: Optional[:class:`SQLDatabase`]
        If you pass the :class:`SQLDatabase` instance from :func:`toppy.webhook.create_webhook_server`
        it will automatically connection to the database.
    **kwargs:
        The kwargs to pass into ``site_class``.

    Returns
    --------
    The instance of the site class passed into `site_class`.
    """
    if connect_db is not None:
        await connect_db.connect()

    runner = web.AppRunner(application)
    await runner.setup()

    site = site_class(runner, **kwargs)
    await site.start()

    return site
