from flask import Flask, request, jsonify, send_file, render_template
from PIL import Image
import io
import os
from biz import ImageProcessor

app = Flask(__name__)

# 允许的文件扩展名
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    """检查文件是否有允许的扩展名。"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route("/", methods=["GET"])
def index():
    """主页面"""
    return render_template('home.html')

@app.route("/page/compress", methods=["GET"])
def index_compress():
    """压缩图片网页"""
    return render_template('compress.html')

@app.route("/page/replaceColor", methods=["GET"])
def index_replace_color():
    """更换图片底色网页"""
    return render_template('replaceColor.html')

@app.route("/compress", methods=["POST"])
def compress():
    if request.method != 'POST':
        return jsonify({"msg": "Method not allowed"}), 405

    if 'image' not in request.files:
        return jsonify({"msg": "No image part in the request"}), 400

    file = request.files['image']

    if file.filename == '':
        return jsonify({"msg": "No selected file"}), 400

    # 获取目标文件大小（KB）并验证
    max_size_kb_input = request.form.get('max_size_kb', '').strip()
    try:
        max_size_kb = float(max_size_kb_input) if max_size_kb_input else 100.0
    except ValueError:
        return jsonify({"msg": "请输入有效的文件大小（KB）"}), 400

    # 获取最小宽度和高度并验证
    try:
        min_width = int(request.form.get('min_width', 0))
        min_height = int(request.form.get('min_height', 0))
    except ValueError:
        return jsonify({"msg": "请输入有效的最小宽度和高度"}), 400

    if file and allowed_file(file.filename):
        original_file_size_kb = len(file.read()) / 1024
        file.seek(0)  # 重置文件指针

        if max_size_kb > original_file_size_kb:
            return jsonify({"msg": f"请输入不大于原图大小（{original_file_size_kb:.2f} KB）的数值！"}), 400

        image = Image.open(file)
        processor = ImageProcessor(image)
        compressed_img_io = processor.compress_image(max_size_kb, min_width, min_height)

        # 返回压缩后的图片
        return send_file(
            compressed_img_io,
            mimetype='image/jpeg',
            as_attachment=True,
            download_name="compressed_" + file.filename
        )
    else:
        return jsonify({"msg": "File type not allowed"}), 400

@app.route("/replace_color", methods=["POST"])
def replace_color():
    print("Received request to /replace_color")

    if request.method != 'POST':
        print("Method not allowed: ", request.method)
        return jsonify({"msg": "Method not allowed"}), 405

    if 'image' not in request.files:
        print("No image part found in the request.")
        return jsonify({"msg": "No image part in the request"}), 400

    file = request.files['image']

    if file.filename == '':
        print("No selected file")
        return jsonify({"msg": "No selected file"}), 400

    # 获取目标颜色和替换颜色并验证
    try:
        target_color_input = request.form.get('target_color', '255,255,255')
        replacement_color_input = request.form.get('replacement_color', '0,0,0')
        print(f"Target color input: {target_color_input}")
        print(f"Replacement color input: {replacement_color_input}")

        target_color = tuple(map(int, target_color_input.split(',')))
        replacement_color = tuple(map(int, replacement_color_input.split(',')))
    except ValueError as e:
        print(f"Color value error: {e}")
        return jsonify({"msg": "请输入有效的颜色值（RGB）"}), 400

    # 获取容差值并验证
    try:
        tolerance = int(request.form.get('tolerance', 30))
        print(f"Tolerance value: {tolerance}")
    except ValueError as e:
        print(f"Tolerance value error: {e}")
        return jsonify({"msg": "请输入有效的容差值"}), 400

    if file and allowed_file(file.filename):
        print(f"Processing image: {file.filename}")
        image = Image.open(file)
        processor = ImageProcessor(image)
        new_image = processor.replace_color(target_color, replacement_color, tolerance)

        # 将图片保存到字节流中
        img_byte_arr = io.BytesIO()
        new_image.save(img_byte_arr, format='JPEG')
        img_byte_arr.seek(0)

        # 返回替换颜色后的图片
        return send_file(
            img_byte_arr,
            mimetype='image/jpeg',
            as_attachment=True,
            download_name="replaced_" + file.filename
        )
    else:
        print("File type not allowed")
        return jsonify({"msg": "File type not allowed"}), 400

if __name__ == "__main__":
    app.run(debug=True)