import logging
from app.core.database import engine, Base
from app.models.job import Job

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def reset_db():
    logger.warning("DROPPING ALL TABLES. Data will be lost.")
    Base.metadata.drop_all(bind=engine)
    
    logger.info("CREATING ALL TABLES with updated schema...")
    Base.metadata.create_all(bind=engine)
    logger.info("Database reset successful.")

if __name__ == "__main__":
    reset_db()
