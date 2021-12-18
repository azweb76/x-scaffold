from getpass import getpass
from typing import Dict, List


class ScaffoldRuntime:
    def log(self, message: str):
        pass

    def ask(self, prompt):
        pass

class ScaffoldConsoleRuntime(ScaffoldRuntime):
     def ask(self, prompt):
         description = prompt.get('description')
         if prompt.get('secure', False):
             return getpass(prompt=description)
         else:
            return input(description)
