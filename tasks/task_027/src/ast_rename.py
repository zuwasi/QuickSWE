"""
AST-based variable renamer for Python source code.

Renames a specified variable in a given function scope while respecting
nested scopes that shadow the same variable name.
"""

import ast
import textwrap
from typing import Set, Optional, List, Dict


class ScopeAnalyzer(ast.NodeVisitor):
    """Analyzes variable scopes in Python AST."""

    def __init__(self):
        self.scopes: Dict[str, Set[str]] = {}
        self._current_scope: Optional[str] = None

    def analyze(self, tree: ast.Module) -> Dict[str, Set[str]]:
        self.scopes = {"<module>": set()}
        self._current_scope = "<module>"
        self.visit(tree)
        return self.scopes

    def visit_FunctionDef(self, node: ast.FunctionDef):
        parent_scope = self._current_scope
        scope_name = node.name
        self.scopes[scope_name] = set()

        for arg in node.args.args:
            self.scopes[scope_name].add(arg.arg)

        self._current_scope = scope_name
        self.generic_visit(node)
        self._current_scope = parent_scope

    def visit_Assign(self, node: ast.Assign):
        for target in node.targets:
            if isinstance(target, ast.Name):
                if self._current_scope:
                    self.scopes[self._current_scope].add(target.id)
        self.generic_visit(node)

    def visit_For(self, node: ast.For):
        if isinstance(node.target, ast.Name):
            if self._current_scope:
                self.scopes[self._current_scope].add(node.target.id)
        self.generic_visit(node)


class VariableRenamer(ast.NodeTransformer):
    """Renames a variable in a specific function scope."""

    def __init__(self, target_func: str, old_name: str, new_name: str):
        self.target_func = target_func
        self.old_name = old_name
        self.new_name = new_name
        self._in_target = False
        self._scope_depth = 0

    def rename(self, source: str) -> str:
        tree = ast.parse(textwrap.dedent(source))
        new_tree = self.visit(tree)
        ast.fix_missing_locations(new_tree)
        return ast.unparse(new_tree)

    def visit_FunctionDef(self, node: ast.FunctionDef):
        if node.name == self.target_func and not self._in_target:
            self._in_target = True
            self._scope_depth = 0
            node.args = self._rename_args(node.args)
            self.generic_visit(node)
            self._in_target = False
            return node

        if self._in_target:
            self._scope_depth += 1
            self.generic_visit(node)
            self._scope_depth -= 1
            return node

        return node

    def visit_Name(self, node: ast.Name):
        if self._in_target and node.id == self.old_name:
            node.id = self.new_name
        return node

    def _rename_args(self, args: ast.arguments) -> ast.arguments:
        for arg in args.args:
            if arg.arg == self.old_name:
                arg.arg = self.new_name
        return args

    def visit_arg(self, node: ast.arg):
        if self._in_target and node.arg == self.old_name:
            node.arg = self.new_name
        return node


class BulkRenamer:
    """Performs multiple renames across a source file."""

    def __init__(self):
        self._renames: List[Dict] = []

    def add_rename(self, target_func: str, old_name: str, new_name: str):
        self._renames.append({
            "target_func": target_func,
            "old_name": old_name,
            "new_name": new_name,
        })

    def apply(self, source: str) -> str:
        result = source
        for r in self._renames:
            renamer = VariableRenamer(r["target_func"], r["old_name"], r["new_name"])
            result = renamer.rename(result)
        return result


def find_all_references(source: str, variable_name: str) -> List[int]:
    tree = ast.parse(textwrap.dedent(source))
    refs = []

    class RefFinder(ast.NodeVisitor):
        def visit_Name(self, node):
            if node.id == variable_name:
                refs.append(node.lineno)
            self.generic_visit(node)

    RefFinder().visit(tree)
    return refs


def get_function_locals(source: str, func_name: str) -> Set[str]:
    tree = ast.parse(textwrap.dedent(source))
    analyzer = ScopeAnalyzer()
    scopes = analyzer.analyze(tree)
    return scopes.get(func_name, set())
