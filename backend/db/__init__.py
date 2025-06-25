from .database import Base, engine, get_db
from .models import *

# Create all tables
Base.metadata.create_all(bind=engine)
