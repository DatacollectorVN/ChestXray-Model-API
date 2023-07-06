import os, uuid, sys
sys.path.append(os.getcwd())
import json
import pandas as pd
import numpy as np
from datetime import datetime
import urllib
from pydantic import BaseModel
from fastapi import APIRouter, HTTPException, Request
from app.src.utils import logger
from app.connectors.azure_dl import initialize_storage_account
from app.config.config_reader import config_reader
from app.src.azure_dl_engine import upload_file, dowload_file
from app.run_background.bg_call_endpoint_model import inference_handler
from app.connectors.azure_sql import MSSQLDatabase, CursorMSSQLDatabase, ConnectionMSSQLDatabase
import cv2

router = APIRouter()
CURRENT_DIR = os.getcwd()
TBL_UPDATE = 'users_image_prediction'
STM_UPDATE = """
    UPDATE [{tbl_update}]
    SET [{col_update}] = '%s'
    WHERE [{col_ref}] = %s
"""
COL_REF = 'id'

TBL_INSERT = 'users_disease_prediction'


class EntryAPI(BaseModel):
    # user_id: int
    # predict_id: int
    file_system_name: str
    file_path: str
    output_folder_path: str

@router.post("/submit_predict")
async def submit_predict(item: EntryAPI):
    engine = None
    try:
        now = datetime.now()
        month_str = str(now.month)
        if len(month_str) == 1:
            month_str = '0' + month_str
        
        day_str = str(now.day)
        if len(day_str) == 1:
            day_str = '0' + day_str

        date_key = int(f'{now.year}{month_str}{day_str}')
        file_system_name = item.file_system_name
        file_path = item.file_path
        output_folder_path = item.output_folder_path

        # initialized connection
        ## datalake connection
        service_client = initialize_storage_account(config_reader.azure_storage['azure_storage_account_name']
            ,  config_reader.azure_storage['azure_storage_account_key']
        )

        ## azure sql connection
        server = config_reader.azure_sql['server']
        database = config_reader.azure_sql['database']
        username = config_reader.azure_sql['username']
        password = config_reader.azure_sql['password'].strip('"')
        driver = config_reader.azure_sql['driver'].strip('"')
        odbc = config_reader.azure_sql['odbc'].strip('"').format(
            driver = driver, server = server, database = database,
            username = username, password = password
        )
        odbc_parse_quote = urllib.parse.quote_plus(odbc)
        url = config_reader.azure_sql['url'].strip('"').format(odbc_parse_quote = odbc_parse_quote)
        MSSQLDatabase.initalize(url)
        engine = MSSQLDatabase.get_engine()

        # dowload input image from data lake to fix name: app/imgs/input_img.*
        file_path_extension = os.path.splitext(file_path)[1]
        input_img_path = os.path.join(CURRENT_DIR, config_reader.azure_storage['imgs_dir_path']
            , config_reader.azure_storage['input_img_file_without_extension'] + file_path_extension
        )
        state_download = dowload_file(service_client = service_client, file_system_name = file_system_name
            , file_path = file_path,  output_path = input_img_path
        )

        if state_download is False:
            raise Exception(f'state_download is {state_download}')
        logger.info(f'[submit_predict]__: Dowloaded file to {input_img_path}')

        # model predict image then save output image to local: app/imgs/output.*
        results = inference_handler(input_img_path)
        if results is False:
            raise Exception(f'inference_handler made error')
        
        logger.info(f'[submit_predict]__: Completed inference')

        output_img_path = os.path.join(CURRENT_DIR, config_reader.azure_storage['imgs_dir_path']
            , config_reader.azure_storage['output_img_file_without_extension'] + file_path_extension
        )
        output_img = cv2.cvtColor(results['output_img'], cv2.COLOR_RGB2BGR)
        cv2.imwrite(output_img_path, output_img)

        logger.info(f'[submit_predict]__: Saved output file to {output_img_path}')

        # uploaded output image to data lake
        input_img_file = file_path.split('/')[1] # input_image_<img_id>_<user_id>.*
        img_id = int(input_img_file.split('_')[2])
        user_id = int(input_img_file.split('_')[3].split('.')[0])
        output_file = f'output_image_{img_id}_{user_id}{file_path_extension}'
        output_path = os.path.join(output_folder_path, output_file)
        state_upload = upload_file(service_client = service_client, file_system_name = file_system_name
            , directory_path = output_folder_path, output_file = output_file, src_path = output_img_path
        )
        if state_upload is False:
            raise Exception(f'state_upload is {state_upload}')
        logger.info(f'[submit_predict]__: Uploaded output file to {output_path}')

        # update sql database
        with CursorMSSQLDatabase() as cursor:
            col_update = 'output_image'
            stm_update = STM_UPDATE.format(tbl_update = TBL_UPDATE, col_update = col_update, col_ref = COL_REF)
            stm_update = stm_update % (output_path, img_id)
            cursor.execute(stm_update)
            col_update = 'status'
            stm_update = STM_UPDATE.format(tbl_update = TBL_UPDATE, col_update = col_update, col_ref = COL_REF)
            stm_update = stm_update % ('Complete', img_id)
            cursor.execute(stm_update)
        
        logger.info(f'[submit_predict]__: Completed update to {TBL_UPDATE}')

        # insert sql database
        num_disease = len(results['pred_classes_id'])
        if num_disease > 0:
            location_xyxy = []
            for bbox in results['pred_bboxes_xyxy']:
                bbox_str = f'{bbox[0]},{bbox[1]},{bbox[2]},{bbox[3]}'
                location_xyxy.append(bbox_str)

            df_insert = pd.DataFrame({'timestamp': [now for _ in range(num_disease)]
                , 'date_key': [date_key for _ in range(num_disease)]
                , 'image_prediction_id': [img_id for _ in range(num_disease)]
                , 'disease': results['pred_classes'].tolist()
                , 'location_xyxy': location_xyxy
                , 'score': results['pred_confidence_scores'].tolist()
                , 'user_id': [user_id for _ in range(num_disease)]}
            )
        else:
            df_insert = pd.DataFrame({'timestamp': [now]
                , 'date_key': [date_key]
                , 'image_prediction_id': [img_id]
                , 'disease': [np.nan]
                , 'location_xyxy': [np.nan]
                , 'score': [np.nan]
                , 'user_id': [user_id]}
            )
        df_insert.to_sql(TBL_INSERT, con = engine, if_exists = 'append', index = False)
        logger.info(f'[submit_predict]__: Completed insert to {TBL_INSERT}')


    except Exception as e:
        logger.error('submit_predict]__Exception: {}'.format(e))
        raise HTTPException(status_code=503, detail="Nope! Has the exception while handling.")
    finally:
        if engine:
            MSSQLDatabase.close_engine()
            logger.info(f'[submit_predict]__: Closed SQL database connection')
