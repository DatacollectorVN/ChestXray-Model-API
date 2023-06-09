import os, uuid, sys
sys.path.append(os.getcwd())
from app.src.utils import logger
from sqlalchemy import create_engine


class MSSQLDatabase:
    __engine = None

    @staticmethod
    def initalize(*args, **kwargs):
        MSSQLDatabase.__engine = create_engine(*args, **kwargs)
    
    @staticmethod
    def get_engine():
        return MSSQLDatabase.__engine

    @staticmethod
    def get_connection():
        return MSSQLDatabase.__engine.raw_connection()
    
    @staticmethod
    def close_connection(connection):
        connection.close()

    @staticmethod
    def close_engine():
        MSSQLDatabase.__engine.dispose()


class ConnectionMSSQLDatabase:
    def __init__(self):
        self.connection = None
    
    def __enter__(self):
        self.connection = MSSQLDatabase.get_connection()
        return self.connection

    def __exit__(self, excep_type, excep_value, excep_traceback):
        if excep_value:
            if self.connection:
                self.connection.rollback()
                logger.error(f'[ConnectionMSSQLDatabase][Exception]:__{excep_value}')
            else:
                logger.error(f'[ConnectionMSSQLDatabase][Exception]:__{excep_value} and not initialize connection')
        else:
            self.connection.commit()
            logger.info(f'[ConnectionMSSQLDatabase]:__Completed commit')
        
        MSSQLDatabase.close_connection(self.connection)
        logger.info(f'[ConnectionMSSQLDatabase]:__Close connection')


class CursorMSSQLDatabase:
    def __init__(self):
        self.connection = None
        self.cursor = None

    def __enter__(self):
        self.connection = MSSQLDatabase.get_connection()
        self.cursor = self.connection.cursor()
        return self.cursor
    
    def __exit__(self, exception_type, exception_value, exception_traceback):
        if exception_value:
            if self.cursor and self.connection:
                self.connection.rollback()
                logger.error(f'[CursorMSSQLDatabase][Exception]:__{exception_value}')
            else:
                logger.error(f'[CursorMSSQLDatabase][Exception]:__{exception_value} and not initialize connection')
        else:
            self.cursor.close()
            self.connection.commit()
            logger.info(f'[CursorMSSQLDatabase]:__Completed commit')
        
        MSSQLDatabase.close_connection(self.connection)
        logger.info(f'[CursorMSSQLDatabase]:____Close connection and cursor')