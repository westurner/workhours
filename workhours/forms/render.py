# TODO: XXX
import colander
import jinja2
def render_form(request,
                form,
                appstruct=colander.null,
                submitted='submit',
                success=None,
                readonly=False):
    captured = None

    if submitted in request.POST:
        # the request represents a form submission
        try:
            # try to validate the submitted values
            controls = list(request.POST.items())
            captured = form.validate(controls)
            if success: # TODO: XXX ???
                response = success()
                if response is not None:
                    return response
            html = form.render(captured)
        except deform.ValidationFailure as e:
            # the submitted values could not be validated
            html = e.render()

    else:
        # the request requires a simple form rendering
        html = form.render(appstruct, readonly=readonly)

    # TODO
    #if request.is_xhr:
    #    return request.response.body = html
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
        'title': 'Deform Form Demo', # TODO
        }


