import json
import os
import yaml

from jinja2 import Environment
from jinja2 import FileSystemLoader

from x_scaffold.context import ScaffoldContext

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
            return yaml.load(file_handle, Loader=yaml.FullLoader)


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


def render_text(text, context: ScaffoldContext):
    """Used to render a Jinja template."""

    env = Environment()
    env.filters['formatlist'] = format_list
    env.filters['yaml'] = yaml_format
    env.filters['json'] = json_format
    utils = RenderUtils()

    template = env.from_string(text)

    return template.render(env=context.environ, context=context, utils=utils)

def render_options(options: dict, context: ScaffoldContext):
    opts = options.copy()
    for k, v in opts.items():
        if isinstance(v, str):
            opts[k] = render_text(v, context)
        elif isinstance(v, dict):
            opts[k] = render_options(v, context)
    return opts