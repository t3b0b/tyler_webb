from flask_migrate import migrate,Migrate


def init(app,db):


    with app.app_context():
        db.create_all()