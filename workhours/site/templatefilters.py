from workhours.models.json import dumps

from jinja2 import pass_eval_context
from markupsafe import Markup


@pass_eval_context
def skipautoescape(eval_ctx, value):
    if eval_ctx.autoescape:
        return Markup(value)
    return value


@pass_eval_context
def jsonify(eval_ctx, value):
    result = None
    if value:
        result = dumps(value)
        if eval_ctx.autoescape:
            result = Markup(result)
    return result


@pass_eval_context
def jsonify_indent(eval_ctx, value):
    result = None
    if value:
        result = dumps(
            {k: v for k, v in value.items() if not k.startswith("_")}, indent=2
        )
        if eval_ctx.autoescape:
            result = Markup(result)
    return result
