import yaml

def gopigo3_navigation_parse_namespace_yaml_file(yaml_source_file_path, yaml_destination_file_path, ns_key='[my_namespace]', ns_val='', mapns_key='[map_namespace]', mapns_val=''):
  with open(yaml_source_file_path, 'r') as f:
    print(f"Now '{mapns_key}' with '{mapns_val}'")
    data = yaml.safe_load(f)
    ns_val_load = ns_val if ns_val == '' else ns_val + '/'
    data = gopigo3_navigation_swap_string_recursively(data, ns_key, ns_val_load)
    mapns_val_load = mapns_val if mapns_val == '' else mapns_val + '/'
    print(f"Replacing '{mapns_key}' with '{mapns_val_load}'")
    data = gopigo3_navigation_swap_string_recursively(data, mapns_key, mapns_val_load)
    if ns_val != '':
      data[ns_val] = data['my_namespace']
      data.pop('my_namespace', None)
    else:
      data.update(data['my_namespace'].items())
      data.pop('my_namespace', None)
  with open(yaml_destination_file_path, 'w') as f:
    yaml.safe_dump(data, f, default_flow_style=False)

def gopigo3_navigation_swap_string_recursively(data, old_str, new_str):
  if isinstance(data, dict):
    return {k: gopigo3_navigation_swap_string_recursively(v, old_str, new_str) for k, v in data.items()}
  elif isinstance(data, list):
    return [gopigo3_navigation_swap_string_recursively(item, old_str, new_str) for item in data]
  elif isinstance(data, str):
    return data.replace(old_str, new_str)
  else:
    return data
