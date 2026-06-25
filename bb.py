import sys
# Ép Python loại bỏ hoàn toàn các đường dẫn trỏ tới thư mục anaconda cũ (nếu có) trong lúc chạy
sys.path = [p for p in sys.path if "anaconda3" not in p and "fgd" not in p]

import os
# Khóa cấu hình OneDNN để tránh lỗi toán tử fused_conv2d
os.environ["FLAGS_use_onednn"] = "0"

import cv2
from paddleocr import PaddleOCR

# --- ĐƯỜNG DẪN ĐẾN CÁC THƯ MỤC MÔ HÌNH CÓ SẴN CỦA BẠN ---
# Bạn hãy kiểm tra lại tên thư mục con chính xác trong máy của bạn và sửa lại cho đúng nhé
thu_muc_whl = r"C:\tupn\phan_mem\tools_ocr\models_paddleocr\whl"

duong_dan_det = os.path.join(thu_muc_whl, "en_PP-OCRv3_det_infer") # Hoặc tên thư mục chứa model det của bạn
duong_dan_rec = os.path.join(thu_muc_whl, "en_PP-OCRv3_rec_infer") # Hoặc tên thư mục chứa model rec của bạn
duong_dan_cls = os.path.join(thu_muc_whl, "ch_ppocr_mobile_v2.0_cls_infer") # Hoặc tên thư mục chứa model cls của bạn

# --- KHỞI TẠO PADDLEOCR DÙNG MÔ HÌNH LOCAL ---
ocr = PaddleOCR(
    use_angle_cls=True, 
    lang="en", 
    show_log=False,
    enable_mkldnn=False, # Tắt MKLDNN từ gốc
    det_model_dir=duong_dan_det, # Ép đọc model det tại đây
    rec_model_dir=duong_dan_rec, # Ép đọc model rec tại đây
    cls_model_dir=duong_dan_cls  # Ép đọc model cls tại đây
)

image_path = "1.jpg"

if not os.path.exists(image_path):
    print(f"Không tìm thấy file ảnh: {image_path}")
else:
    print(f"--> Đang OCR ảnh bằng mô hình có sẵn tại {thu_muc_whl}...")
    img = cv2.imread(image_path)
    result = ocr.ocr(img, cls=True)
    
    if result and result[0] is not None:
        print("\n=== KẾT QUẢ ===")
        for line in result[0]:
            print(f"Chữ nhận diện được: {line[1][0]} (Độ chính xác: {line[1][1]*100:.2f}%)")
    else:
        print("Không tìm thấy chữ!")