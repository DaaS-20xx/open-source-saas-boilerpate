import importlib
from flask import Blueprint, render_template
from flask_restplus import Namespace, Resource, Api

auth_blueprint = Blueprint('auth', __name__, template_folder='../../app/auth')


auth_app = Api (auth_blueprint,
    title='DaaS auth pages',
    version='1.0',
    description='DaaS authentication pages'
)

# This is where you add API namespaces
auth_api = Namespace('auth')
auth_app.add_namespace(auth_api)



@auth_blueprint.route('/auth/<path:path>', methods=['GET'])
def all_auth_requests(path):
    return render_template('auth.html')