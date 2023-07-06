import os, uuid, sys
sys.path.append(os.getcwd())
import yaml
from PIL import Image
import torch
import numpy as np
from app.src.utils import detectron2_prediction, get_outputs_detectron2, draw_bbox_infer
from detectron2.engine import  DefaultPredictor
from detectron2.config import get_cfg
from detectron2 import model_zoo
import streamlit as st
import time
from detectron2.utils.logger import setup_logger
setup_logger()
import logging
logger = logging.getLogger("detectron2")

FILE_INFER_CONFIG = os.path.join("app", "config", "model_config.yaml")
with open(FILE_INFER_CONFIG) as file:
    params = yaml.load(file, Loader = yaml.FullLoader)

def load_model(cfg):
    return DefaultPredictor(cfg)

def setup_config_infer(params):
    cfg = get_cfg()
    cfg.merge_from_file(model_zoo.get_config_file(params["MODEL"]))
    cfg.OUTPUT_DIR = params["OUTPUT_DIR"]
    cfg.MODEL.WEIGHTS = os.path.join(cfg.OUTPUT_DIR, params["TRANSFER_LEARNING"])
    cfg.DATALOADER.NUM_WORKERS = 0
    cfg.MODEL.DEVICE = params["DEVICE"]
    
    if "retina" in params["MODEL"]:
        cfg.MODEL.RETINANET.SCORE_THRESH_TEST = params["SCORE_THR"]
        cfg.MODEL.RETINANET.NUM_CLASSES = params["NUM_CLASSES"]
        cfg.MODEL.RETINANET.NMS_THRESH_TEST = params["NMS_THR"]
    else:
        cfg.MODEL.ROI_HEADS.SCORE_THRESH_TEST = params["SCORE_THR"]
        cfg.MODEL.ROI_HEADS.NUM_CLASSES = params["NUM_CLASSES"]
        cfg.MODEL.ROI_HEADS.NMS_THRESH_TEST = params["NMS_THR"]

    return cfg

def inference_handler(input_img_path):
    results = None
    try:
        cfg = setup_config_infer(params)
        model = load_model(cfg)
        img = Image.open(input_img_path)
        img = np.array(img.convert("RGB"))
        start = time.time()
        outputs = detectron2_prediction(model, img)
        duration = time.time() - start
        pred_bboxes, pred_confidence_scores, pred_classes_id = get_outputs_detectron2(outputs)
        pred_bboxes = pred_bboxes.detach().numpy().astype(int)
        pred_confidence_scores = pred_confidence_scores.detach().numpy()
        pred_confidence_scores = np.round(pred_confidence_scores, 2)
        pred_classes_id = pred_classes_id.detach().numpy().astype(int)
        pred_classes = np.asarray([params["CLASSES_NAME"][i] for i in pred_classes_id])
        output_img = draw_bbox_infer(img, pred_bboxes, 
            pred_classes_id, pred_confidence_scores,
            params["CLASSES_NAME"], params["COLOR"], 5
        )
        
        results = {'output_img': output_img, 'pred_classes_id': pred_classes_id
            , 'pred_classes': pred_classes, 'pred_bboxes_xyxy': pred_bboxes
            , 'pred_confidence_scores': pred_confidence_scores, 'duration': duration
        }

    except Exception as e:
        results = False
    finally:
        return results