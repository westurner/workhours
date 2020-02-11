from workhours.models.json import dumps

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
        result = dumps(value)
        if eval_ctx.autoescape:
            result = Markup(result)
    return result


@evalcontextfilter
def jsonify_indent(eval_ctx, value):
    result = None
    if value:
        result = dumps(
            {k: v for k, v in value.items() if not k.startswith("_")}, indent=2
        )
        if eval_ctx.autoescape:
            result = Markup(result)
    return result
