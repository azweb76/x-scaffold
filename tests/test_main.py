from unittest.mock import patch
from x_scaffold import main, plugins
import tests

def test_main():
    with patch('sys.stdout.write') as mock_write, patch('x_scaffold.main.read_input', return_value='') as mock_input:
        main.execute_scaffold({}, {
            'package': tests.get_fixture('basic')
        }, [], [])
    #mock_write.assert_called_once_with({})
