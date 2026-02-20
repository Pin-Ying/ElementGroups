from app import create_app
from app.config import settings

app = create_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", debug=False, port=settings.PORT)
