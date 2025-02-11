from flask import Flask, request, jsonify, render_template
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.sql import text  # Importa la función text

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+mysqlconnector://root:@localhost/optica'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Tabla intermedia para la relación muchos a muchos entre OrdenCompra y Producto
relacion_oc_p = db.Table('relacion_oc_p',
    db.Column('id_oc', db.Integer, db.ForeignKey('orden_compra.id'), primary_key=True),
    db.Column('id_p', db.Integer, db.ForeignKey('producto.id'), primary_key=True)
)

# Tabla intermedia para la relación muchos a muchos entre Venta y OrdenCompra
class RelacionVOC(db.Model):
    __tablename__ = 'relacion_v_oc'
    id = db.Column(db.Integer, primary_key=True)
    id_oc = db.Column(db.Integer, db.ForeignKey('orden_compra.id'))
    id_v = db.Column(db.Integer, db.ForeignKey('venta.id'))
    metodo_pago = db.Column(db.Enum('Efectivo', 'Credito', 'Debito'))
    pago_inicial = db.Column(db.Numeric(7, 2))
    estado = db.Column(db.Boolean)
    deuda = db.Column(db.Numeric(7, 2))
    fecha_pago = db.Column(db.DateTime)

class Sucursal(db.Model):
    __tablename__ = 'sucursal'
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(255))
    direccion = db.Column(db.String(255))
    correo = db.Column(db.String(255))
    telefono = db.Column(db.String(15))

class Producto(db.Model):
    __tablename__ = 'producto'
    id = db.Column(db.Integer, primary_key=True)
    tipo = db.Column(db.Enum('Oftálmico', 'Solar', 'Contacto'))
    precio = db.Column(db.Numeric(7, 2))
    disponible = db.Column(db.Boolean)
    ordenes_compra = db.relationship('OrdenCompra', secondary=relacion_oc_p, back_populates='productos')

class OrdenCompra(db.Model):
    __tablename__ = 'orden_compra'
    id = db.Column(db.Integer, primary_key=True)
    total_global = db.Column(db.Numeric(9, 2))
    fecha_compra = db.Column(db.DateTime)
    productos = db.relationship('Producto', secondary=relacion_oc_p, back_populates='ordenes_compra')
    ventas = db.relationship('Venta', secondary='relacion_v_oc', back_populates='ordenes_compra')

class Venta(db.Model):
    __tablename__ = 'venta'
    id = db.Column(db.Integer, primary_key=True)
    metodo_venta = db.Column(db.Boolean)
    entrega = db.Column(db.DateTime)
    cliente = db.Column(db.String(255))
    telefono_cliente = db.Column(db.String(20))
    id_sucursal = db.Column(db.Integer, db.ForeignKey('sucursal.id'))
    sucursal = db.relationship('Sucursal')
    ordenes_compra = db.relationship('OrdenCompra', secondary='relacion_v_oc', back_populates='ventas')

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

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)