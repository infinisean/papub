from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, MetaData, Table
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from db_connect import create_db_engine

Base = declarative_base()

class FirewallHealth(Base):
    __tablename__ = 'firewall_health'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    hostname = Column(String(255), nullable=False)
    timestamp = Column(DateTime, nullable=False)
    cpu_usage = Column(Float)
    memory_used = Column(Float)
    memory_free = Column(Float)
    disk_usage = Column(Float)
    network_bandwidth = Column(Float)
    packet_rate = Column(Float)
    concurrent_connections = Column(Integer)
    new_connections_per_sec = Column(Integer)
    vpn_sessions = Column(Integer)
    firewall_drops = Column(Integer)
    icmp_latency = Column(Float)
    packet_loss = Column(Float)

def setup_database():
    engine = create_db_engine()
    Base.metadata.create_all(engine)

if __name__ == "__main__":
    setup_database()