from typing import Dict, List


class ScaffoldContext(dict):
    notes: List[str] = []
    todos: List[str] = []
    environ: Dict[str, str] = {}
