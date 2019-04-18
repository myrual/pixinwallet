from sqlalchemy import Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()
class ScannedSnapshots(Base):
    __tablename__ = 'scannedsnapshots'
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
    def __repr__(self):
        return "<Snap (id='%s', created at ='%s')>" % (
                                self.snap_snapshot_id, self.snap_created_at)
class MySnapshot(Base):
    __tablename__ = 'mysnapshot'
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
class Mixin_asset_record(Base):
    __tablename__ = 'mixin_asset_record'
    # Here we define columns for the table person
    # Notice that each column is also a normal Python instance attribute.
    id = Column(Integer, primary_key=True)
    asset_id = Column(String(64))
    asset_symbol = Column(String(64))
    asset_name = Column(String(256))

    def __repr__(self):
        return "<Asset (id='%s', symbol ='%s', name ='%s')>" % (
                                self.asset_id, self.asset_symbol, self.asset_name)
class Ocean_trade_record(Base):
    __tablename__ = 'ocean_trade_record_list'
    # Here we define columns for the table person
    # Notice that each column is also a normal Python instance attribute.
    id = Column(Integer, primary_key=True)
    pay_asset_id = Column(String(64))
    pay_asset_amount = Column(String(64))
    asset_id = Column(String(64))
    price = Column(String(64))
    operation_type = Column(String(256))
    side = Column(String(64))
    order_id = Column(String(64))

    def __repr__(self):
        return "<Asset (id='%s', symbol ='%s', name ='%s')>" % (
                                self.asset_id, self.asset_symbol, self.asset_name)

