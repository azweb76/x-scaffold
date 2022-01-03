import click
from click.decorators import help_option

from x_scaffold import engine
from x_scaffold.context import ScaffoldContext
from x_scaffold.runtime import ScaffoldConsoleRuntime

@click.command('apply', help='Apply a new scaffold')
@click.argument('package')
@click.option('-v', '--version', default=None, help='The version of the scaffold to apply')
@click.option('-n', '--name', default='xscaffold', help='The name of the scaffold to apply')
def apply_cli(package, version, name):
    engine.execute_scaffold(ScaffoldContext({}), {
        'package': package,
        'version': version,
        'name': name
    }, ScaffoldConsoleRuntime())

@click.group(context_settings=dict(help_option_names=['-h', '--help']))
def cli():
    pass

cli.add_command(apply_cli)

if __name__ == '__main__':
    cli()
