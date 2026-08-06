from app import create_app
from extensions import db
from models import Product

app = create_app()

to_remove = ["Caramel Delight", "Hazelnut Delight", "Peach Delight", "Pistachio Delight"]

with app.app_context():
    deleted = 0
    for name in to_remove:
        product = Product.query.filter_by(name=name).first()
        if product:
            db.session.delete(product)
            deleted += 1
    db.session.commit()
    print(f"Removed {deleted} products from database.")
