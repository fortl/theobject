import asyncio

async def run(cmd):
    proc = await asyncio.create_subprocess_shell(
        cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE)

    stdout, stderr = await proc.communicate()
    return stdout

async def client_status():
    stdout = await run('ifconfig wlan1')
    if 'inet ' in str(stdout):
        return True
    return False

async def client(status):
    if status == 'stop':
        await run('/etc/wifi-manage-scripts/client-stop')
    else:
        await run('/etc/wifi-manage-scripts/client-start')

async def hotspot(status):
    if status == 'stop':
        await run('/etc/wifi-manage-scripts/hotspot-stop')
    else:
        await run('/etc/wifi-manage-scripts/hotspot-start')

async def restart_wifi(mode):
    await client('stop')
    await hotspot('stop')
    if mode == 'hotspot':
        await hotspot('start')
    else:
        await client('start')
