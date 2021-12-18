from unittest.mock import patch
from x_scaffold import engine, plugins
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

    helloworldPackage = tests.get_fixture('helloworld')
    runtime = TestRuntime()
    context = ScaffoldContext({
        'helloworldPackage': helloworldPackage
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
        }
    }
    assert context.notes == [
        'Hello john doe!'
    ]
    assert context.todos == []
    #mock_write.assert_called_once_with({})
