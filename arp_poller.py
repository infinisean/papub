import time
from datetime import datetime
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError
from schema import ARPEntry, ARPHistory, Device, setup_database
from db_connect import create_db_engine

def get_arp_table(device):
    # Placeholder function to simulate ARP table retrieval
    # Replace with actual API call to get ARP table from the device
    return [
        {'ip_address': '192.168.1.1', 'mac_address': '00:11:22:33:44:55'},
        # Add more entries as needed
    ]

def update_arp_entries():
    engine = create_db_engine()
    Session = sessionmaker(bind=engine)
    session = Session()

    try:
        devices = session.query(Device).all()
        for device in devices:
            current_arp_entries = get_arp_table(device)
            for entry in current_arp_entries:
                arp_entry = session.query(ARPEntry).filter_by(
                    device_id=device.id,
                    ip_address=entry['ip_address'],
                    mac_address=entry['mac_address']
                ).first()

                if arp_entry:
                    # Update existing entry
                    if arp_entry.status != 'online':
                        arp_entry.status = 'online'
                        # Log the status change in history
                        history_entry = ARPHistory(
                            device_id=device.id,
                            ip_address=entry['ip_address'],
                            mac_address=entry['mac_address'],
                            timestamp=datetime.now(),
                            status='online'
                        )
                        session.add(history_entry)
                    arp_entry.timestamp = datetime.now()
                else:
                    # Add new entry
                    new_arp_entry = ARPEntry(
                        device_id=device.id,
                        ip_address=entry['ip_address'],
                        mac_address=entry['mac_address'],
                        timestamp=datetime.now(),
                        status='online'
                    )
                    session.add(new_arp_entry)
                    # Log the new entry in history
                    history_entry = ARPHistory(
                        device_id=device.id,
                        ip_address=entry['ip_address'],
                        mac_address=entry['mac_address'],
                        timestamp=datetime.now(),
                        status='online'
                    )
                    session.add(history_entry)

            # Mark entries not seen in the current poll as offline
            offline_entries = session.query(ARPEntry).filter(
                ARPEntry.device_id == device.id,
                ARPEntry.timestamp < datetime.now()
            ).all()
            for offline_entry in offline_entries:
                if offline_entry.status != 'offline':
                    offline_entry.status = 'offline'
                    # Log the status change in history
                    history_entry = ARPHistory(
                        device_id=offline_entry.device_id,
                        ip_address=offline_entry.ip_address,
                        mac_address=offline_entry.mac_address,
                        timestamp=datetime.now(),
                        status='offline'
                    )
                    session.add(history_entry)

        session.commit()
    except SQLAlchemyError as e:
        print(f"An error occurred: {e}")
        session.rollback()
    finally:
        session.close()

if __name__ == "__main__":
    setup_database()
    while True:
        update_arp_entries()
        time.sleep(600)  # Poll every 10 minutes