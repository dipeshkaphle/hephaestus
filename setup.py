import os
import shutil
import glob
import distutils
import subprocess
from setuptools import setup, find_packages, Command
from pathlib import Path


here = os.path.abspath(os.path.dirname(__file__))


class CleanCommand(Command):
    """Custom clean command to tidy up the project root."""
    CLEAN_FILES = './build ./dist ./*.pyc ./*.tgz ./*.egg-info ./*/__pycache__/ ./*/*/__pycache__/ .pytest_cache'.split(' ')

    user_options = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        global here

        for path_spec in self.CLEAN_FILES:
            # Make paths absolute and relative to this path
            abs_paths = glob.glob(os.path.normpath(os.path.join(
                here, path_spec)))
            for path in [str(p) for p in abs_paths]:
                if not path.startswith(here):
                    # Die if path in CLEAN_FILES is absolute
                    raise ValueError("%s is not a path inside %s" % (path,
                                                                     here))
                print('removing %s' % os.path.relpath(path))
                shutil.rmtree(path)


class PylintCommand(distutils.cmd.Command):
    """A custom command to run Pylint on all Python source files."""

    description = 'run Pylint on Python source files'
    user_options = [
        # The format is (long option, short option, description).
        ('pylint-rcfile=', None, 'path to Pylint config file'),
    ]

    def initialize_options(self):
        """Set default values for options."""
        # Each user option must be listed here with their default value.
        self.pylint_rcfile = os.path.join(here, 'pylintrc')

    def finalize_options(self):
        """Post-process options."""
        if self.pylint_rcfile:
            assert os.path.exists(self.pylint_rcfile), (
            'Pylint config file %s does not exist.' % self.pylint_rcfile)

    def run(self):
        """Run command."""
        command = ['pytest']
        command.append('--pylint')
        command.append('--flake8')
        command.append(os.path.join(here, 'src'))
        self.announce(
            'Running command: %s' % str(command),
            level=distutils.log.INFO)
        try:
            subprocess.check_call(command)
        except subprocess.CalledProcessError:
            pass


class TestCommand(distutils.cmd.Command):
    """A custom command to run tests using pytest."""

    description = 'run tests with pytest'
    user_options = [
        ('pytest-args=', 'a', 'Arguments to pass to pytest'),
    ]

    def initialize_options(self):
        """Set default values for options."""
        self.pytest_args = ''

    def finalize_options(self):
        """Post-process options."""
        pass

    def run(self):
        """Run command."""
        import sys

        # Check if pytest is available
        try:
            import pytest
        except ImportError:
            print("Error: pytest is not installed.")
            print("Install test dependencies with:")
            print("  pip install pytest mock")
            sys.exit(1)

        # Run pytest
        command = [sys.executable, '-m', 'pytest']
        if self.pytest_args:
            command.extend(self.pytest_args.split())
        else:
            command.append('tests/')

        self.announce(
            'Running command: %s' % ' '.join(command),
            level=distutils.log.INFO)
        errno = subprocess.call(command)
        sys.exit(errno)


setup(
    name='hephaestus',
    version='0.0.1',
    description='Check Type Systems',
    python_requires='>=3.4, <4',
    packages=find_packages(include=['src*']),
    package_data={'src': ['resources/*']},
    include_package_data=True,
    scripts=['hephaestus.py'],
    cmdclass={
        'clean': CleanCommand,
        'lint': PylintCommand,
        'test': TestCommand,
    },
)
