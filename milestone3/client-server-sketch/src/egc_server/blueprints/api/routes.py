from . import api

@api.get('/health')
async def health():
    return {'status': 'ok'}
