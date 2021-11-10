import importlib
from flask import Blueprint, render_template
from flask_restplus import Namespace, Resource, Api

homepage_blueprint = Blueprint('home', __name__, template_folder='../../app/homepage/template')


home_app = Api (homepage_blueprint,
    title='Universal Transcriber Home',
    version='1.0',
    description='Home Landing Page of the Universal Transcriber App'
)

# This is where you add API namespaces
home_api = Namespace('home')
home_app.add_namespace(home_api)



@homepage_blueprint.route('/<path:path>', methods=['GET'])
def all_auth_requests(path):
    return render_template('transcribe_home.html')