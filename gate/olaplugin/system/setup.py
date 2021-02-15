import os
import pathlib

BASE_DIR = pathlib.Path(__file__).parent

def rewrite_configs(config):
    path_prefix = str(BASE_DIR / config['platform'])
    for currentpath, folders, files in os.walk(path_prefix):
        for file in files:
            real_path = os.path.join('/', os.path.relpath(currentpath, path_prefix))
            real_path_file = os.path.join(real_path, file)
            print('Write ', real_path_file)
            with open(os.path.join(currentpath, file), 'r') as f:
                text = f.read()
                text = text.format(**config)
                f.close()
            pathlib.Path(real_path).mkdir(parents=True, exist_ok=True)
            with open(real_path_file, 'w') as f:
                f.write(text)
                f.close()
            if real_path == '/etc/wifi-manage-scripts' or file == 'rc.local':
                print('Chmod ', real_path_file)
                os.chmod(real_path_file, 0o755)
    
    