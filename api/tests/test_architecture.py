import ast
from pathlib import Path
import unittest


APP_ROOT = Path(__file__).parents[1] / "app"


def imported_modules(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(), filename=str(path))
    modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            modules.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            modules.add(node.module)
    return modules


class HumqDependencyTest(unittest.TestCase):
    def assert_tree_does_not_import(self, directory: str, forbidden: tuple[str, ...]):
        violations: list[str] = []
        for path in sorted((APP_ROOT / directory).rglob("*.py")):
            for imported in imported_modules(path):
                if imported.startswith(forbidden):
                    violations.append(f"{path.relative_to(APP_ROOT)} -> {imported}")
        self.assertEqual(violations, [])

    def test_handlers_only_enter_business_logic_through_usecases(self):
        self.assert_tree_does_not_import("handler", ("app.module", "app.query"))

    def test_modules_do_not_depend_on_usecases_or_queries(self):
        self.assert_tree_does_not_import("module", ("app.usecase", "app.query"))

    def test_queries_do_not_depend_on_usecases(self):
        self.assert_tree_does_not_import("query", ("app.usecase",))

    def test_policy_is_not_a_standalone_layer(self):
        policy_files = list((APP_ROOT / "policy").glob("*.py"))
        self.assertEqual(policy_files, [])
        self.assert_tree_does_not_import(".", ("app.policy",))


if __name__ == "__main__":
    unittest.main()
