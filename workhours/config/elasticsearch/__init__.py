
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
    "http_port": 9200,
    "disable_http": False,

    "number_of_shards": 5,
    "number_of_replicas": 1
}

def get_local_context():
    hours_path=os.environ.get('VIRTUAL_ENV')
    hours_context = {
        "etcdir": os.path.join(hours_path, "/etc/elasticsearch" ),
        "datadir": os.path.join(hours_path, "/var/lib/elasticsearch"),
        "tmpdir": os.path.join(hours_path, "/tmp/elasticsearch"),
        "logdir": os.path.join(hours_path, "/var/log/elasticsearch"),
        "plugindir": "/usr/share/elasticsearch/plugins",
        "http_port": 9200,
        "disable_http": False,

        "number_of_shards": 1,
        "number_of_replicas": 0
    }
    return hours_context

def render():
    template_name = "elasticsearch.yml.jinja2"
    template_path = os.path.abspath(os.path.dirname(__file__))

    loader = (
        jinja2.FileSystemLoader(
            template_path,
            auto_reload=True, # TODO
            autoescape=False, # NOTE
        ))
    env = jinja2.Environment(loader=loader)

    template = env.get_template('elasticsearch.yml.jinja2')

    template.render(get_local_context())

if __name__=="__main__":
    render()
