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


class color:
    PURPLE = '\033[35m'
    BLUE = '\033[34m'
    GREEN = '\033[32m'
    YELLOW = '\033[33m'
    RED = '\033[31m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    ITALIC = '\033[3m'
    END = '\033[0m'


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

        required = item.get('required', False)
        while True:
            s = term_color('%s: ' % item['text'].format(default=item.get('default', None)), color.BOLD)
            if 'description' in item:
                desc = term_color('%s' % item['description'], color.ITALIC)
                sys.stdout.write('%s\n' % desc)

            d = raw_input(s)

            if d == '' or d is None:
                if not required:
                    return convert(item.get('default', d), item.get('type', 'str'))
            else:
                return convert(d, item.get('type', 'str'))


ScaffoldLoader.add_constructor('!prompt', ScaffoldLoader.prompt)


def convert(v, type):
    if type == 'bool':
        return str2bool(v)
    return str(v)

def str2bool(v):
    if v is None:
        return False
    return v.lower() in ("yes", "true", "t", "1", "y")


def main():
    try:
        options = {}
        scaffold_file = os.path.expanduser('~/.xscaffold')
        if os.path.exists(scaffold_file):
            with open(scaffold_file, 'r') as fhd:
                options = yaml.load(fhd)

        parser = argparse.ArgumentParser(description='Scaffold a directory of files.')
        parser.add_argument('-u', '--url', default=options.get('url', 'https://github.com'), help='github repo url')
        parser.add_argument('-t', '--temp', default=options.get('temp_dir', tempfile.gettempdir()), help='temporary directory')

        subparsers = parser.add_subparsers(help='actions')

        parser_a = subparsers.add_parser('apply', help='scaffold a directory')
        parser_a.add_argument('name', help='package name')
        parser_a.add_argument('-v', '--version', default='master', help='package version')
        parser_a.set_defaults(func=apply_cli)

        parser_a = subparsers.add_parser('config', help='configure this process')
        parser_a.add_argument('action', default='view', help='save or view configuration')
        parser_a.set_defaults(func=config_cli)

        args = parser.parse_args()
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

def apply_cli(args):
    dest = os.path.join(args.temp, args.name)

    if os.path.exists(dest):
        rc = os.system("""(cd {dest} && git pull >/dev/null 2>&1)""".format(dest=dest))
    else:
        rc = os.system("""
    git clone {url}/{name} {dest} >/dev/null 2>&1
    """.format(dest=dest, url=args.url, name=args.name))
    if rc != 0:
        sys.stdout.write('Failed to pull scaffold package %s' % args.name)

    rc = os.system("""(cd {dest} && git checkout -f {version} >/dev/null 2>&1)""".format(version=args.version, dest=dest))
    if rc != 0:
        sys.stdout.write('Failed to load version %s' % args.version)

    scaffold_file = os.path.join(dest, './scaffold.yaml')
    if os.path.exists(scaffold_file):
        with open(scaffold_file, 'r') as fhd:
            config = yaml.load(fhd, ScaffoldLoader)
    else:
        config = {}

    for f in config.get('files', []):
        paths = glob2.glob(os.path.join(dest, f['name']))
        for p in paths:
            content = render_file(p, config.get('context', {}))
            with open(f['target'], 'w') as fhd:
                fhd.write(content)


if __name__ == '__main__':
    main()
