import olaplugin.views as v

def setup_routes(app):
    app.router.add_get('/', v.light, name='light')
    app.router.add_get('/channel', v.set_channel)
    app.router.add_get('/wifi', v.wifi, name='wifi')
    app.router.add_get('/touchosc', v.touchosc)
    app.router.add_get()
    