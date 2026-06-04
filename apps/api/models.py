from sqlalchemy import Column, Integer, Float, String, JSON, DateTime
from sqlalchemy.sql import func
from apps.api.db import Base


class CachedTimeSeries(Base):
    __tablename__ = "cached_time_series"

    id = Column(Integer, primary_key=True)
    lat = Column(Float, nullable=False)
    lon = Column(Float, nullable=False)
    lat_key = Column(Float, nullable=False)
    lon_key = Column(Float, nullable=False)
    data = Column(JSON, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class CachedForecast(Base):
    __tablename__ = "cached_forecasts"

    id = Column(Integer, primary_key=True)
    lat_key = Column(Float, nullable=False)
    lon_key = Column(Float, nullable=False)
    scenario = Column(String(50), nullable=False)
    data = Column(JSON, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
