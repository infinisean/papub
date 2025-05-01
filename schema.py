from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Boolean
from sqlalchemy.ext.declarative import declarative_base
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

class Device(Base):
    __tablename__ = 'devices'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    hostname = Column(String(255), nullable=False)
    mgmt_ip = Column(String(45), nullable=False)  # Supports IPv4 and IPv6
    serial_number = Column(String(255), nullable=False)
    mac_address = Column(String(17), nullable=False)
    lat_long = Column(String(50))  # Latitude and Longitude as a string
    bu = Column(String(50))  # Business Unit, e.g., 'retail' or 'corp'
    lifecycle = Column(String(50))  # e.g., 'prod', 'dev', 'stage'
    model = Column(String(255))
    sw_version = Column(String(50))
    ha = Column(Boolean, default=False)  # High Availability
    ha_partner = Column(String(255))
    interface_ips = Column(String(255))  # Comma-separated list of IPs

def setup_database():
    engine = create_db_engine()
    Base.metadata.create_all(engine)

if __name__ == "__main__":
    setup_database()