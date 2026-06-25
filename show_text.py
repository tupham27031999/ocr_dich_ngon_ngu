from PIL import Image, ImageDraw, ImageFont
import cv2
import numpy as np

# Đường dẫn tới ảnh và font chữ
image_path = 'path_to_image.jpg'
font_path = 'path_to_font.ttf'  # Đường dẫn tới file font chữ hỗ trợ tiếng Việt

# Mở ảnh bằng OpenCV
# img = cv2.imread(image_path)
img = np.zeros((500, 500, 3), dtype=np.uint8)

# Chuyển đổi ảnh từ định dạng OpenCV sang định dạng PIL
img_pil = Image.fromarray(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))

# Tạo đối tượng ImageDraw
draw = ImageDraw.Draw(img_pil)

# Định nghĩa font chữ và kích thước
font = ImageFont.truetype(font_path, 40)

# Vị trí và nội dung văn bản
text = "Xin chào, thế giới!"
position = (50, 50)

# Màu sắc văn bản (RGB)
color = (255, 0, 0)  # Màu đỏ

# Vẽ văn bản lên ảnh
draw.text(position, text, font=font, fill=color)

# Chuyển đổi ảnh từ định dạng PIL sang định dạng OpenCV
img = cv2.cvtColor(np.array(img_pil), cv2.COLOR_RGB2BGR)

# Lưu hoặc hiển thị ảnh
# cv2.imwrite('output_image.jpg', img)
cv2.imshow('Image with Text', img)
cv2.waitKey(0)
cv2.destroyAllWindows()