# restore_pgadmin_products.py — возвращаем твои оригинальные 6 товаров из pgAdmin
from run import app, db, Product

with app.app_context():
    
    Product.query.delete()
    db.session.commit()

    p1 = Product(name="Худи Oversize Black",    price=15990, image="static/css/images/hudi_black.jpg")
    p2 = Product(name="Джинсы Baggy",         price=27990, image="static/css/images/cargo_beige.jpg")
    p3 = Product(name="Кожаная куртка косуха оверсайз",        price=34990, image="static/css/images/leather.jpg")
    p4 = Product(name="Кроп-топ с открытой спиной",     price=4990, image="static/css/images/crop.jpg")
    p5 = Product(name="Джинсовая куртка с вышивкой дракона",        price=64990, image="static/css/images/dragon.jpg")
    p6 = Product(name="Спортивный костюм Y2K серебро",           price=29990, image="static/css/images/y2k_silver.jpg")

    db.session.add_all([p1, p2, p3, p4, p5, p6])
    db.session.commit()

    print("ГОТОВО! Твои оригинальные 6 товаров из pgAdmin восстановлены")
    print("Запускай: python3 run.py")