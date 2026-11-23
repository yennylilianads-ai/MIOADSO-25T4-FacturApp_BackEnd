from flask import Blueprint, jsonify, request
from src.models.clients import Clients, DocumentType
from src.models.users import Role
from src.utils.auth import token_required, role_required

clients_bp = Blueprint('clients_v1', __name__, url_prefix='/api/v1')

def client_to_dict(client):
    return {
        'id': client.id,
        'document_type': client.document_type,
        'document_number': client.document_number,
        'name': client.name,
        'email': client.email,
        'phone': client.phone,
        'address': client.address,
        'active': client.active
    }

@clients_bp.route('/clients', methods=['GET'])
@token_required
@role_required(Role.ADMIN, Role.SELLER)
def get_clients():
    page = request.args.get('page', default=1, type=int)
    per_page = request.args.get('per_page', default=3, type=int)
    clients, total_clients = Clients.get_paginated(page=page, per_page=per_page)
    total_pages = (total_clients + per_page - 1) // per_page
    return jsonify({
        'data': [client_to_dict(c) for c in clients],
        'meta': {
            'page': page,
            'per_page': per_page,
            'total_pages': total_pages,
            'total_clients': total_clients,
            'has_next': page < total_pages,
            'has_prev': page > 1
        }
    }), 200

@clients_bp.route('/clients/<int:client_id>', methods=['GET'])
@token_required
@role_required(Role.ADMIN, Role.SELLER)
def get_client_by_id(client_id):
    client = Clients.get_by_id(client_id)
    if client:
        return jsonify(client_to_dict(client)), 200
    return jsonify({'success': False, 'message': 'Client not found'}), 404

@clients_bp.route('/clients', methods=['POST'])
@token_required
@role_required(Role.ADMIN)
def post_clients():
    data = request.get_json()
    document_type = data.get('document_type')
    document_number = data.get('document_number')
    name = data.get('name')
    email = data.get('email')
    phone = data.get('phone')
    address = data.get('address')
    errors = {}

    # document_type
    if not document_type:
        errors['document_type'] = 'document_type is required'
    elif document_type not in [t.value for t in DocumentType]:
        errors['document_type'] = 'document_type must be one of: CC, NIT, CE'

    # document_number
    if not document_number:
        errors['document_number'] = 'document_number is required'
    elif Clients.get_by_document_number(document_number):
        errors['document_number'] = 'document_number must be unique'

    # name
    if not name:
        errors['name'] = 'name is required'

    # email
    if not email:
        errors['email'] = 'email is required'
    elif '@' not in email:
        errors['email'] = 'email is not valid'

    # phone, address
    if not phone:
        errors['phone'] = 'phone is required'
    if not address:
        errors['address'] = 'address is required'

    if errors:
        return jsonify({'success': False, 'message': 'Errors in data validation', 'validation-errors': errors}), 400

    new_client = Clients(document_type=document_type, document_number=document_number, name=name, email=email, phone=phone, address=address)
    Clients.save(new_client)
    return jsonify(client_to_dict(new_client)), 201

@clients_bp.route('/clients/<int:client_id>', methods=['PUT'])
@token_required
@role_required(Role.ADMIN)
def put_clients(client_id):
    client = Clients.get_by_id(client_id)
    if not client:
        return jsonify({'success': False, 'message': 'Client not found'}), 404

    data = request.get_json()
    document_type = data.get('document_type')
    document_number = data.get('document_number')
    name = data.get('name')
    email = data.get('email')
    phone = data.get('phone')
    address = data.get('address')
    active = data.get('active')
    errors = {}

    # VALIDAR PRIMERO, sin tocar client todavia - igual que HU2001
    if document_type is not None and document_type not in [t.value for t in DocumentType]:
        errors['document_type'] = 'document_type must be one of: CC, NIT, CE'

    if document_number is not None and document_number != client.document_number:
        if Clients.get_by_document_number(document_number):
            errors['document_number'] = 'document_number must be unique'

    if name is not None and not name:
        errors['name'] = 'name is required'

    if email is not None:
        if not email:
            errors['email'] = 'email is required'
        elif '@' not in email:
            errors['email'] = 'email is not valid'

    if phone is not None and not phone:
        errors['phone'] = 'phone is required'

    if address is not None and not address:
        errors['address'] = 'address is required'

    if active is not None and active not in (0, 1):
        errors['active'] = 'active must be 0 or 1'

    if errors:
        return jsonify({'success': False, 'message': 'Errors in data validation', 'validation-errors': errors}), 400

    # Solo si NO hay errores, asignamos
    if document_type is not None:
        client.document_type = document_type
    if document_number is not None:
        client.document_number = document_number
    if name is not None:
        client.name = name
    if email is not None:
        client.email = email
    if phone is not None:
        client.phone = phone
    if address is not None:
        client.address = address
    if active is not None:
        client.active = active

    Clients.update(client)
    return jsonify(client_to_dict(client)), 200

@clients_bp.route('/clients/<int:client_id>', methods=['DELETE'])
@token_required
@role_required(Role.ADMIN)
def delete_clients(client_id):
    client = Clients.get_by_id(client_id)
    if not client:
        return jsonify({'success': False, 'message': 'Client not found'}), 404

    Clients.delete(client)
    return jsonify({'success': True, 'message': 'Client deleted'}), 200