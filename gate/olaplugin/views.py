from olaplugin.interface import channels_block
from olaplugin.net_helper import ip_list
from olaplugin.config import config, save_config

from aiohttp import web
import aiohttp_jinja2
import asyncio
import re

@aiohttp_jinja2.template('light.html')
async def light(request):
    if request.url.host not in ip_list:
        raise web.HTTPFound(location='http://192.168.42.1/')
    return {}

@aiohttp_jinja2.template('wifi.html')
async def wifi(request):
    proc = await asyncio.create_subprocess_shell(
        'iw dev wlan1 scan',
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE)

    stdout, stderr = await proc.communicate()
    def parse_wifi_string(net):
        m = re.match(r'.*SSID: ([\w\s\-]+)\\n.*', net)
        if not m:
            return 
        return {"ssid": m.group(1)}
    nets = [ parse_wifi_string(net) 
        for net in re.split(r'BSS \S+\(on wlan.?\)', str(stdout), flags=re.M) ]
    nets = [i for i in nets if i] 
    return { "ssid_list": nets, "config": config }

async def set_wifi(request):
    print(await request.post())
    raise web.HTTPFound(location=request.app.router['wifi'].url_for())

@aiohttp_jinja2.template('touchosc.html')
async def touchosc(request):
    return {}

@aiohttp_jinja2.template('settings.html')
async def settings(request):
    return {}

async def set_channel(request):
    channels_block.set_all(request.query['set'])
    raise web.HTTPFound(location=request.app.router['light'].url_for())