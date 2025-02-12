from flask import Flask, request, jsonify, render_template
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.sql import text

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+mysqlconnector://root:@localhost/optica'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)


# Tabla intermedia para la relación muchos a muchos entre OrdenCompra y Producto
oc_p_relationship = db.Table('relacion_oc_p',
    db.Column('id_oc', db.Integer, db.ForeignKey('orden_compra.id'), primary_key=True),
    db.Column('id_p', db.Integer, db.ForeignKey('producto.id'), primary_key=True)
)


class VOC_Relationship(db.Model):
    __tablename__ = 'relacion_v_oc'
    id = db.Column(db.Integer, primary_key=True)
    id_oc = db.Column(db.Integer, db.ForeignKey('orden_compra.id'))
    id_v = db.Column(db.Integer, db.ForeignKey('venta.id'))
    payment_method = db.Column(db.Enum('Efectivo', 'Credito', 'Debito'))
    down_payment = db.Column(db.Numeric(7, 2))
    status = db.Column(db.Boolean)
    debt = db.Column(db.Numeric(7, 2))
    payment_date = db.Column(db.DateTime)

    def __init__(self, id_oc, id_v, payment_method, down_payment, status, debt, payment_date):
        self.id_oc = id_oc
        self.id_v = id_v
        self.payment_method = payment_method
        self.down_payment = down_payment
        self.status = status
        self.debt = debt
        self.payment_date = payment_date


class Branch(db.Model): 
    __tablename__ = 'sucursal'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255))
    address = db.Column(db.String(255))
    cellphone_number = db.Column(db.String(255))
    email_address = db.Column(db.String(255))

    def __init__(self, name, address, cellphone_number, email_address):
        self.name = name
        self.address = address
        self.cellphone_number = cellphone_number
        self.email_address = email_address


class Product(db.Model): 
    __tablename__ = 'producto'
    id = db.Column(db.Integer, primary_key=True)
    type = db.Column(db.Enum('Oftalmologico', 'Solar', 'Contacto'))
    price = db.Column(db.Numeric(7, 2))
    available = db.Column(db.Boolean)

    def __init__(self, type, price, available): 
        self.type = type
        self.price = price
        self.available = available


class PurchaseOrder(db.Model): 
    __tablename__ = 'orden_compra'
    id = db.Column(db.Integer, primary_key=True)
    total_global = db.Column(db.Numeric(9, 2))
    purchase_date = db.Column(db.DateTime)
    products = db.relationship('Product', secondary=oc_p_relationship, back_populates='purchase_orders')
    sales = db.relationship('Sale', secondary='relacion_v_oc', back_populates='purchase_orders')

    def __init__(self, total_global, purchase_date, products, sales):
        self.total_global = total_global
        self.purchase_date = purchase_date
        self.products = products
        self.sales = sales


class Sale(db.Model):
    __tablename__ = 'venta'
    id = db.Column(db.Integer, primary_key=True)
    sales_method = db.Column(db.Boolean)
    delivery = db.Column(db.DateTime)
    client = db.Column(db.String(255))
    phone_number_client = db.Column(db.String(20))
    id_branch = db.Column(db.Integer, db.ForeignKey('sucursal.id'))
    branch = db.relationship('Branch')
    purchase_orders = db.relationship('PurchaseOrder', secondary='relacion_v_oc', back_populates='sales')

    def __init__(self, sales_method, delivery, client, phone_number_client, id_branch, purchase_orders):
        self.sales_method = sales_method
        self.delivery = delivery
        self.client = client
        self.phone_number_client = phone_number_client
        self.id_branch = id_branch
        self.purchase_orders = purchase_orders


@app.route('/')
def index():
    return render_template('index.html')

@app.route('/check_db')
def check_db():
    try:
        db.session.execute(text('SELECT 1'))
        return jsonify({"message": "DB is running well"}), 200
    
    except Exception as e:
        print(f"Error connecting to the database: {e}")
        return jsonify({"message": "DB is not running", "error": str(e)}), 500


# CRUD operations for Product

# Create
@app.route('/product', methods=['POST'])
def create_product():
    data = request.get_json()
    new_product = Product(type=data['type'], price=data['price'], available=data['available'])
    db.session.add(new_product)
    db.session.commit()
    return jsonify({"message": "Product created successfully"}), 201


# Read
@app.route('/product', methods=['GET'])
def get_products():
    products = Product.query.all()
    return jsonify([{"id": product.id, "type": product.type, "price": product.price, "available": product.available} for product in products]), 200

@app.route('/product/<int:id>', methods=['GET'])
def get_product(id):
    product = Product.query.get(id)
    if product is None:
        return jsonify({"message": "Product not found"}), 404
    
    return jsonify({"id": product.id, "type": product.type, "price": product.price, "available": product.available}), 200


# Update
@app.route('/product/<int:id>', methods=['PUT'])
def update_product(id):
    data = request.get_json()
    product = Product.query.get(id)
    if product is None:
        return jsonify({"message": "Product not found"}), 404
    
    product.type = data['type']
    product.price = data['price']
    product.available = data['available']
    db.session.commit()
    return jsonify({"message": "Product updated successfully"}), 200


# Delete
@app.route('/product/<int:id>', methods=['DELETE'])
def delete_product(id):
    product = Product.query.get(id)
    if product is None:
        return jsonify({"message": "Product not found"}), 404
    
    db.session.delete(product)
    db.session.commit()
    return jsonify({"message": "Product deleted successfully"}), 200



# CRUD operations for PurchaseOrder

# Create
@app.route('/purchase_order', methods=['POST'])
def create_purchase_order():
    data = request.get_json()
    new_purchase_order = PurchaseOrder(
        total_global=data['total_global'], 
        purchase_date=data['purchase_date'], 
        products=[], 
        sales=[]
    )
    db.session.add(new_purchase_order)
    db.session.commit()
    return jsonify({"message": "Purchase order created successfully"}), 201

# Read
@app.route('/purchase_order', methods=['GET'])
def get_purchase_orders():
    purchase_orders = PurchaseOrder.query.all()
    return jsonify([{
        "id": po.id, 
        "total_global": po.total_global, 
        "purchase_date": po.purchase_date
    } for po in purchase_orders]), 200

@app.route('/purchase_order/<int:id>', methods=['GET'])
def get_purchase_order(id):
    purchase_order = PurchaseOrder.query.get(id)
    if purchase_order is None:
        return jsonify({"message": "Purchase order not found"}), 404
    
    return jsonify({
            "id": purchase_order.id, 
            "total_global": purchase_order.total_global, 
            "purchase_date": purchase_order.purchase_date
        }), 200


# Update
@app.route('/purchase_order/<int:id>', methods=['PUT'])
def update_purchase_order(id):
    data = request.get_json()
    purchase_order = PurchaseOrder.query.get(id)
    if purchase_order is None:
        return jsonify({"message": "Purchase order not found"}), 404
    purchase_order.total_global = data['total_global']
    purchase_order.purchase_date = data['purchase_date']
    db.session.commit()
    return jsonify({"message": "Purchase order updated successfully"}), 200


# Delete
@app.route('/purchase_order/<int:id>', methods=['DELETE'])
def delete_purchase_order(id):
    purchase_order = PurchaseOrder.query.get(id)
    if purchase_order is None:
        return jsonify({"message": "Purchase order not found"}), 404
    
    db.session.delete(purchase_order)
    db.session.commit()
    return jsonify({"message": "Purchase order deleted successfully"}), 200



# CRUD operations for Sale

# Create
@app.route('/sale', methods=['POST'])
def create_sale():
    data = request.get_json()
    new_sale = Sale(
        sales_method=data['sales_method'], 
        delivery=data['delivery'], 
        client=data['client'], 
        phone_number_client=data['phone_number_client'], 
        id_branch=data['id_branch'], 
        purchase_orders=[]
    )
    db.session.add(new_sale)
    db.session.commit()
    return jsonify({"message": "Sale created successfully"}), 201

# Read
@app.route('/sale', methods=['GET'])
def get_sales():
    sales = Sale.query.all()
    return jsonify([{
        "id": sale.id, 
        "sales_method": sale.sales_method, 
        "delivery": sale.delivery, 
        "client": sale.client, 
        "phone_number_client": sale.phone_number_client, 
        "id_branch": sale.id_branch
    } for sale in sales]), 200

@app.route('/sale/<int:id>', methods=['GET'])
def get_sale(id):
    sale = Sale.query.get(id)
    if sale is None:
        return jsonify({"message": "Sale not found"}), 404
    return jsonify({
        "id": sale.id, 
        "sales_method": sale.sales_method, 
        "delivery": sale.delivery, 
        "client": sale.client, 
        "phone_number_client": sale.phone_number_client, 
        "id_branch": sale.id_branch
    }), 200


# Update
@app.route('/sale/<int:id>', methods=['PUT'])
def update_sale(id):
    data = request.get_json()
    sale = Sale.query.get(id)
    if sale is None:
        return jsonify({"message": "Sale not found"}), 404
    sale.sales_method = data['sales_method']
    sale.delivery = data['delivery']
    sale.client = data['client']
    sale.phone_number_client = data['phone_number_client']
    sale.id_branch = data['id_branch']
    db.session.commit()
    return jsonify({"message": "Sale updated successfully"}), 200


# Delete
@app.route('/sale/<int:id>', methods=['DELETE'])
def delete_sale(id):
    sale = Sale.query.get(id)
    if sale is None:
        return jsonify({"message": "Sale not found"}), 404
    db.session.delete(sale)
    db.session.commit()
    return jsonify({"message": "Sale deleted successfully"}), 200


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)