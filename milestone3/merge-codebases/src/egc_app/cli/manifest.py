import click
from egc_app.cli.utils import RoleAwareGroup

@click.group(cls=RoleAwareGroup)
def manifest() -> None:
    "Create and announce an election manifest."

@manifest.command(roles=['admin'])
def create():
    raise NotImplementedError


@manifest.command(roles=['admin'])
@multi_load('manifest', ???, ['json'])
def create(
    manifest: ???,
):
    '''Build a minimal valid manifest.
    For now it handles two types of contests:
    \b
        - office with candidates
        - referendum (yes/no)
    '''
    asyncio.run(Client().manifest_create(manifest=manifest))


@manifest.command(roles=['admin'])
def announce():
    raise NotImplementedError
