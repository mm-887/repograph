def flatten_attr(node):
    if node is None:
        return ""
    if node.type == "identifier":
        return node.text.decode("utf-8")
    if node.type == "attribute":
        obj = node.child_by_field_name("object")
        attr = node.child_by_field_name("attribute")
        left = flatten_attr(obj)
        right = flatten_attr(attr)
        if left and right:
            return f"{left}.{right}"
        return left or right
    if node.type == "call":
        return flatten_attr(node.child_by_field_name("function"))
    return node.text.decode("utf-8", "replace")

def traverse(node, entities, file_path, relationships, current_function=None, current_class_name = None, current_class_id = None):
    if node.type == 'module':
        entity_name = str(file_path)
        entities.append({
            'type': 'module',
            'name': entity_name,
            'id': f"{file_path}:{entity_name}:{node.start_point.row}",
            'start_line': node.start_point.row,
            'end_line': node.end_point.row,
            'file': file_path,
            'code': node.text.decode('utf-8',errors='replace')
        })

    if node.type == 'function_definition':
        raw = node.child_by_field_name('name').text.decode('utf-8')
        entity_name = f"{current_class_name}.{raw}" if current_class_name else raw
        entity_id = f"{file_path}:{entity_name}:{node.start_point.row}"
        current_function = entity_id
        entities.append({
            'type': node.type,
            'name': entity_name,
            'id': entity_id,
            'start_line': node.start_point.row,
            'end_line': node.end_point.row,
            "file": file_path,
            'code': node.text.decode('utf-8',errors='replace')
        })
        if current_class_id:
            relationships.append({
                'type': 'defines',
                'from': current_class_id,
                'to': entity_id
            })


    if node.type == 'class_definition':
        class_name = node.child_by_field_name('name').text.decode('utf-8')
        class_id = f"{file_path}:{class_name}:{node.start_point.row}"
        next_class = node.child_by_field_name('name').text.decode('utf-8')
        entities.append({
            'type': node.type,
            'name': next_class,
            'id': class_id,
            'start_line': node.start_point.row,
            'end_line': node.end_point.row,
            "file": file_path,
            'code': node.text.decode('utf-8',errors='replace')
        })
        superclasses_node = node.child_by_field_name('superclasses')
        if superclasses_node:
            for child in superclasses_node.children:
                if child.type not in ('(', ')', ','):
                    base_name = child.text.decode('utf-8', errors='replace')
                    relationships.append({
                        'type': 'inherits',
                        'from': class_id,
                        'to': base_name
                    })


    if node.type == 'call':
        func_node = node.child_by_field_name('function')
        if func_node and current_function:
            relationships.append({
                'type': 'calls',
                'from': current_function,
                'to': flatten_attr(func_node)
            })
    
    if node.type == "function_definition":
        next_function = entity_id
    else:
        next_function = current_function

    if node.type == "import_statement":
        mod_node = node.child_by_field_name('name')
        if mod_node:
            relationships.append({
                'type': 'imports',
                'from': file_path,
                'to': mod_node.text.decode('utf-8')
            })

    elif node.type == "import_from_statement":
        mod_node = node.child_by_field_name('module_name')
        if mod_node:
            relationships.append({
                'type': 'imports',
                'from': file_path,
                'to': mod_node.text.decode('utf-8')
            })

    if node.type == "class_definition":
        next_class_name = node.child_by_field_name('name').text.decode('utf-8')
        next_class_id = f"{file_path}:{next_class_name}:{node.start_point.row}"
    else:
        next_class_name = current_class_name
        next_class_id = current_class_id

    for child in node.children:
        traverse(child, entities, file_path, relationships, next_function, next_class_name, next_class_id)


def extract_entities(tree, file_path):
    entities = []
    relationships = []
    traverse(tree.root_node, entities, file_path, relationships)
    return entities, relationships
