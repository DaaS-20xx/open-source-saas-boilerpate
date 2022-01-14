import importlib, sys
from flask import Blueprint, render_template, request, current_app
from flask_login import login_required, current_user
from flask_restplus import Namespace, Resource, Api
from .stripe_action import StripeAction

payment_blueprint = Blueprint('payment', __name__, template_folder='../../app/payment/template')#, url_prefix='/payment')


payment_app = Api (payment_blueprint,
    title='Universal Transcriber Payment',
    version='1.0',
    description='Payment  Page of the Universal Transcriber App'
)

# This is where you add API namespaces
payment_api = Namespace('payment')
payment_app.add_namespace(payment_api)


@payment_blueprint.route('/setup_payment', methods=['POST'])
@login_required
def setup_payment():
    data = request.get_json(force=True)
    #data['user_id'] = "aea80863-5e43-4a68-b7aa-918d25a47f05" # to be substituted by current_user.id (the user who is authenticated before confirming the payment)
    data['user_id'] = current_user.id
    print("payment_blueprint - currentUserId: "+str(data['user_id']), file=sys.stdout)
    action = StripeAction(current_app)
    return action.setup_payment(request)

@payment_blueprint.route("/webhook_pay_success", methods=["POST"])
def succesful_payment():
    '''
        Endpoint for receving the checkout.session.complete webhook request from Stripe. 


        Parameters
        ----------
        request : JSON data
            This is a payload from Stripe. Contains Stripe's Checkout Session object.

        Returns (JSON)
        -------
        {
            message : string
                Empty string if the request went well. Contains debugging information
                if the request went bad.
            status : int
                HTTP status code.
        }
    '''
    action = StripeAction(current_app)
    return action.succesful_payment(request)

@payment_blueprint.route("/webhook_invoice_paid", methods=["POST"])
def invoice_paid():
    '''
        Endpoint for receving the invoice.payment_succeeded from Stripe. 
        When the customer pays his subscription for another month,
        we need to update when his current_period_end in the db.

        (Webhook is also received the first time the customer pays. In
        any case, this will not be a problem. It's handled correctly.)

        Parameters
        ----------
        request : JSON data
            This is a payload from Stripe.

        Returns (JSON)
        -------
        message : string
            Empty string if the request went well. Contains debugging information
            if the request went bad.
        status : int
            HTTP status code.
    '''
    action = StripeAction(current_app)
    return action.invoice_paid(request)

@payment_blueprint.route("/webhook_subscription_ended", methods=["POST"])
def subscription_ended():
    '''
        Endpoint for receving the customer.subscription.deleted from Stripe. 
        This webhook is received if the user cancelled his subscription
        at an earlier time, and the current_period_end in the database
        is less than current time.

        When a subscription is cancelled, the subscription lasts for the
        period paid. When the period is over, this webhook is sent from
        Stripe.

        Removes all access to the services provided for paid subscriptions.

        Parameters
        ----------
        request : JSON data
            This is a payload from Stripe.

        Returns (JSON)
        -------
        message : string
            Empty string if the request went well. Contains debugging information
            if the request went bad.
        status : int
            HTTP status code.
    '''
    action = StripeAction(current_app)
    return action.subscription_ended(request)

@payment_blueprint.route("/get_active_subscription/<user_id>", methods=["GET"])
def get_active_subscription(user_id):
    action = StripeAction(current_app)
    return action.get_active_subscription(user_id)

@payment_blueprint.route("/get_active_subscription_by_email/<user_email>", methods=["GET"])
def get_active_subscription_by_email(user_email):
    action = StripeAction(current_app)
    print("entered api", file=sys.stdout)
    return action.get_active_subscription_by_email(user_email)