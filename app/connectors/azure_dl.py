import os, uuid, sys
sys.path.append('/home/nathan/project/ChestXray-Model-API/')
print(sys.path)
from azure.storage.filedatalake import DataLakeServiceClient
from azure.core._match_conditions import MatchConditions
from azure.storage.filedatalake._models import ContentSettings
from app.src.utils import logger
from app.config.config_reader import ConfigReader

def initialize_storage_account(storage_account_name, storage_account_key):
    
    try:  
        global service_client

        service_client = DataLakeServiceClient(account_url='{}://{}.dfs.core.windows.net'.format(
            'https', storage_account_name), credential=storage_account_key)
    
    except Exception as e:
        logger.error(f'[initialize_storage_account][Exception]__: {e}')

if __name__ == '__main__':
    config_reader = ConfigReader(file_name = 'app/config/config.ini')
    initialize_storage_account(ConfigReader.azure_storage['azure_storage_account_name']
        ,  ConfigReader.azure_storage['azure_storage_account_key']
    )
    print(service_client)