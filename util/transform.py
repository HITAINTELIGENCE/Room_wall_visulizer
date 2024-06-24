'''
Định nghĩa các phép augmentation trên ảnh
Sử dụng thư viện Albumentations, tham khảo thêm: https://albumentations.ai/docs/api_reference/full_reference/ 

Nhưng tôi không muốn cài đặt thư viện nên mình viết lại để cho nó nhẹ.

train_transform = A.Compose([
    A.Resize(width=trainsize, height=trainsize),
    A.HorizontalFlip(),
    A.RandomBrightnessContrast(),
    A.Blur(),
    A.Sharpen(),
    A.RGBShift(),
    A.Cutout(num_holes=5, max_h_size=25, max_w_size=25, fill_value=0),
    A.Normalize(mean=(0.485, 0.456, 0.406), std=(0.229, 0.224, 0.225), max_pixel_value=255.0),
    ToTensorV2(),
])
Có các phép augmentation như:
- Resize: thay đổi kích thước ảnh
- HorizontalFlip: lật ảnh theo chiều ngang
- RandomBrightnessContrast: thay đổi độ sáng và độ tương phản
- Blur: làm mờ ảnh
- Sharpen: làm nét ảnh
- RGBShift: thay đổi màu RGB
- Cutout: cắt ảnh
- Normalize: chuẩn hóa ảnh
- ToTensorV2: chuyển ảnh sang tensor
'''