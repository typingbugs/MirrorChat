from flask import Flask, request, send_file, jsonify
import requests
import os
import uuid
from datetime import datetime
from pydub import AudioSegment
from concurrent.futures import ThreadPoolExecutor
from queue import Queue
import json
from io import BytesIO
from chatgpt_api_config import chatgpt_apis

app = Flask(__name__)

tts_servers = [
    'http://127.0.0.1:9995/tts',
    'http://127.0.0.1:9996/tts'
]
tts_server_index = 0
executor = ThreadPoolExecutor(max_workers=len(tts_servers))

zh_punc = {'。', '？', '！', '\n'}
en_punc = {'.', '?', '!', '\n'}

def merge_audio_files(base_audio, increment):
    """将多段语音拼接"""
    base_audio += increment
    return base_audio

def call_tts_api(server_url, response_text, language, audio):
    """调用ChatTTS API，回答转语音"""
    response = requests.post(
        server_url, 
        data={
            "text": response_text,
            'language': language
        },
        files={'audio': open(audio, 'rb')}
    )
    if response.status_code == 200:
        audio_segment = AudioSegment.from_file(file=BytesIO(response.content), format='wav')
        return audio_segment
    else:
        print(f"Error: {response.json()['error']}")
        return None


def generate_response_stream(transcription):
    """调用ChatGPT API，回答问题"""
    for index, chatgpt_api in enumerate(chatgpt_apis):
        url = chatgpt_api['url']
        api_key = chatgpt_api['key']

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        data = {
            "model": "gpt-3.5-turbo",
            "messages": [
                {"role": "user", "content": transcription}
            ],
            "temperature": 0.7,
            "stream": True
        }
        response = requests.post(url, headers=headers, json=data, stream=True)
        print(f"ChatGPT API {index} Response Status Code: {response.status_code}")
        if response.status_code == 200:
            return response
    return None


@app.route('/tts', methods=['POST'])
def tts():
    global tts_server_index

    unique_id = str(uuid.uuid4())
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    os.makedirs('temp', exist_ok=True)
    input_audio_filename = f"input_{timestamp}_{unique_id}.wav"
    input_audio_path = os.path.join('temp', input_audio_filename)
    output_audio_filename = f"output_{timestamp}_{unique_id}.wav"
    output_audio_path = os.path.join('temp', output_audio_filename)

    base_audio = AudioSegment.silent(duration=0)  # 初始化一个空音频段

    collected_chunks = []
    collected_messages = ['']
    futures = []
    audio_queue = Queue()

    language = request.form['language']
    response_stream = generate_response_stream(request.form['text'])
    if response_stream == None:
        return jsonify({"error": "Something wrong with ChatGPT API."}), 502
    speaker_file = request.files['audio']
    speaker_file.save(input_audio_path)

    try:
        for chunk in response_stream.iter_lines():
            if chunk:
                decoded_line = chunk.decode('utf-8')
                if decoded_line.startswith('data: '):
                    content = decoded_line[6:]
                    if content.strip() == '[DONE]':
                        break
                    response_json = json.loads(content)
                    collected_chunks.append(response_json)
                    chunk_message = response_json['choices'][0]['delta']
                    collected_messages[-1] += chunk_message.get('content', '')

                    if len(collected_messages[-1]) > 0 and collected_messages[-1][-1] in (zh_punc if language == 'chinese' else en_punc):
                        partial_text = collected_messages[-1]
                        if partial_text:
                            print(f"{partial_text}", end="")
                            server_url = tts_servers[tts_server_index % len(tts_servers)]
                            tts_server_index += 1
                            future = executor.submit(call_tts_api, server_url, partial_text, language, input_audio_path)
                            futures.append((partial_text, future))
                        collected_messages.append("")

        # 处理所有 future 并按顺序添加到队列中
        for partial_text, future in futures:
            audio_data = future.result()
            if audio_data:
                audio_queue.put((partial_text, audio_data))

        # 拼接音频文件
        while not audio_queue.empty():
            _, audio_segment = audio_queue.get()
            base_audio = merge_audio_files(base_audio, audio_segment)

        # 将最终的音频文件保存到硬盘
        base_audio.export(output_audio_path, format='wav')
        print("\n")

        # 返回生成的回答音频
        return send_file(output_audio_path, as_attachment=True, download_name='response.wav')
    finally:
        if os.path.exists(input_audio_path):
            os.remove(input_audio_path)
        if os.path.exists(output_audio_path):
            os.remove(output_audio_path)


if __name__ == '__main__':
    app.run()
