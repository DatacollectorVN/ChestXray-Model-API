import os, uuid, sys
sys.path.append(os.getcwd())
from azure.storage.filedatalake import DataLakeServiceClient
from azure.core._match_conditions import MatchConditions
from azure.storage.filedatalake._models import ContentSettings
from app.src.utils import logger
from app.config.config_reader import ConfigReader

def initialize_storage_account(storage_account_name, storage_account_key):
    try:  
        service_client = DataLakeServiceClient(account_url='{}://{}.dfs.core.windows.net'.format(
            'https', storage_account_name), credential=storage_account_key)
        
    except Exception as e:
        logger.error(f'[initialize_storage_account][Exception]__: {e}')
    
    finally:
        return service_client

if __name__ == '__main__':
    pass
    # config_reader = ConfigReader(file_name = '/home/nathan/project/ChestXray-Model-API/app/config/config.ini')
    # initialize_storage_account(config_reader.azure_storage['azure_storage_account_name']
    #     ,  config_reader.azure_storage['azure_storage_account_key']
    # )
    # # print(service_client.list_file_systems())
    # # for i in service_client.list_file_systems():
    # #     print(i)
    # file_system_client = service_client.get_file_system_client(file_system='prediction')
    # file_client = file_system_client.get_file_client(file_path = 'chest_xray/user_id_1/test1.jpeg')
    
    # output_path = os.path.join("/home/nathan/project/ChestXray-Model-API/app/", "images_1.jpeg")
    # with open(output_path,'wb') as local_file:
    #     download= file_client.download_file()
    #     downloaded_bytes = download.readall()

    #     local_file.write(downloaded_bytes)
        
    # with open("/home/nathan/project/ChestXray-Model-API/app/images.jpeg", "rb") as file:
    #     file_system_client = directory_client.create_file("test1.jpeg")
    #     file_system_client.upload_data(file,  overwrite=True)
    # directory_client = service_client.get_directory_client(file_system_client.file_system_name, "chest_xray")


    