from flask_sqlalchemy import SQLAlchemy

alchemy_db = SQLAlchemy()
sess = alchemy_db.session


class ElementGroups(alchemy_db.Model):
    __tablename__ = "ElementGroups"
    symbol = alchemy_db.Column(
        alchemy_db.String(30), unique=True, nullable=False, primary_key=True
    )
    img = alchemy_db.Column(alchemy_db.String(100), nullable=True)
    description = alchemy_db.Column(alchemy_db.String(100), nullable=True)

    def __init__(self, symbol, img, description):
        self.symbol = symbol
        self.img = img
        self.description = description

    @staticmethod
    def addData(symbol, img, description):
        try:
            data = ElementGroups(symbol, img, description)
            sess.add(data)
            sess.commit()
        except Exception as e:
            print("addData error!", e)
            return "error!"
        return "addData ok"

    @staticmethod
    def readData(symbol):
        query = ElementGroups.query.filter_by(symbol=symbol).first()
        return query

    @staticmethod
    def updateData(symbol, img, description):
        query = ElementGroups.query.filter_by(symbol=symbol).first()
        if query:
            query.img = img
            query.description = description
            sess.commit()
        else:
            ElementGroups.addData(symbol=symbol, img=img, description=description)
        return "updateData ok"

    @staticmethod
    def deleteData(symbol):
        query = ElementGroups.query.filter_by(symbol=symbol).first()
        sess.delete(query)
        sess.commit()
        return "deleteData ok"
