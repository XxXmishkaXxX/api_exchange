from sqlalchemy import Column, Integer, String


from app.db.database import Base


class Asset(Base):
    __tablename__ = "assets"

    id = Column(Integer, primary_key=True, autoincrement=True)
    ticker = Column(String(10), unique=True, nullable=False)
    name = Column(String(100), nullable=False)

    def __repr__(self):
        return f"<Ticker(id={self.id}, symbol={self.ticker}, name={self.name})>"

