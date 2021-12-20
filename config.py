from dotenv import load_dotenv
load_dotenv()

import os

basedir = os.path.abspath(os.path.dirname(__file__))

class Config(object):
    ENV = ''
    DEBUG = True
    BASE_URL='localhost'
    BASE_PORT = '5000'
    PROTOCOL='http'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_DATABASE_URI = os.environ.get('db_url') # Store it in the hosting config
    COMPANY_NAME = 'DaaS' # Change to your company name
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY')
    SECRET_KEY = os.environ.get('SECRET_KEY')
    WTF_CSRF_CHECK_DEFAULT = False

    MAIL_SERVER = os.environ.get('MAIL_SERVER')
    MAIL_PORT = os.environ.get('MAIL_PORT')
    MAIL_USE_SSL = True if os.getenv('MAIL_USE_SSL') == 'True' else False
    MAIL_USE_TLS = True if os.getenv('MAIL_USE_TLS') == 'True' else False
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    ADMIN_EMAIL = os.environ.get('ADMIN_EMAIL')

    #AWS
    AWS_ACCESS_KEY_ID = os.environ.get('AWS_ACCESS_KEY_ID')
    AWS_SECRET_KEY = os.environ.get('AWS_SECRET_KEY')
    AWS_BUCKET_NAME = os.environ.get('AWS_BUCKET_NAME') # Create additional variables for other buckets
    AWS_SQS_QUEUE_URL = 'https://sqs.eu-central-1.amazonaws.com/363802231370/TranscribeSessions.fifo'
    AWS_SQS_QUEUE_NAME = 'TranscribeSessions.fifo'
    
    
    #STRIPE Cancel & Success return-urls to pass during stripe.checkout.Session.create in strype_action.py (invoked by /setup_payment)
    STRIPE_RETURN_SUCCESS_URL = 'http://localhost:5000/billing'
    STRIPE_RETURN_CANCEL_URL = 'http://localhost:5000/dashboard'
    
    #STRIPE    
    # Public and secret keys for stripe to validate
    # https://dashboard.stripe.com/dashboard
    STRIPE_PUBLIC_KEY='pk_test_51K07DRJB3mmO7xd8OwdKFPJDssQKj02XrGl5BUlSNS3OYcdruJ5HMRLuYd8dFZoMay55M6PvS8X5kS3hRKOKqanD00vXz9JFI9'
    STRIPE_SECRET_KEY='sk_test_51K07DRJB3mmO7xd8u276GpCKL17eFyI8ldEg8KVqnYq4lDyQK5cF0bou9rWnlcRV973ijaOPkVjSmKspLIs5vbJx006lvXb3Je'

    # Make a product and make plans for the product
    # https://dashboard.stripe.com/subscriptions/products
    STRIPE_PLAN_SMALL='price_1K1dHFJB3mmO7xd8e8SD9wp3'
    STRIPE_PLAN_MEDIUM='price_1K1dHFJB3mmO7xd81z0l4V3I'
    STRIPE_PLAN_TOP='price_1K1dHFJB3mmO7xd8eOqWI7gr'

    # Configure three endpoints; checkout.session.completed, invoice.payment_succeeded, customer.subscription.deleted
    # https://dashboard.stripe.com/webhooks
    WEBHOOK_SIGNING_SECRET='whsec_1x3VOzAp117XJOLEQrgycsZqwdU0z0aq'
    WEBHOOK_CHECKOUT_SESSION_COMPLETED='whsec_ieFGgePn5lc7gI07xBKbxjLlPNcmVHlO'
    WEBHOOK_INVOICE_PAYMENT_SUCCEEDED='whsec_yhJouD3zYctgH9kPQffkSQ4aPyyAGWzE'
    WEBHOOK_CUSTOMER_SUBSCRIPTION_DELETED='whsec_dT95mU3oXpsHpbcpLi3RpEpeEyl2H0qW'
    

class ProductionConfig(Config):
    ENV = 'prod'
    DEBUG = False

class DevelopmentConfig(Config):
    ENV = 'dev'
    DEVELOPMENT = True
    DEBUG = True

class TestingConfig(Config):
    ENV = 'test'
    TESTING = True

config = {
    'dev': DevelopmentConfig,
    'test': TestingConfig,
    'prod': ProductionConfig,
    'default' : DevelopmentConfig
}


class ConfigHelper:

    # Allows setting config from argument, or from "env" environment variable (see Activate.bat)

    @staticmethod
    def __check_config_name(env_name):
        return env_name is not None and env_name != '' and env_name in config is not None

    @staticmethod
    def set_config(args):
        if (args is not None and len(args) > 1):
            # Check argument
            if ConfigHelper.__check_config_name(args[1]):
                return config[args[1]]
        
        # Check os env var
        env = os.environ.get('env')
        if ConfigHelper.__check_config_name(env):
            if config.get(env):
                return config.get(env)

        # Nothing worked, return default config
        return config['default']
    