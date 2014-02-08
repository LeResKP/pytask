from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    create_engine,
    ForeignKey,
)

from sqlalchemy.orm import (
    scoped_session,
    sessionmaker,
    backref,
    relationship,
)

from zope.sqlalchemy import ZopeTransactionExtension
from sqla_declarative import extended_declarative_base

import datetime


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
    description = Column(String(255), nullable=False)
    creation_date = Column(DateTime, nullable=False,
                           default=datetime.datetime.now)
    bug_id = Column(String(255), nullable=True)

    times = relationship('TaskTime', backref=backref("task", uselist=False))


class TaskTime(Base):
    idtasktime = Column(Integer,
                        nullable=False,
                        autoincrement=True,
                        primary_key=True)
    idtask = Column(Integer,
                    ForeignKey('task.idtask'),
                    nullable=False)
    start_date = Column(DateTime, nullable=False,
                        default=datetime.datetime.now)
    end_date = Column(DateTime, nullable=True)
