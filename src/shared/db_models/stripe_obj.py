from src.shared.utils.extensions import db
from sqlalchemy import Column, Integer, DateTime, String, Boolean, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from src.shared.utils.global_functions import get_config_var

class Stripe(db.Model):
    __tablename__ = 'stripe'
    id = Column(Integer, primary_key=True)
    #user_id = Column(Integer, unique=False, nullable=False)
    created = Column(DateTime(), nullable=True)
    user_uid = Column(String(256), unique=False, nullable=False)
    user_name = Column(String(256), unique=False, nullable=True)
    user_email = Column(String(256), unique=False, nullable=False)
    subscription_id = Column(String(256), unique=False, nullable=True)
    plan = Column(String(256), unique=False, nullable=True)
    plan_name = Column(String(256), unique=False, nullable=True)
    customer_id = Column(String(256), unique=False, nullable=False)
    payment_method_id = Column(String(256), unique=False, nullable=True)
    subscription_active = Column(Boolean, default=False)
    amount = Column(Integer, unique=False)
    current_period_start = Column(Integer, unique=False)
    current_period_start_dt = Column(DateTime(), nullable=True)
    current_period_end = Column(Integer, unique=False)
    current_period_end_dt = Column(DateTime(), nullable=True)
    subscription_cancelled_at = Column(Integer, unique=False)
    payment_vendor_code = Column(String(64), nullable=True) # For example, 'stripe' or 'paypal'
    total_month_minutes = Column(db.Integer)
    current_consumed_seconds = Column(db.Integer) #seconds are stores, not minutes

    def __repr__(self):
        return 'id: '.join([str(id)])

    def as_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}

    def update(self, **kwargs):
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)