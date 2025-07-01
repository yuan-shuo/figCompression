from flask import Flask, request, jsonify, send_file, render_template
from PIL import Image
import io
import os

app = Flask(__name__)

def compress_image(image, target_size_kb, min_width=None, min_height=None):
    """
    Compresses the image to be as close as possible to the specified size in kilobytes (kb),
    while trying to preserve quality.
    """
    min_quality = 10
    max_quality = 95
    img_byte_arr = io.BytesIO()

    def save_and_check_quality(quality, img=image):
        img_byte_arr.seek(0)
        img_byte_arr.truncate(0)
        img.save(img_byte_arr, format='JPEG', quality=quality)
        return img_byte_arr.tell() / 1024

    # First resize the image according to user-specified minimum width and height if provided
    original_width, original_height = image.size
    if min_width is not None and min_height is not None:
        scale_factor = min(min_width / original_width, min_height / original_height, 1.0)
        new_width = int(original_width * scale_factor)
        new_height = int(original_height * scale_factor)
        image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)

    # Initial check with maximum quality after resizing
    file_size_kb = save_and_check_quality(max_quality)

    if file_size_kb <= target_size_kb:
        return img_byte_arr  # Already within the target size

    # Binary search for the best quality that fits within the target size
    while max_quality - min_quality > 1:
        mid_quality = (min_quality + max_quality) // 2
        file_size_kb = save_and_check_quality(mid_quality)
        if file_size_kb <= target_size_kb:
            min_quality = mid_quality
        else:
            max_quality = mid_quality

    # Final check between min_quality and max_quality
    final_quality = min_quality
    final_size_kb = save_and_check_quality(final_quality)

    if final_size_kb <= target_size_kb:
        img_byte_arr.seek(0)
        return img_byte_arr

    # As a last resort, use the smallest possible quality and dimensions
    img_byte_arr.seek(0)
    img_byte_arr.truncate(0)
    image.save(img_byte_arr, format='JPEG', quality=min_quality)
    img_byte_arr.seek(0)
    return img_byte_arr

@app.route("/", methods=["GET"])
def index():
    """Render the upload form."""
    return render_template('upload.html')

@app.route("/learn", methods=["POST"])
def t():
    if request.method != 'POST':
        return jsonify({"msg": "Method not allowed"}), 405
    
    if 'image' not in request.files:
        return jsonify({"msg": "No image part in the request"}), 400
    
    file = request.files['image']
    
    if file.filename == '':
        return jsonify({"msg": "No selected file"}), 400
    
    # 获取 max_size_kb 的值，并进行验证
    max_size_kb_input = request.form.get('max_size_kb', '').strip()
    try:
        # 使用默认值 100KB 如果用户未提供有效输入
        max_size_kb = float(max_size_kb_input) if max_size_kb_input else 100.0
    except ValueError:
        return jsonify({"msg": "请输入有效的文件大小（KB）"}), 400
    
    # 获取最小宽度和高度，并进行验证
    try:
        min_width = int(request.form.get('min_width', 0))
        min_height = int(request.form.get('min_height', 0))
    except ValueError:
        return jsonify({"msg": "请输入有效的最小宽度和高度"}), 400

    if file and allowed_file(file.filename):
        original_file_size_kb = len(file.read()) / 1024
        file.seek(0)  # Reset file pointer after reading it
        
        if max_size_kb > original_file_size_kb:
            return jsonify({"msg": f"请输入不大于原图大小（{original_file_size_kb:.2f} KB）的数值！"}), 400

        image = Image.open(file)
        image = image.convert('RGB')  # Remove EXIF data by converting to RGB mode
        compressed_img_io = compress_image(image, max_size_kb, min_width, min_height)

        # Return the compressed image as a response
        return send_file(
            compressed_img_io,
            mimetype='image/jpeg',
            as_attachment=True,
            download_name="compressed_" + file.filename
        )
    else:
        return jsonify({"msg": "File type not allowed"}), 400

def allowed_file(filename):
    """Check if the file has an allowed extension."""
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

if __name__ == "__main__":
    app.run(debug=True)