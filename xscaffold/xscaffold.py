#!/usr/bin/env python
# coding: utf-8

import argparse
import os
import readline
import yaml
import glob2
import logging
import json
import sys
import re
import tempfile
from jinja2 import Environment
from jinja2 import FileSystemLoader

log = logging.getLogger(__name__)


def complete(text, state):
    if str(text).startswith('~/'):
        home = os.path.expanduser('~/')
        p = os.path.join(home, text[2:])
    else:
        p = text
        home = None

    items = glob2.glob(p+'*')
    if items is not None and home is not None:
        items = ['~/' + x[len(home):] for x in items]
    return (items+[None])[state]


readline.set_completer_delims(' \t\n;')
readline.parse_and_bind("tab: complete")
readline.set_completer(complete)


class AttributeDict(dict):
    __getattr__ = dict.__getitem__
    __setattr__ = dict.__setitem__


class color:
    PURPLE = '\033[35m'
    CYAN = '\033[36m'
    BLUE = '\033[34m'
    GREEN = '\033[32m'
    YELLOW = '\033[33m'
    RED = '\033[31m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    ITALIC = '\033[3m'
    END = '\033[0m'


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


class RenderUtils(object):  # pylint: disable=R0903
    """Template utilities."""

    @classmethod
    def read_file(cls, path, parse=False):
        """Used to read a file and return its contents."""

        with open(path, 'r') as file_handle:
            if parse:
                parser = get_parser(path)
                return parser.load(file_handle)
            else:
                return file_handle.read()

    @classmethod
    def read_json(cls, path):
        """Used to read a JSON file and return its contents."""

        with open(path, 'r') as file_handle:
            return json.load(file_handle)

    @classmethod
    def read_yaml(cls, path):
        """Used to read a YAML file and return its contents."""

        with open(path, 'r') as file_handle:
            return yaml.load(file_handle)


def format_list(value, format='{value}'):
    for idx, x in enumerate(value):
        value[idx] = format.format(value=value[idx], index=idx)
    return value


def yaml_format(value):
    if value is None:
        return 'null'
    return yaml.dump(value, default_flow_style=True)

def json_format(value):
    if value is None:
        return 'null'
    return json.dumps(value)

def get_parser(path):
    ext = os.path.splitext(path)[1]
    if ext == '.yaml' or ext == '.yml':
        return yaml
    elif ext == '.json':
        return json
    else:
        exit('Parser format not supported: %s' % ext)


def render(template_name, context, template_dir):
    """Used to render a Jinja template."""

    env = Environment(loader=FileSystemLoader(template_dir))
    env.filters['formatlist'] = format_list
    env.filters['yaml'] = yaml_format
    env.filters['json'] = json_format
    utils = RenderUtils()

    template = env.get_template(template_name)

    return template.render(env=os.environ, context=context, utils=utils)


def render_file(path, context):
    """Used to render a Jinja template."""

    template_dir, template_name = os.path.split(path)
    return render(template_name, context, template_dir)


class ScaffoldLoader(yaml.Loader):
    def __init__(self, stream):
        if stream is not None:
            if isinstance(stream, file):
                self._root = os.path.split(stream.name)[0]

        super(ScaffoldLoader, self).__init__(stream)

    # def include(self, node):
    #     filename = os.path.join(self._root, self.construct_scalar(node))
    #     files = glob2.glob(filename, with_matches=False)
    #
    #     x = None
    #     if len(files) == 0:
    #         log.warning('no !include files found matching %s' % filename)
    #         return x
    #
    #     for f in files:
    #         name, ext = os.path.splitext(f)
    #         if ext == '.jinja':
    #             content = render_file(f, {})
    #             y = yaml.load(content)
    #         else:
    #             with open(f, 'r') as fhd:
    #                 y = yaml.load(fhd, CicdLoader)
    #
    #         if isinstance(y, str):
    #             x = y
    #         else:
    #             x = extend(y, x, merge=True)
    #
    #     return x
    #
    # def resolve_path(self, node):
    #     filename = os.path.join(self._root, self.construct_scalar(node))
    #     return filename
    #
    # def shared_path(self, node):
    #     root = os.path.expandvars('$CICD_SHARED')
    #     filename = os.path.join(root, self.construct_scalar(node))
    #     return filename
    #
    # def template(self, tag_prefix, node):
    #     item = self.construct_mapping(node, 9999)
    #
    #     template_path = os.path.expandvars('$CICD_SHARED/templates/%s.yaml' % tag_prefix)
    #     return yaml.load(render_file(template_path, item), CicdLoader)
    #
    # def encrypted(self, node):
    #     value = self.construct_scalar(node)
    #     try:
    #         return xcrypto.decrypt(value)
    #     except Exception as e:
    #         log.warning('unable to decrypt value in yaml')
    #         return None
    #
    # def merge_list(self, node):
    #     item = self.construct_mapping(node, 9999)
    #     return MergeList(item)
    def prompt(self, node):
        item = self.construct_mapping(node, 9999)

        if not item.get('enabled', True):
            return item.get('default', None)

        required = item.get('required', False)
        while True:
            s = term_color('%s: ' % item['text'].format(default=item.get('default', None)), color.BOLD)
            if 'description' in item:
                desc = term_color('%s' % item['description'], color.ITALIC)
                sys.stdout.write('%s\n' % desc)

            d = raw_input(s)

            if d == '' or d is None:
                if not required:
                    return item.get('default', None)
                else:
                    sys.stdout.write(term_color('[required] ', color.RED))
            else:
                if 'validate' in item:
                    matches = re.match(item['validate'], d)
                    if matches is None:
                        sys.stdout.write(term_color('[invalid, %s] ' % item['validate'], color.RED))
                        continue
                return convert(d, item.get('type', 'str'))


ScaffoldLoader.add_constructor('!prompt', ScaffoldLoader.prompt)


def convert(v, type):
    if type in known_types:
        return known_types[type](v)
    return str(v)


def main():
    try:
        options = {}
        scaffold_file = os.path.expanduser('~/.xscaffold')
        if os.path.exists(scaffold_file):
            with open(scaffold_file, 'r') as fhd:
                options = yaml.load(fhd)

        parser = argparse.ArgumentParser(description='Scaffold a directory of files.')

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
        parser_a.add_argument('-v', '--version', default='master', help='package version')
        parser_a.add_argument('-n', '--name', default='scaffold', help='name of scaffold file (<name>.yaml)')
        parser_a.add_argument('-x', '--extend-context', default=True, help='allow child packages to extend context')
        parser_a.set_defaults(func=apply_cli)

        parser_a = subparsers.add_parser('config', help='configure this process')
        parser_a.add_argument('action', default='view', help='save or view configuration')
        parser_a.set_defaults(func=config_cli)

        args = parser.parse_args()
        logging.basicConfig(level=getattr(logging, args.log_level))

        args.func(args)
    except KeyboardInterrupt:
        exit(0)


def config_cli(args):
    options = {}
    scaffold_file = os.path.expanduser('~/.xscaffold')
    if os.path.exists(scaffold_file):
        with open(scaffold_file, 'r') as fhd:
            options = yaml.load(fhd)

    if args.action == 'save':
        options['url'] = args.url

        with open(scaffold_file, 'w') as fhd:
            yaml.dump(options, fhd, default_flow_style=False)
    elif args.action == 'view':
        sys.stdout.write('url: %s' % options.get('url', 'not defined'))


def execute_command(context, pkg_dir, commands):
    for c in commands:
        cmd = c.format(pkg_dir=pkg_dir, context=AttributeDict(context))
        rc = os.system(cmd)
        if rc != 0:
            raise RuntimeError('Failed to execute command')


def apply_cli(args):
    todos = []
    notes = []
    execute_scaffold({}, args, todos, notes)

    if len(todos) > 0:
        sys.stdout.write('\n=== Follow-up Checklist ===\n\n')
        for todo in todos:
            sys.stdout.write(term_color('[ ] %s' % todo, color.GREEN) + '\n')
        sys.stdout.write('\n')

    if len(notes) > 0:
        sys.stdout.write('\n=== Notes ===\n\n')
        for note in notes:
            sys.stdout.write(term_color('%s' % note, color.GREEN) + '\n')
        sys.stdout.write('\n\n')

def execute_scaffold(parent_context, args, todos, notes):
    if os.path.exists(args.package):
        sys.stdout.write(
            term_color('[info] using local package \'%s\'...' % args.package, color.YELLOW) + '\n')
        pkg_dir = args.package
    else:
        pkg_dir = os.path.join(args.temp, args.package)

        if os.path.exists(pkg_dir):
            sys.stdout.write(
                term_color('[git] updating %s package...' % args.package, color.YELLOW) + '\n')
            rc = os.system("""(cd {pkg_dir} && git pull >/dev/null 2>&1)""".format(pkg_dir=pkg_dir))
        else:
            sys.stdout.write(
                term_color('[git] pulling %s package...' % args.package, color.YELLOW) + '\n')
            rc = os.system("""
        git clone {url}/{package} {pkg_dir} >/dev/null 2>&1
        """.format(pkg_dir=pkg_dir, url=args.url, package=args.package))
        if rc != 0:
            sys.stdout.write('Failed to pull scaffold package %s' % args.package)

        rc = os.system("""(cd {pkg_dir} && git checkout -f {version} >/dev/null 2>&1)""".format(version=args.version, pkg_dir=pkg_dir))
        if rc != 0:
            sys.stdout.write('Failed to load version %s' % args.version)

    scaffold_file = os.path.join(pkg_dir, '%s.yaml' % args.name)
    if os.path.exists(scaffold_file):
        with open(scaffold_file, 'r') as fhd:
            config = yaml.load(fhd, ScaffoldLoader)
    else:
        log.warn('scaffold file %s not found', scaffold_file)
        config = {}

    if args.extend_context:
        context = dict(parent_context, **config.get('context', {}))
    else:
        context = config.get('context', {})
        context['parent'] = parent_context

    files = config.get('files', [])

    render_files(context, pkg_dir, files)

    tasks = config.get('tasks', [])
    for task in tasks:
        if task.get('enabled', True):
            sys.stdout.write(term_color('[task] %s' % task['task'], color.CYAN) + '\n')
            if 'files' in task:
                render_files(context, pkg_dir, task['files'])
            if 'exec' in task:
                execute_command(context, pkg_dir, task['exec'])
            if 'scaffold' in task:
                scaffold = AttributeDict(dict({
                    'url': args.url,
                    'temp': args.temp,
                    'version': args.version,
                    'extend_context': args.extend_context
                }, **task['scaffold']))

                execute_scaffold(context, scaffold, todos, notes)

            if 'todo' in task:
                todos.append(task['todo'])

    if 'notes' in config:
        notes.append(config['notes'])

    sys.stdout.write(term_color('[done] scaffolding %s::%s complete!' % (args.package, args.name), color.CYAN) + '\n')


def render_files(context, pkg_dir, files):
    for f in files:
        target = f['target']
        if not target.endswith('/'):
            p = os.path.join(pkg_dir, f['name'])
            base, name = os.path.split(p)
            tbase, tname = os.path.split(target)
            if not os.path.exists(tbase):
                os.makedirs(tbase)
            content = render_file(p, context)
            with open(target, 'w') as fhd:
                fhd.write(content)
        else:
            source = os.path.join(pkg_dir, f['name'])
            sbase, sname = os.path.split(source)
            paths = glob2.glob(source)

            for p in paths:
                tfile = p[len(sbase) + 1:]
                t = os.path.join(target, tfile)
                tbase, tname = os.path.split(t)
                if not os.path.exists(tbase):
                    os.makedirs(tbase)
                content = render_file(p, context)
                with open(t, 'w') as fhd:
                    fhd.write(content)


if __name__ == '__main__':
    main()
