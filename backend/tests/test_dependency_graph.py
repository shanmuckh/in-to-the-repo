"""Dependency-graph import resolution (relative, package, src-layout)."""
from src.services.analysis.file_graph_generator import build_dependency_graph
from src.services.analysis.parse_utils import resolve_python_relative


def test_resolve_python_relative():
    assert resolve_python_relative(".ctx", "src/flask/app.py") == "src/flask/ctx"
    assert resolve_python_relative(".", "src/flask/app.py") == "src/flask"
    assert resolve_python_relative("..utils", "pkg/sub/mod.py") == "pkg/utils"
    assert resolve_python_relative(".sansio.app", "src/flask/app.py") == "src/flask/sansio/app"


def _imp(module):
    return {"source_module": module, "metadata": {"is_third_party": False}}


def test_graph_resolves_package_srclayout_and_dedupes():
    ast = {
        "src/flask/__init__.py": {"imports": [_imp("src/flask/app")]},
        "src/flask/app.py": {"imports": [_imp("src/flask/ctx"), _imp("src/flask/ctx"), _imp("os")]},
        "src/flask/ctx.py": {"imports": [_imp("src/flask")]},
        "tests/test_app.py": {"imports": [_imp("flask/app"), _imp("json")]},
        "web/main.ts": {"imports": [_imp("web/components")]},
        "web/components/index.ts": {"imports": []},
    }
    edges = {e["id"] for e in build_dependency_graph(ast)["edges"]}
    assert edges == {
        "src/flask/app->src/flask/__init__",
        "src/flask/ctx->src/flask/app",           # duplicate import collapsed
        "src/flask/__init__->src/flask/ctx",      # `from . import x` -> __init__
        "src/flask/app->tests/test_app",          # absolute import, src/ layout
        "web/components/index->web/main",         # directory import -> index
    }
