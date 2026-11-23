from sqlalchemy import Column, Integer, Float, ForeignKey
from src.models import Base, session

class InvoiceDetails(Base):
    __tablename__ = 'invoice_details'

    id = Column(Integer, primary_key=True)
    invoice_id = Column(Integer, ForeignKey('invoices.id'), nullable=False)
    product_id = Column(Integer, ForeignKey('products.id'), nullable=False)
    quantity = Column(Integer, nullable=False)
    price = Column(Float, nullable=False)
    subtotal = Column(Float, nullable=False)
    active = Column(Integer, default=1)

    def __init__(self, invoice_id, product_id, quantity, price):
        self.invoice_id = invoice_id
        self.product_id = product_id
        self.quantity = quantity
        self.price = price
        self.subtotal = price * quantity

    def __repr__(self):
        return f"InvoiceDetail(id={self.id}, invoice_id={self.invoice_id}, product_id={self.product_id}, quantity={self.quantity})"

    def get_by_id(detail_id):
        detail = session.query(InvoiceDetails).filter_by(id=detail_id).first()
        return detail

    def get_by_invoice(invoice_id):
        details = session.query(InvoiceDetails).filter_by(invoice_id=invoice_id, active=1).all()
        return details

    def save(self):
        session.add(self)
        session.commit()