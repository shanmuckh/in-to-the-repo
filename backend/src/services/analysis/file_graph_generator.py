import os
import random
from collections import defaultdict
from src.core.logging import get_logger

logger = get_logger(__name__)

# Files that stand in for their directory (`import pkg`, `import './dir'`).
_PACKAGE_ENTRY = ("__init__", "index")


def _strip_ext(path: str) -> str:
    return os.path.splitext(os.path.normpath(path))[0].replace(os.sep, "/")


def _build_resolver(known: set):
    """
    Return a function mapping an import's source_module to a known file (no
    extension), or None. Tries, in order:
      1. the exact path, then pkg/__init__ and dir/index
      2. a unique path suffix of >= 2 segments, so absolute imports in
         src/-layout repos resolve (flask/app -> src/flask/app)
    """
    by_suffix = defaultdict(set)
    for f in known:
        parts = f.split("/")
        if parts[-1] in _PACKAGE_ENTRY and len(parts) > 1:
            parts = parts[:-1]  # src/flask/__init__ is reachable as src/flask
        for i in range(len(parts) - 1):  # suffixes with >= 2 segments
            by_suffix["/".join(parts[i:])].add(f)

    def resolve(module: str):
        m = _strip_ext(module)
        for cand in (m, *(f"{m}/{e}" for e in _PACKAGE_ENTRY)):
            if cand in known:
                return cand
        hits = by_suffix.get(m)
        if hits and len(hits) == 1:
            return next(iter(hits))
        return None

    return resolve


def build_dependency_graph(ast_dict):
    logger.info("Building dependency graph")
    known = {_strip_ext(p) for p in ast_dict}
    resolve = _build_resolver(known)

    def node(fid):
        return {
            "id": fid,
            "data": {"label": os.path.basename(fid)},
            "position": {"x": random.randint(0, 800), "y": random.randint(0, 800)},
        }

    nodes = {}
    edges = {}
    for file_path, file_info in ast_dict.items():
        target = _strip_ext(file_path)
        nodes.setdefault(target, node(target))

        for imp in file_info.get("imports", []):
            if imp["metadata"].get("is_third_party", False):
                continue
            module = imp.get("source_module")
            if not module:
                continue
            source = resolve(module)
            if not source or source == target:
                continue
            edge_id = f"{source}->{target}"
            if edge_id not in edges:  # many `from .x import a, b` lines -> one edge
                edges[edge_id] = {"id": edge_id, "source": source, "target": target, "animated": True}
            nodes.setdefault(source, node(source))

    logger.info(f"Dependency graph built: {len(nodes)} nodes, {len(edges)} edges")
    return {"nodes": list(nodes.values()), "edges": list(edges.values())}
