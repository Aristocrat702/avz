from aiohttp import web
import json
import os

async def index(request):
    return web.FileResponse('./web/index.html')

app = web.Application()
app.router.add_get('/', index)

if __name__ == '__main__':
    web.run_app(app, port=8080)
