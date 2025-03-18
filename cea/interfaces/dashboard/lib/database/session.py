import os
import sys
from contextlib import contextmanager

from fastapi import Depends
from sqlmodel import create_engine, Session, SQLModel, select

from typing_extensions import Annotated

from cea.interfaces.dashboard.lib.database.models import User, LOCAL_USER_ID
from cea.interfaces.dashboard.settings import get_settings


def get_default_db_directory():
    """Get platform-specific directory for storing application data"""
    try:
        if sys.platform == 'win32':
            # Windows: %APPDATA%\CityEnergyAnalyst
            app_data = os.environ.get('APPDATA', os.path.expandvars(r"%APPDATA%"))
            return os.path.join(app_data, "CityEnergyAnalyst")
        elif sys.platform == 'darwin':
            # macOS: ~/Library/Application Support/CityEnergyAnalyst
            return os.path.join(os.path.expanduser('~'), 'Library', 'Application Support', 'CityEnergyAnalyst')
        else:
            # Linux/Unix: ~/.local/share/CityEnergyAnalyst
            return os.path.join(os.path.expanduser('~'), '.local', 'share', 'CityEnergyAnalyst')
    except Exception:
        # Fallback to user home directory
        return os.path.join(os.path.expanduser('~'), '.cea')


def get_local_database_path():
    """Get the path to the database file."""
    # Try to get from settings (if available)
    settings = get_settings()
    db_dir = settings.db_path

    # Use default location if not configured
    if db_dir is None:
        db_dir = get_default_db_directory()

    os.makedirs(db_dir, exist_ok=True)
    return os.path.join(db_dir, "database.db")


def get_database_props():
    settings = get_settings()
    # Use database_url if set (priority)
    # Support postgres for now
    if settings.db_url is not None:
        return settings.db_url, {}

    return f"sqlite:///{get_local_database_path()}", {"check_same_thread": False}


db_url, connect_args = get_database_props()
engine = create_engine(db_url, connect_args=connect_args)


def get_session():
    with Session(engine) as session:
        yield session


@contextmanager
def get_session_context():
    with Session(engine) as session:
        yield session


def create_db_and_tables():
    print(f"Preparing database...")
    SQLModel.metadata.create_all(engine)

    if get_settings().local:
        print("Using local user...")
        with Session(engine) as session:
            user = session.exec(select(User).where(User.id == LOCAL_USER_ID))
            if user is None:
                print("Default local user not found. Creating...")
                user = User(id=LOCAL_USER_ID)
                session.add(user)


SessionDep = Annotated[Session, Depends(get_session)]
