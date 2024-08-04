import cv2
import numpy as np
import torch
from .datasets import sequence
from .trainer import core
import os

torch.backends.cudnn.benchmark = True


class Predictor:
    def __init__(self, weight_path):
        self.model = core.LayoutSeg.load_from_checkpoint(
            weight_path, backbone="resnet101", map_location="cpu"
        )
        self.model.freeze()

    @torch.no_grad()
    def feed(self, image: torch.Tensor, alpha=0.4) -> np.ndarray:
        _, outputs = self.model(image.unsqueeze(0))
        label = core.label_as_rgb_visual(outputs.cpu()).squeeze(0)
        return label.permute(1, 2, 0).numpy()


# Load predictor
predictor = Predictor(  
    weight_path=os.path.join("wall_estimation", "weight", "model_retrained.ckpt")
)


def wall_estimation(path, image_size=320):
    """Thực hiện phân đoạn phòng để lấy vị trí của các bức tường riêng biệt

    Args:
        path (str): đường dẫn đến ảnh của căn phòng
        image_size (int, optional): kích thước để scale ảnh. Mặc định là 320.

    Returns:
        np.ndarray: kết quả phân đoạn, trong đó mỗi pixel tương ứng với một trong 5 lớp
        (tường trái, tường trung tâm, tường phải, trần và sàn)
    """
    images = sequence.ImageFolder(image_size, path)
    path = os.path.abspath(path)

    image, shape, _ = list(images)[0]

    output = predictor.feed(image)
    output = cv2.resize(output, shape)

    result = output[..., ::-1].astype(np.uint8) * 255

    return result
