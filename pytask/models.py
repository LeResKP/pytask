from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    Boolean,
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


class Project(Base):
    idproject = Column(Integer,
                       nullable=False,
                       autoincrement=True,
                       primary_key=True)
    name = Column(String(255), nullable=False)
    bug_id = Column(String(255), nullable=True)


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
    bug_id = Column(String(255), nullable=True)

    times = relationship('TaskTime', backref=backref("task", uselist=False))
    project = relationship('Project', backref="tasks", uselist=False)

    def get_data_for_display(self, _date_to_str, **kw):
        """Returns the data for the display of a task in 'table'
        """
        bug_id = self.bug_id
        if not bug_id and self.project:
            bug_id = self.project.bug_id
        dic = {
            'ID': self.idtask,
            'Bug ID': bug_id and '#%s' % bug_id or None,
            'Project': self.project and self.project.name or '',
            'Description': self.description,
            'Status': self.status,
            'Priority': self.priority,
            'Creation': _date_to_str(self.creation_date),
            'Completed': (self.completed_date and
                          _date_to_str(self.completed_date) or None),
        }
        dic.update(kw)
        return dic


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


class Status(Base):
    idstatus = Column(Integer,
                      nullable=False,
                      autoincrement=True,
                      primary_key=True)

    active = Column(Boolean, nullable=True)
