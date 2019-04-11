from sqlalchemy import create_engine

from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()
class Snapshot(Base):
    __tablename__ = 'snapshot'
    # Here we define columns for the table person
    # Notice that each column is also a normal Python instance attribute.
    id = Column(Integer, primary_key=True)
    snap_amount = Column(String(100))
    snap_type = Column(String(100))
    snap_created_at = Column(String(64))
    snap_asset_name = Column(String(250))
    snap_asset_asset_id = Column(String(64))
    snap_asset_chain_id = Column(String(64))
    snap_asset_symbol   = Column(String(250))
    snap_snapshot_id = Column(String(64))

    snap_memo = Column(String(512), nullable=True)
    snap_source = Column(String(250), nullable=True)
    snap_user_id = Column(String(64), nullable=True)
    snap_trace_id = Column(String(64), nullable=True)
    snap_opponent_id = Column(String(64), nullable=True)

    def __repr__(self):
        return "<Snap (id='%s', created at ='%s')>" % (
                                self.snap_snapshot_id, self.snap_created_at)
