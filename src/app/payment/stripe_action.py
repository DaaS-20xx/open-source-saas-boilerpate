from flask import Flask, current_app, jsonify
from sqlalchemy.exc import IntegrityError
import stripe, json, sys, os, traceback, requests
from datetime import timedelta, datetime
from types import SimpleNamespace
from sys import stdout
from uuid import UUID
from json import JSONEncoder

from stripe.api_resources import line_item, product
from src.shared.services.stripe_db import StripeAccess
from src.shared.services import db_user_service, publish_sns

db_access = StripeAccess()

class UUIDEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, UUID):
            # if the obj is uuid, we simply return the value of uuid
            return obj.hex
        return json.JSONEncoder.default(self, obj)
    
class DateTimeEncoder(JSONEncoder):
        #Override the default method
        def default(self, obj):
            if isinstance(obj, (datetime.date, datetime.datetime, datetime.time)):
                return obj.isoformat()

class StripeAction():
    def __init__(self, app):
        self.app = app
        #self.user_service = 'http://' + self.app.config['BASE_URL'] + ':' + app.config['USER_PORT'] + '/'

        stripe.api_key = app.config['STRIPE_SECRET_KEY']  
        #sys.stdout.write(app.config['STRIPE_SECRET_KEY'])

    def setup_payment(self, request):
        try:
            # Get the data from AJAX request
            data = request.get_json(force=True)
            sys.stdout.write("entered setup")
            # Find the plan id in the config file
            plan = self.app.config['STRIPE_PLAN_' + data['plan']]
            
            
            # Get stripe obj from database
            stripe_obj = db_access.get_stripe(user_id=str(data['user_id']))

            # Get user object
            """ TO BE REENGINERED
            r = requests.get(self.user_service + 'getuser/' + str(data['user_id']))
            if r.status_code != 200:
                return json.dumps({'message': 'something went wrong'})
                
            user_json = json.loads(r.text)
            user = SimpleNamespace(**user_json)
            """
            user = db_user_service.get_user_by_id(userid=data['user_id'])
            print(user.email)
            customer_id = None
            if stripe_obj != None and stripe_obj.customer_id != None:
                customer_id = stripe_obj.customer_id

            ####base_url = self.app.config['PROTOCOL'] + '://' + self.app.config['BASE_URL'] + ':' + self.app.config['FRONTEND_PORT']
            print(self.app.config['STRIPE_RETURN_SUCCESS_URL'])
            # Setup a Stripe session, completed with a webhook
            session = stripe.checkout.Session.create(
                line_items=[{
                    'price':'price_1K1dHFJB3mmO7xd81z0l4V3I',
                    'description': 'test',
                    'quantity':1,
                }],
                mode='subscription',
                customer_email=user.email,
                customer=customer_id,
                payment_method_types=['card'],
                ####success_url=base_url + '/landing',
                success_url=self.app.config['STRIPE_RETURN_SUCCESS_URL'],
                cancel_url=self.app.config['STRIPE_RETURN_CANCEL_URL']
                ####cancel_url=base_url + '/pricing',
            )

            # Used for redirect
            variables = dict(stripe_public_key=self.app.config['STRIPE_PUBLIC_KEY'],
                            session_id=session.id)
            return json.dumps(variables), 200
        except Exception as ex:
            stacktrace = traceback.format_exc()
            print(stacktrace)
            return json.dumps({'message':'Something went wrong'}), 500

    def cancel_subscription(self, request):
        try:
            data = request.get_json(force=True)
            stripe_id, is_present = self._is_subscription_id_present_in_user(data['user_id'], data['sub_id'])

            if not is_present:
                return json.dumps({'message':'User does not have subscription id'}), 401

            # Cancel at period end means that the subscription is still active,
            # and the user still has access to the service for the currently paid period.
            session = stripe.Subscription.modify(
                data['sub_id'],
                cancel_at_period_end=True
            )

            timestamp = session['cancel_at']
            subscription_ends = datetime.utcfromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')
            stripe_update = dict(subscription_cancelled_at=int(timestamp))
            db_access.update_stripe_by_dict(stripe_id, stripe_update)

            variables = dict(message='Success. You unsubscribed and will not be billed anymore. Your subscription will last until ' + subscription_ends)

            return json.dumps(variables), 200
        except Exception as ex:
            stacktrace = traceback.format_exc()
            print(stacktrace)
            return json.dumps({'message':'Something went wrong'}), 500

    def reactivate_subscription(self, request):
        try:
            data = request.get_json(force=True)
            stripe_id, is_present = self._is_subscription_id_present_in_user(data['user_id'], data['sub_id'])

            if not is_present:
                return json.dumps({'message':'User does not have subscription id'}), 401

            session = stripe.Subscription.modify(
                data['sub_id'],
                cancel_at_period_end=False
            )

            stripe_update = dict(subscription_cancelled_at=None)
            db_access.update_stripe_by_dict(stripe_id, stripe_update)

            variables = dict(message='Success. You will automatically be billed every month.')

            return json.dumps(variables), 200
        except Exception as ex:
            stacktrace = traceback.format_exc()
            print(stacktrace)
            return json.dumps({'message':'Something went wrong'}), 500

    def succesful_payment(self, request):
        try:
            # Validate if the request is a valid request received from Stripe
            data = self._validate_stripe_data(request, 'WEBHOOK_CHECKOUT_SESSION_COMPLETED')

            if data['type'] == 'checkout.session.completed':
                # Find the data object and corresponding user
                data_object = data['data']['object']
                #print(data, file=sys.stdout)
                # Get user object from user service
                ####r = requests.get(self.user_service + 'getuser/email/' + data_object['customer_email'])
                ####if r.status_code != 200:
                    ####return json.dumps({'message': 'something went wrong'})
                
                user = db_user_service.find_user_by_email(data_object['customer_email'])
                
                ####user_json = json.loads(r.text)
                ####user = SimpleNamespace(**user_json)

                if user != None:
                    # Get the stripe subscription
                    sub = stripe.Subscription.retrieve(data_object['subscription']) 
                    plan = sub['plan']
                    #print("stripe.Plan.retrieve: "+str(plan), file=stdout)
                    # Find and update the subscription data
                    subscription_id = data_object['subscription']
                    customer_id = data_object['customer']
                    amount = data_object['amount_total']
                    plan_id = plan['id']
                    amount = plan['amount']
                    current_period_start = sub['current_period_start']
                    current_period_start_dt = datetime.fromtimestamp(current_period_start)
                    current_period_end = sub['current_period_end']
                    current_period_end_dt = datetime.fromtimestamp(current_period_end)

                    new_stripe = dict(user_uid=user.id,
                                    user_email=user.email,
                                    user_name=user.username,
                                    plan=plan_id,
                                    subscription_id=subscription_id,
                                    customer_id=customer_id,
                                    subscription_active=True,
                                    amount=amount,
                                    current_period_start=current_period_start,
                                    current_period_start_dt=current_period_start_dt,
                                    current_period_end=current_period_end,
                                    current_period_end_dt=current_period_end_dt,
                                    created=datetime.now(),
                                    plan_name=plan['nickname'],
                                    subscription_cancelled_at=None)

                    db_access.create_stripe(new_stripe)
                    
                    #Send data to aws sqs queue as well, to sync the db on the websocket container
                    print("SEND EVENT TO publish_to_sns")
                    publish_sns.publish_to_sns(new_stripe, str(user.id))

            return "", 200
        except IntegrityError:
            return "User already has an active subscription", 400
        except ValueError:
            return "Bad payload", 400
        except stripe.error.SignatureVerificationError:
            return "Bad signature", 400
        except Exception as ex:
            stacktrace = traceback.format_exc()
            print(stacktrace)
            sys.stdout.flush()
            return str(stacktrace), 500

    def invoice_paid(self, request):
        try:
            data = self._validate_stripe_data(request, 'WEBHOOK_INVOICE_PAYMENT_SUCCEEDED')
            return self._update_subscription_when_paid(data)

        except IntegrityError:
            return "Something went wrong", 400
        except ValueError:
            return "Bad payload", 400
        except stripe.error.SignatureVerificationError:
            return "Bad signature", 400
        except Exception as ex:
            stacktrace = traceback.format_exc()
            print(stacktrace)
            return str(stacktrace), 500

    def subscription_ended(self, request):
        try:
            data = self._validate_stripe_data(request, 'WEBHOOK_CUSTOMER_SUBSCRIPTION_DELETED')

            data_object = data['data']['object']
            if data_object['status'] == 'canceled':
                sub_id = data_object['items']['data'][0]['subscription']
                stripe_obj = db_access.get_stripe(subscription_id=sub_id)

                if stripe_obj != None:
                    stripe_update = dict(subscription_active=False)
                    db_access.update_stripe_by_dict(stripe_obj.id, stripe_update)

                    return "", 200
                else:
                    return "stripe_obj is null", 500
        except ValueError:
            return "Bad payload", 400
        except stripe.error.SignatureVerificationError:
            return "Bad signature", 400
        except Exception as ex:
            stacktrace = traceback.format_exc()
            print(stacktrace)
            return str(stacktrace), 500

    def get_subscriptions(self, user_id, get_all=False):
        stripe_obj = db_access.get_stripe(user_id=user_id, as_dict=True, get_all=get_all)

        if stripe_obj != None:
            return jsonify(stripe_obj), 200
        else:
            return json.dumps({'message':'User was not found'}), 404

    def get_active_subscription(self, user_id):
        stripe_obj = db_access.get_stripe(user_id=user_id, as_dict=True, only_active=True)

        if stripe_obj != None:
            return jsonify(stripe_obj), 200
        else:
            return json.dumps({'message':'User was not found'}), 404

    def _validate_stripe_data(self, request, webhook_from_config):
        '''
            A function for validating webhook content
        '''

        payload = request.data.decode("utf-8")
        received_sig = request.headers.get("Stripe-Signature", None)

        # Verify received data
        with current_app.app_context():
            event = stripe.Webhook.construct_event(
                payload, received_sig, current_app.config[webhook_from_config]
            )

        # JSON to Python Dictionary
        data = json.loads(payload)

        return data

    def _update_subscription_when_paid(self, data, already_called = False):
        '''
            Method for updating a subscription, when it has been paid.
        '''
        if data['type'] == 'invoice.payment_succeeded':
            # Get data object and subscription id
            data_object = data['data']['object']
            sub_id = data_object['subscription']

            # If the subscription id is null, we can't update the subscription
            if sub_id == None:
                return "subscription_id was null", 402

            stripe_obj = db_access.get_stripe(subscription_id=sub_id)
            
            if stripe_obj != None:
                # Find the new end of period
                current_period_end = data_object['lines']['data'][0]['period']['end']
                current_period_end_dt = datetime.fromtimestamp(current_period_end)
                stripe_update = dict(current_period_end=current_period_end,current_period_end_dt=current_period_end_dt)

                # Get the payment method to setup the default payment method
                pi = stripe.PaymentIntent.retrieve(data_object['payment_intent'])

                if stripe_obj.payment_method_id == None:
                    stripe_obj.payment_method_id = pi['payment_method']

                    stripe.Customer.modify(
                        stripe_obj.customer_id,
                        invoice_settings={'default_payment_method': stripe_obj.payment_method_id}
                    )

                db_access.update_stripe_by_dict(stripe_obj.id, stripe_update)
                return "", 200
            else:
                self._create_subscription_in_db(sub_id)
                if not already_called:
                    self._update_subscription_when_paid(data, True)

                return "subscription_id did not exist, created a new row", 200
        else:
            return "Wrong request type", 400

    def _create_subscription_in_db(self, subscription_id):
        '''
            Given a subscription id, create the subscription in database.
            Finds all the relevant information from the stripe subscription object
        '''
        # Get the subscription object and customer_id
        sub = stripe.Subscription.retrieve(subscription_id)
        customer_id = sub['customer']

        # Find the customer in db
        stripe_obj = db_access.get_stripe(customer_id=customer_id)

        if stripe_obj != None:
            amount = sub['items']['data'][0]['plan']['amount']
            
            current_period_start = sub['current_period_start']
            current_period_end = sub['current_period_end']

            new_stripe = dict(user_id=stripe_obj.user_id,
                                subscription_id=subscription_id,
                                customer_id=customer_id,
                                subscription_active=True,
                                amount=amount,
                                current_period_start=current_period_start,
                                current_period_end=current_period_end,
                                subscription_cancelled_at=None)

            db_access.create_stripe(new_stripe)

    def _is_subscription_id_present_in_user(self, user_id, sub_id):
        '''
            Provided a user id and subscription id, check if the user has
            the provided subscription id.
            Returns the row in database where the subscription id exists
        '''
        stripe_obj = db_access.get_stripe(user_id=user_id, get_all=True)

        # If the provided subscription id exists, return the row
        for row in stripe_obj:
            if row.subscription_id == sub_id:
                return row.id, True
            
        return None, False