#!/usr/bin/env python
# encoding: utf-8

from workhours.tasks import QUEUES

from collections import namedtuple
Source = namedtuple('Source', ('type','key','url'))

import os.path
def read_queues_from_config(_config, queues=QUEUES):
    """
    read queues from a ConfigParser config that looks like::

        [queue.name1]
        key = path1
        key2 = path2

    :return: (queue_name, key, path) tuples

    """
    # read TaskQueues from config file sections with names listed in
    # QUEUES
    for queue_name in (
        sorted( set(queues.keys()) & set(_config.sections()))):

        for k,v in _config.items(queue_name):
            entry = v.strip()
            values = [str.strip(x) for x in entry.split('\n')]
            for value in values:
                yield Source(queue_name, k, os.path.expanduser(value))
