import click
import asyncio
import uvicorn
from egc_app.client import Client

@click.group()
def server() -> None:
	pass

@server.command()
@click.option("--host", default="0.0.0.0")
@click.option("--port", default=8000, type=int)
@click.option("--workers", default=1, type=int)
@click.option("--log-level", default="info")
def start(host, port, workers, log_level):
    """Run the API server."""
    uvicorn.run(
        "egc_app.server.app:create_app",
        factory=True,
        host=host,
        port=port,
        reload=True,
        workers=1, # TODO more for production?
        log_level=log_level,
    )

@server.command()
def health():
    """Is the server OK?"""
    resp = asyncio.run(Client().health())
    click.echo(resp)
