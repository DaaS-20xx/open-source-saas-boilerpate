import importlib, sys
from flask import Blueprint, render_template, redirect
from flask_restplus import Namespace, Resource, Api
from flask_login import login_required, current_user

homepage_blueprint = Blueprint('home', __name__, template_folder='../../app/homepage/template')#, url_prefix='/home')


home_app = Api (homepage_blueprint,
    title='Universal Transcriber Home',
    version='1.0',
    description='Home Landing Page of the Universal Transcriber App'
)

# This is where you add API namespaces
home_api = Namespace('home')
home_app.add_namespace(home_api)

@homepage_blueprint.route('/')
def index():
    return redirect('/landing')

@homepage_blueprint.route('/landing', methods=['GET'])
def home_requests():
    return render_template('transcribe_home.html')

@homepage_blueprint.route('/pricing', methods=['GET'])
def pricing():
    return render_template('transcribe_kit1-pricing.html')

@homepage_blueprint.route('/faq', methods=['GET'])
def faq():
    return render_template('transcribe_kit1-faq.html')

@homepage_blueprint.route('/download', methods=['GET'])
def download_app():
    return render_template('transcribe_kit1-download.html')

@homepage_blueprint.route('/subscribe', methods=['GET'])
@login_required
def subscribe():
    user_id = current_user.id
    print(user_id)
    sys.stdout.flush()
    return render_template('transcribe_commerce-payment-flow.html')