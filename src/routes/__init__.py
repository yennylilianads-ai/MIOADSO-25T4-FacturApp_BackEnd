
from src.routes.v1.products_routes import products_bp
from src.routes.v1.auth_routes import auth_bp
from src.routes.v1.users_routes import users_bp  # NCFC: users routes (assign role)
from src.routes.v1.clients_routes import clients_bp
from src.routes.v1.invoices_routes import invoices_bp
from src.routes.v1.invoice_details_routes import invoice_details_bp


def register_routes(app):  # Register the routes with the Flask app
    app.register_blueprint(products_bp)  # Register the products blueprint
    app.register_blueprint(auth_bp)  # Register the auth blueprint
    app.register_blueprint(clients_bp)  # Register the clients blueprint
    app.register_blueprint(users_bp)  # NCFC: Register the users blueprint
    app.register_blueprint(invoices_bp)  # Register the invoices blueprint
    app.register_blueprint(invoice_details_bp)  # Register the invoice details blueprint
    