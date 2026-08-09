import click
from egc_app.cli.utils import RoleAwareGroup, multi_load
from egc import EgcManifest
import electionguard as eg


@click.group(cls=RoleAwareGroup)
def manifest() -> None:
    "Build election manifests."


@manifest.command(roles=['admin'])
@multi_load('manifest', EgcManifest, ['json'])
def create(manifest: EgcManifest):
    '''Build a minimal valid manifest.
    For now it handles two types of contests:

    \b
        1. office with candidates
        2. referendum (yes/no)
    '''
    click.echo(manifest)
    # TODO do on server:
    eg_manifest = manifest.to_eg()
    click.echo(eg_manifest)
    # asyncio.run(Client().manifest_create(manifest=manifest))
