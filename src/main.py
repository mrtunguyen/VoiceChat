import json
import os

import llama_cpp
from RealtimeSTT import AudioToTextRecorder
from RealtimeTTS import CoquiEngine, TextToAudioStream

FOLDER = os.path.dirname(os.path.abspath(__file__))

def replace_placeholders(params, char, user, scenario):
    for key in params:
        if isinstance(params[key], str):
            params[key] = params[key].replace("{char}", char)
            params[key] = params[key].replace("{user}", user)
            params[key] = params[key].replace("{scenario}", scenario)
    return params

def write_file(file_path, content, mode='w'):
    with open(file_path, mode) as f:
        f.write(content)

def clear_console():
    os.system('clear' if os.name == 'posix' else 'cls')

def encode(string):
    return model.tokenize(string.encode() if isinstance(string, str) else string)

def count_tokens(string):
    return len(encode(string))

def create_prompt(chat_params):
    prompt = f'<|system|>\n{chat_params["system_prompt"]}</s>\n'

    if chat_params["initial_message"]:
        prompt += f"<|assistant|>\n{chat_params['initial_message']}</s>\n"

    return prompt + "".join(history) + "<|assistant|>"

def generate(chat_params, completion_params):
    global output
    output = ""
    prompt = create_prompt(chat_params)
    write_file('last_prompt.txt', prompt)
    completion_params['prompt'] = prompt
    first_chunk = True
    for completion_chunk in model.create_completion(**completion_params):
        text = completion_chunk['choices'][0]['text']
        if first_chunk and text.isspace():
            continue
        first_chunk = False
        output += text
        yield text

if __name__ == "__main__":
    with open(os.path.join(FOLDER, 'creation_params.json')) as f:
        creation_params = json.load(f)
    with open(os.path.join(FOLDER, 'completion_params.json')) as f:
        completion_params = json.load(f)
    with open(os.path.join(FOLDER, 'chat_params.json')) as f:
        chat_params = json.load(f)
    
    chat_params = replace_placeholders(chat_params, 
                                       chat_params["char"], 
                                       chat_params["user"], 
                                       chat_params["scenario"])

    if not completion_params['logits_processor']:
        completion_params['logits_processor'] = None

    model = llama_cpp.Llama(**creation_params)
    coqui_engine = CoquiEngine(cloning_reference_wav="female.wav", language="en")

    stream = TextToAudioStream(coqui_engine, log_characters=True)
    recorder = AudioToTextRecorder(model='tiny.en', language='en', spinner=False)

    history = []
    while True:
        print(f'>>> {chat_params["user"]}: ', end="", flush=True)
        print(f'{(user_text := recorder.text())}\n<<< {chat_params["char"]}: ', end="", flush=True)
        history.append(f"<|user|>\n{user_text}</s>\n")

        tokens_history = count_tokens(create_prompt(chat_params))
        while tokens_history > 8192 - 500:
            history.pop(0)
            history.pop(0)
            tokens_history = count_tokens(create_prompt(chat_params))

        generator = generate(chat_params,completion_params)
        stream.feed(generator)
        stream.play(fast_sentence_fragment=True, 
                    buffer_threshold_seconds=999, 
                    minimum_sentence_length=18, 
                    log_synthesized_text=True)
        history.append(f"<|assistant|>\n{output}</s>\n")
        write_file('last_prompt.txt', create_prompt(chat_params))
