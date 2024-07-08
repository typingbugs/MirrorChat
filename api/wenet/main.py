from flask import Flask, request, jsonify
import wenet
import os
import uuid
from datetime import datetime

app = Flask(__name__)

# 加载wenet模型
wenet_model_cn = wenet.load_model('chinese', device='cuda')
wenet_model_en = wenet.load_model('english', device='cuda')

def transcribe_audio(audio_path, language):
    """Transcribe audio file to text using wenet."""
    if language == 'chinese':
        result = wenet_model_cn.transcribe(audio_path)['text']
    else:
        result = wenet_model_en.transcribe(audio_path)['text']
        result = result.replace("▁", " ")
    print(result)
    return result

@app.route('/transcribe', methods=['POST'])
def transcribe():
    if 'audio' not in request.files or 'language' not in request.form:
        return jsonify({"error": "Audio file and language must be provided"}), 400

    audio_file = request.files['audio']
    language = request.form['language']

    if language not in ['chinese', 'english']:
        return jsonify({"error": "Unsupported language"}), 400

    # 设置缓存音频文件地址
    unique_id = str(uuid.uuid4())
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    os.makedirs('temp', exist_ok=True)
    input_audio_filename = f"input_{timestamp}_{unique_id}.wav"
    input_audio_path = os.path.join('temp', input_audio_filename)
    audio_file.save(input_audio_path)

    try:
        # 使用wenet，音频转文本
        response_text = transcribe_audio(input_audio_path, language)
        if language == "chinese":
            response_text = response_text.replace("：", "，")
            response_text = response_text.replace("*", "")
        else:
            response_text = response_text.replace(":", ",")
            response_text = response_text.replace("*", "")
        return jsonify({"text": response_text})
    finally:
        # 清理缓存音频文件
        if os.path.exists(input_audio_path):
            os.remove(input_audio_path)

if __name__ == '__main__':
    app.run()
