import click

@click.group()
def config() -> None:
    "View and manage the current EGC node config."

@config.command()
def node():
    pass

@config.command()
def election():
    pass

@config.command()
def batch():
    pass
