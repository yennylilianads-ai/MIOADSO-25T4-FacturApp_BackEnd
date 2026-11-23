from flask import Blueprint, jsonify, request, g
from src.models.invoices import Invoices
from src.models.clients import Clients
from src.models.users import Users, Role
from src.utils.auth import token_required, role_required
from src.models.invoice_details import InvoiceDetails
from src.models.products import Products

invoices_bp = Blueprint('invoices_v1', __name__, url_prefix='/api/v1')

def invoice_to_dict(invoice):
    return {
        'id': invoice.id,
        'client_id': invoice.client_id,
        'user_id': invoice.user_id,
        'date': invoice.date.isoformat() if invoice.date else None,
        'total': invoice.total,
        'completed': invoice.completed,
        'active': invoice.active
    }

@invoices_bp.route('/invoices', methods=['GET'])
@token_required
@role_required(Role.ADMIN, Role.SELLER)
def get_invoices():
    page = request.args.get('page', default=1, type=int)
    per_page = request.args.get('per_page', default=3, type=int)
    invoices, total_invoices = Invoices.get_paginated(page=page, per_page=per_page)
    total_pages = (total_invoices + per_page - 1) // per_page
    return jsonify({
        'data': [invoice_to_dict(i) for i in invoices],
        'meta': {
            'page': page,
            'per_page': per_page,
            'total_pages': total_pages,
            'total_invoices': total_invoices,
            'has_next': page < total_pages,
            'has_prev': page > 1
        }
    }), 200

@invoices_bp.route('/invoices/<int:invoice_id>', methods=['GET'])
@token_required
@role_required(Role.ADMIN, Role.SELLER)
def get_invoice_by_id(invoice_id):
    invoice = Invoices.get_by_id(invoice_id)
    if invoice:
        return jsonify(invoice_to_dict(invoice)), 200
    return jsonify({'success': False, 'message': 'Invoice not found'}), 404

@invoices_bp.route('/invoices', methods=['POST'])
@token_required
@role_required(Role.ADMIN, Role.SELLER)
def post_invoices():
    data = request.get_json()
    client_id = data.get('client_id')
    user_id = data.get('user_id')
    errors = {}

    # client_id
    if not client_id:
        errors['client_id'] = 'client_id is required'
    else:
        client = Clients.get_by_id(client_id)
        if not client:
            errors['client_id'] = 'client_id does not exist'
        elif client.active != 1:
            errors['client_id'] = 'client must be active'

    # user_id
    if not user_id:
        errors['user_id'] = 'user_id is required'
    else:
        user = Users.get_by_id(user_id)
        if not user:
            errors['user_id'] = 'user_id does not exist'
        elif user.active != 1:
            errors['user_id'] = 'user must be active'
        elif user.role != Role.SELLER.value:
            errors['user_id'] = 'user must have SELLER role'

    # Regla SELLER: solo puede usar su propio user_id
    # g.current_user lo pone token_required
        current_user = g.get('current_user')
    if current_user and getattr(current_user, 'role', None) == Role.SELLER.value:
        if user_id and user_id != getattr(current_user, 'id', None):
            errors['user_id'] = 'SELLER can only create invoices with their own user_id'
    if errors:
        return jsonify({'success': False, 'message': 'Errors in data validation', 'validation-errors': errors}), 400

    new_invoice = Invoices(client_id=client_id, user_id=user_id)
    Invoices.save(new_invoice)
    return jsonify(invoice_to_dict(new_invoice)), 201

    # HU2007 - Complete invoice
@invoices_bp.route('/invoices/<int:invoice_id>/complete', methods=['PUT'])
@token_required
@role_required(Role.ADMIN, Role.SELLER)
def complete_invoice(invoice_id):
    invoice = Invoices.get_by_id(invoice_id)
    if not invoice:
        return jsonify({'success': False, 'message': 'Invoice not found'}), 404

    if invoice.active == 0:
        return jsonify({'success': False, 'message': 'Invoice is cancelled and cannot be modified'}), 409

    if invoice.completed:
        return jsonify({'success': False, 'message': 'Invoice is already completed'}), 409

    details = InvoiceDetails.get_by_invoice(invoice_id)
    if not details:
        return jsonify({'success': False, 'message': 'Invoice has no details and cannot be completed'}), 409

    invoice.completed = True
    Invoices.save(invoice)
    return jsonify(invoice_to_dict(invoice)), 200

# HU2007 - Update invoice
@invoices_bp.route('/invoices/<int:invoice_id>', methods=['PUT'])
@token_required
@role_required(Role.ADMIN)
def update_invoice(invoice_id):
    invoice = Invoices.get_by_id(invoice_id)
    if not invoice:
        return jsonify({'success': False, 'message': 'Invoice not found'}), 404

    if invoice.active == 0:
        return jsonify({'success': False, 'message': 'Invoice is cancelled and cannot be modified'}), 409

    if invoice.completed:
        return jsonify({'success': False, 'message': 'Invoice is completed and cannot be modified'}), 409

    data = request.get_json() or {}
    errors = {}
    new_client = None
    new_user = None

    if 'client_id' in data:
        new_client = Clients.get_by_id(data['client_id'])
        if not new_client:
            errors['client_id'] = 'client does not exist'
        elif new_client.active == 0:
            errors['client_id'] = 'client must be active'

    if 'user_id' in data:
        new_user = Users.get_by_id(data['user_id'])
        if not new_user:
            errors['user_id'] = 'user does not exist'
        elif new_user.active == 0:
            errors['user_id'] = 'user must be active'
        elif new_user.role != Role.SELLER:
            errors['user_id'] = 'user must have SELLER role'

    if errors:
        return jsonify({'success': False, 'message': 'Errors in data validation', 'validation-errors': errors}), 400

    if new_client:
        invoice.client_id = new_client.id
    if new_user:
        invoice.user_id = new_user.id

    Invoices.save(invoice)
    return jsonify(invoice_to_dict(invoice)), 200

# HU2007 - Cancel invoice
@invoices_bp.route('/invoices/<int:invoice_id>', methods=['DELETE'])
@token_required
@role_required(Role.ADMIN)
def cancel_invoice(invoice_id):
    invoice = Invoices.get_by_id(invoice_id)
    if not invoice:
        return jsonify({'success': False, 'message': 'Invoice not found'}), 404

    if invoice.active == 0:
        return jsonify({'success': False, 'message': 'Invoice is already cancelled'}), 409

    details = InvoiceDetails.get_by_invoice(invoice_id)
    for d in details:
        product = Products.get_by_id(d.product_id)
        if product:
            product.stock += d.quantity
            Products.save(product)

    invoice.active = 0
    Invoices.save(invoice)
    return jsonify(invoice_to_dict(invoice)), 200