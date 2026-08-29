from app import create_app
from app.models.base import db
from sqlalchemy import text

app = create_app()
with app.app_context():
    try:
        db.session.execute(text("ALTER TABLE property MODIFY COLUMN status VARCHAR(50) NOT NULL DEFAULT 'Pending'"))
        db.session.commit()
        print("Successfully altered property status column to VARCHAR(50)!")
    except Exception as e:
        db.session.rollback()
        print("Migration error:", e)
