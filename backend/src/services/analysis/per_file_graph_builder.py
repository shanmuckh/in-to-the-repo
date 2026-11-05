from collections import defaultdict
import networkx as nx
import os
import random

def build_per_file_graph(file_path: str, file_ast: dict) -> dict:
    nodes = {}
    edges = []

    file = os.path.splitext(file_path)[0]
    # Root node
    nodes[file]= {
        "id": file,
        "data":{"label":os.path.basename(file)},
        "position": {"x":random.randint(0,800), "y":random.randint(0,800)}
    }


    # Functions
    for func in file_ast.get("functions", []):
        name = func["name"]

        func_id = f"{file_path}::function::{name}"
        nodes[func_id] = {
            "id": func_id,
            "data":{"label":func["name"]},
            "position": {"x":random.randint(0,800), "y":random.randint(0,800)}
        }
        edge_id = f"{file}->{func_id}"
        edges.append({
            "id":edge_id,
            "source": file,
            "target": func_id,
            "animated": True
        })

    # Classes and methods
    for cls in file_ast.get("classes", []):
        class_id = f"{file_path}::class::{cls['name']}"
        nodes[class_id] = {
            "id": class_id,
            "data":{"label":cls["name"]},
            "position": {"x":random.randint(0,800), "y":random.randint(0,800)}
        }
        edge_id = f"{file}->{class_id}"
        edges.append({
            "id":edge_id,
            "source": file,
            "target": class_id,
            "animated": True
        })

        for method in cls.get("methods", []):
            method_id = f"{class_id}::method::{method['name']}"
            nodes[method_id] = {
                "id": method_id,
                "data":{"label":method["name"]},
                "position": {"x":random.randint(0,800), "y":random.randint(0,800)}
            }
            edge_id = f"{class_id}->{method_id}"
            edges.append({
                "id":edge_id,
                "source": class_id,
                "target": method_id,
                "animated": True
            })

    return {
        "nodes": list(nodes.values()),
        "edges": edges
    }

def build_call_graph(file_ast, file_path="callgraph"):
    nodes_dict = {}
    edges = []

    calls = file_ast.get("calls", [])
    
    # For generating random positions
    def random_pos():
        return {"x": random.randint(0, 800), "y": random.randint(0, 800)}

    # Track duplicates so that nodes are unique
    for call in calls:
        caller = call.get("caller", "<unknown>")
        callee = call.get("callee", "<unknown>")

        # Create caller node if not exists
        if caller not in nodes_dict:
            nodes_dict[caller] = {
                "id": caller,
                "data": {"label": caller},
                "position": random_pos()
            }
        # Create callee node if not exists
        if callee not in nodes_dict:
            nodes_dict[callee] = {
                "id": callee,
                "data": {"label": callee},
                "position": random_pos()
            }

        # Create edge id uniquely
        edge_id = f"{caller}->{callee}"

        edges.append({
            "id": edge_id,
            "source": caller,
            "target": callee,
            "animated": True,
            "type": "calls"
        })

    nodes = list(nodes_dict.values())

    return {
        "nodes": nodes,
        "edges": edges
    }