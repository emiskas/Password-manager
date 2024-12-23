from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.orm import declarative_base

engine = create_engine("sqlite:///passwords.sqlite")
Base = declarative_base()

class Passwords(Base):
    __tablename__ = "passwords"
    id = Column(Integer, primary_key=True)
    platform = Column("platform", String)
    login_name = Column("login_name", String)
    password_hash = Column("password_hash", String)


    def __init__(self, platform, login_name, password_hash):
        self.platform = platform
        self.login_name = login_name
        self.password_hash = password_hash


if __name__ == "__main__":
    Base.metadata.create_all(engine)