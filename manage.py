
import os
import unittest
#import coverage
from app import app, db
from flask.ext.script import Manager
from flask.ext.migrate import Migrate, MigrateCommand
app.config.from_object(os.environ['APP_SETTINGS'])

migrate = Migrate(app, db)
manager = Manager(app)

manager.add_command('db', MigrateCommand)

@manager.command
def test():
    """Runs the unit tests without coverage."""
    tests = unittest.TestLoader().discover('tests')
    result = unittest.TextTestRunner(verbosity=2).run(tests)
    if result.wasSuccessful():
        return 0
    else:
        return 1


if __name__ == '__main__':
    manager.run()