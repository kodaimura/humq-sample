"""Structural architecture guardrails for humq-sample.

This suite contains both:

1. Core HUMQ architectural rules
2. Additional conventions adopted by humq-sample

Rules such as one Usecase class per file, the ``*Usecase`` naming convention,
the ``execute()`` entry point, and the ``@transactional`` marker are
sample-specific conventions and are not mandatory requirements of HUMQ itself.

These AST checks detect common structural violations. They do not prove that an
implementation is semantically correct or completely HUMQ-compliant; raw SQL,
external database objects, and responsibilities hidden behind misleading names
still require design review.
"""

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
        if path.name != "__init__.py" and not path.stem.startswith("_")
    ]


def public_usecase_files() -> list[Path]:
    return [
        path
        for path in sorted(USECASE_ROOT.rglob("*.py"))
        if path.name != "__init__.py" and not path.stem.startswith("_")
    ]


class CoreHumqRulesTest(unittest.TestCase):
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
                if imported.endswith(("_policies", "_operations", "_transaction")):
                    internal_imports.append(
                        f"{path.relative_to(APP_ROOT)} -> {imported}"
                    )
        self.assertEqual(internal_imports, [])

    def test_handler_usecases_live_in_the_matching_resource_directory(self):
        violations: list[str] = []
        for path in sorted((APP_ROOT / "handler").glob("*.py")):
            if path.name == "__init__.py" or path.stem.startswith("_"):
                continue
            for node in ast.walk(parsed(path)):
                if not isinstance(node, ast.ImportFrom) or not node.module:
                    continue
                prefix = "app.usecase."
                if not node.module.startswith(prefix):
                    continue
                imported_usecases = [
                    alias.name for alias in node.names if alias.name.endswith("Usecase")
                ]
                if not imported_usecases:
                    continue
                resource = node.module.removeprefix(prefix).split(".", maxsplit=1)[0]
                if resource != path.stem:
                    violations.append(
                        f"{path.relative_to(APP_ROOT)}:{node.lineno} -> "
                        f"{node.module} imports {', '.join(imported_usecases)}"
                    )
        self.assertEqual(violations, [])

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
                if imported.endswith(("_policies", "_operations", "_transaction")):
                    violations.append(f"{path.relative_to(APP_ROOT)} -> {imported}")
        self.assertEqual(violations, [])


class HumqSampleConventionsTest(unittest.TestCase):
    def test_public_usecase_files_define_one_primary_flow(self):
        violations: list[str] = []
        for path in public_usecase_files():
            usecase_classes = [
                node
                for node in parsed(path).body
                if isinstance(node, ast.ClassDef) and node.name.endswith("Usecase")
            ]
            if len(usecase_classes) != 1:
                violations.append(
                    f"{path.relative_to(APP_ROOT)} -> "
                    f"{len(usecase_classes)} public Primary Flows"
                )
                continue
            execute_methods = [
                node
                for node in usecase_classes[0].body
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
                and node.name == "execute"
            ]
            if len(execute_methods) != 1:
                violations.append(
                    f"{path.relative_to(APP_ROOT)} -> "
                    f"{usecase_classes[0].name} has {len(execute_methods)} execute methods"
                )
        self.assertEqual(violations, [])

    def test_state_changing_usecases_declare_transaction_boundary(self):
        violations: list[str] = []
        for path in public_usecase_files():
            tree = parsed(path)
            usecase_classes = [
                node
                for node in tree.body
                if isinstance(node, ast.ClassDef) and node.name.endswith("Usecase")
            ]
            if len(usecase_classes) != 1:
                continue
            usecase_class = usecase_classes[0]
            owns_session = any(
                isinstance(target, ast.Attribute)
                and attribute_path(target) == ("self", "db")
                for node in ast.walk(usecase_class)
                for target in assignment_targets(node)
            )
            execute_methods = [
                node
                for node in usecase_class.body
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
                and node.name == "execute"
            ]
            if len(execute_methods) != 1:
                continue
            execute = execute_methods[0]
            decorators = {
                attribute_path(decorator)[-1]
                for decorator in execute.decorator_list
                if attribute_path(decorator)
            }
            if owns_session and "transactional" not in decorators:
                violations.append(
                    f"{path.relative_to(APP_ROOT)} -> missing @transactional"
                )
            if not owns_session and "transactional" in decorators:
                violations.append(
                    f"{path.relative_to(APP_ROOT)} -> read flow is @transactional"
                )
            for method in called_methods(path) & {"commit", "rollback"}:
                violations.append(
                    f"{path.relative_to(APP_ROOT)} -> calls {method}() directly"
                )
        self.assertEqual(violations, [])

    def test_schema_declares_no_implicit_cross_table_writes(self):
        violations: list[str] = []
        schema_files = [
            *sorted((APP_ROOT / "module").rglob("model.py")),
            *sorted((APP_ROOT / "alembic" / "versions").glob("*.py")),
        ]
        for path in schema_files:
            source = path.read_text()
            normalized = " ".join(source.lower().split())
            for marker in (
                "create trigger",
                "on delete cascade",
                "on update cascade",
            ):
                if marker in normalized:
                    violations.append(
                        f"{path.relative_to(APP_ROOT)} -> contains {marker}"
                    )
            for node in ast.walk(parsed(path)):
                if not isinstance(node, ast.Call):
                    continue
                call_path = attribute_path(node.func)
                call_name = call_path[-1] if call_path else ""
                if call_name in {"ForeignKey", "ForeignKeyConstraint"}:
                    for keyword in node.keywords:
                        if keyword.arg not in {"ondelete", "onupdate"}:
                            continue
                        action = (
                            keyword.value.value.upper()
                            if isinstance(keyword.value, ast.Constant)
                            and isinstance(keyword.value.value, str)
                            else None
                        )
                        if action not in {"NO ACTION", "RESTRICT"}:
                            violations.append(
                                f"{path.relative_to(APP_ROOT)}:{node.lineno} -> "
                                f"{keyword.arg}={action or 'dynamic'}"
                            )
                if call_name == "relationship":
                    for keyword in node.keywords:
                        if keyword.arg != "cascade":
                            continue
                        cascade = (
                            keyword.value.value.lower()
                            if isinstance(keyword.value, ast.Constant)
                            and isinstance(keyword.value.value, str)
                            else "dynamic"
                        )
                        if "delete" in cascade or cascade == "dynamic":
                            violations.append(
                                f"{path.relative_to(APP_ROOT)}:{node.lineno} -> "
                                f"relationship cascade={cascade}"
                            )
        self.assertEqual(violations, [])

    def test_usecases_do_not_use_assert_for_business_preconditions(self):
        violations = [
            f"{path.relative_to(APP_ROOT)}:{node.lineno}"
            for path in public_usecase_files()
            for node in ast.walk(parsed(path))
            if isinstance(node, ast.Assert)
        ]
        self.assertEqual(violations, [])


if __name__ == "__main__":
    unittest.main()
