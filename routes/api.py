from flask import Blueprint, jsonify, request, session

from auth_utils import api_admin_required, api_login_required, login_user
from extensions import db
from models import Order, Product, User

api_bp = Blueprint("api", __name__, url_prefix="/api")


@api_bp.get("/health")
def health():
    return jsonify({"ok": True, "message": "Jay Bhawani backend is running"})


@api_bp.get("/products")
def list_products():
    category = request.args.get("category")
    query = Product.query
    if category:
        query = query.filter_by(category=category.lower())
    products = [p.to_dict() for p in query.order_by(Product.category, Product.name).all()]
    return jsonify({"ok": True, "products": products})


@api_bp.get("/products/<category>")
def products_by_category(category):
    products = Product.query.filter_by(category=category.lower()).all()
    return jsonify({"ok": True, "category": category, "products": [p.to_dict() for p in products]})


@api_bp.post("/signup")
def api_signup():
    data = request.get_json(silent=True) or request.form
    fullname = (data.get("fullname") or "").strip()
    email = (data.get("email") or "").strip().lower()
    mobile = (data.get("mobile") or "").strip()
    username = (data.get("username") or "").strip()
    password = data.get("password") or ""
    confirm = data.get("confirm-password") or data.get("confirm_password") or password

    if not all([fullname, email, mobile, username, password]):
        return jsonify({"ok": False, "error": "All fields are required"}), 400
    if password != confirm:
        return jsonify({"ok": False, "error": "Passwords do not match"}), 400
    if len(mobile) != 10 or not mobile.isdigit():
        return jsonify({"ok": False, "error": "Mobile must be 10 digits"}), 400
    if User.query.filter_by(username=username).first():
        return jsonify({"ok": False, "error": "Username already taken"}), 409
    if User.query.filter_by(email=email).first():
        return jsonify({"ok": False, "error": "Email already registered"}), 409

    user = User(fullname=fullname, email=email, mobile=mobile, username=username)
    user.set_password(password)
    db.session.add(user)
    db.session.commit()
    return jsonify({"ok": True, "message": "Account created", "user": user.to_dict()}), 201


@api_bp.post("/login")
def api_login():
    data = request.get_json(silent=True) or request.form
    username = (data.get("username") or "").strip()
    password = data.get("password") or ""

    user = User.query.filter_by(username=username).first()
    if not user or not user.check_password(password):
        return jsonify({"ok": False, "error": "Invalid username or password"}), 401

    login_user(user)
    return jsonify({"ok": True, "message": "Login successful", "user": user.to_dict()})


@api_bp.post("/logout")
def api_logout():
    session.clear()
    return jsonify({"ok": True, "message": "Logged out"})


@api_bp.get("/me")
@api_login_required
def api_me():
    from auth_utils import get_current_user

    user = get_current_user()
    return jsonify({"ok": True, "user": user.to_dict()})


@api_bp.post("/orders")
@api_login_required
def create_order():
    from auth_utils import get_current_user

    data = request.get_json(silent=True) or request.form
    product_name = (data.get("product_name") or "").strip()
    category = (data.get("category") or "").strip().lower()
    payment_method = (data.get("payment_method") or "cash").strip().lower()
    delivery_name = (data.get("delivery_name") or "").strip()
    delivery_phone = (data.get("delivery_phone") or "").strip()
    address_line = (data.get("address_line") or "").strip()
    city = (data.get("city") or "").strip()
    state = (data.get("state") or "").strip()
    pincode = (data.get("pincode") or "").strip()
    try:
        quantity = int(data.get("quantity") or 1)
    except (TypeError, ValueError):
        return jsonify({"ok": False, "error": "Quantity must be a number"}), 400

    if not product_name or category not in ("bites", "crunch", "delight"):
        return jsonify({"ok": False, "error": "Invalid order data"}), 400
    if quantity < 1:
        return jsonify({"ok": False, "error": "Quantity must be at least 1"}), 400
    if payment_method not in ("cash", "upi", "card"):
        return jsonify({"ok": False, "error": "Invalid payment method"}), 400
    if not all([delivery_name, delivery_phone, address_line, city, state, pincode]):
        return jsonify({"ok": False, "error": "Complete delivery address is required"}), 400
    if len(delivery_phone) != 10 or not delivery_phone.isdigit():
        return jsonify({"ok": False, "error": "Delivery phone must be 10 digits"}), 400
    if len(pincode) != 6 or not pincode.isdigit():
        return jsonify({"ok": False, "error": "Pincode must be 6 digits"}), 400

    order = Order(
        user_id=get_current_user().id,
        product_name=product_name,
        category=category,
        quantity=quantity,
        payment_method=payment_method,
        payment_status="pending" if payment_method == "cash" else "paid",
        delivery_name=delivery_name,
        delivery_phone=delivery_phone,
        address_line=address_line,
        city=city,
        state=state,
        pincode=pincode,
    )
    db.session.add(order)
    db.session.commit()
    return jsonify({"ok": True, "message": "Order placed", "order": order.to_dict()}), 201


@api_bp.get("/orders")
@api_login_required
def my_orders():
    from auth_utils import get_current_user

    orders = Order.query.filter_by(user_id=get_current_user().id).order_by(Order.created_at.desc()).all()
    return jsonify({"ok": True, "orders": [o.to_dict() for o in orders]})


@api_bp.delete("/orders/<int:order_id>")
@api_login_required
def delete_my_order(order_id):
    from auth_utils import get_current_user

    order = Order.query.filter_by(id=order_id, user_id=get_current_user().id).first()
    if not order:
        return jsonify({"ok": False, "error": "Order not found"}), 404

    db.session.delete(order)
    db.session.commit()
    return jsonify({"ok": True, "message": "Order removed"})


@api_bp.get("/admin/users")
@api_admin_required
def admin_users():
    users = User.query.order_by(User.created_at.desc()).all()
    return jsonify({"ok": True, "users": [u.to_dict() for u in users]})


@api_bp.get("/admin/orders")
@api_admin_required
def admin_orders():
    orders = Order.query.order_by(Order.created_at.desc()).all()
    result = []
    for o in orders:
        row = o.to_dict()
        row["username"] = o.user.username if o.user else None
        result.append(row)
    return jsonify({"ok": True, "orders": result})


@api_bp.patch("/admin/orders/<int:order_id>")
@api_admin_required
def update_admin_order(order_id):
    data = request.get_json(silent=True) or request.form
    status = (data.get("status") or "").strip().lower()
    if status not in ("pending", "accepted", "delivered", "cancelled"):
        return jsonify({"ok": False, "error": "Invalid order status"}), 400

    order = Order.query.get_or_404(order_id)
    order.status = status
    if status in ("accepted", "delivered") and order.payment_method in ("upi", "card"):
        order.payment_status = "paid"
    db.session.commit()
    return jsonify({"ok": True, "message": "Order updated", "order": order.to_dict()})
