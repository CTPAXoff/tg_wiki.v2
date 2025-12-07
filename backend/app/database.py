from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, JSON, Index
from sqlalchemy.pool import NullPool
from datetime import datetime
from .config import config

class Base(DeclarativeBase):
    pass

class Session(Base):
    __tablename__ = "sessions"
    
    id = Column(Integer, primary_key=True, default=1)
    phone = Column(String(20))
    string_session = Column(Text)
    phone_code_hash = Column(String(100))
    status = Column(String(20), default="empty")  # empty, valid, invalid
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Message(Base):
    __tablename__ = "messages"
    
    id = Column(Integer, primary_key=True)
    chat_id = Column(Integer)  # Telegram chat ID
    msg_id = Column(Integer)   # Telegram message ID
    sender_id = Column(Integer)
    sender_name = Column(String(255))
    text = Column(Text)
    date = Column(DateTime)
    is_reply = Column(Boolean, default=False)
    reply_to_msg_id = Column(Integer, nullable=True)
    entities = Column(JSON, nullable=True)
    raw_json = Column(JSON)

    __table_args__ = (
        Index('idx_chat_msg', 'chat_id', 'msg_id'),
        Index('idx_sender', 'sender_id'),
        Index('idx_date', 'date'),
    )

# Database setup
engine = create_async_engine(
    config.DATABASE_URL,
    poolclass=NullPool,
    connect_args={
        "check_same_thread": False,
        "timeout": config.SQLITE_BUSY_TIMEOUT,
    },
    echo=False
)

# Enable WAL mode
async def enable_wal_mode():
    async with engine.begin() as conn:
        await conn.execute("PRAGMA journal_mode=WAL")
        await conn.execute("PRAGMA busy_timeout=%d" % config.SQLITE_BUSY_TIMEOUT)

SessionLocal = async_sessionmaker(
    engine, 
    class_=AsyncSession, 
    expire_on_commit=False
)

async def get_db():
    async with SessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()