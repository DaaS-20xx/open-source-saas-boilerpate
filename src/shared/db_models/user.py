import datetime
from sqlalchemy.dialects.postgresql import UUID
from flask_sqlalchemy import SQLAlchemy
import uuid
from flask import current_app
from flask_login import UserMixin
from passlib.hash import pbkdf2_sha256 as sha256
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer

from src.shared.utils.global_functions import get_config_var
from src.shared.db_models.role import Role
from src.shared.db_models.account import Account

from src.shared.utils.extensions import db, login_manager

class User(UserMixin, db.Model):
    __tablename__ = 'user'

    id = db.Column(UUID(as_uuid=True),
        primary_key=True, default=lambda: uuid.uuid4().hex)
    username = db.Column(db.String(120), nullable = False)
    userpic_url = db.Column(db.String(), nullable = True)
    email = db.Column(db.String(64), unique=True)
    password_hash = db.Column(db.String(120), nullable = False)
    role_id = db.Column(UUID(as_uuid=True), db.ForeignKey('role.id'))
    confirmed = db.Column(db.Boolean, default=False, server_default='f')
    account_id = db.Column(UUID(as_uuid=True), db.ForeignKey('account.id'))
    account = db.relationship('Account', back_populates='user', cascade='all,delete')
    created = db.Column(db.DateTime(), nullable=True)
    ### new column: User Status ("Active" when subscription in Stripe table is created and active)
    user_status = db.Column(db.String(30), nullable=True)
    ### new column: Subscription Plan (Small, Medium, Business)
    plan = db.Column(db.String(30), nullable=True)
    ### new column: Plan Start Date (date time)
    plan_start_dt = db.Column(db.DateTime(), nullable=True)
    ### new column: Plan Expiration Date (date time)
    plan_exp_dt = db.Column(db.DateTime(), nullable=True)
    ### new column: total initial minutes for the period (integer, number of seconds)
    plan_minutes = db.Column(db.Integer, nullable=True)
    ### new column: remaining minutes (remaining minutes in the current period) (integer, number of seconds)
    remaining_minutes = db.Column(db.Integer, nullable=True)


    def __init__(self, **kwargs):
        super(User, self).__init__(**kwargs)
        if self.role is None:
            admin_emails = get_config_var('ADMIN_EMAIL').split(' ') if get_config_var('ADMIN_EMAIL') is not None else []
            if len(admin_emails) > 0 and self.email in admin_emails:
                self.role = Role.query.filter_by(name='Admin').first()
            else:
                default_role = Role.query.filter_by(is_default=True).first()
                self.role = default_role
        if self.account == None:
            self.account = Account()
    
    def set_password(self, password):
        '''
        Creates a hash from a password
        '''
        hash = self.generate_hash(password)
        self.password_hash = hash

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(uuid.UUID(user_id))

    def generate_hash(self, password):
        return sha256.hash(password)

    def verify_hash(self, password):
        return sha256.verify(password, self.password_hash)

    # Is used for confirmation and forgot password feature
    def generate_verification_token(self, key='confirm', expiration=3600):
        s = Serializer(get_config_var('SECRET_KEY'), expiration)
        return s.dumps({key: self.id.__str__()}).decode('utf-8')

    def verify(self, token, key='confirm'):
        s = Serializer(get_config_var('SECRET_KEY'))
        try:
            data = s.loads(token.encode('utf-8'))
        except:
            return False
        if data.get(key) != self.id.__str__():
            return False
        self.confirmed = True
        return True

    def ping(self):
        self.last_seen = datetime.utcnow()
        db.session.add(self)

    def save(self):
        try:
            db.session.add(self)
            db.session.commit()
        except Exception as ex:
            print('ERROR while saving user:')
            print(ex) # to-do: log
            return False
        return True