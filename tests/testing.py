import unittest
from sqlalchemy import create_engine
import pytask.models as models


class DBTestCase(unittest.TestCase):

    def setUp(self):
        engine = create_engine('sqlite://')
        models.DBSession.remove()
        models.DBSession.configure(bind=engine)
        models.Base.metadata.create_all(engine)

    def tearDown(self):
        models.DBSession.remove()
