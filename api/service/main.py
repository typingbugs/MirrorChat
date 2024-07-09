from flask import Flask, request, jsonify, send_file, Response, stream_with_context
from flask_cors import CORS
import io
import requests
import uuid
from datetime import datetime
import os

app = Flask(__name__)
CORS(app, supports_credentials=True)

def transcribe_audio(audio, language):
    """调用WeNet API，用户提问转文字"""
    url = "http://127.0.0.1:9991/transcribe"
    files = {'audio': open(audio, 'rb')}
    data = {'language': language}
    response = requests.post(url, files=files, data=data)
    if response.status_code == 200:
        return response.json()['text']
    else:
        raise Exception("Error transcribing audio")


def generate_response_audio(transcription, language, audio):
    """调用生成回答音频API"""
    url = "http://127.0.0.1:9992/tts"
    data = {
        "text": transcription, 
        'language': language
    }
    files = {'audio': open(audio, 'rb')}
    response_audio = requests.post(url, data=data, files=files)
    if response_audio.status_code == 200:
        return io.BytesIO(response_audio.content)
    else:
        raise Exception("Error generating response audio")

@app.route('/process_audio', methods=['POST'])
def process_audio():
    # 检查语言表单项
    if 'audio' not in request.files or 'language' not in request.form:
        return jsonify({"error": "Audio file and language must be provided"}), 400

    # 从请求中获取语言设置和音频
    request_audio = request.files['audio']
    language = request.form['language']

    if language not in ['chinese', 'english']:
        return jsonify({"error": "Unsupported language"}), 400
    
    unique_id = str(uuid.uuid4())
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    os.makedirs('temp', exist_ok=True)
    input_audio_filename = f"input_{timestamp}_{unique_id}.wav"
    input_audio_path = os.path.join('temp', input_audio_filename)
    request_audio.save(input_audio_path)

    try:
        # 使用WeNet，音频转文本
        transcription = transcribe_audio(input_audio_path, language)
        # 生成回答音频
        response_audio = generate_response_audio(transcription, language, input_audio_path)

        # 返回生成的音频文件
        return send_file(response_audio, as_attachment=True, download_name='response.wav', mimetype='audio/wav')
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        if os.path.exists(input_audio_path):
            os.remove(input_audio_path)

if __name__ == '__main__':
    app.run()
