import os
import sys
from typing import Any
import cv2
import numpy as np
from paddleocr import PaddleOCR
import pyautogui
from deep_translator import GoogleTranslator
import time
import threading
import tkinter as tk
from tkinter import ttk

# --- CẤU HÌNH BIẾN MÔI TRƯỜNG CHỐNG LỖI ---
os.environ["FLAGS_use_onednn"] = "0"

NGON_NGU_GOC = "en"
NGON_NGU_DICH = "vi"

# Khởi tạo mô hình OCR ổn định
ocr = PaddleOCR(use_angle_cls=True, lang=NGON_NGU_GOC, show_log=False)
translator = GoogleTranslator(source=NGON_NGU_GOC, target=NGON_NGU_DICH)

# Biến toàn cục kiểm soát tọa độ và luồng
vung_chup = None
running = True
is_snipping = False  
cum_tu_cu = ""

# Lưu trữ instance của các cửa sổ giao diện
control_panel = None
translation_overlay = None

# =====================================================================
# BƯỚC 1: CỬA SỔ KHOANH VÙNG BẰNG CHUỘT (DÙNG TOPLEVEL ĐỂ TRÁNH LỖI LUỒNG)
# =====================================================================
class ScreenSnipperToplevel:
    def __init__(self, parent, on_callback):
        self.parent = parent
        self.on_callback = on_callback
        
        self.top = tk.Toplevel(parent)
        self.top.attributes("-alpha", 0.3)  # Làm mờ màn hình
        self.top.attributes("-fullscreen", True)
        self.top.attributes("-topmost", True)
        self.top.config(cursor="cross")

        self.canvas = tk.Canvas(self.top, cursor="cross", bg="grey")
        self.canvas.pack(fill="both", expand=True)

        self.canvas.bind("<ButtonPress-1>", self.on_button_press)
        self.canvas.bind("<B1-Motion>", self.on_move_press)
        self.canvas.bind("<ButtonRelease-1>", self.on_button_release)

        self.start_x = None
        self.start_y = None
        self.rect = None

    def on_button_press(self, event):
        self.start_x = event.x
        self.start_y = event.y
        self.rect = self.canvas.create_rectangle(self.start_x, self.start_y, 1, 1, outline="red", width=2)

    def on_move_press(self, event):
        cur_x, cur_y = (event.x, event.y)
        self.canvas.coords(self.rect, self.start_x, self.start_y, cur_x, cur_y)

    def on_button_release(self, event):
        global vung_chup
        end_x, end_y = (event.x, event.y)
        
        x = min(self.start_x, end_x)
        y = min(self.start_y, end_y)
        w = abs(self.start_x - end_x)
        h = abs(self.start_y - end_y)
        
        if w > 10 and h > 10:  
            vung_chup = (x, y, w, h)
            self.on_callback() # Kích hoạt callback khi khoanh vùng xong
        
        self.top.destroy()

# =====================================================================
# BƯỚC 2: CỬA SỔ HIỂN THỊ BẢN DỊCH PHỤ ĐỀ (OVERLAY WINDOW)
# =====================================================================
class TranslationOverlay:
    def __init__(self, parent):
        self.parent = parent
        self.root = tk.Toplevel(parent)
        self.root.title("Bản Dịch Phụ Đề")
        
        # Cấu hình cửa sổ không viền, luôn nổi lên trên cùng
        self.root.overrideredirect(True)
        self.root.attributes("-topmost", True)
        self.root.attributes("-alpha", 0.9) 
        
        # Đặt vị trí mặc định ban đầu ở nửa dưới màn hình
        screen_w = self.root.winfo_screenwidth()
        screen_h = self.root.winfo_screenheight()
        self.root.geometry(f"550x110+{int(screen_w/2 - 275)}+{int(screen_h - 180)}")
        
        # Thanh tiêu đề nhỏ để giữ chuột kéo di chuyển
        self.title_bar = tk.Frame(self.root, bg="#2c3e50", height=25)
        self.title_bar.pack(fill="x", side="top")
        
        lbl_hint = tk.Label(self.title_bar, text=" ↕ Giữ chuột tại đây để kéo di chuyển ô dịch", fg="#ecf0f1", bg="#2c3e50", font=("Arial", 9, "bold"))
        lbl_hint.pack(side="left", padx=5)

        # Nút ẩn tạm thời ô dịch nếu vướng video
        btn_hide = tk.Button(self.title_bar, text=" 👁 Ẩn ô ", bg="#7f8c8d", fg="white", bd=0, font=("Arial", 9, "bold"), command=self.hide_overlay)
        btn_hide.pack(side="right", fill="y", padx=2)

        # Khung hiển thị text dịch thiết kế chữ to rõ nét
        self.lbl_text = tk.Label(self.root, text="Vui lòng nhấn 'Chọn vùng dịch' ở bảng điều khiển...", font=("Helvetica", 14, "bold"), fg="#111111", bg="#f1c40f", wraplength=530, justify="center")
        self.lbl_text.pack(fill="both", expand=True)

        # Bind sự kiện kéo thả chuột
        self.title_bar.bind("<ButtonPress-1>", self.start_move)
        self.title_bar.bind("<B1-Motion>", self.on_move)

    def start_move(self, event):
        self.x = event.x
        self.y = event.y

    def on_move(self, event):
        deltax = event.x - self.x
        deltay = event.y - self.y
        x = self.root.winfo_x() + deltax
        y = self.root.winfo_y() + deltay
        self.root.geometry(f"+{x}+{y}")

    def update_text(self, text):
        self.lbl_text.config(text=text)

    def show_overlay(self):
        self.root.deiconify()

    def hide_overlay(self):
        self.root.withdraw()

# =====================================================================
# BƯỚC 3: BẢNG ĐIỀU KHIỂN TRUNG TÂM (MAIN CONTROL PANEL)
# =====================================================================
class MainControlPanel:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("PaddleOCR - Điều Khiển Dịch")
        self.root.geometry("320x180")
        self.root.attributes("-topmost", True)
        self.root.resizable(False, False)
        
        # Setup giao diện Modern tinh tế
        style = ttk.Style()
        style.theme_use('clam')
        
        lbl_title = tk.Label(self.root, text="HỆ THỐNG DỊCH YOUTUBE AI", font=("Arial", 12, "bold"), fg="#2c3e50")
        lbl_title.pack(pady=10)

        # Nút bấm 1: Tiến hành Khoanh vùng dịch mới
        self.btn_snip = tk.Button(self.root, text="🎯 Khoanh Vùng Dịch Mới", bg="#2980b9", fg="white", font=("Arial", 10, "bold"), bd=0, height=2, width=25, command=self.trigger_snipper)
        self.btn_snip.pack(pady=5)

        # Nút bấm 2: Hiện lại ô dịch nếu lỡ tay ẩn đi
        self.btn_show_overlay = tk.Button(self.root, text="👁 Hiện Ô Dịch", bg="#27ae60", fg="white", font=("Arial", 10, "bold"), bd=0, height=1, width=25, command=self.restore_overlay_ui)
        self.btn_show_overlay.pack(pady=5)

        # Trạng thái hiển thị tọa độ hiện hành
        self.lbl_status = tk.Label(self.root, text="Trạng thái: Chưa chọn vùng dịch", font=("Arial", 8, "italic"), fg="#7f8c8d")
        self.lbl_status.pack(side="bottom", pady=5)

        # Khởi tạo ô dịch ngầm luôn (Ban đầu sẽ hiển thị chờ)
        global translation_overlay
        translation_overlay = TranslationOverlay(self.root)

        self.root.protocol("WM_DELETE_WINDOW", self.exit_all)

    def trigger_snipper(self):
        """Kích hoạt màn hình chụp mà không làm crash app chính"""
        global is_snipping, cum_tu_cu
        is_snipping = True
        cum_tu_cu = "" 
        
        # Ẩn ô dịch đi khi đang khoanh chuột cho đỡ vướng
        translation_overlay.hide_overlay()
        
        # Gọi màn hình chụp dạng Toplevel
        ScreenSnipperToplevel(self.root, self.on_snipping_done)

    def on_snipping_done(self):
        """Hàm tự động chạy khi người dùng thả chuột khoanh vùng xong"""
        global is_snipping
        self.lbl_status.config(text=f"Vùng quét: X:{vung_chup[0]}, Y:{vung_chup[1]} | W:{vung_chup[2]}xH:{vung_chup[3]}")
        translation_overlay.update_text("Đang kết nối nhận diện chữ...")
        translation_overlay.show_overlay()
        is_snipping = False

    def restore_overlay_ui(self):
        translation_overlay.show_overlay()

    def exit_all(self):
        global running
        running = False
        self.root.destroy()
        os._exit(0)

# =====================================================================
# BƯỚC 4: LUỒNG THỰC THI OCR VÀ GOOGLE TRANSLATE CHẠY NGẦM
# =====================================================================
def ocr_and_translate_loop():
    global cum_tu_cu, running, is_snipping
    
    while running:
        if is_snipping or vung_chup is None:
            time.sleep(0.4)
            continue
            
        try:
            # 1. Chụp vùng màn hình đã khoanh bằng chuột
            screen_shot = pyautogui.screenshot(region=vung_chup)
            frame = np.array(screen_shot)
            frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
            
            # 2. Nhận diện chữ bằng PaddleOCR ổn định bản 2.x
            result = ocr.ocr(frame, cls=True)
            
            text_cum_tai = ""
            if result and result[0] is not None:
                lines = [line[1][0] for line in result[0]]
                text_cum_tai = " ".join(lines).strip()
            
            # 3. Gửi chuỗi lên Google Translator dịch nếu phát hiện text mới
            if text_cum_tai and text_cum_tai != cum_tu_cu:
                cum_tu_cu = text_cum_tai
                try:
                    ban_dich = translator.translate(text_cum_tai)
                    print(f"\n[Quét vùng]: {vung_chup}\n[Gốc]: {text_cum_tai}\n[Dịch]: {ban_dich}")
                    
                    # Cập nhật văn bản dịch lên ô Overlay di động một cách an toàn
                    if translation_overlay and translation_overlay.root.winfo_exists():
                        translation_overlay.root.after(0, translation_overlay.update_text, ban_dich)
                except Exception as ex:
                    print(f"Lỗi kết nối dịch: {ex}")
                    
        except Exception as e:
            print(f"Lỗi luồng xử lý OCR: {e}")
            
        time.sleep(0.7) # Chu kỳ quét mượt mà tối ưu CPU

# =====================================================================
# KHỞI CHẠY ỨNG DỤNG
# =====================================================================
if __name__ == "__main__":
    # 1. Tạo và khởi động luồng tính toán AI ngầm
    backend_thread = threading.Thread(target=ocr_and_translate_loop, daemon=True)
    backend_thread.start()
    
    # 2. Kích hoạt bảng điều khiển trung tâm chính trên màn hình
    panel = MainControlPanel()
    panel.root.mainloop()