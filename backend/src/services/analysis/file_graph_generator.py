import os
import random
from src.core.logging import get_logger

logger = get_logger(__name__)

def build_dependency_graph(ast_dict):
    logger.info("Building dependency graph")
    nodes = {}
    edges = []

    # Normalize and strip extensions from known files
    ast_files_no_ext = {
        os.path.splitext(os.path.normpath(path))[0]
        for path in ast_dict.keys()
    }

    for file_path, file_info in ast_dict.items():
        norm_file_path = os.path.normpath(file_path)
        file = os.path.splitext(norm_file_path)[0]

        # Create node if not already added
        if file not in nodes:
            nodes[file] = {
                "id": file,
                "data": { "label": os.path.basename(file) },
                "position": { "x": random.randint(0, 800), "y": random.randint(0, 800) }
            }

        for import_file in file_info.get("imports", []):
            if not import_file["metadata"].get("is_third_party", False):
                base_dir = os.path.dirname(norm_file_path)
                source_module = import_file.get("source_module")

                if not source_module:
                    continue

                import_path = os.path.normpath(source_module)
                source_file = os.path.splitext(import_path)[0]

                if source_file in ast_files_no_ext:
                    # Add edge  
                    edge_id = f"{source_file}->{file}"
                    edges.append({
                        "id": edge_id,
                        "source": source_file,
                        "target": file,
                        "animated": True
                    })

                    # Ensure source node is also created
                    if source_file not in nodes:
                        nodes[source_file] = {
                            "id": source_file,
                            "data": { "label": os.path.basename(source_file) },
                            "position": { "x": random.randint(0, 800), "y": random.randint(0, 800) }
                        }

    logger.info("React Flow dependency graph built.")
    logger.info(f"Total nodes: {len(nodes)}, Total edges: {len(edges)}")

    return {
        "nodes": list(nodes.values()),
        "edges": edges
    }
