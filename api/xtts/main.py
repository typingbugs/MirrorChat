from flask import Flask, request, jsonify, send_file
import uuid
from datetime import datetime
from TTS.api import TTS
import os


app = Flask(__name__)
device = os.getenv('APP_DEVICE', 'cpu')  # 使用环境变量获取设备

lang2short = {'english': 'en', 'chinese': 'zh-cn'}

tts = TTS("tts_models/multilingual/multi-dataset/xtts_v2", gpu=('cuda' in device)).to(device)


def generate_wav(response_text, speaker_wav, language, output_file_path):
    tts.tts_to_file(
        text=response_text,
        speaker_wav=speaker_wav,
        language=lang2short[language],
        file_path=output_file_path
    )


@app.route('/tts', methods=['POST'])
def generate():
    if 'audio' not in request.files or 'language' not in request.form or 'text' not in request.form:
        return jsonify({"error": "Speaker audio file, text and language must be provided"}), 400

    speaker_wav = request.files['audio']
    language = request.form['language']
    text = request.form['text']

    if language not in ['chinese', 'english']:
        return jsonify({"error": "Unsupported language"}), 400

    # 设置缓存音频文件地址
    unique_id = str(uuid.uuid4())
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    os.makedirs('temp', exist_ok=True)
    input_audio_filename = f"speaker_{timestamp}_{unique_id}.wav"
    input_audio_path = os.path.join('temp', input_audio_filename)
    output_audio_filename = f"output_{timestamp}_{unique_id}.wav"
    output_audio_path = os.path.join('temp', output_audio_filename)
    speaker_wav.save(input_audio_path)

    try:
        # 生成音频数据
        generate_wav(text, input_audio_path, language, output_audio_path)

        return send_file(
            output_audio_path,
            mimetype='audio/wav',
            as_attachment=True,
            download_name='generated_audio.wav'
        )
    finally:
        # 清理缓存音频文件
        if os.path.exists(input_audio_path):
            os.remove(input_audio_path)
        if os.path.exists(output_audio_path):
            os.remove(output_audio_path)


if __name__ == '__main__':
    app.run()
