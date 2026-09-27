from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from .database import Base

class UserPortfolio(Base):
    __tablename__ = "user_portfolios"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    total_value = Column(Float, default=100000.0)  # Total value (assets + cash)
    cash = Column(Float, default=100000.0)         # Uninvested cash
    risk_tolerance = Column(String, default="moderate")  # conservative, moderate, aggressive
    target_esg_score = Column(Float, default=70.0)  # User's target ESG rating (0-100)
    current_esg_score = Column(Float, default=0.0)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    assets = relationship("PortfolioAsset", back_populates="portfolio", cascade="all, delete-orphan")
    rebalances = relationship("RebalanceLog", back_populates="portfolio", cascade="all, delete-orphan")

class PortfolioAsset(Base):
    __tablename__ = "portfolio_assets"

    id = Column(Integer, primary_key=True, index=True)
    portfolio_id = Column(Integer, ForeignKey("user_portfolios.id"))
    ticker = Column(String, index=True)
    shares = Column(Float, default=0.0)
    avg_buy_price = Column(Float, default=0.0)
    current_price = Column(Float, default=0.0)
    esg_score = Column(Float, default=0.0)

    # Relationships
    portfolio = relationship("UserPortfolio", back_populates="assets")

class RebalanceLog(Base):
    __tablename__ = "rebalance_logs"

    id = Column(Integer, primary_key=True, index=True)
    portfolio_id = Column(Integer, ForeignKey("user_portfolios.id"))
    timestamp = Column(DateTime, default=datetime.utcnow)
    action_summary = Column(String)  # Description of trades made
    old_esg_score = Column(Float)
    new_esg_score = Column(Float)
    old_sentiment = Column(Float)
    new_sentiment = Column(Float)

    # Relationships
    portfolio = relationship("UserPortfolio", back_populates="rebalances")
