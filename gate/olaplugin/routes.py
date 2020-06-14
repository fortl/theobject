import olaplugin.views as v

def setup_routes(app, base_dir):
    app.router.add_get('/', v.light, name='light')
    app.router.add_get('/channel', v.set_channel)
    app.router.add_get('/wifi', v.wifi, name='wifi')
    app.router.add_post('/wifi', v.set_wifi)
    app.router.add_get('/touchosc', v.touchosc)
    app.router.add_get('/settings', v.settings)
    app.router.add_static('/static', path=str(base_dir / 'static'))
    