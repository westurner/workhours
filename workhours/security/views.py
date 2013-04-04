
import colander
from pyramid.view import view_config
from pyramid.url import route_url
from pyramid.renderers import render
from pyramid.httpexceptions import HTTPFound
from pyramid.security import authenticated_userid, remember, forget

from pyramid_simpleform.form import Form
from pyramid_simpleform.renderers import FormRenderer

# i178n
#from pyramid.i18n import TranslationStringFactory
#_ = TranslationStringFactory('workhours')

from ..models import DBSession
from ..models import User #, Idea, Tag


def validate_username(*args, **kwargs):
    return formencode.validators.PlainText(*args, not_empty=True, **kwargs)

def validate_passphrase(*args, **kwargs):
    return formencode.validators.String(*args, not_empty=True, **kwargs)

class RegistrationSchema(colander.MappingSchema):
    username = colander.SchemaNode(colander.String(), validator=colander.Length(255))
    email = colander.SchemaNode(colander.String(), validator=colander.Email())
    name = colander.SchemaNode(colander.String(), validator=colander.Length(255))
    passphrase = colander.SchemaNode(colander.String(), validator=colander.Length(255))
    confirm_passphrase = colander.SchemaNode(colander.String(), validator=colander.Length(255))

    #chained_validators = [
    #    formencode.validators.FieldsMatch('passphrase','confirm_passphrase')
    #]


@view_config(permission='view', route_name='register',
             renderer='security/templates/user_add.jinja2')
def user_add(request):

    form = Form(request, schema=RegistrationSchema())

    if 'loginform.submitted' in request.POST:
        if form.validate():
            session = DBSession()
            username=form.data['username']
            user = User(
                username=username,
                passphrase=form.data['passphrase'],
                name=form.data['name'],
                email=form.data['email']
            )
            session.add(user)

            headers = remember(request, username)

            redirect_url = route_url('main', request)

            return HTTPFound(location=redirect_url, headers=headers)
        else:
            raise Exception()
            request.session.flash("Failed to add user")

    login_form = login_form_view(request)

    return {
        'form': FormRenderer(form),
        'login_form': login_form,
        'title': 'create an account',
    }


@view_config(permission='view', route_name='user',
             renderer='security/templates/user.jinja2')
def user_view(request):
    username = request.matchdict['username']
    user = User.get_by_username(username)
    login_form = login_form_view(request)
    return {
        'user': user,
        'login_form' :login_form,
    }


class LoginSchema(colander.MappingSchema):
    username = colander.SchemaNode(colander.String(), validator=colander.Length(255))
    passphrase = colander.SchemaNode(colander.String(), validator=colander.Length(255))


@view_config(permission='view', route_name='login',
        renderer='workhours:security/templates/login_view.jinja2')
def login_view(request):
    main_view = route_url('main', request)
    came_from = request.params.get('came_from', main_view)
    user = authenticated_userid(request)
    form = Form(request, schema=LoginSchema())

    if request.POST:
        if 'loginform.submitted' in request.POST:
            if form.validate():
                username = form.data['username']
                passphrase = form.data['passphrase']

                if User.check_passphrase(username, passphrase):
                    headers = remember(request, username)
                    request.session.flash(u'Logged in successfully.')
                    return HTTPFound(location=came_from, headers=headers)

        request.session.flash(u'Failed to login.')
    #return HTTPFound(location=came_from)
    return {
        'title': not user and 'log in' or 'logged in',
        'form': FormRenderer(form),
        'loggedin': authenticated_userid(request),
        '_full': True }


@view_config(permission='post', route_name='logout')
def logout_view(request):
    request.session.invalidate()
    request.session.flash(u'Logged out.')
    headers = forget(request)
    return HTTPFound(location=route_url('main', request),
                     headers=headers)

def login_form_view(request):
    logged_in = authenticated_userid(request)
    return render('workhours:security/templates/_login.jinja2',
            {'loggedin': logged_in,
             '_partial': True,
             'form': FormRenderer(Form(request, schema=LoginSchema))},
            request)


