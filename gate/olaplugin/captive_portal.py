from aiohttp import web

@web.middleware
async def captive_portal(request, handler):
    try:
        response = await handler(request)
        if response.status != 404:
            return response
        message = response.message
    except web.HTTPException as ex:
        if ex.status != 404:
            raise
        message = ex.reason
    raise web.HTTPFound(location='http://192.168.42.1/')
