from sqlalchemy import (
    Column,
    Integer,
    Text,
    String,
    create_engine,
    ForeignKey,
    Table,
    Boolean,
    DateTime,
)

from sqlalchemy.orm import (
    scoped_session,
    sessionmaker,
    relationship,
    backref
)

from zope.sqlalchemy import ZopeTransactionExtension
from sqla_declarative import extended_declarative_base


DBSession = scoped_session(sessionmaker(extension=ZopeTransactionExtension()))
Base = extended_declarative_base(DBSession)
engine = create_engine('sqlite:///pytask.db', echo=False)
DBSession.configure(bind=engine)
Base.metadata.bind = engine


class Task(Base):

    idtask = Column(Integer,
                    nullable=False,
                    autoincrement=True,
                    primary_key=True)
    name = Column(String(255), nullable=False)
    times = relationship('TaskTime', backref=backref("task", uselist=False))


class TaskTime(Base):

    idtasktime = Column(Integer,
                        nullable=False,
                        autoincrement=True,
                        primary_key=True)
    idtask = Column(Integer,
                    ForeignKey('task.idtask'),
                    nullable=False)
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=True)
