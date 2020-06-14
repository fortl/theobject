import olaplugin.wifi.setup as setup
import olaplugin.wifi.manage as manage
from olaplugin.config import config

import asyncio
import sys 

async def print_status():
    status = await manage.client_status()
    print('client is connected' if status else 'client isn\'t connected')

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print("Usage: python -m olaplugin.wifi {setup|restart|status}")
        exit(0)
    action = sys.argv[1]
    if action == 'setup':
        setup.rewrite_configs(config)
    elif action == 'restart':
        asyncio.run(manage.restart(config['wifi_mode']))
    elif action == 'status':
        asyncio.run(print_status())