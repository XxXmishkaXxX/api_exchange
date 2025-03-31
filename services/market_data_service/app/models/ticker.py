from sqlalchemy import Column, Integer, String


from app.db.database import Base


class Ticker(Base):
    __tablename__ = "tickers"

    id = Column(Integer, primary_key=True, autoincrement=True)
    symbol = Column(String(10), unique=True, nullable=False)
    name = Column(String(100), nullable=False)

    def __repr__(self):
        return f"<Ticker(id={self.id}, symbol={self.symbol}, name={self.name})>"

