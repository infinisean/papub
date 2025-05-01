import argparse
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Boolean, ForeignKey, Enum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from db_connect import create_db_engine

Base = declarative_base()

# Define the possible values for the 'bu' and 'lifecycle' columns
BUEnum = Enum('retail', 'corp', name='bu_enum')
LifecycleEnum = Enum('prod', 'dev', 'stage', name='lifecycle_enum')

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
    bu = Column(BUEnum, nullable=False)  # Business Unit as an enum
    lifecycle = Column(LifecycleEnum, nullable=False)  # Lifecycle as an enum
    model = Column(String(50))
    sw_version = Column(String(50))
    ha = Column(Boolean, default=False)  # High Availability
    ha_partner = Column(String(30))
    interface_ips = Column(String(255))  # Comma-separated list of IPs

    # Establish a relationship with FirewallHealth
    health_records = relationship("FirewallHealth", back_populates="device")

class Thresholds(Base):
    __tablename__ = 'thresholds'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    hostname = Column(String(30), ForeignKey('devices.hostname'), nullable=False, unique=True)
    cpu_high = Column(Float)
    cpu_low = Column(Float)
    memory_used_high = Column(Float)
    memory_used_low = Column(Float)
    memory_free_high = Column(Float)
    memory_free_low = Column(Float)
    disk_usage_high = Column(Float)
    disk_usage_low = Column(Float)
    network_bandwidth_high = Column(Float)
    network_bandwidth_low = Column(Float)
    packet_rate_high = Column(Float)
    packet_rate_low = Column(Float)
    concurrent_connections_high = Column(Integer)
    concurrent_connections_low = Column(Integer)
    new_connections_per_sec_high = Column(Integer)
    new_connections_per_sec_low = Column(Integer)
    vpn_sessions_high = Column(Integer)
    vpn_sessions_low = Column(Integer)
    firewall_drops_high = Column(Integer)
    firewall_drops_low = Column(Integer)
    icmp_latency_high = Column(Float)
    icmp_latency_low = Column(Float)
    packet_loss_high = Column(Float)
    packet_loss_low = Column(Float)

class ARPEntry(Base):
    __tablename__ = 'arp_entries'
    
    device_id = Column(Integer, ForeignKey('devices.id'), primary_key=True)
    ip_address = Column(String(40), primary_key=True)  # Supports IPv4 and IPv6
    mac_address = Column(String(17), primary_key=True)
    timestamp = Column(DateTime, nullable=False)
    status = Column(String(10), nullable=False)  # "online" or "offline"

class ARPHistory(Base):
    __tablename__ = 'arp_history'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    device_id = Column(Integer, ForeignKey('devices.id'), nullable=False)
    ip_address = Column(String(40), nullable=False)
    mac_address = Column(String(17), nullable=False)
    timestamp = Column(DateTime, nullable=False)
    status = Column(String(10), nullable=False)  # "online" or "offline"

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