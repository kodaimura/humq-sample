import ast
from pathlib import Path
import unittest


APP_ROOT = Path(__file__).parents[1] / "app"
USECASE_ROOT = APP_ROOT / "usecase"


def imported_modules(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(), filename=str(path))
    modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            modules.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            modules.add(node.module)
    return modules


def parsed(path: Path) -> ast.AST:
    return ast.parse(path.read_text(), filename=str(path))


def called_methods(path: Path) -> set[str]:
    methods: set[str] = set()
    for node in ast.walk(parsed(path)):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            methods.add(node.func.attr)
    return methods


def attribute_path(node: ast.AST) -> tuple[str, ...]:
    parts: list[str] = []
    while isinstance(node, ast.Attribute):
        parts.append(node.attr)
        node = node.value
    if isinstance(node, ast.Name):
        parts.append(node.id)
    return tuple(reversed(parts))


def assignment_targets(node: ast.AST) -> list[ast.AST]:
    if isinstance(node, ast.Assign):
        return node.targets
    if isinstance(node, (ast.AnnAssign, ast.AugAssign)):
        return [node.target]
    return []


def usecase_implementation_files() -> list[Path]:
    return [
        path
        for path in sorted(USECASE_ROOT.rglob("*.py"))
        if path.name not in {"__init__.py", "_policies.py"}
    ]


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
        internal_imports: list[str] = []
        for path in sorted((APP_ROOT / "handler").rglob("*.py")):
            for imported in imported_modules(path):
                if imported.endswith(("_policies", "_operations")):
                    internal_imports.append(
                        f"{path.relative_to(APP_ROOT)} -> {imported}"
                    )
        self.assertEqual(internal_imports, [])

    def test_handlers_do_not_access_the_database_directly(self):
        violations: list[str] = []
        database_methods = {
            "add",
            "add_all",
            "begin",
            "commit",
            "delete",
            "execute",
            "flush",
            "get",
            "merge",
            "refresh",
            "rollback",
            "scalar",
            "scalars",
        }
        for path in sorted((APP_ROOT / "handler").rglob("*.py")):
            for node in ast.walk(parsed(path)):
                if not isinstance(node, ast.Call) or not isinstance(
                    node.func, ast.Attribute
                ):
                    continue
                call_path = attribute_path(node.func)
                if (
                    len(call_path) >= 2
                    and call_path[-2] in {"db", "session"}
                    and call_path[-1] in database_methods
                ):
                    violations.append(
                        f"{path.relative_to(APP_ROOT)}:{node.lineno} -> "
                        f"{'.'.join(call_path)}()"
                    )
        self.assertEqual(violations, [])

    def test_modules_do_not_depend_on_usecases_or_queries(self):
        self.assert_tree_does_not_import("module", ("app.usecase", "app.query"))

    def test_modules_stay_with_one_table_and_do_not_commit(self):
        violations: list[str] = []
        for path in sorted((APP_ROOT / "module").glob("*/module.py")):
            for node in ast.walk(parsed(path)):
                if isinstance(node, ast.ImportFrom):
                    imported = node.module or ""
                    if (
                        imported.startswith("app.module")
                        and imported != "app.module.business_types"
                    ):
                        violations.append(
                            f"{path.relative_to(APP_ROOT)}:{node.lineno} -> {imported}"
                        )
                    if node.level > 1 or (
                        node.level == 1 and imported not in {"model"}
                    ):
                        violations.append(
                            f"{path.relative_to(APP_ROOT)}:{node.lineno} -> relative import"
                        )
            for method in called_methods(path) & {"begin", "commit", "rollback"}:
                violations.append(f"{path.relative_to(APP_ROOT)} -> {method}()")
        self.assertEqual(violations, [])

    def test_queries_do_not_depend_on_usecases(self):
        self.assert_tree_does_not_import("query", ("app.usecase",))

    def test_queries_are_read_only(self):
        violations: list[str] = []
        forbidden_calls = {
            "add",
            "add_all",
            "begin",
            "commit",
            "delete",
            "flush",
            "merge",
            "rollback",
        }
        forbidden_sql = {"delete", "insert", "update"}
        for path in sorted((APP_ROOT / "query").rglob("*.py")):
            tree = parsed(path)
            for node in ast.walk(tree):
                if isinstance(node, ast.ImportFrom) and node.module == "sqlalchemy":
                    for alias in node.names:
                        if alias.name in forbidden_sql:
                            violations.append(
                                f"{path.relative_to(APP_ROOT)}:{node.lineno} -> {alias.name}"
                            )
                if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
                    if node.func.attr in forbidden_calls:
                        violations.append(
                            f"{path.relative_to(APP_ROOT)}:{node.lineno} -> {node.func.attr}()"
                        )
                for target in assignment_targets(node):
                    if not isinstance(target, ast.Attribute):
                        continue
                    target_path = attribute_path(target)
                    if target_path and target_path[0] != "self":
                        violations.append(
                            f"{path.relative_to(APP_ROOT)}:{node.lineno} -> {'.'.join(target_path)}"
                        )
        self.assertEqual(violations, [])

    def test_policy_is_not_a_standalone_layer(self):
        policy_files = list((APP_ROOT / "policy").glob("*.py"))
        self.assertEqual(policy_files, [])
        self.assert_tree_does_not_import(".", ("app.policy",))

    def test_internal_files_use_private_module_names(self):
        public_internal_files = [
            str(path.relative_to(APP_ROOT))
            for path in USECASE_ROOT.rglob("*.py")
            if path.name in {"policies.py", "operations.py"}
        ]
        internal_directories = [
            str(path.relative_to(APP_ROOT))
            for path in USECASE_ROOT.rglob("*")
            if path.is_dir() and path.name in {"operations", "steps"}
        ]
        self.assertEqual(public_internal_files, [])
        self.assertEqual(internal_directories, [])
        self.assertFalse((USECASE_ROOT / "_operations.py").exists())

    def test_policies_are_pure(self):
        violations: list[str] = []
        for path in sorted(USECASE_ROOT.rglob("_policies.py")):
            for imported in imported_modules(path):
                imports_runtime_dependency = imported.startswith(
                    (
                        "sqlalchemy",
                        "app.client",
                        "app.integration",
                        "app.query",
                        "app.core.database",
                        "app.core.mailer",
                    )
                ) or (
                    imported.startswith("app.module")
                    and imported != "app.module.business_types"
                )
                if imports_runtime_dependency:
                    violations.append(f"{path.relative_to(APP_ROOT)} -> {imported}")
            for method in called_methods(path) & {
                "begin",
                "commit",
                "rollback",
                "flush",
            }:
                violations.append(f"{path.relative_to(APP_ROOT)} -> {method}()")
        self.assertEqual(violations, [])

    def test_operations_join_the_calling_usecase_transaction(self):
        violations: list[str] = []
        for path in sorted(USECASE_ROOT.rglob("_operations.py")):
            tree = parsed(path)
            for imported in imported_modules(path):
                if imported.endswith("_operations") or imported.startswith(
                    ("app.client", "app.integration")
                ):
                    violations.append(f"{path.relative_to(APP_ROOT)} -> {imported}")
            for method in called_methods(path) & {"begin", "commit", "rollback"}:
                violations.append(f"{path.relative_to(APP_ROOT)} -> {method}()")
            for node in ast.walk(tree):
                if not isinstance(node, ast.ClassDef) or node.name.startswith("_"):
                    continue
                methods = {
                    child.name
                    for child in node.body
                    if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef))
                }
                if not node.name.endswith("Operation"):
                    violations.append(f"{path.relative_to(APP_ROOT)} -> {node.name}")
                if "run" not in methods or "execute" in methods:
                    violations.append(
                        f"{path.relative_to(APP_ROOT)} -> {node.name} methods"
                    )
        self.assertEqual(violations, [])

    def test_usecases_do_not_import_other_usecases(self):
        violations: list[str] = []
        for path in sorted(USECASE_ROOT.rglob("*.py")):
            if path.name in {"_policies.py", "_operations.py"}:
                continue
            for node in ast.walk(parsed(path)):
                if not isinstance(node, ast.ImportFrom):
                    continue
                if not (node.level or (node.module or "").startswith("app.usecase")):
                    continue
                for alias in node.names:
                    if alias.name.endswith("Usecase"):
                        violations.append(
                            f"{path.relative_to(APP_ROOT)} -> {alias.name}"
                        )
        self.assertEqual(violations, [])

    def test_usecases_delegate_orm_persistence_to_modules(self):
        violations: list[str] = []
        persistence_methods = {
            "add",
            "add_all",
            "delete",
            "execute",
            "flush",
            "get",
            "merge",
            "refresh",
            "scalar",
            "scalars",
        }
        for path in usecase_implementation_files():
            tree = parsed(path)
            imported_model_names: set[str] = set()
            for node in ast.walk(tree):
                if not isinstance(node, ast.ImportFrom):
                    continue
                imported = node.module or ""
                allowed_sqlalchemy_imports = {
                    "sqlalchemy.exc": {"IntegrityError"},
                    "sqlalchemy.orm": {"Session"},
                }
                if imported.startswith("sqlalchemy") and not (
                    imported in allowed_sqlalchemy_imports
                    and all(
                        alias.name in allowed_sqlalchemy_imports[imported]
                        for alias in node.names
                    )
                ):
                    violations.append(
                        f"{path.relative_to(APP_ROOT)}:{node.lineno} -> {imported}"
                    )
                if (
                    not imported.startswith("app.module")
                    or imported == "app.module.business_types"
                ):
                    continue
                imported_model_names.update(
                    alias.asname or alias.name
                    for alias in node.names
                    if not alias.name.endswith("Module")
                )

            for node in ast.walk(tree):
                if isinstance(node, ast.Call):
                    if isinstance(node.func, ast.Attribute):
                        call_path = attribute_path(node.func)
                        if (
                            len(call_path) >= 2
                            and call_path[-2] in {"db", "session"}
                            and call_path[-1] in persistence_methods
                        ):
                            violations.append(
                                f"{path.relative_to(APP_ROOT)}:{node.lineno} -> "
                                f"{'.'.join(call_path)}()"
                            )
                    elif (
                        isinstance(node.func, ast.Name)
                        and node.func.id in imported_model_names
                    ):
                        violations.append(
                            f"{path.relative_to(APP_ROOT)}:{node.lineno} -> "
                            f"constructs {node.func.id}"
                        )
                for target in assignment_targets(node):
                    if not isinstance(target, ast.Attribute):
                        continue
                    target_path = attribute_path(target)
                    if target_path and target_path[0] != "self":
                        violations.append(
                            f"{path.relative_to(APP_ROOT)}:{node.lineno} -> "
                            f"mutates {'.'.join(target_path)}"
                        )
        self.assertEqual(violations, [])

    def test_usecases_do_not_dispatch_unrelated_actions(self):
        violations: list[str] = []
        for path in usecase_implementation_files():
            for node in ast.walk(parsed(path)):
                if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    continue
                if node.name != "execute":
                    continue
                argument_names = {
                    argument.arg
                    for argument in [*node.args.args, *node.args.kwonlyargs]
                }
                if "action" in argument_names:
                    violations.append(
                        f"{path.relative_to(APP_ROOT)}:{node.lineno} -> action"
                    )
        self.assertEqual(violations, [])

    def test_internal_modules_are_not_reexported(self):
        violations: list[str] = []
        for path in sorted(USECASE_ROOT.rglob("__init__.py")):
            for imported in imported_modules(path):
                if imported.endswith(("_policies", "_operations")):
                    violations.append(f"{path.relative_to(APP_ROOT)} -> {imported}")
        self.assertEqual(violations, [])


if __name__ == "__main__":
    unittest.main()
