from flask import Response, flash, redirect, render_template, request, url_for, session, jsonify
from sqlalchemy import inspect, text

from auth_utils import admin_required_web, get_current_user, login_required, login_user, logout_user
from extensions import db
from models import Order, Product, User
from seed import seed_database


def register_web_routes(app):

    @app.route("/css/page-background.css")
    def page_background_css():
        return Response(render_template("page-background.css"), mimetype="text/css")

    @app.context_processor
    def inject_globals():
        ctx = {
            "bg_image_url": url_for("static", filename="images/background.jpg"),
            "page_bg_css_url": url_for("page_background_css"),
            "current_user": None,
        }
        if not login_required():
            ctx["current_user"] = get_current_user()
        return ctx

    @app.route("/")
    def home():
        if login_required():
            return redirect(url_for("login"))
        return render_template("home.html")

    @app.route("/profile")
    def profile():
        if login_required():
            flash("Please log in to view your profile.", "warning")
            return redirect(url_for("login"))
        user = get_current_user()
        orders = (
            Order.query.filter_by(user_id=user.id)
            .order_by(Order.created_at.desc())
            .all()
        )
        return render_template("profile.html", user=user, orders=orders)

    @app.route("/login", methods=["GET", "POST"])
    def login():
        if request.method == "POST":
            username = request.form.get("username", "").strip()
            password = request.form.get("password", "")
            user = User.query.filter_by(username=username).first()
            if user and user.check_password(password):
                login_user(user)
                flash("Login successful!", "success")
                return redirect(url_for("home"))
            flash("Invalid username or password", "danger")
        return render_template("login.html")

    @app.route("/signup", methods=["GET", "POST"])
    def signup():
        if request.method == "POST":
            fullname = request.form.get("fullname", "").strip()
            email = request.form.get("email", "").strip().lower()
            mobile = request.form.get("mobile", "").strip()
            username = request.form.get("username", "").strip()
            password = request.form.get("password", "")
            confirm = request.form.get("confirm-password", "")

            if password != confirm:
                flash("Passwords do not match", "danger")
                return render_template("signup.html")
            if len(mobile) != 10 or not mobile.isdigit():
                flash("Mobile number must be 10 digits", "danger")
                return render_template("signup.html")
            if User.query.filter_by(username=username).first():
                flash("Username already taken", "danger")
                return render_template("signup.html")
            if User.query.filter_by(email=email).first():
                flash("Email already registered", "danger")
                return render_template("signup.html")

            user = User(fullname=fullname, email=email, mobile=mobile, username=username)
            user.set_password(password)
            db.session.add(user)
            db.session.commit()
            flash("Account created. Please log in.", "success")
            return redirect(url_for("login"))
        return render_template("signup.html")

    @app.route("/logout")
    def logout():
        logout_user()
        flash("Logged out successfully.", "info")
        return redirect(url_for("login"))

    @app.route("/forgot-password")
    def forgot_password():
        return render_template("forgot.html")

    @app.route("/forgot")
    def forgot_alias():
        return redirect(url_for("forgot_password"))

    @app.route("/admin")
    def admin():
        guard = admin_required_web()
        if guard:
            return guard
        user = get_current_user()
        orders = Order.query.order_by(Order.created_at.desc()).limit(20).all()
        return render_template(
            "admin.html",
            admin_user=user,
            orders=orders,
            user_count=User.query.count(),
            order_count=Order.query.count(),
        )

    @app.route("/admin/order/<int:order_id>/status", methods=["POST"])
    def update_order_status(order_id):
        guard = admin_required_web()
        if guard:
            return guard

        status = request.form.get("status", "").strip().lower()
        if status not in ("pending", "accepted", "delivered", "cancelled"):
            flash("Invalid order status.", "danger")
            return redirect(url_for("admin"))

        order = Order.query.get_or_404(order_id)
        order.status = status
        if status in ("accepted", "delivered") and order.payment_method in ("upi", "card"):
            order.payment_status = "paid"
        db.session.commit()
        flash(f"Order #{order.id} marked as {status}.", "success")
        return redirect(url_for("admin"))

    def products_for_category(category):
        return [p.to_dict() for p in Product.query.filter_by(category=category).order_by(Product.name).all()]

    @app.route("/cart")
    def cart():
        cart_items = session.get("cart", [])
        enriched_cart = []
        total = 0
        import re
        for item in cart_items:
            prod = Product.query.filter_by(name=item.get("product_name")).first()
            if prod:
                price_num = 0
                if prod.price:
                    digits = re.sub(r'[^\d]', '', prod.price)
                    if digits:
                        price_num = int(digits)
                item_total = price_num * item.get("quantity", 1)
                total += item_total
                enriched_cart.append({
                    "product_name": item.get("product_name"),
                    "category": item.get("category", ""),
                    "quantity": item.get("quantity", 1),
                    "image": prod.image,
                    "desc": prod.description,
                    "price_str": prod.price,
                    "price_num": price_num,
                    "item_total": item_total
                })
        return render_template("cart.html", enriched_cart=enriched_cart, total=total)

    @app.route("/cart/update", methods=["POST"])
    def update_cart():
        product_name = request.form.get("product_name")
        action = request.form.get("action")
        cart = session.get("cart", [])
        
        for item in cart:
            if item.get("product_name") == product_name:
                if action == "increase":
                    item["quantity"] += 1
                elif action == "decrease":
                    item["quantity"] -= 1
                elif action == "delete":
                    item["quantity"] = 0
                break
                
        # Remove items with 0 or less quantity
        cart = [item for item in cart if item.get("quantity", 0) > 0]
        
        session["cart"] = cart
        session.modified = True
        return redirect(url_for("cart"))

    @app.route("/create_razorpay_order", methods=["POST"])
    def create_razorpay_order():
        if not get_current_user():
            return jsonify({"error": "Unauthorized"}), 401
            
        cart_items = session.get("cart", [])
        if not cart_items:
            return jsonify({"error": "Cart is empty"}), 400
            
        import re
        total = 0
        for item in cart_items:
            product = Product.query.filter_by(name=item["product_name"]).first()
            if product:
                price_str = re.sub(r"[^\d.]", "", product.price)
                if price_str:
                    total += float(price_str) * item["quantity"]
                    
        if total == 0:
            return jsonify({"error": "Invalid cart total"}), 400
            
        import razorpay
        client = razorpay.Client(auth=(app.config['RAZORPAY_KEY_ID'], app.config['RAZORPAY_KEY_SECRET']))
        
        order_amount = int(total * 100)
        order_currency = 'INR'
        order_receipt = 'order_rcptid_' + str(get_current_user().id)
        
        try:
            razorpay_order = client.order.create(dict(amount=order_amount, currency=order_currency, receipt=order_receipt))
            return jsonify({
                "order_id": razorpay_order['id'],
                "amount": order_amount,
                "currency": order_currency,
                "key_id": app.config['RAZORPAY_KEY_ID']
            })
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @app.route("/checkout", methods=["POST"])
    def checkout():
        if login_required():
            flash("Please log in to checkout.", "warning")
            return redirect(url_for("login"))
            
        cart_items = session.get("cart", [])
        if not cart_items:
            flash("Your cart is empty.", "warning")
            return redirect(url_for("cart"))

        payment_method = request.form.get("payment_method", "cash").strip().lower()
        
        # Razorpay fields
        razorpay_payment_id = request.form.get("razorpay_payment_id", "").strip()
        razorpay_order_id = request.form.get("razorpay_order_id", "").strip()
        razorpay_signature = request.form.get("razorpay_signature", "").strip()
        
        delivery_name = request.form.get("delivery_name", "").strip()
        delivery_phone = request.form.get("delivery_phone", "").strip()
        address_line = request.form.get("address_line", "").strip()
        city = request.form.get("city", "").strip()
        state = request.form.get("state", "").strip()
        pincode = request.form.get("pincode", "").strip()
        
        if payment_method not in ("cash", "online"):
            payment_method = "cash"
            
        if not all([delivery_name, delivery_phone, address_line, city, state, pincode]):
            flash("Please fill in all delivery details.", "danger")
            return redirect(url_for("cart"))
            
        # Verify Razorpay signature if online payment
        if payment_method == "online":
            import razorpay
            client = razorpay.Client(auth=(app.config['RAZORPAY_KEY_ID'], app.config['RAZORPAY_KEY_SECRET']))
            try:
                client.utility.verify_payment_signature({
                    'razorpay_order_id': razorpay_order_id,
                    'razorpay_payment_id': razorpay_payment_id,
                    'razorpay_signature': razorpay_signature
                })
            except razorpay.errors.SignatureVerificationError:
                flash("Payment verification failed. Please try again.", "danger")
                return redirect(url_for("cart"))
            except Exception as e:
                flash(f"Payment error: {str(e)}", "danger")
                return redirect(url_for("cart"))
            
        user_id = get_current_user().id
        
        for item in cart_items:
            db.session.add(
                Order(
                    user_id=user_id,
                    product_name=item["product_name"],
                    category=item["category"],
                    quantity=item.get("quantity", 1),
                    payment_method=payment_method,
                    payment_status="paid" if payment_method == "online" else "pending",
                    razorpay_order_id=razorpay_order_id if payment_method == "online" else "",
                    razorpay_payment_id=razorpay_payment_id if payment_method == "online" else "",
                    razorpay_signature=razorpay_signature if payment_method == "online" else "",
                    delivery_name=delivery_name,
                    delivery_phone=delivery_phone,
                    address_line=address_line,
                    city=city,
                    state=state,
                    pincode=pincode,
                )
            )
            
        db.session.commit()
        session.pop("cart", None)
        flash("Order completed successfully!", "success")
        return redirect(url_for("profile"))

    @app.route("/api/cart")
    def api_cart_html():
        cart_items = session.get("cart", [])
        total = 0
        import re
        for item in cart_items:
            product = Product.query.filter_by(name=item["product_name"]).first()
            if product:
                item["image"] = product.image
                price_str = re.sub(r"[^\d.]", "", product.price)
                if price_str:
                    total += float(price_str) * item["quantity"]
        
        # Render a tiny HTML template for the offcanvas body (using string format since we don't have a template file for it)
        html = ""
        if not cart_items:
            html = '<div class="text-center mt-5"><p class="text-muted">Your cart is empty.</p></div>'
        else:
            html += '<ul class="list-group mb-3">'
            for item in cart_items:
                product = Product.query.filter_by(name=item["product_name"]).first()
                item_total = 0
                if product:
                    price_str = re.sub(r"[^\d.]", "", product.price)
                    if price_str:
                        item_total = float(price_str) * item["quantity"]
                        
                html += f'''
                <li class="list-group-item d-flex justify-content-between lh-sm">
                  <div>
                    <h6 class="my-0">{item["product_name"]}</h6>
                    <small class="text-muted">Qty: {item["quantity"]}</small>
                  </div>
                  <span class="text-muted">₹{item_total}</span>
                </li>'''
            html += f'''
                <li class="list-group-item d-flex justify-content-between">
                  <span>Total (INR)</span>
                  <strong>₹{total}</strong>
                </li>
            </ul>
            <a href="{url_for('cart')}" class="btn btn-primary w-100">Proceed to Checkout</a>
            '''
        return html

    @app.route("/bites")
    def bites():
        if login_required():
            flash("Please log in to view products.", "warning")
            return redirect(url_for("login"))
        return render_template("products.html", products=products_for_category("bites"), category="Bites")

    @app.route("/crunch")
    def crunch():
        if login_required():
            flash("Please log in to view products.", "warning")
            return redirect(url_for("login"))
        return render_template("products.html", products=products_for_category("crunch"), category="Crunch")

    @app.route("/delight")
    def delight():
        if login_required():
            flash("Please log in to view products.", "warning")
            return redirect(url_for("login"))
        return render_template("products.html", products=products_for_category("delight"), category="Delight")

    @app.route("/order", methods=["POST"])
    def place_order():

        product_name = request.form.get("product_name", "").strip()
        category = request.form.get("category", "").strip().lower()
        action = request.form.get("action", "buy")
        try:
            quantity = int(request.form.get("quantity") or 1)
        except (TypeError, ValueError):
            quantity = 1

        if product_name and category in ("bites", "crunch", "delight"):
            if "cart" not in session:
                session["cart"] = []
            
            # Check if item is already in cart, if so, increase quantity
            cart = session["cart"]
            item_found = False
            for item in cart:
                if item["product_name"] == product_name:
                    item["quantity"] += quantity
                    item_found = True
                    break
                    
            if not item_found:
                cart.append({
                    "product_name": product_name,
                    "category": category,
                    "quantity": max(1, quantity)
                })
                
            session.modified = True
            
            is_ajax = request.headers.get("X-Requested-With") == "XMLHttpRequest"
            if is_ajax:
                return jsonify({"success": True, "cart_count": len(session["cart"]), "message": f"Added {product_name} to cart!", "action": action})
            
            if action == "buy":
                flash(f"Added {product_name} to your cart. Complete your order below!", "success")
                return redirect(url_for("cart"))
            else:
                flash(f"Added {quantity}x {product_name} to cart!", "success")
                return redirect(request.referrer or url_for("home"))
                
        is_ajax = request.headers.get("X-Requested-With") == "XMLHttpRequest"
        if is_ajax:
            return jsonify({"success": False, "message": "Could not process request."}), 400
            
        flash("Could not process request.", "danger")
        return redirect(url_for("home"))

    @app.route("/order/<int:order_id>/delete", methods=["POST"])
    def delete_order(order_id):
        if login_required():
            flash("Please log in to remove an order.", "warning")
            return redirect(url_for("login"))

        order = Order.query.filter_by(id=order_id, user_id=get_current_user().id).first()
        if not order:
            flash("Order not found.", "danger")
            return redirect(url_for("profile"))

        db.session.delete(order)
        db.session.commit()
        flash(f"Removed order for {order.product_name}.", "info")
        return redirect(url_for("profile"))


def init_database(app):
    with app.app_context():
        db.create_all()
        ensure_order_columns()
        seed_database()


def ensure_order_columns():
    inspector = inspect(db.engine)
    if "orders" not in inspector.get_table_names():
        return

    columns = {column["name"] for column in inspector.get_columns("orders")}
    migrations = {
        "payment_method": "ALTER TABLE orders ADD COLUMN payment_method VARCHAR(20) NOT NULL DEFAULT 'cash'",
        "payment_status": "ALTER TABLE orders ADD COLUMN payment_status VARCHAR(20) NOT NULL DEFAULT 'pending'",
        "delivery_name": "ALTER TABLE orders ADD COLUMN delivery_name VARCHAR(120) NOT NULL DEFAULT ''",
        "delivery_phone": "ALTER TABLE orders ADD COLUMN delivery_phone VARCHAR(15) NOT NULL DEFAULT ''",
        "address_line": "ALTER TABLE orders ADD COLUMN address_line VARCHAR(240) NOT NULL DEFAULT ''",
        "city": "ALTER TABLE orders ADD COLUMN city VARCHAR(80) NOT NULL DEFAULT ''",
        "state": "ALTER TABLE orders ADD COLUMN state VARCHAR(80) NOT NULL DEFAULT ''",
        "pincode": "ALTER TABLE orders ADD COLUMN pincode VARCHAR(10) NOT NULL DEFAULT ''",
    }
    for column, statement in migrations.items():
        if column not in columns:
            db.session.execute(text(statement))
    db.session.commit()
