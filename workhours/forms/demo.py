from pyramid.view import view_config
from workhours.forms.render import render_form

@view_config(
    renderer='workhours:templates/formdemo.jinja2',
    route_name='pyramid_csrf_demo')
def pyramid_csrf_demo(request):

    class DemoSchema(CSRFSchema):
        text = colander.SchemaNode(
            colander.String(),
            validator=colander.Length(max=100),
            widget=deform.widget.TextInputWidget(size=60),
            description='Enter some text'
            )

    schema = DemoSchema().bind(request=request)
    form = deform.Form(schema, buttons=('submit',))
    return render_form(request, form)
