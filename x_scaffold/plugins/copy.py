import os
from ..context import ScaffoldContext

from ..rendering import render
from ..steps import ScaffoldStep
from ..runtime import ScaffoldRuntime
from ..plugin import ScaffoldPluginContext

from fnmatch import fnmatch


def init(context: ScaffoldPluginContext):
    context.add_step('fetch', FetchStep())


def is_match(path, templates):
    for template in templates:
        if fnmatch(path, template):
            return True
    return False


def render_file(path, context):
    """Used to render a Jinja template."""

    template_dir, template_name = os.path.split(path)
    return render(template_name, context, template_dir)


class FetchStep(ScaffoldStep):
    def run(self, context: ScaffoldContext, step: dict, runtime: ScaffoldRuntime):
        files = step
        pkg_dir = context['pkg_dir']
        full_pkg_dir = os.path.realpath(pkg_dir)
        for f in files:
            target = f['target'].format(**context)
            full_target = os.path.realpath(target)

            source = os.path.join(full_pkg_dir, f['source'].format(**context))
            if os.path.exists(source) and os.path.isfile(source):
                tbase, tname = os.path.split(target)
                if not os.path.exists(tbase):
                    os.makedirs(tbase)
                content = render_file(source, context)
                with open(target, 'w') as fhd:
                    fhd.write(content)
            else:
                templates = f.get('templates', [])
                exclude = f.get('exclude', ['.git', '.git/*'])

                paths = os.PathLike.Path(full_pkg_dir).rglob(f['name'].format(**context))

                for p_obj in paths:
                    p = str(p_obj)
                    tfile = p[len(full_pkg_dir)+1:]
                    t = os.path.join(full_target, tfile)
                    tbase, tname = os.path.split(t)
                    if is_match(tfile, exclude):
                        continue
                    if not os.path.exists(tbase):
                        os.makedirs(tbase)

                    if p_obj.is_file():
                        if is_match(tfile, templates):
                            content = render_file(p, context)
                            with open(t, 'w') as fhd:
                                fhd.write(content)
                        else:
                            with open(p, 'r') as fhd:
                                with open(t, 'w') as fhd2:
                                    fhd2.write(fhd.read())
