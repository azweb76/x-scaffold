from x_scaffold import rendering
from x_scaffold.context import ScaffoldContext

def test_render_options():
    opts = rendering.render_options({
        'fname': '{{ context.fname }}',
        'list': [
            '{{ context.fname }}'
        ],
        'list_of_dicts': [
            { 'fname': '{{ context.fname }}' }
        ]
    }, ScaffoldContext({
        'fname': 'john',
    }))

    assert opts == {
        'fname': 'john',
        'list': [
            'john'
        ],
        'list_of_dicts': [
            { 'fname': 'john' }
        ]
    }

def test_render_token():
    assert rendering.render_tokens('test: FNAME', ScaffoldContext({
        'FNAME': 'john'
    })) == 'test: john'