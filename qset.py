#!/usr/bin/python
# encoding: utf-8

import sys
import os
from subprocess import Popen, PIPE
from workflow import Workflow, ICON_INFO

def main(wf):
    wf.add_item("To ensure your file is found, make sure it ends in '.qvlibrary'", icon=ICON_INFO)
    out, err = Popen(["mdfind","-name",".qvlibrary"], stdout=PIPE, stderr=PIPE).communicate()
    out = out.split("\n")
    for i in out:
        wf.add_item(os.path.split(i)[1],i, arg=i, valid=True, icon="icons/lib.icns")

    wf.send_feedback()

if __name__ == '__main__':
    wf = Workflow()
    # Assign Workflow logger to a global variable, so all module
    # functions can access it without having to pass the Workflow
    # instance around
    log = wf.logger
    sys.exit(wf.run(main))
