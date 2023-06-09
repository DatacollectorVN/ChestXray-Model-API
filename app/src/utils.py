import loguru
import cv2

def get_custom_loggers():
    loguru.logger.level('BUG', no = 38, color = '<red>')
    return loguru.logger
logger = get_custom_loggers()

def detectron2_prediction(model, img):
    '''
        Args:
            + model: Detectron2 model file.
            + img: Image file with RGB channel
        Return:
            + outputs: Ouput of detetron2's predictions
    '''
    
    img_copy = img.copy()
    img_copy = cv2.cvtColor(img_copy, cv2.COLOR_RGB2BGR)
    return model(img_copy)

def get_outputs_detectron2(outputs, to_cpu=True):
    if to_cpu:
        instances = outputs["instances"].to("cpu")
    else:
        instances = outputs["instances"]

    pred_bboxes = instances.get("pred_boxes").tensor
    pred_confidence_scores = instances.get("scores")
    pred_classes = instances.get("pred_classes")
    return pred_bboxes, pred_confidence_scores, pred_classes

def draw_bbox_infer(img, pred_bboxes, pred_classes_id, pred_scores, classes_name, color, thickness=5):
    img_draw = img.copy()
    for i, img_bbox in enumerate(pred_bboxes):
        img_draw = cv2.rectangle(img_draw, pt1 = (int(img_bbox[0]), int(img_bbox[1])), 
                                 pt2 = (int(img_bbox[2]), int(img_bbox[3])), 
                                 color = color[classes_name.index(classes_name[pred_classes_id[i]])],
                                 thickness = thickness)         
        cv2.putText(img_draw,
                    text = classes_name[pred_classes_id[i]].upper() + " (" + str(round(pred_scores[i] * 100, 2)) + "%)",
                    org = (int(img_bbox[0]), int(img_bbox[1]) - 5),
                    fontFace = cv2.FONT_HERSHEY_SIMPLEX,
                    fontScale = 0.6,
                    color = (255, 0, 0),
                    thickness = 1, lineType = cv2.LINE_AA)     
    return img_draw