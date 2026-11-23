from flask import Blueprint, jsonify, request
from src.models.invoice_details import InvoiceDetails
from src.models.invoices import Invoices
from src.models.products import Products
from src.models.users import Role
from src.utils.auth import token_required, role_required

invoice_details_bp = Blueprint('invoice_details_v1', __name__, url_prefix='/api/v1')

@invoice_details_bp.route('/invoice_details', methods=['POST'])
@token_required
@role_required(Role.ADMIN, Role.SELLER)
def create_detail():
    data = request.get_json()
    invoice_id = data.get('invoice_id')
    product_id = data.get('product_id')
    quantity = data.get('quantity')

    if not invoice_id or not product_id or not quantity:
        return jsonify({'error': 'invoice_id, product_id and quantity are required'}), 400

    invoice = Invoices.get_by_id(invoice_id)
    if not invoice or not invoice.active:
        return jsonify({'error': 'Invoice not found'}), 404

    product = Products.get_by_id(product_id)
    if not product or not product.active:
        return jsonify({'error': 'Product not found'}), 404

    if product.stock < quantity:
        return jsonify({'error': 'Not enough stock'}), 400

    detail = InvoiceDetails(
        invoice_id=invoice_id,
        product_id=product_id,
        quantity=quantity,
        price=product.price
    )
    detail.save()

    # Actualizar stock y total de la factura
    product.stock -= quantity
    product.save()
    invoice.total += detail.subtotal
    invoice.save(invoice)

    return jsonify({
        'id': detail.id,
        'invoice_id': detail.invoice_id,
        'product_id': detail.product_id,
        'quantity': detail.quantity,
        'price': detail.price,
        'subtotal': detail.subtotal,
        'invoice_total': invoice.total
    }), 201

@invoice_details_bp.route('/invoices/<int:invoice_id>/details', methods=['GET'])
@token_required
@role_required(Role.ADMIN, Role.SELLER)
def get_details_by_invoice(invoice_id):
    details = InvoiceDetails.get_by_invoice(invoice_id)
    return jsonify({'data': [{
        'id': d.id,
        'invoice_id': d.invoice_id,
        'product_id': d.product_id,
        'quantity': d.quantity,
        'price': d.price,
        'subtotal': d.subtotal
    } for d in details]}), 200
@invoice_details_bp.route('/invoice_details/<int:id>', methods=['PUT'])
@token_required
@role_required(Role.ADMIN)
def update_detail(id):
    detail = InvoiceDetails.get_by_id(id)
    if not detail or not detail.active:
        return jsonify({'error': 'Detail not found'}), 404

    data = request.get_json()
    new_quantity = data.get('quantity')
    if not new_quantity:
        return jsonify({'error': 'quantity is required'}), 400

    product = Products.get_by_id(detail.product_id)
    invoice = Invoices.get_by_id(detail.invoice_id)

    # 1. Devolver el stock viejo
    product.stock += detail.quantity

    # 2. Validar stock nuevo
    if product.stock < new_quantity:
        return jsonify({'error': 'Not enough stock'}), 400

    # 3. Calcular subtotales viejo y nuevo
    old_subtotal = detail.quantity * detail.price
    new_subtotal = new_quantity * detail.price

    # 4. Actualizar detalle y stock
    detail.quantity = new_quantity
    detail.save()

    product.stock -= new_quantity
    product.save()

    # 5. Recalcular total de la factura
    invoice.total = invoice.total - old_subtotal + new_subtotal
    invoice.save(invoice)

    return jsonify({
        'message': 'Detail updated',
        'detail': {
            'id': detail.id,
            'invoice_id': detail.invoice_id,
            'product_id': detail.product_id,
            'quantity': detail.quantity,
            'price': detail.price
        },
        'invoice_total': invoice.total
    }), 200

@invoice_details_bp.route('/invoice_details/<int:id>', methods=['DELETE'])
@token_required
@role_required(Role.ADMIN)
def delete_detail(id):
    detail = InvoiceDetails.get_by_id(id)
    if not detail or not detail.active:
        return jsonify({'error': 'Detail not found'}), 404

    product = Products.get_by_id(detail.product_id)
    invoice = Invoices.get_by_id(detail.invoice_id)

    subtotal = detail.quantity * detail.price

    # 1. Devolver stock
    product.stock += detail.quantity
    product.save()

    # 2. Restar del total
    invoice.total -= subtotal
    invoice.save(invoice)

    # 3. Borrado lógico
    detail.active = False
    detail.save()

    return jsonify({'message': 'Detail deleted'}), 200