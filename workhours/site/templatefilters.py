import workhours.models.json as json

from jinja2 import evalcontextfilter, Markup
@evalcontextfilter
def skipautoescape(eval_ctx, value):
    if eval_ctx.autoescape:
        result = Markup(value)
    return result


@evalcontextfilter
def jsonify(eval_ctx, value):
    result = None
    if value:
        result = json.dumps(value)
        if eval_ctx.autoescape:
            result = Markup(result)
    return result
