import click

@click.group()
def config() -> None:
    pass

@config.command()
def node():
    pass

@config.command()
def election():
    pass

@config.command()
def batch():
    pass
