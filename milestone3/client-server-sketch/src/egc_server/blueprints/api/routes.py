from . import api
from quart import current_app

@api.get('/health')
async def health():
    return {'status': 'ok'}

@api.get('/status')
async def status():
    return current_app.state

@api.post('/incr/<int:n>')
async def incr(n):
    current_app.state += n
