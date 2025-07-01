from PIL import Image
import io
import numpy as np

class ImageProcessor:
    def __init__(self, image):
        """
        初始化图片处理器。
        
        :param image: PIL.Image 对象
        """
        self.image = image

    def compress_image(self, target_size_kb, min_width=None, min_height=None):
        """
        压缩图片到指定大小（KB），同时尽量保留质量。
        
        :param target_size_kb: 目标文件大小（KB）
        :param min_width: 最小宽度（可选）
        :param min_height: 最小高度（可选）
        :return: 压缩后的图片字节流
        """
        min_quality = 10
        max_quality = 95
        img_byte_arr = io.BytesIO()

        def save_and_check_quality(quality, img=self.image):
            img_byte_arr.seek(0)
            img_byte_arr.truncate(0)
            img.save(img_byte_arr, format='JPEG', quality=quality)
            return img_byte_arr.tell() / 1024

        # 如果指定了最小宽度和高度，先调整图片大小
        if min_width is not None and min_height is not None:
            original_width, original_height = self.image.size
            scale_factor = min(min_width / original_width, min_height / original_height, 1.0)
            new_width = int(original_width * scale_factor)
            new_height = int(original_height * scale_factor)
            self.image = self.image.resize((new_width, new_height), Image.Resampling.LANCZOS)

        # 初始检查最大质量
        file_size_kb = save_and_check_quality(max_quality)

        if file_size_kb <= target_size_kb:
            return img_byte_arr  # 已经在目标大小范围内

        # 二分查找最佳质量
        while max_quality - min_quality > 1:
            mid_quality = (min_quality + max_quality) // 2
            file_size_kb = save_and_check_quality(mid_quality)
            if file_size_kb <= target_size_kb:
                min_quality = mid_quality
            else:
                max_quality = mid_quality

        # 最终检查
        final_quality = min_quality
        final_size_kb = save_and_check_quality(final_quality)

        if final_size_kb <= target_size_kb:
            img_byte_arr.seek(0)
            return img_byte_arr

        # 如果仍然超出目标大小，使用最小质量
        img_byte_arr.seek(0)
        img_byte_arr.truncate(0)
        self.image.save(img_byte_arr, format='JPEG', quality=min_quality)
        img_byte_arr.seek(0)
        return img_byte_arr

    def replace_color(self, target_color, replacement_color, tolerance=30):
        """
        替换图片中的颜色。
        
        :param target_color: 被替换颜色 (RGB)
        :param replacement_color: 新颜色 (RGB)
        :param tolerance: 容差值
        :return: 替换颜色后的图片
        """
        image = self.image.convert('RGB')
        pixels = image.load()
        width, height = image.size

        for x in range(width):
            for y in range(height):
                pixel_color = pixels[x, y]
                if (abs(pixel_color[0] - target_color[0]) <= tolerance and
                    abs(pixel_color[1] - target_color[1]) <= tolerance and
                    abs(pixel_color[2] - target_color[2]) <= tolerance):
                    pixels[x, y] = replacement_color

        return image