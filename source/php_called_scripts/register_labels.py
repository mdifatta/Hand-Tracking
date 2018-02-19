import sys
import os
sys.path.append(os.path.realpath(os.path.join(os.path.split(__file__)[0], "..")))

from php_called_scripts.utils import *

if __name__ == '__main__':
    labels = sys.argv[1]
    frame = sys.argv[2]
    if len(sys.argv) > 2:
        contributor = sys.argv[3].replace(" ", "")
    else:
        contributor = None
    register_labels(labelstring=labels, frame=frame, contributor=contributor)
