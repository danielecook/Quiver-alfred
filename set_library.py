#!/usr/bin/python
# encoding: utf-8

import sys
from workflow import Workflow

file_loc = ' '.join(sys.argv[1:])
wf = Workflow()
wf.store_data('library_location', file_loc)

print file_loc