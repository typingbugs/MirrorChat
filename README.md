# 1. 什么是Mirror Chat？

Mirror Chat是一个AI驱动的音频对话系统。该系统实现一个后端模型API：请求方输入语言选择（支持中/英）和音频，API返回AI生成的回答音频，该音频克隆了请求方音频的发音人音色。



# 2. 系统架构

<img src="images\架构图.drawio.svg" alt="架构图.drawio" style="zoom: 50%;" />



# 3. 安装方法

环境：Ubuntu 22.04，显存8G以上

各个组件以API的形式独立运行（可以运行在不同服务器中），可以在同一局域网中调用，也可以通过内网穿透的方式调用。

## 3.1. WeNet

参考[WeNet的Github页面](https://github.com/wenet-e2e/wenet)

1. 克隆仓库

   在MirrorChat目录下：

   ```sh
   cd dependencies
   git clone https://github.com/wenet-e2e/wenet.git
   ```

2. 创建Conda环境

   ```sh
   conda create -n wenet python=3.10
   conda activate wenet
   ```

3. 安装CUDA，建议12.1版本以上

4. 安装torch和torchaudio，以及其他依赖包

   ```sh
   pip install torch==2.2.2+cu121 torchaudio==2.2.2+cu121 -f https://download.pytorch.org/whl/torch_stable.html
   pip install -r requirements.txt
   pre-commit install  # for clean and tidy code
   ```

5. （可选）构建部署

   ```
   # runtime build requires cmake 3.14 or above
   cd runtime/libtorch
   mkdir build && cd build && cmake -DGRAPH_TOOLS=ON .. && cmake --build .
   ```

6. 运行

   在MirrorChat目录下：

   ```sh
   cd api/wenet
   bash run_wenet.sh
   ```

## 3.2. xTTS

参考[xTTS的Github页面](https://github.com/coqui-ai/TTS?tab=readme-ov-file)

1. 克隆仓库

   在MirrorChat目录下：

   ```sh
   cd dependencies
   git clone https://github.com/coqui-ai/TTS
   ```

2. 创建Conda环境

   ```sh
   conda create -n xtts python=3.10
   conda activate xtts
   ```

3. 安装依赖包

   ```sh
   pip install TTS
   pip install -e .
   ```

4. 运行

   在MirrorChat目录下：

   ```sh
   cd api/xtts
   bash run_xtts.sh
   ```

当显存充足时，可以编辑 `run_xtts.sh` 在不同端口开启多个服务，并在 `3.3. 问答TTS` 的 `main.py` 文件中对应修改调用接口，可以提高并行度，提高响应效率。

## 3.3. 问答TTS

1. 将上述模型运行起来后，在MirrorChat目录下：

   ```sh
   cd api/tts
   ```

2. 创建ChatGPT API的配置文件 `chatgpt_api_config.py`

   ```sh
   touch chatgpt_api_config.py
   vim chatgpt_api_config.py
   ```

   并将ChatGPT API的配置以以下形式写入（支持多个API，默认使用第1个API，当前面的API无法使用，会自动使用后面的API）：

   ```python
   chatgpt_apis = [
       {
           'url': "https://api.openai.com/v1/chat/completions",
           'key': "sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
       },
   ]
   ```

3. 运行

   在 `MirrorChat/api/tts` 目录下：

   ```sh
   bash run_tts.sh
   ```

## 3.4. 对外接口

进入 `MirrorChat/api/service` 目录，运行对外接口服务

```sh
cd api/service
bash run_service.sh
```

## 3.5. 调用方法

你可以使用类型下面python代码的方式调用该接口：

```python
import requests

def test_process_audio(api_url, audio_file_path, language):
    url = f"{api_url}/process_audio"
    files = {'audio': open(audio_file_path, 'rb')}
    data = {'language': language}
    response = requests.post(url, files=files, data=data)
    
    if response.status_code == 200:
        output_audio_path = 'response_audio.wav'
        with open(output_audio_path, 'wb') as f:
            f.write(response.content)
        print(f"Response audio saved to {output_audio_path}")
    else:
        print(f"Error: {response.status_code}")
        print(response.json())
```





