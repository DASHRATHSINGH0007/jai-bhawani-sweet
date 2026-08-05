from models import Product, User
from products_data import PRODUCTS
from extensions import db


def seed_database():
    if not User.query.filter_by(username="admin").first():
        if not User.query.filter_by(email="admin@jaybhawani.com").first():
            admin = User(
                fullname="Bhopal Singh",
                email="admin@jaybhawani.com",
                mobile="9999999999",
                username="admin",
                is_admin=True,
            )
            admin.set_password("admin123")
            db.session.add(admin)
            db.session.commit()

    if Product.query.count() == 0:
        for category, items in PRODUCTS.items():
            for item in items:
                db.session.add(
                    Product(
                        category=category,
                        name=item["name"],
                        image=item["image"],
                        description=item["desc"],
                        price=item["price"],
                    )
                )
        db.session.commit()
