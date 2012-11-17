
# from deformdemo

import colander
import deform
@colander.deferred
def deferred_csrf_default(node, kw):
    request = kw.get('request')
    csrf_token = request.session.get_csrf_token()
    return csrf_token

@colander.deferred
def deferred_csrf_validator(node, kw):
    def validate_csrf(node, value):
        request = kw.get('request')
        csrf_token = request.session.get_csrf_token()
        if value != csrf_token:
            raise ValueError('Bad CSRF token')
    return validate_csrf


class CSRFSchema(colander.Schema):
    _csrf = colander.SchemaNode(
        colander.String(),
        default = deferred_csrf_default,
        validator = deferred_csrf_validator,
        widget = deform.widget.HiddenWidget(),
        )


# TODO: XXX
import jinja2
def render_form(request, form, appstruct=colander.null, submitted='submit',
                success=None, readonly=False):

    captured = None

    if submitted in request.POST:
        # the request represents a form submission
        try:
            # try to validate the submitted values
            controls = request.POST.items()
            captured = form.validate(controls)
            if success:
                response = success()
                if response is not None:
                    return response
            html = form.render(captured)
        except deform.ValidationFailure, e:
            # the submitted values could not be validated
            html = e.render()

    else:
        # the request requires a simple form rendering
        html = form.render(appstruct, readonly=readonly)

    if request.is_xhr:
        return Response(html)

    #code, start, end = self.get_code(2)

    reqts = form.get_widget_resources()

    # values passed to template for rendering
    return {
        'form':jinja2.Markup(html),
        'field': form,
        'captured':repr(captured),
        #'code': code,
        #'start':start,
        #'end':end,
        #'demos':self.get_demos(),
        'showmenu':True,
        #'title':self.get_title(),
        'css_links':reqts['css'],
        'js_links':reqts['js'],
        'title': 'Deform Form Demo',
        }

from pyramid.view import view_config
@view_config(renderer='workhours:templates/formdemo.jinja2', route_name='pyramid_csrf_demo')
def pyramid_csrf_demo(request):

    # subclass from CSRFSchema everywhere to get CSRF validation
    class MySchema(CSRFSchema):
        text = colander.SchemaNode(
            colander.String(),
            validator=colander.Length(max=100),
            widget=deform.widget.TextInputWidget(size=60),
            description='Enter some text'
            )

    schema = MySchema().bind(request=request)
    form = deform.Form(schema, buttons=('submit',))
    return render_form(request, form)
