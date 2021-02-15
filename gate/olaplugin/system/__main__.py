import pathlib
import sys
BASE_DIR = pathlib.Path(__file__).parent.parent.parent
sys.path.append(BASE_DIR.__str__())

import asyncio

import olaplugin.system.setup as setup
import olaplugin.system.manage as manage
from olaplugin.config import config

async def print_status():
    status = await manage.client_status()
    print('client is connected' if status else 'client isn\'t connected')

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print("Usage: python -m olaplugin.system {setup|restart|status}")
        exit(0)
    action = sys.argv[1]
    if action == 'setup':
        setup.rewrite_configs(config)
    elif action == 'restart_wifi':
        asyncio.run(manage.restart_wifi(config['wifi_mode']))
    elif action == 'status':
        asyncio.run(print_status())