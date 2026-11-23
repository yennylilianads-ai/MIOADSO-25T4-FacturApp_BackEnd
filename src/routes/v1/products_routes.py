from flask import Blueprint, jsonify, request
from src.models.products import Products
from src.models.categories import Categories
from src.models.users import Role
from src.utils.auth import token_required, role_required

products_bp = Blueprint('products_v1', __name__, url_prefix='/api/v1')

@products_bp.route('/products', methods=['GET'])
@token_required
@role_required(Role.ADMIN, Role.SELLER)
def get_products():
    page = request.args.get('page', default=1, type=int)
    per_page = request.args.get('per_page', default=3, type=int)
    products, total_products = Products.get_paginated(page=page, per_page=per_page)
    total_pages = (total_products + per_page - 1) // per_page
    return jsonify({
        'data': [{
            'id': product.id,
            'name': product.name,
            'description': product.description,
            'price': product.price,
            'stock': product.stock,
            'category_id': product.category_id,
            'active': product.active
        } for product in products],
        'meta': {
            'page': page,
            'per_page': per_page,
            'total_pages': total_pages,
            'total_products': total_products,
            'has_next': page < total_pages,
            'has_prev': page > 1
        }
    }), 200

@products_bp.route('/products/<int:product_id>', methods=['GET'])
@token_required
@role_required(Role.ADMIN, Role.SELLER)
def get_product_by_id(product_id):
    product = Products.get_by_id(product_id)
    if product:
        return jsonify({
            'id': product.id,
            'name': product.name,
            'description': product.description,
            'price': product.price,
            'stock': product.stock,
            'category_id': product.category_id,
            'active': product.active
        })
    else:
        return jsonify({'success': False,
                         'message': 'Product not found'}), 404

@products_bp.route('/products', methods=['POST'])
@token_required
@role_required(Role.ADMIN)
def post_products():
    data = request.get_json()
    name = data.get('name')
    description = data.get('description')
    price = data.get('price')
    stock = data.get('stock', 0)
    category_id = data.get('category_id')
    errors = {}

    # name
    if not name:
        errors['name'] = 'name is required'
    else:
        existing_product = Products.get_by_name(name)
        if existing_product:
            errors['name'] = 'name must be unique'

    # price - HU2002: con is None, el 0 SI es valido
    if price is None:
        errors['price'] = 'price is required'
    else:
        try:
            price = float(price)
            if price < 0:
                errors['price'] = 'price must be a non-negative number'
        except (ValueError, TypeError):
            errors['price'] = 'price must be a number'

    # stock - HU2002: nuevo, se valida siempre
    try:
        stock = float(stock)
        if stock < 0:
            errors['stock'] = 'stock must be a non-negative number'
    except (ValueError, TypeError):
        errors['stock'] = 'stock must be a number'

    # category_id - HU2002: debe existir
    if category_id is None:
        errors['category_id'] = 'category_id is required'
    elif not Categories.get_by_id(category_id):
        errors['category_id'] = 'category_id does not exist'

    if errors:
        return jsonify({'success': False,
                         'message': 'Errors in data validation',
                         'validation-errors': errors}), 400

    new_product = Products(name=name, description=description, price=price, stock=stock, category_id=category_id)
    Products.save(new_product)
    return jsonify({
        'id': new_product.id,
        'name': new_product.name,
        'description': new_product.description,
        'price': new_product.price,
        'stock': new_product.stock,
        'category_id': new_product.category_id,
        'active': new_product.active
    }), 201

@products_bp.route('/products/<int:product_id>', methods=['PUT'])
@token_required
@role_required(Role.ADMIN)
def put_products(product_id):
    product = Products.get_by_id(product_id)
    if not product:
        return jsonify({'success': False,
                         'message': 'Product not found'}), 404

    data = request.get_json()
    name = data.get('name')
    description = data.get('description')
    price = data.get('price')
    stock = data.get('stock')
    category_id = data.get('category_id')
    errors = {}

    # HU2001: VALIDAR PRIMERO, sin tocar product todavia
    if name is not None and name != product.name:
        existing_product = Products.get_by_name(name)
        if existing_product:
            errors['name'] = 'name must be unique'

    if price is not None:
        try:
            price = float(price)
            if price < 0:
                errors['price'] = 'price must be a non-negative number'
        except (ValueError, TypeError):
            errors['price'] = 'price must be a number'

    if stock is not None:
        try:
            stock = float(stock)
            if stock < 0:
                errors['stock'] = 'stock must be a non-negative number'
        except (ValueError, TypeError):
            errors['stock'] = 'stock must be a number'

    if category_id is not None:
        if not Categories.get_by_id(category_id):
            errors['category_id'] = 'category_id does not exist'

    if errors:
        return jsonify({'success': False,
                         'message': 'Errors in data validation',
                         'validation-errors': errors}), 400

    # HU2001: solo si NO hay errores, ahora si asignamos
    if name is not None:
        product.name = name
    if description is not None:
        product.description = description
    if price is not None:
        product.price = price
    if stock is not None:
        product.stock = stock
    if category_id is not None:
        product.category_id = category_id

    Products.update(product)
    return jsonify({
        'id': product.id,
        'name': product.name,
        'description': product.description,
        'price': product.price,
        'stock': product.stock,
        'category_id': product.category_id,
        'active': product.active
    })