import argparse
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Boolean, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from db_connect import create_db_engine

Base = declarative_base()

class FirewallHealth(Base):
    __tablename__ = 'firewall_health'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    hostname = Column(String(30), ForeignKey('devices.hostname'), nullable=False)
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

    # Establish a relationship with Device
    device = relationship("Device", back_populates="health_records")

class Device(Base):
    __tablename__ = 'devices'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    hostname = Column(String(30), nullable=False, unique=True)  # Ensure hostname is unique
    mgmt_ip = Column(String(40), nullable=False)  # Supports IPv4 and IPv6
    serial_number = Column(String(30), nullable=False)
    mac_address = Column(String(17), nullable=False)
    lat_long = Column(String(50))  # Latitude and Longitude as a string
    bu = Column(String(50))  # Business Unit, e.g., 'retail' or 'corp'
    lifecycle = Column(String(50))  # e.g., 'prod', 'dev', 'stage'
    model = Column(String(50))
    sw_version = Column(String(50))
    ha = Column(Boolean, default=False)  # High Availability
    ha_partner = Column(String(30))
    interface_ips = Column(String(255))  # Comma-separated list of IPs

    # Establish a relationship with FirewallHealth
    health_records = relationship("FirewallHealth", back_populates="device")

def setup_database(drop_tables=False):
    engine = create_db_engine()
    if drop_tables:
        confirmation = input("Are you sure you want to drop these tables? This can't be undone!! (yes/no): ")
        if confirmation.lower() != 'yes':
            print("Operation cancelled.")
            return
        Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Setup the database schema.")
    parser.add_argument('-d', '--drop', action='store_true', help="Drop tables before creating them.")
    args = parser.parse_args()

    setup_database(drop_tables=args.drop)