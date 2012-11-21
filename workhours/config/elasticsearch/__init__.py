#!/usr/bin/env python
# encoding: utf-8
from __future__ import print_function

import jinja2
from jinja2 import Template
import os.path

#template_path = os.path.join(
#        os.path.abspath(os.path.dirname(__file__)),
#        'elasticsearch.yml.jinja2')

DEFAULT_CONTEXT = {
    "etcdir":"/etc/elasticsearch" ,
    "datadir": "/var/lib/elasticsearch",
    "tmpdir": "/tmp/elasticsearch",
    "logdir": "/var/log/elasticsearch",
    "plugindir": "/usr/share/elasticsearch/plugins",
    "transport_tcp_port": 9300,
    "http_port": 9200,
    "disable_http": False,

    "number_of_shards": 5,
    "number_of_replicas": 1,

    "multicast_enabled": "true"
}

def get_local_context():
    hours_path=os.environ.get('VIRTUAL_ENV')
    hours_context = {
        "etcdir": os.path.join(hours_path, "etc/elasticsearch" ),
        "datadir": os.path.join(hours_path, "var/lib/elasticsearch"),
        "tmpdir": os.path.join(hours_path, "tmp/elasticsearch"),
        "logdir": os.path.join(hours_path, "var/log/elasticsearch"),
        "plugindir": "/usr/share/elasticsearch/plugins",
        "transport_tcp_port": 9500,
        "http_port": 9600,
        "disable_http": False,

        "number_of_shards": 1,
        "number_of_replicas": 0,

        "multicast_enabled": "false",
    }
    return hours_context

TEMPLATE_PATH = os.path.abspath(os.path.dirname(__file__))
TEMPLATE_NAME = "elasticsearch.yml.jinja2"

def render(template_name, context, template_path=TEMPLATE_PATH):
    loader = (
        jinja2.FileSystemLoader(
            template_path,
        ))
    env = jinja2.Environment(loader=loader,
            auto_reload=True, # TODO
            autoescape=False)

    template = env.get_template(template_name)

    return template.render(context)

if __name__=="__main__":

    import sys
    _output = sys.stdout
    debug = False

    if sys.argv[1:]:
        _output_filename = sys.argv[1].strip()
        if _output_filename:
            _output = open(_output_filename, 'w')

    try:
        context = get_local_context()

        if debug:
            import json
            print( json.dumps(context, indent=2), file=sys.stdout )

        print( render(TEMPLATE_NAME, context) , file=_output)
    finally:
        if _output is not sys.stdout:
            _output.close
