from sqlalchemy import DateTime, Float, Integer, String, func
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base


class Property(Base):
    __tablename__ = "properties"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    address: Mapped[str] = mapped_column(String(500), index=True)
    price_text: Mapped[str] = mapped_column(String(100), index=True)
    price_value: Mapped[float] = mapped_column(Float, index=True)
    link: Mapped[str] = mapped_column(String(1000), unique=True, index=True)
    embedding_vector: Mapped[list[float] | None] = mapped_column(ARRAY(Float), nullable=True)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())
