from getpass import getpass
from typing import Dict, List
import sys
import click

from x_scaffold.context import ScaffoldContext

CLI_COLORS = {
    'PURPLE': '\033[35m',
    'CYAN':  '\033[36m',
    'BLUE':  '\033[34m',
    'GREEN':  '\033[32m',
    'YELLOW':  '\033[33m',
    'RED':  '\033[31m',
    'BOLD':  '\033[1m',
    'UNDERLINE':  '\033[4m',
    'ITALIC':  '\033[3m',
    'END':  '\033[0m',
}

class ScaffoldRuntime:
    def write(self, message: str):
        pass

    def ask(self, prompt):
        pass

class ScaffoldConsoleRuntime(ScaffoldRuntime):
    def log(self, message):
        self.write(message + '\n')

    def ask(self, prompt):
        name = prompt.get('name')
        description = prompt.get('description', name)
        if prompt.get('secure', False):
            return getpass(prompt=description)
        else:
            return input(f'{description}: ')
    
    def write(self, message: str):
        click.echo(message.format(**CLI_COLORS))

    def print_todos(self, context: ScaffoldContext):
        self.write('{BLUE}{BOLD}TODO:{END}')
        for todo in context.todos:
            self.write(f'  - {todo}')

    def print_notes(self, context: ScaffoldContext):
        self.write('{GREEN}{BOLD}NOTES:{END}')
        for note in context.notes:
            self.write(f'  {note}\n')

