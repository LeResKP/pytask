from .. import models
import transaction

if __name__ == '__main__':
    # models.Base.metadata.create_all(models.engine)
    models.Status.metadata.create_all(models.engine)
    with transaction.manager:
        s = models.Status(active=True)
        models.DBSession.add(s)
