import yaml

def gopigo3_simulation_parse_namespace_yaml_file(yaml_source_file_path, yaml_destination_file_path, ns_key='[my_namespace]', ns_val=''):
  with open(yaml_source_file_path, 'r') as f:
    print(f"Replacing '{ns_key}' with '{ns_val}'")
    data = yaml.safe_load(f)
    ns_val_load = ns_val if ns_val == '' else ns_val + '/'
    data = gopigo3_simulation_swap_string_recursively(data, ns_key, ns_val_load)
  with open(yaml_destination_file_path, 'w') as f:
    yaml.safe_dump(data, f, default_flow_style=False)

def gopigo3_simulation_swap_string_recursively(data, old_str, new_str):
  if isinstance(data, dict):
    return {k: gopigo3_simulation_swap_string_recursively(v, old_str, new_str) for k, v in data.items()}
  elif isinstance(data, list):
    return [gopigo3_simulation_swap_string_recursively(item, old_str, new_str) for item in data]
  elif isinstance(data, str):
    return data.replace(old_str, new_str)
  else:
    return data
