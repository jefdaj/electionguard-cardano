from . import api
from quart import current_app, redirect, url_for

@api.get('/health')
async def health():
    return {'status': 'ok'}

@api.get('/state')
async def state():
    return {'state': current_app.state}

@api.post('/incr/<int:n>')
async def incr(n):
    current_app.state += n
    return await state()
