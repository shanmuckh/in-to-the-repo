language_node_maps = {
    "python": {
        "imports": ["import_statement", "import_from_statement"],
        "classes": ["class_definition"],
        "functions": ["function_definition"],
        "variables": ["assignment"],
        "calls": ["call"],
        "control_flow": ["if_statement", "for_statement", "while_statement", "try_statement"],
        "returns": ["return_statement"],
        "decorators": ["decorator"],
        "types": ["type_alias", "type_argument"],
        "async": ["async_statement"]
    },
    "javascript": {
        "imports": ["import_declaration", "import_statement"],
        "classes": ["class_declaration"],
        "functions": ["function_declaration", "arrow_function"],
        "variables": ["variable_declarator"],
        "calls": ["call_expression"],
        "control_flow": ["if_statement", "for_statement", "while_statement", "try_statement"],
        "returns": ["return_statement"],
        "jsx": ["jsx_element", "jsx_self_closing_element"],
        "promises": ["await_expression"]
    },
    "typescript": {
        "imports": ["import_statement"],
        "classes": ["class_declaration"],
        "functions": ["function_declaration", "arrow_function"],
        "interfaces": ["interface_declaration"],
        "types": ["type_alias_declaration"],
        "decorators": ["decorator"],
        "generics": ["type_parameter"],
        "calls": ["call_expression"]  # same as JS
    },
    "tsx": {
        "imports": ["import_statement"],
        "classes": ["class_declaration"],
        "functions": ["function_declaration", "arrow_function"],
        "interfaces": ["interface_declaration"],
        "types": ["type_alias_declaration"],
        "decorators": ["decorator"],
        "generics": ["type_parameter"],
        "calls": ["call_expression"],
        "jsx": ["jsx_element", "jsx_self_closing_element"],
    },
    "java": {
        "imports": ["import_declaration"],
        "classes": ["class_declaration"],
        "methods": ["method_declaration"],
        "variables": ["field_declaration"],
        "annotations": ["annotation"],
        "exceptions": ["throw_statement"],
        "generics": ["type_parameter"],
        "calls": ["method_invocation"]  # <-- added
    },
    "cpp": {
        "includes": ["preproc_include"],
        "classes": ["class_specifier"],
        "functions": ["function_definition"],
        "templates": ["template_declaration"],
        "namespaces": ["namespace_definition"],
        "macros": ["preproc_def"],
        "calls": ["call_expression"]  # add calls for function calls in C++
    },
    "c": {
        "includes": ["preproc_include"],
        "functions": ["function_definition"],
        "structs": ["struct_specifier"],
        "macros": ["preproc_def"],
        "pointers": ["pointer_declarator"],
        "calls": ["call_expression"]  # add calls for C
    }
}
