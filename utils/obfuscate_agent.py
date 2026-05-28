import random, string, os, sys

def obfuscate_code(source_path, output_path=None):
    with open(source_path, 'r') as f:
        code = f.read()
    func_names = ['connect', 'get_id', 'load_plugins', 'detect_honeypot']
    var_names = ['BOT_ID', 'C2_URL', 'PLUGIN_DIR', 'plugins']
    mapping = {}
    for name in func_names:
        new_name = ''.join(random.choices(string.ascii_lowercase, k=8))
        code = code.replace(name, new_name)
        mapping[name] = new_name
    for name in var_names:
        new_name = ''.join(random.choices(string.ascii_lowercase, k=8))
        code = code.replace(name, new_name)
        mapping[name] = new_name
    lines = code.split('\n')
    new_lines = []
    for line in lines:
        new_lines.append(line)
        if random.random() < 0.1:
            new_lines.append(f"# {''.join(random.choices(string.ascii_letters, k=20))}")
    output = '\n'.join(new_lines)
    out_path = output_path or source_path + '.obf'
    with open(out_path, 'w') as f:
        f.write(output)
    return out_path

if __name__ == '__main__':
    obfuscate_code('agent.py', 'agent_obfuscated.py')
