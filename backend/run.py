from app import create_app
from app.models import alchemy_db
from app.config import settings

app = create_app()

with app.app_context():
    alchemy_db.create_all()

if __name__ == "__main__":
    app.run(host="0.0.0.0", debug=False, port=settings.PORT)
