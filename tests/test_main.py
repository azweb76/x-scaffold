from tempfile import gettempdir, tempdir
from unittest.mock import patch
from x_scaffold import engine
import tests
from x_scaffold.runtime import ScaffoldRuntime
from x_scaffold.context import ScaffoldContext


def test_main():
    class TestRuntime(ScaffoldRuntime):
        logs = []
        def ask(self, prompt):
            return 'john'
        def log(self, message: str):
            self.logs.append(message)

    tmpdir = gettempdir()
    helloworldPackage = tests.get_fixture('helloworld')
    runtime = TestRuntime()
    context = ScaffoldContext({
        'helloworldPackage': helloworldPackage,
        '__target': tmpdir
    })

    package = tests.get_fixture('basic')
    with patch('sys.stdout.write') as mock_write:
        engine.run(context, {
            'package': package
        }, runtime)
    assert context == {
        'fname': 'john',
        'fullname': 'john doe',
        'lname': 'doe',
        'helloworldPackage': helloworldPackage,
        '__package': {
            'path': package,
            'options': {
                'package': package
            }
        },
        '__target': tmpdir
    }
    assert context.notes == [
        'Hello john doe!',
        'test note from basic'
    ]
    assert context.todos == [
        'test todo from basic'
    ]
