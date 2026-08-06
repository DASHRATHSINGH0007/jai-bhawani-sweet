from app import create_app
from extensions import db
from models import Product
from products_data import PRODUCTS

app = create_app()

with app.app_context():
    for category, items in PRODUCTS.items():
        for item in items:
            product = Product.query.filter_by(name=item["name"]).first()
            if product:
                product.image = item["image"]
                product.description = item["desc"]
                product.price = item["price"]
                product.category = category
            else:
                product = Product(
                    category=category,
                    name=item["name"],
                    image=item["image"],
                    description=item["desc"],
                    price=item["price"],
                )
                db.session.add(product)
    db.session.commit()
    print("Products synchronized!")
