#! TESTE PADDLE OCR V5
from paddleocr import PaddleOCR  
import time

print("asd")
ocr = PaddleOCR(
    use_doc_orientation_classify=False, # Disables document orientation classification model via this parameter
    use_doc_unwarping=False, # Disables text image rectification model via this parameter
    use_textline_orientation=False, # Disables text line orientation classification model via this parameter
    # text_detection_model_name="PP-OCRv5_mobile_det",
    # text_recognition_model_name="PP-OCRv5_mobile_rec",
    # text_detection_model_dir="models/PP-OCRv5_mobile_det_infer",
    # text_recognition_model_dir="models/PP-OCRv5_mobile_rec_infer"
)
print("foi")
# ocr = PaddleOCR(lang="en") # Uses English model by specifying language parameter
# ocr = PaddleOCR(ocr_version="PP-OCRv4") # Uses other PP-OCR versions via version parameter
# ocr = PaddleOCR(device="gpu") # Enables GPU acceleration for model inference via device parameter
# ocr = PaddleOCR(
#     text_detection_model_name="PP-OCRv5_mobile_det",
#     text_recognition_model_name="PP-OCRv5_mobile_rec",
#     use_doc_orientation_classify=False,
#     use_doc_unwarping=False,
#     use_textline_orientation=False,
# ) # Switch to PP-OCRv5_mobile models
init = time.time()
result = ocr.predict("imgs\\ifny1.jpg")
final = time.time() - init
print("Tempo para dar o predict: ", final)
print(result[0]['rec_texts'])
for res in result:  
    res.print()
    res.save_to_img("output")
    res.save_to_json("output")