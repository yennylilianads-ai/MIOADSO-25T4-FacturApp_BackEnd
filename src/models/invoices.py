from sqlalchemy import Column, Integer, Float, Boolean, DateTime, ForeignKey, func
from src.models import Base, session

class Invoices(Base):
    __tablename__ = 'invoices'

    id = Column(Integer, primary_key=True)
    client_id = Column(Integer, ForeignKey('clients.id'), nullable=False)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    date = Column(DateTime, default=func.now(), nullable=False)
    total = Column(Float, default=0, nullable=False)
    completed = Column(Boolean, default=False, nullable=False)
    active = Column(Integer, default=1)

    def __init__(self, client_id, user_id):
        self.client_id = client_id
        self.user_id = user_id

    def __repr__(self):
        return f"<Invoice(id={self.id}, client_id={self.client_id}, user_id={self.user_id}, total={self.total})>"

    @staticmethod
    def get_paginated(page, per_page):
        total_invoices = session.query(func.count(Invoices.id)).scalar()
        invoices = session.query(Invoices).offset((page - 1) * per_page).limit(per_page).all()
        return invoices, total_invoices

    @staticmethod
    def get_by_id(invoice_id):
        return session.query(Invoices).filter_by(id=invoice_id).first()

    @staticmethod
    def save(invoice):
        session.add(invoice)
        session.commit()
        return invoice