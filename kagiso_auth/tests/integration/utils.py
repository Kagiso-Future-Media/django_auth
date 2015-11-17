import uuid


def random_email():
    return '{0}@email.com'.format(uuid.uuid4().hex)
