from sqlalchemy import Column, DECIMAL, DateTime, String, TIMESTAMP, text
from sqlalchemy.dialects.mysql import INTEGER
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()
metadata = Base.metadata


class DefiMonitorBalance(Base):
    __tablename__ = 'defi_monitor_balance'

    id = Column(INTEGER(11), primary_key=True, unique=True)
    log_datetime = Column(DateTime)
    address = Column(String(50))
    project_name = Column(String(45))
    amount_lp = Column(DECIMAL(18, 4))
    lp_token_name = Column(String(45))
    name_token1 = Column(String(45))
    amount_token1 = Column(DECIMAL(18, 4))
    name_token2 = Column(String(45))
    amount_token2 = Column(DECIMAL(18, 4))
    name_claim_reward1 = Column(String(45))
    amount_claim_reward1 = Column(DECIMAL(18, 4))
    name_claim_reward2 = Column(String(45))
    amount_claim_reward2 = Column(DECIMAL(18, 4))
    name_claim_reward3 = Column(String(45))
    amount_claim_reward3 = Column(DECIMAL(18, 4))
    create_time = Column(TIMESTAMP, server_default=text("CURRENT_TIMESTAMP"))
    upate_time = Column(TIMESTAMP, server_default=text("CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP"))
    price_lp_token1 = Column(DECIMAL(18, 4))
    price_lp_token2 = Column(DECIMAL(18, 4))
    usd_value_lp_token1 = Column(DECIMAL(18, 4))
    usd_value_lp_token2 = Column(DECIMAL(18, 4))
    lp_eth_value = Column(DECIMAL(18, 4))
    total_claimable_usd_value = Column(DECIMAL(18, 4))


class DefiWalletToken(Base):
    __tablename__ = 'defi_wallet_token'

    id = Column(INTEGER(11), primary_key=True)
    address = Column(String(45))
    network = Column(String(20))
    token = Column(String(45))
    log_time = Column(DateTime)
    amount = Column(DECIMAL(18, 4))
    usd_value = Column(DECIMAL(18, 4))
    price = Column(DECIMAL(18, 4))