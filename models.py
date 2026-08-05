from datetime import datetime

from werkzeug.security import check_password_hash, generate_password_hash

from extensions import db


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    fullname = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    mobile = db.Column(db.String(15), nullable=False)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=False)
    is_admin = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    orders = db.relationship("Order", backref="user", lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def to_dict(self):
        return {
            "id": self.id,
            "fullname": self.fullname,
            "email": self.email,
            "mobile": self.mobile,
            "username": self.username,
            "is_admin": self.is_admin,
        }


class Product(db.Model):
    __tablename__ = "products"

    id = db.Column(db.Integer, primary_key=True)
    category = db.Column(db.String(20), nullable=False, index=True)
    name = db.Column(db.String(120), nullable=False)
    image = db.Column(db.String(120), nullable=False)
    description = db.Column(db.Text, nullable=False)
    price = db.Column(db.String(30), nullable=False)

    def to_dict(self):
        return {
            "id": self.id,
            "category": self.category,
            "name": self.name,
            "image": self.image,
            "desc": self.description,
            "price": self.price,
        }


class Order(db.Model):
    __tablename__ = "orders"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    product_name = db.Column(db.String(120), nullable=False)
    category = db.Column(db.String(20), nullable=False)
    quantity = db.Column(db.Integer, default=1, nullable=False)
    payment_method = db.Column(db.String(20), default="cash", nullable=False)
    payment_status = db.Column(db.String(20), default="pending", nullable=False)
    delivery_name = db.Column(db.String(120), default="", nullable=False)
    delivery_phone = db.Column(db.String(15), default="", nullable=False)
    address_line = db.Column(db.String(240), default="", nullable=False)
    city = db.Column(db.String(80), default="", nullable=False)
    state = db.Column(db.String(80), default="", nullable=False)
    pincode = db.Column(db.String(10), default="", nullable=False)
    status = db.Column(db.String(20), default="pending", nullable=False)
    transaction_id = db.Column(db.String(100), default="", nullable=True)
    razorpay_order_id = db.Column(db.String(100), default="", nullable=True)
    razorpay_payment_id = db.Column(db.String(100), default="", nullable=True)
    razorpay_signature = db.Column(db.String(200), default="", nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "product_name": self.product_name,
            "category": self.category,
            "quantity": self.quantity,
            "payment_method": self.payment_method,
            "payment_status": self.payment_status,
            "delivery_address": {
                "name": self.delivery_name,
                "phone": self.delivery_phone,
                "address_line": self.address_line,
                "city": self.city,
                "state": self.state,
                "pincode": self.pincode,
            },
            "status": self.status,
            "razorpay_order_id": self.razorpay_order_id,
            "razorpay_payment_id": self.razorpay_payment_id,
            "created_at": self.created_at.isoformat(),
        }
