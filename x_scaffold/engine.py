#!/usr/bin/env python
# coding: utf-8

import argparse
import io
import os
import pathlib

import yaml
import logging
import getpass
import json
import sys
import re
import tempfile
import importlib
from collections import defaultdict
from fnmatch import fnmatch

from .context import ScaffoldContext
from .runtime import ScaffoldRuntime
from .plugins import load_plugins
from .rendering import render_text
from .steps import ScaffoldStep
from .plugin import ScaffoldPluginContext

_log = logging.getLogger(__name__)


def complete(text, state):
    if str(text).startswith('~/'):
        home = os.path.expanduser('~/')
        p = os.path.join(home, text[2:])
    else:
        p = text
        home = None

    items = pathlib.Path(os.getcwd()).glob(p + '*')
    if items is not None and home is not None:
        items = ['~/' + x[len(home):] for x in items]
    return (items + [None])[state]


def set_readline():
    try:
        import readline
        readline.set_completer_delims(' \t\n;')
        readline.parse_and_bind("tab: complete")
        readline.set_completer(complete)
    except:
        pass


class AttributeDict(dict):
    __getattr__ = dict.__getitem__
    __setattr__ = dict.__setitem__


color = AttributeDict({
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
})


def dict_to_str(d, fmt='%s=%s\n'):
    s = ''
    for x in d:
        s += fmt % (x, d[x])
    return s


def str2bool(v):
    if v is None:
        return False
    return v.lower() in ("yes", "true", "t", "1", "y")


known_types = {
    'int': int,
    'bool': str2bool,
    'str': str,
    'float': float
}


def term_color(text, *text_colors):
    return ''.join(text_colors) + text + color.END




# def render_file(path, context):
#     """Used to render a Jinja template."""

#     template_dir, template_name = os.path.split(path)
#     return render(template_name, context, template_dir)


def is_enabled(options):
    if 'enabled' in options:
        return options['enabled']
    if 'disabled' in options:
        return not options['disabled']
    if 'enabledif' in options:
        enabledif = options['enabledif']
        value = enabledif['value']
        if 'equals' in enabledif:
            return value == enabledif['equals']
        elif 'notequals' in enabledif:
            return value != enabledif['notequals']
    return True


def read_input(s):
    return input(s)


# class Prompt:

#     def __init__(self, d):
#         self._dict = d
#         self._value = None

#     def get(self):
#         if self._value is None:
#             self._value = self._get_value(self._dict)
#         return self._value

#     def _get_value(self, prompt):
#         default = prompt.get('default', None)
#         if isinstance(default, str):
#             default = default.format(env=os.environ)

#         if not is_enabled(prompt):
#             return default

#         required = prompt.get('required', False)
#         while True:
#             s = term_color('%s: ' % prompt['description'].format(
#                 default=default, env=os.environ), color.BOLD)
#             # if 'description' in prompt:
#             #     desc = term_color('%s' % prompt['description'], color.ITALIC)
#             #     sys.stdout.write('%s\n' % desc)

#             if 'choices' in prompt:
#                 s = term_color('%s: ' % prompt['description'].format(
#                     default=default), color.BOLD)
#                 sys.stdout.write('%s\n\n' % s)

#                 choices = prompt['choices']
#                 while True:
#                     opts = []
#                     max_len = 0
#                     for c in choices:
#                         keywords = ', '.join(c['keywords'])
#                         if len(keywords) > max_len:
#                             max_len = len(keywords)
#                         opts.append({'kw': keywords, 't': c['text']})

#                     for opt in opts:
#                         s = '%s' % c['text']
#                         opt['kw'] = opt['kw'].ljust(max_len)
#                         sys.stdout.write('[{kw}] {t}\n'.format(**opt))

#                     d = read_input(term_color('\nchoice: ', color.BOLD))

#                     for c in choices:
#                         if d in c['keywords']:
#                             v = c.get('value', d)
#                             if isinstance(v, dict):
#                                 v = defaultdict(
#                                     lambda: '', c.get('default', {}), **v)
#                             return v

#                     sys.stdout.write('\n%s please select a keyword on the left\n\n' %
#                                      term_color('[invalid choice] ', color.RED))
#             else:
#                 if prompt.get('secure', False):
#                     d = getpass.getpass(prompt=s)
#                 else:
#                     d = read_input(s)

#             if d == '' or d is None:
#                 if not required:
#                     return default
#                 else:
#                     sys.stdout.write(term_color('[required] ', color.RED))
#             else:
#                 if 'validate' in prompt:
#                     matches = re.match(prompt['validate'], d)
#                     if matches is None:
#                         sys.stdout.write(term_color(
#                             '[invalid, %s] ' % prompt['validate'], color.RED))
#                         continue
#                 if 'load' in prompt:
#                     if prompt['load'] == 'yaml':
#                         with open(d, 'r') as fhd:
#                             return yaml.load(fhd, Loader=yaml.FullLoader)
#                 return convert(d, prompt.get('type', 'str'))


# class ScaffoldLoader(yaml.Loader):

#     def __init__(self, stream):
#         if stream is not None:
#             if isinstance(stream, io.FileIO):
#                 self._root = os.path.split(stream.name)[0]
#             elif isinstance(stream, dict):
#                 d = stream
#                 stream = d['fhd']
#                 self._root = os.path.splitext(stream.name)[0]
#                 self._context = d['context']

#         super(ScaffoldLoader, self).__init__(stream)

#     def module(self, node):
#         item = self.construct_mapping(node, 9999)

#         if not is_enabled(item):
#             return None

#         fn = load_module(item)
#         if 'args' in item:
#             return fn(**item['args'])
#         else:
#             return fn()

    

#     def prompt(self, node):
#         item = self.construct_mapping(node, 9999)

#         return Prompt(item).get()

#     def prompt2(self, node):
#         item = self.construct_mapping(node, 9999)

#         return Prompt(item)


# ScaffoldLoader.add_constructor('!prompt2', ScaffoldLoader.prompt2)
# ScaffoldLoader.add_constructor('!prompt', ScaffoldLoader.prompt)
# ScaffoldLoader.add_constructor('!module', ScaffoldLoader.module)


def convert(v, type):
    if type in known_types:
        return known_types[type](v)
    return str(v)


def read_parameter(prompt, runtime: ScaffoldRuntime):
    default = prompt.get('default', None)
    if isinstance(default, str):
        default = default.format(env=os.environ)

    if not is_enabled(prompt):
        return default

    name = prompt.get('name', 'parameter')
    required = prompt.get('required', False)
    description = prompt.get('description', name)
    while True:
        s = term_color('%s: ' % description.format(
            default=default, env=os.environ), color.BOLD)
        # if 'description' in prompt:
        #     desc = term_color('%s' % prompt['description'], color.ITALIC)
        #     sys.stdout.write('%s\n' % desc)

        if 'choices' in prompt:
            s = term_color('%s: ' % description.format(
                default=default), color.BOLD)
            sys.stdout.write('%s\n\n' % s)

            choices = prompt['choices']
            while True:
                opts = []
                max_len = 0
                for c in choices:
                    keywords = ', '.join(c['keywords'])
                    if len(keywords) > max_len:
                        max_len = len(keywords)
                    opts.append({'kw': keywords, 't': c['text']})

                for opt in opts:
                    s = '%s' % c['text']
                    opt['kw'] = opt['kw'].ljust(max_len)
                    sys.stdout.write('[{kw}] {t}\n'.format(**opt))

                d = None #read_input(term_color('\nchoice: ', color.BOLD))


                for c in choices:
                    if d in c['keywords']:
                        v = c.get('value', d)
                        if isinstance(v, dict):
                            v = defaultdict(
                                lambda: '', c.get('default', {}), **v)
                        return v

                sys.stdout.write('\n%s please select a keyword on the left\n\n' %
                                    term_color('[invalid choice] ', color.RED))
        else:
            d = runtime.ask(prompt)

        if d == '' or d is None:
            if not required:
                return default
            else:
                sys.stdout.write(term_color('[required] ', color.RED))
        else:
            if 'validate' in prompt:
                matches = re.match(prompt['validate'], d)
                if matches is None:
                    sys.stdout.write(term_color(
                        '[invalid, %s] ' % prompt['validate'], color.RED))
                    continue
            if 'load' in prompt:
                if prompt['load'] == 'yaml':
                    with open(d, 'r') as fhd:
                        return yaml.load(fhd, Loader=yaml.FullLoader)
            return convert(d, prompt.get('type', 'str'))

def main():
    try:
        options = {}
        set_readline()
        scaffold_file = os.path.expanduser('~/.xscaffold')
        if os.path.exists(scaffold_file):
            with open(scaffold_file, 'r') as fhd:
                options = yaml.load(fhd, Loader=yaml.FullLoader)

        parser = argparse.ArgumentParser(
            description='Scaffold a directory of files.')

        parser.add_argument(
            '-l',
            '--log-level',
            dest='log_level',
            default='INFO',
            choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
            help='optional. Set the log level.')

        parser.add_argument('-u', '--url', default=options.get('url', 'https://github.com'), help='github repo url')
        parser.add_argument('-t', '--temp', default=options.get('temp_dir', tempfile.gettempdir()), help='temporary directory')

        subparsers = parser.add_subparsers(help='actions')

        parser_a = subparsers.add_parser('apply', help='scaffold a directory')
        parser_a.add_argument('package', help='package name')
        parser_a.add_argument(
            '-v', '--version', default='master', help='package version')
        parser_a.add_argument('-n', '--name', default='scaffold',
                              help='name of scaffold file (<name>.yaml)')
        parser_a.add_argument('-x', '--extend-context', default=None,
                              help='allow child packages to extend context')
        parser_a.set_defaults(func=apply_cli)

        parser_a = subparsers.add_parser(
            'config', help='configure this process')
        parser_a.add_argument('action', default='view',
                              help='save or view configuration')
        parser_a.set_defaults(func=config_cli)

        parser_a = subparsers.add_parser(
            'upgrade', help='upgrade x-scaffold using pip')
        parser_a.set_defaults(func=upgrade_cli)

        args = parser.parse_args()
        logging.getLogger('requests').setLevel(logging.ERROR)
        logging.basicConfig(level=getattr(logging, args.log_level))

        args.func(args)
    except KeyboardInterrupt:
        exit(0)


def upgrade_cli(args):
    rc = os.system(
        'pip install x-scaffold --upgrade >/dev/null 2>&1')
    if rc == 0:
        log('x-scaffold was {GREEN}successfully{END} upgraded.')
    else:
        log('x-scaffold {RED}failed{END} to upgrade [rc=%s].' % rc)


def config_cli(args):
    options = {}
    scaffold_file = os.path.expanduser('~/.xscaffold')
    if os.path.exists(scaffold_file):
        with open(scaffold_file, 'r') as fhd:
            options = yaml.load(fhd, Loader=yaml.FullLoader)

    if args.action == 'save':
        options['url'] = args.url

        with open(scaffold_file, 'w') as fhd:
            yaml.dump(options, fhd, default_flow_style=False)
    elif args.action == 'view':
        sys.stdout.write('url: %s' % options.get('url', 'not defined'))


# def log(s, context={}):
#     sys.stdout.write(
#         render_text(s, context)
#     )


# def execute_command(context, pkg_dir, commands):
#     cmds = commands.format(**context)
#     term_colors = dict_to_str(color, 'TERM_%s="%s"\n')
#     cmd = """
# set +x -ae
# %s
# %s
# """ % (term_colors, cmds)
#     rc = os.system(cmd)
#     if rc != 0:
#         raise RuntimeError('Failed to execute command')


# def load_module(m):
#     mod = importlib.import_module('modules.%s' % m['name'])
#     if hasattr(mod, 'init'):
#         getattr(mod, 'init')(sys.modules[__name__])

#     return getattr(mod, m.get('function', 'execute'))


# def execute_modules(context, pkg_dir, modules):
#     for m in modules:
#         execute_fn = load_module(m)
#         execute_fn(context, pkg_dir, m)


def apply_cli(args):

    todos = []
    notes = []
    context = execute_scaffold(color, args, todos, notes)

    # if len(todos) > 0:
    #     sys.stdout.write('\n=== Follow-up Checklist ===\n\n')
    #     for todo in todos:
    #         log('[ ] %s\n' % todo, context=context)
    #     sys.stdout.write('\n')

    # if len(notes) > 0:
    #     sys.stdout.write('\n=== Notes ===\n\n')
    #     for note in notes:
    #         log('%s\n' % note, context=context)
    #     sys.stdout.write('\n\n')


def rm_rf(d):
    for path in (os.path.join(d, f) for f in os.listdir(d)):
        if os.path.isdir(path):
            rm_rf(path)
        else:
            os.unlink(path)
    os.rmdir(d)


def process_prompts(d):
    pass
    # for x in d:
    #     if isinstance(d[x], Prompt):
    #         d[x] = read_parameter(d[x].get()
    #     elif isinstance(d[x], dict):
    #         process_prompts(d[x])


def process_parameters(parameters, context: ScaffoldContext, runtime: ScaffoldRuntime):
    for parameter in parameters:
        parameter_name = parameter['name']
        if parameter_name in context:
            context[parameter_name] = context[parameter_name]
        else:
            context[parameter_name] = read_parameter(parameter, runtime)


def run(context: ScaffoldContext, options, runtime: ScaffoldRuntime):
    execute_scaffold(context, options, runtime)


def execute_scaffold(context: ScaffoldContext, options, runtime: ScaffoldRuntime):
    tempdir = options.get('temp', tempfile.gettempdir())
    package = options['package']
    version = options.get('version', 'main')
    name = 'xscaffold'
    url = 'github.com'
    if os.path.exists(package):
        runtime.log(
            '[info] using local package \'%s\'...' % package + '\n')
        pkg_dir = package
    else:
        pkg_dir = os.path.join(tempdir, f'${package}@{version}')

        rc = 9999
        if os.path.exists(pkg_dir):
            runtime.log('{YELLOW}[git] updating %s package...{END}\n' % package)
            rc = os.system(
                """(cd {pkg_dir} && git pull >/dev/null 2>&1)""".format(pkg_dir=pkg_dir))
            if rc != 0:
                runtime.log('{RED}[error]{YELLOW} package %s is having issues, repairing...{END}\n' % package)
                rm_rf(pkg_dir)

        if rc != 0:
            runtime.log('[git] pulling %s package...' % package + '\n')
            rc = os.system("""
        git clone {url}/{package} {pkg_dir} >/dev/null 2>&1
        """.format(pkg_dir=pkg_dir, url=url, package=package))
        if rc != 0:
            runtime.log(
                'Failed to pull scaffold package %s' % package)

        rc = os.system("""(cd {pkg_dir} && git checkout -f {version} >/dev/null 2>&1)""".format(
            version=version, pkg_dir=pkg_dir))
        if rc != 0:
            runtime.log('Failed to load version %s' % version)

    sys.path.append(pkg_dir)
    scaffold_file = os.path.join(pkg_dir, '%s.yaml' % name)
    if os.path.exists(scaffold_file):
        with open(scaffold_file, 'r') as fhd:
            config = yaml.load(fhd, Loader=yaml.FullLoader)
    else:
        _log.warning('scaffold file %s not found', scaffold_file)
        config = {
            'steps': [
                {
                    'fetch': {
                        'source': '.',
                        'target': '.'
                    }
                }
            ]
        }

    plugin_context = ScaffoldPluginContext(
        config.get('plugins', {})
    )
    plugins: list = load_plugins()
    for plugin in plugins:
        plugin.init(plugin_context)

    # extend_context = False
    # if extend_context:
    #     context = defaultdict(lambda: '', parent_context,
    #                           **args.extend_context)
    # else:
    context.update(config.get('context', {}))
    #context = ScaffoldContext(config.get('context', {}))
        #context['parent'] = parent_context

    process_parameters(config.get('parameters', []), context, runtime)

    context['__package'] = {
        'path': pkg_dir,
        'options': options
    }

    steps: list = config.get('steps', [])
    step: dict

    for step in steps:
        for step_name in step:
            plugin_step = plugin_context.steps[step_name]
            plugin_step.run(context, step[step_name], runtime)

            # if 'task' in task:
            #     sys.stdout.write(term_color('[task] %s' % task[
            #                      'task'], color.CYAN) + '\n')
            # if 'copy' in task:
            #     render_files(context, pkg_dir, task['copy'])
            # if 'shell' in task:
            #     execute_command(context, pkg_dir, task['shell'])
            # if 'modules' in task:
            #     execute_modules(context, pkg_dir, task['modules'])
            # if 'scaffold' in task:
            #     scaffold = AttributeDict(dict({
            #         'url': url,
            #         'temp': tempdir,
            #         'version': version,
            #         'package': package,
            #         'extend_context': extend_context
            #     }, **task['scaffold']))

            #     context = execute_scaffold(context, scaffold, todos, notes)
            # if 'log' in task:
            #     log(task['log'], context)
            # if 'todo' in task:
            #     todo = task['todo']
            #     if isinstance(todo, list):
            #        for todo_item in todo:
            #            todos.append(todo_item)
            #     else:
            #         todos.append(todo)

    # if 'notes' in config:
    #     notes.append(config['notes'])

    # runtime.log(term_color('[done] scaffolding %s::%s complete!' % (
    #     package, name), color.CYAN) + '\n')

    return context


if __name__ == '__main__':
    main()
