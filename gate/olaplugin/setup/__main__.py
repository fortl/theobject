import olaplugin.setup.setup as setup
import pathlib

BASE_DIR = pathlib.Path(__file__).parent.parent

if __name__ == '__main__':
    print(BASE_DIR)
    setup.rewrite_configs()