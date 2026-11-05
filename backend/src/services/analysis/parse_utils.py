import os
from typing import Optional

def is_third_party_module(module_name, language):
    """Determine if a module is third-party based on language-specific patterns."""
    if not module_name:
        return False
        
    if language in {"python", "javascript", "typescript", "tsx"}:   
        return False
    
    elif language == "java":
        return not (module_name.startswith("java.") or 
                   module_name.startswith("javax.") or
                   module_name.startswith("com.sun.") or
                   module_name.startswith("com.oracle."))
    
    elif language in {"c", "cpp"}:
        if module_name.startswith("<") and module_name.endswith(">"):
            return False
        return "/" in module_name or "\\" in module_name
    
    return False  


def extract_import_data(node, code, language, current_file_path: Optional[str] = None):

    import_info = {
        "content": code[node.start_byte:node.end_byte],
        "start_line": node.start_point[0] + 1,
        "source_module": None, 
        "imported_items": [],
        "metadata": {
            "type": None,
            "is_third_party": False
        }
    }

    if language == "python":
        if node.type == 'import_from_statement':
            import_info["metadata"]["type"] = "from_import"
            
            module_node = node.child_by_field_name("module_name")
            if module_node:
                module = module_node.text.decode()
                
                if module.startswith(('.', '..')):
                    if current_file_path:
                        current_dir_rel = os.path.dirname(current_file_path)
                        dummy_root = "/repo_root_placeholder" 
                        temp_current_dir_abs = os.path.join(dummy_root, current_dir_rel)
                        temp_resolved_module_path_abs = os.path.abspath(os.path.join(temp_current_dir_abs, module))
                        resolved_module_path_rel = os.path.relpath(temp_resolved_module_path_abs, dummy_root)
                        
                        import_info["source_module"] = resolved_module_path_rel.replace(os.sep, "/")
                        import_info["metadata"]["is_third_party"] = False # Relative imports are always first-party
                    else:
                        print(f"Warning: Missing current_file_path for relative Python import '{module}'")
                        import_info["source_module"] = module.replace(".", "/") 
                        import_info["metadata"]["is_third_party"] = False
                else:
                    # Absolute import (e.g., 'Stark.config' or 'os')
                    import_info["source_module"] = module.replace(".", "/")
                    import_info["metadata"]["is_third_party"] = is_third_party_module(module, language)

            import_list_node = node.child_by_field_name("name")
            if import_list_node:
                if import_list_node.type == "dotted_name":
                    import_info["imported_items"].append(import_list_node.text.decode())
                elif import_list_node.type == "aliased_import":
                    name = import_list_node.child_by_field_name("name")
                    alias = import_list_node.child_by_field_name("alias")
                    if name:
                        item = name.text.decode()
                        if alias:
                            item += f" as {alias.text.decode()}"
                        import_info["imported_items"].append(item)
                elif import_list_node.type == "wildcard_import":
                    import_info["imported_items"].append("*")
                elif import_list_node.type == "parenthesized_list":
                    for child_item in import_list_node.children:
                        if child_item.type == "import_as_name":
                            name = child_item.child_by_field_name("name")
                            alias = child_item.child_by_field_name("alias")
                            if name:
                                item = name.text.decode()
                                if alias:
                                    item += f" as {alias.text.decode()}"
                                import_info["imported_items"].append(item)
                        elif child_item.type == "identifier":
                            import_info["imported_items"].append(child_item.text.decode())
            
            # Additional check for children 
            for child in node.children:
                if child.type in ["aliased_import", "import_as_name"]:
                    name_node = child.child_by_field_name("name")
                    if name_node and name_node.text.decode() not in import_info["imported_items"]:
                        import_info["imported_items"].append(name_node.text.decode())
                elif child.type == "identifier" and \
                     (child.parent.type == "import_list" or child.parent.type == "import_from_statement") and \
                     child.text.decode() not in import_info["imported_items"] and \
                     child != module_node:
                    import_info["imported_items"].append(child.text.decode())
                elif child.type == "wildcard_import" and "*" not in import_info["imported_items"]:
                    import_info["imported_items"].append("*")


        elif node.type == 'import_statement':
            import_info["metadata"]["type"] = "direct_import"
            
            for child in node.children:
                if child.type == "dotted_name": # e.g., 'import os', 'import package.module'
                    module = child.text.decode()
                    import_info["source_module"] = module.replace(".", "/")
                    import_info["metadata"]["is_third_party"] = is_third_party_module(module, language)

                    import_info["imported_items"].append(module) 
                elif child.type == "aliased_import": # e.g., 'import numpy as np'
                    name_node = child.child_by_field_name("name")
                    alias_node = child.child_by_field_name("alias")
                    if name_node:
                        module = name_node.text.decode()
                        import_info["source_module"] = module.replace(".", "/")
                        import_info["metadata"]["is_third_party"] = is_third_party_module(module, language)
                        item = module
                        if alias_node:
                            item += f" as {alias_node.text.decode()}"
                        import_info["imported_items"].append(item)
            
    elif language in {"javascript", "tsx", "typescript"}:
        # Existing JavaScript/TypeScript implementation
        if node.type in ["import_statement", "import_require_clause", "import_call"]:
            import_info["metadata"]["type"] = "es_module_import"
            for child in node.children:
                if child.type == 'string':
                    module = child.text.decode().strip('"').strip("'")
                    
                    if module.startswith(('.', '..')) and current_file_path:
                        current_dir_rel = os.path.dirname(current_file_path)
                        dummy_root = "/repo_root_placeholder" 
                        temp_current_dir_abs = os.path.join(dummy_root, current_dir_rel)
                        temp_resolved_module_path_abs = os.path.abspath(os.path.join(temp_current_dir_abs, module))
                        resolved_module_path_rel = os.path.relpath(temp_resolved_module_path_abs, dummy_root)
                        
                        import_info["source_module"] = resolved_module_path_rel.replace(os.sep, "/")
                        import_info["metadata"]["is_third_party"] = False # Relative imports are always first-party
                    else:
                        import_info["source_module"] = module
                        import_info["metadata"]["is_third_party"] = is_third_party_module(module, language)

                elif child.type == 'import_clause':
                    # Logic for extracting imported_items and metadata.type remains unchanged
                    for sub in child.children:
                        if sub.type == 'identifier':
                            import_info["imported_items"].append(sub.text.decode())
                            if not import_info["metadata"]["type"]:
                                import_info["metadata"]["type"] = 'default'
                        elif sub.type == 'named_imports':
                            import_info["metadata"]["type"] = 'named'
                            for ni in sub.named_children:
                                if ni.type == 'import_specifier':
                                    name_node = ni.child_by_field_name('name')
                                    alias_node = ni.child_by_field_name('alias')
                                    if name_node:
                                        item = name_node.text.decode()
                                        if alias_node:
                                            item += f" as {alias.text.decode()}"
                                        import_info["imported_items"].append(item)
                        elif sub.type == 'namespace_import':
                            import_info["metadata"]["type"] = 'namespace'
                            as_node = sub.child_by_field_name('name')
                            if as_node:
                                import_info["imported_items"].append('* as ' + as_node.text.decode())
                elif node.type == "import_call": # Dynamic imports
                    import_info["metadata"]["type"] = "dynamic_import"
                    for arg_child in child.children:
                        if arg_child.type == "string":
                            module = arg_child.text.decode().strip('"').strip("'")
                            if module.startswith(('.', '..')) and current_file_path:
                                current_dir_rel = os.path.dirname(current_file_path)
                                dummy_root = "/repo_root_placeholder" 
                                temp_current_dir_abs = os.path.join(dummy_root, current_dir_rel)
                                temp_resolved_module_path_abs = os.path.abspath(os.path.join(temp_current_dir_abs, module))
                                resolved_module_path_rel = os.path.relpath(temp_resolved_module_path_abs, dummy_root)
                                import_info["source_module"] = resolved_module_path_rel.replace(os.sep, "/")
                                import_info["metadata"]["is_third_party"] = False
                            else:
                                import_info["source_module"] = module
                                import_info["metadata"]["is_third_party"] = is_third_party_module(module, language)
                            break # Assume first string argument is the module path


    elif language == "java":
        # Java import parsing
        if node.type == "import_declaration":
            import_info["metadata"]["type"] = "java_import"
            for child in node.children:
                if child.type == "scoped_identifier":
                    module_parts = []
                    for part in child.children:
                        if part.type == "identifier":
                            module_parts.append(part.text.decode())
                    full_logical_path = ".".join(module_parts)
                    
                    # Convert logical Java path to a file-system-like path relative to repo root
                    # e.g., "com.example.MyClass" -> "com/example/MyClass"
                    import_info["source_module"] = full_logical_path.replace(".", "/")
                    import_info["metadata"]["is_third_party"] = is_third_party_module(full_logical_path, language)

                    # Check if it's a wildcard import 
                    if child.children and child.children[-1].type == "asterisk":
                        import_info["imported_items"].append("*")
                        import_info["metadata"]["type"] = "wildcard"
                    else:
                        import_info["imported_items"].append(module_parts[-1])
                    
                elif child.type == "asterisk": # This might be a redundant check for wildcard if scoped_identifier handles it
                    import_info["imported_items"].append("*")
                    import_info["metadata"]["type"] = "wildcard"

    elif language in {"c", "cpp"}:
        # C/C++ include parsing
        if node.type == "preproc_include":
            import_info["metadata"]["type"] = "include"
            for child in node.children:
                if child.type == "string_literal":
                    header = child.text.decode().strip('"')
                    # For quoted includes, source_module is the path relative to the current file.
                    # We need to resolve this to be relative to the repo root.
                    if current_file_path:
                        current_dir_rel = os.path.dirname(current_file_path)
                        resolved_header_path = os.path.normpath(os.path.join(current_dir_rel, header))
                        import_info["source_module"] = resolved_header_path.replace(os.sep, "/")
                    else:
                        import_info["source_module"] = header # Fallback if current_file_path is missing
                    import_info["metadata"]["is_third_party"] = is_third_party_module(header, language) # Check original header name

                elif child.type == "system_lib_string":
                    header = child.text.decode().strip("<>")
                    # For angle-bracket includes, source_module is just the header name
                    import_info["source_module"] = header
                    import_info["metadata"]["is_third_party"] = is_third_party_module(header, language)
            
            # For C/C++, the imported item is typically the entire header (logic unchanged)
            if import_info["source_module"]:
                import_info["imported_items"].append(import_info["source_module"])

    return import_info if import_info["source_module"] or import_info["imported_items"] else None

