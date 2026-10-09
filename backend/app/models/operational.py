from __future__ import annotations
from datetime import datetime, date
from sqlalchemy import (
    Column,
    Integer,
    BigInteger,
    String,
    Numeric,
    Text,
    Date,
    DateTime,
    ForeignKey,
    Boolean,
    JSON,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class Customer(Base):
    __tablename__ = "customers"

    id = Column(Integer, primary_key=True, index=True)
    customer_code = Column(String(20), unique=True, nullable=False, index=True)
    company_name = Column(String(150), nullable=False)
    industry_type = Column(String(50), nullable=False)
    pic_name = Column(String(100), nullable=False)
    pic_phone = Column(String(30), nullable=False)
    pic_email = Column(String(100), nullable=False)
    delivery_port = Column(String(100), nullable=False)
    payment_term_days = Column(Integer, default=30)
    credit_limit_usd = Column(Numeric(15, 2), default=0.00)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    shipments = relationship("BargeShipment", back_populates="customer")


class Supplier(Base):
    __tablename__ = "suppliers"

    id = Column(Integer, primary_key=True, index=True)
    supplier_code = Column(String(20), unique=True, nullable=False, index=True)
    company_name = Column(String(150), nullable=False)
    concession_area = Column(String(100), nullable=False)
    pit_location = Column(String(100), nullable=False)
    pic_name = Column(String(100), nullable=False)
    pic_phone = Column(String(30), nullable=False)
    status = Column(String(20), default="ACTIVE")
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    inventory_batches = relationship("CoalInventory", back_populates="supplier")


class Stockpile(Base):
    __tablename__ = "stockpiles"

    id = Column(Integer, primary_key=True, index=True)
    stockpile_code = Column(String(20), unique=True, nullable=False, index=True)
    stockpile_name = Column(String(100), nullable=False)
    location = Column(String(100), nullable=False)
    province = Column(String(50), nullable=False)
    max_capacity_mt = Column(Numeric(12, 2), nullable=False)
    current_stock_mt = Column(Numeric(12, 2), nullable=False, default=0.00)
    manager_name = Column(String(100), nullable=False)
    contact_phone = Column(String(30), nullable=False)
    status = Column(String(20), default="OPERATIONAL")
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    inventory = relationship("CoalInventory", back_populates="stockpile", cascade="all, delete-orphan")
    origin_shipments = relationship("BargeShipment", back_populates="origin_stockpile")


class CoalInventory(Base):
    __tablename__ = "coal_inventory"

    id = Column(Integer, primary_key=True, index=True)
    stockpile_id = Column(Integer, ForeignKey("stockpiles.id", ondelete="CASCADE"), nullable=False, index=True)
    grade = Column(String(20), nullable=False, index=True)
    calorific_value_gar = Column(Integer, nullable=False)
    total_moisture_pct = Column(Numeric(5, 2), nullable=False)
    ash_content_pct = Column(Numeric(5, 2), nullable=False)
    total_sulfur_pct = Column(Numeric(5, 2), nullable=False)
    tonnage_mt = Column(Numeric(12, 2), nullable=False)
    batch_number = Column(String(50), nullable=False)
    supplier_id = Column(Integer, ForeignKey("suppliers.id"), nullable=True)
    last_survey_date = Column(Date, nullable=False)
    temperature_celsius = Column(Numeric(5, 2), default=38.5)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    stockpile = relationship("Stockpile", back_populates="inventory")
    supplier = relationship("Supplier", back_populates="inventory_batches")


class Barge(Base):
    __tablename__ = "barges"

    id = Column(Integer, primary_key=True, index=True)
    barge_code = Column(String(20), unique=True, nullable=False, index=True)
    barge_name = Column(String(100), nullable=False)
    tugboat_name = Column(String(100), nullable=False)
    capacity_feet = Column(Integer, nullable=False)
    max_capacity_mt = Column(Numeric(10, 2), nullable=False)
    owner_company = Column(String(100), nullable=False)
    status = Column(String(30), default="AVAILABLE")
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    shipments = relationship("BargeShipment", back_populates="barge")


class BargeShipment(Base):
    __tablename__ = "barge_shipments"

    id = Column(Integer, primary_key=True, index=True)
    shipment_number = Column(String(30), unique=True, nullable=False, index=True)
    barge_id = Column(Integer, ForeignKey("barges.id"), nullable=False)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False, index=True)
    stockpile_origin_id = Column(Integer, ForeignKey("stockpiles.id"), nullable=False)
    coal_grade = Column(String(20), nullable=False)
    tonnage_loaded_mt = Column(Numeric(10, 2), nullable=False)
    origin_jetty = Column(String(100), nullable=False)
    destination_port = Column(String(100), nullable=False)
    status = Column(String(30), nullable=False, index=True)
    etd = Column(DateTime(timezone=True), nullable=False)
    eta = Column(DateTime(timezone=True), nullable=False)
    actual_arrival = Column(DateTime(timezone=True), nullable=True)
    surveyor_company = Column(String(100), default="PT Surveyor Indonesia")
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    barge = relationship("Barge", back_populates="shipments")
    customer = relationship("Customer", back_populates="shipments")
    origin_stockpile = relationship("Stockpile", back_populates="origin_shipments")
