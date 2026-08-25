def traverse(node, entities, file_path, relationships, current_function=None):
    if node.type == 'function_definition':
        entities.append({
            'type': node.type,
            'name': node.child_by_field_name('name').text.decode('utf-8'),
            'start_point': node.start_point,
            'end_point': node.end_point,
            "file": file_path
        })
    elif node.type == 'class_definition':
        entities.append({
            'type': node.type,
            'name': node.child_by_field_name('name').text.decode('utf-8'),
            'start_point': node.start_point,
            'end_point': node.end_point,
            "file": file_path
        })
    if node.type == 'call':
        func_node = node.child_by_field_name('function')
        if func_node and func_node.type == 'identifier' and current_function:
            relationships.append({
                'type': 'calls',
                'from': current_function,
                'to': func_node.text.decode('utf-8')
            })
    if node.type == "function_definition":
        next_function = node.child_by_field_name('name').text.decode('utf-8')
    else:
        next_function = current_function
        
    for child in node.children:
        traverse(child, entities, file_path, relationships, next_function)


def extract_entities(tree, file_path):
    entities = []
    relationships = []
    traverse(tree.root_node, entities, file_path, relationships)
    return entities, relationships