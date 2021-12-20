import importlib, sys, json
from pathlib import Path
from flask import Blueprint, render_template, jsonify, redirect, url_for, current_app
from flask_login import login_required as flask_login_required, login_user, logout_user, current_user
from flask_restplus import Namespace, Resource, Api
from .frontend_action import FrontendAction
#from flask_wtf.csrf import CSRFProtect
#from src.dashboard.api.dashboard_api import dashboard_api
from src.shared.utils.user_auth_wrapper import login_required
from src.modules.auth.api import admin_required
#csrf = CSRFProtect(current_app)

dashboard_blueprint = Blueprint('dashboard', __name__, template_folder='../../app/dashboard')

dashboard_app = Api (dashboard_blueprint,
    title='AI Universal Dashboard',
    version='1.0',
    description='AI Universal Dashboard'
)

# This is where you add API namespaces
dashboard_api = Namespace('dashboard', path = '/app')
dashboard_app.add_namespace(dashboard_api)

def register_api(folder):
    for module in folder.iterdir():
        if module.is_dir():
            module_spec = importlib.util.find_spec('src.{0}.{1}.api'.format(folder.name, module.name))
            if module_spec:
                namespace_module = importlib.import_module('src.{0}.{1}.api'.format(folder.name, module.name))
                if namespace_module:
                    variables = [item for item in dir(namespace_module) if not item.startswith("__")]
                    for var_name in variables:
                        var = getattr(namespace_module, var_name)
                        if isinstance(var, Namespace):
                            dashboard_app.add_namespace(var)
def init():
    '''
    Imports namespaces that should be added to the blueprint
    '''
    shared_modules_folder = Path.joinpath(Path.cwd(), 'src/modules')
    register_api(shared_modules_folder)


init()               

@dashboard_blueprint.route('/', methods=['GET']) # To-do: create a separate endpoint for a landing page
def index_page():
    return redirect(url_for('dashboard.app_index_app'))

@dashboard_blueprint.route('/app', methods=['GET'])
@dashboard_blueprint.route('/app/<path:path>', methods=['GET'])
@flask_login_required
def app_index_app(path = None):
    notifications=[]
    notifications_for_display=[]
    action = FrontendAction(current_app)
    print(current_user, file=sys.stdout)
    sub_active = action.is_user_subscription_active(False)
    print("sub_active: "+str(sub_active), file=sys.stdout)
    variables = dict(name=current_user.username,
                    email=current_user.email,
                    expire_date=current_user.created, # to be added a number of days, e.g. trial period
                    user_is_paying=sub_active,
                    notifications=notifications_for_display,
                    n_messages=len(notifications))
    if sub_active==True:
        return redirect('/billing')
    else:
        return render_template('dashboardpay.html', **variables)
        

@dashboard_blueprint.route("/billing")
@flask_login_required
def billing():
    notifications=[]
    notifications_for_display=[]
    action = FrontendAction(current_app)
    sub_active, show_reactivate, sub_cancelled_at = action.is_user_subscription_active()
    print("retrieval from stripe - sub_active:"+str(sub_active)+" reactivate: "+str(show_reactivate)+" cancelled at: "+str(sub_cancelled_at))
    stripe_objs = action.get_all_stripe_subscriptions_by_user_id(current_user.id)
    print("output_stripe "+str(type(stripe_objs)))
    print(stripe_objs)
    if stripe_objs != None:
        sub_dict = action.subscriptions_to_json(stripe_objs)
    else:
        sub_dict = []
    #notifications, notifications_for_display = action.get_unread_notifications(current_user.id)
    
    variables = dict(subscription_active=sub_active,
                     name=current_user.username,
                     show_reactivate=show_reactivate,
                     subscription_cancelled_at=sub_cancelled_at,
                     subscription_data=sub_dict,
                     notifications=notifications_for_display,
                     n_messages=len(notifications))
    
    return render_template('billing.html', **variables)

# Not actual admin page, just protected page, only for admins
@dashboard_blueprint.route('/admin', methods=['GET'])
@admin_required
def protected_page(path = None):
    return render_template('dashboard.html')

@dashboard_blueprint.route('/app/api/jwttest', methods=['GET'])
@login_required # Protected with JWT, needs more testing
def get_test():
    '''
    This route is protected.
    '''
    return jsonify({'message': 'Protected works', 'result': True})