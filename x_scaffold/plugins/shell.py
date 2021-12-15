import os

color = {
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

def run(context, task):
    commands = task
    cmds = commands.format(**context)
    term_colors = dict_to_str(color, 'TERM_%s="%s"\n')
    cmd = """
set +x -ae
%s
%s
""" % (term_colors, cmds)
    rc = os.system(cmd)
    if rc != 0:
        raise RuntimeError('Failed to execute command')

def dict_to_str(d, fmt='%s=%s\n'):
    s = ''
    for x in d:
        s += fmt % (x, d[x])
    return s
