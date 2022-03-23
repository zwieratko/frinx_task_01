import rapidjson
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy import Column, INTEGER, VARCHAR, JSON

JSON_FILE = "./configClear_v2.json"
selected_group = ["Port-channel", "GigabitEthernet", "TenGigabitEthernet"]  # "BDI", "Loopback",

# CREATE DB TABLE
db_string = "postgresql://postgres:secret@127.0.0.1:5432/postgres"

db = create_engine(db_string)
Base = declarative_base()


class Interface(Base):
    __tablename__ = "interface"

    id = Column(INTEGER, primary_key=True)
    connection = Column(INTEGER)
    name = Column(VARCHAR(255), nullable=False)
    description = Column(VARCHAR(255))
    config = Column(JSON)
    type = Column(VARCHAR(50))
    infra_type = Column(VARCHAR(50))
    port_channel_id = Column(INTEGER)
    max_frame_size = Column(INTEGER)


Session = sessionmaker(db)
session = Session()

Base.metadata.create_all(db)

# PARSE CONFIG FILE & SAVE TO DB
with open(JSON_FILE, mode="r") as data_file:
    all_data = rapidjson.load(
        data_file, parse_mode=rapidjson.PM_TRAILING_COMMAS).get('frinx-uniconfig-topology:configuration', {})
    all_device_interface_config = all_data.get('Cisco-IOS-XE-native:native', {}).get('interface', {})

    for interface_group_name, config_list in all_device_interface_config.items():
        if interface_group_name in selected_group:
            for config in config_list:
                device_name = f"{interface_group_name}{config.get('name', None)}"
                device_description = config.get('description', None)
                device_config = config
                device_port_channel_id = config.get('Cisco-IOS-XE-ethernet:channel-group', {}).get('number', None)
                device_max_frame_size = config.get('mtu', None)

                new_record = Interface(
                    name=device_name,
                    description=device_description,
                    config=device_config,
                    port_channel_id=device_port_channel_id,
                    max_frame_size=device_max_frame_size,
                )

                session.add(new_record)
                session.commit()

    session.close()
