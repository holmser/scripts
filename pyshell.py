#!/usr/bin/env python
import subprocess
MESSAGES = "tail /var/log/messages"
SPACE = "df -h"

cmds = [MESSAGES, SPACE]
count = 0
for cmd in cmds:
    count +=1
    print "Running command number %s" % count
    subprocess.call(cmd, shell=True)

