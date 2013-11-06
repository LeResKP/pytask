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

import datetime

DBSession = scoped_session(sessionmaker(extension=ZopeTransactionExtension()))
Base = extended_declarative_base(DBSession)
engine = create_engine('sqlite:///pytask.db', echo=False)
DBSession.configure(bind=engine)
Base.metadata.bind = engine


class Project(Base):
    idproject = Column(Integer,
                       nullable=False,
                       autoincrement=True,
                       primary_key=True)
    name = Column(String(255), nullable=False)


class Task(Base):
    idtask = Column(Integer,
                    nullable=False,
                    autoincrement=True,
                    primary_key=True)
    description = Column(String(255), nullable=False)
    idproject = Column(Integer,
                       ForeignKey('project.idproject'),
                       nullable=True)
    creation_date = Column(DateTime, nullable=False,
                           default=datetime.datetime.now)
    completed_date = Column(DateTime, nullable=True)
    priority = Column(String(255), nullable=True)
    status = Column(String(255), nullable=True)

    project = relationship('Project', backref="tasks", uselist=False)
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
