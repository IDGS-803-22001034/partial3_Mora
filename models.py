from flask_sqlalchemy import SQLAlchemy
import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()


class Cliente(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100))
    direccion = db.Column(db.String(100))
    telefono = db.Column(db.String(100))
    total = db.Column(db.Float, default=0.0)
    detalles = db.relationship('DetallePizza', backref='venta')
    created_date = db.Column(db.DateTime, 
                             default=datetime.datetime.now)


class DetallePizza(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    idCliente = db.Column(db.Integer, db.ForeignKey('cliente.id'))
    tamanio = db.Column(db.String(20))
    numerop = db.Column(db.Integer, default=1)
    subtotal = db.Column(db.Float)
    ingredientes = db.relationship(
        'IngredientePizza', backref='detalle_pizza')


class IngredientePizza(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    detalle_pizza_id = db.Column(db.Integer, db.ForeignKey('detalle_pizza.id'))
    nombre_ingrediente = db.Column(db.String(50))


class Usuario(UserMixin, db.Model):
    __tablename__ = 'usuario'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    fullname = db.Column(db.String(100), nullable=True)

    def __init__(self, username, password, fullname=""):
        self.username = username
        # genera el hash si la contraseña no es un hash ya puesto en base de datos
        if not password.startswith("scrypt"):
            self.password = generate_password_hash(password)
        else:
            self.password = password  # Aqui ya usa la contraseña en caso de que ya esté hasheada

        self.fullname = fullname

    @classmethod
    def check_password(cls, hashed_password, password):
        return check_password_hash(hashed_password, password)

    def __repr__(self):
        return f'<Usuario {self.username}>'

    
#print(generate_password_hash("Seguridad"))