import pathlib
import sys
BASE_DIR = pathlib.Path(__file__).parent.parent
sys.path.append(BASE_DIR.__str__())
import olaplugin.server as server

if __name__ == '__main__':
    server.run()