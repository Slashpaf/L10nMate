import os
import shutil
import time
import json
import re
import requests
import json
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
INPUT_FOLDER = os.path.join(BASE_DIR, os.getenv("INPUT_FOLDER", "input_files"))
OUTPUT_FOLDER = os.path.join(BASE_DIR, os.getenv("OUTPUT_FOLDER", "output_files"))
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
OPENAI_MODEL = os.environ.get("OPENAI_MODEL", "gpt-4o-mini") #recommended gpt-4o-mini (fast & cheap), gpt-4-turbo (balanced), gpt-4o (expensive and slow)
SOURCE_LANGUAGE = os.environ.get("SOURCE_LANGUAGE", "null")
TARGET_LANGUAGE = os.environ.get("TARGET_LANGUAGE", "fr,de").split(",")
ACCEPTED_EXTENSIONS = os.environ.get("ACCEPTED_EXTENSIONS", "txt,properties,arb").split(",")
DELETE_INPUT = os.environ.get("DELETE_INPUT", "false").lower() == "true"
CONTINUOUS_MONITORING = os.environ.get("CONTINUOUS_MONITORING", "true").lower() == "true"
OVERWRITE_EXISTING = os.environ.get("OVERWRITE_EXISTING", "false").lower() == "true"
SOURCE_FILE = os.environ.get("SOURCE_FILE", "")
UPDATE_EXISTING_JSON = os.environ.get("UPDATE_EXISTING_JSON", "false").lower() == "true"
JSON_MODE = os.environ.get("JSON_MODE", "false").lower() == "true"
UPDATE_SOURCE = os.environ.get("UPDATE_SOURCE", "false").lower() == "true"
MERGE_INTO_STRUCTURE = os.environ.get("MERGE_INTO_STRUCTURE", "false").lower() == "true"
KEYS_FILTER_REGEX = os.environ.get("KEYS_FILTER_REGEX", "null")
MAX_ITEMS_PER_REQUEST = int(os.environ.get("MAX_ITEMS_PER_REQUEST", "0"))  # 0 = no pagination



def translate(text, source_language, target_language):
    print(f"Starting translation from {source_language} to {target_language}")
    instructions = os.environ.get("INSTRUCTIONS", "")
    systemPrompt = f"Translate the following text from {source_language} to {target_language} while keeping the same structure and without including any Markdown or formatting. Never translate or modify the keys of a json structure, only translate the values. {instructions}"
    userPrompt = f"{text}"


    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {OPENAI_API_KEY}"
    }
    data = {
        "model": OPENAI_MODEL,
        "messages": [
            {"role": "system", "content": systemPrompt},
            {"role": "user", "content": userPrompt}
        ],
        "temperature": 0.7
    }
    
    if JSON_MODE:
        data['response_format'] = { 'type': 'json_object' }
        
    print(data)

    try:
        response = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers=headers,
            json=data
        )
        response.raise_for_status()  # Will raise an HTTPError if the HTTP request returned an unsuccessful status code

        print("Response:")
        print("Response:", response.text if response else response.text)

        response_data = response.json()
        translated_text = response_data.get("choices", [{}])[0].get("message", {}).get("content", "")

        if not translated_text:
            print("No translation returned from API")
            return "Translation error"

    except requests.exceptions.RequestException as e:
        print(f"RequestException: {e}")
        print("Response:", response.text if response else "No response")
        return "Translation error"

    return translated_text


def is_valid_json(content):
    try:
        json.loads(content)
        return True
    except ValueError:
        return False

def reorganize_json_content(source_content, target_content):
    """Reorganize the target JSON content to match the key order of the source content."""
    ordered_content = {key: target_content[key] for key in source_content if key in target_content}
    return ordered_content

def paginate_json(data, max_items):
    """Split JSON data into chunks based on max_items."""
    keys = list(data.keys())
    for i in range(0, len(keys), max_items):
        yield {key: data[key] for key in keys[i:i + max_items]}

def translate_and_save(src_path, source_language, target_language):
    print(f"Translating file: {src_path}, from {source_language} to {target_language}")

    with open(src_path, "r", encoding='utf-8') as input_file:
        source_content_raw = input_file.read()

    if not is_valid_json(source_content_raw):
        print(f"File {src_path} is not valid JSON. Skipping JSON-specific processing.")
        source_content = source_content_raw
    else:
        source_content = json.loads(source_content_raw)


    file_base, file_ext = os.path.splitext(os.path.basename(src_path))
    new_file_base = "_".join(file_base.split("_")[:-1]) + f"_{target_language}"
    output_file_path = os.path.join(OUTPUT_FOLDER, new_file_base + file_ext)
    
    if UPDATE_SOURCE:
        output_file_path = src_path+".tmp"
        shutil.copy(src_path, output_file_path)




    if os.path.exists(output_file_path) and UPDATE_EXISTING_JSON and is_valid_json(source_content_raw):
        # Load existing translations from the target file
        with open(output_file_path, "r", encoding='utf-8') as output_file:
            target_content_raw = output_file.read()

        if is_valid_json(target_content_raw):
            target_content = json.loads(target_content_raw)
            print(f"Existing target content keys: {list(target_content.keys())}")

            # Only translate keys that are missing or untranslated in the target file
            keys_to_translate = {
                key: value for key, value in source_content.items()
                if key not in target_content or not target_content[key].strip()
            }

            print(f"Keys to translate: {list(keys_to_translate.keys())}")

            # Translate missing keys in chunks if MAX_ITEMS_PER_REQUEST is set
            if keys_to_translate:
                if MAX_ITEMS_PER_REQUEST > 0:
                    for chunk in paginate_json(keys_to_translate, MAX_ITEMS_PER_REQUEST):
                        translated_chunk = translate(json.dumps(chunk), source_language, target_language)
                        translated_chunk_json = json.loads(translated_chunk)
                        target_content.update(translated_chunk_json)  # Merge translated chunk
                else:
                    # Translate all keys at once if no pagination is set
                    translated_chunk = translate(json.dumps(keys_to_translate), source_language, target_language)
                    translated_chunk_json = json.loads(translated_chunk)
                    target_content.update(translated_chunk_json)

            # Merge new translations and reorganize to match source structure
            translated_content = reorganize_json_content(source_content, target_content)

            # Save the updated content back to the file
            with open(output_file_path, "w", encoding='utf-8') as output_file:
                json.dump(translated_content, output_file, ensure_ascii=False, indent=4)
            print(f"Updated file with new translations: {output_file_path}")
        else:
            print(f"Existing target file {output_file_path} is not valid JSON. Proceeding to translate all.")
            translated_content = json.loads(translate(json.dumps(source_content), source_language, target_language))
    else:
        # Handle case where output file does not exist or we are not updating
        if is_valid_json(source_content_raw):
            if MAX_ITEMS_PER_REQUEST > 0:
                # Paginate JSON content
                translated_content = {}
                for chunk in paginate_json(source_content, MAX_ITEMS_PER_REQUEST):
                    chunk_translation = translate(json.dumps(chunk), source_language, target_language)
                    chunk_translation_json = json.loads(chunk_translation)
                    translated_content.update(chunk_translation_json)
            else:
                # Translate entire JSON file
                translated_content = json.loads(translate(json.dumps(source_content), source_language, target_language))

            if KEYS_FILTER_REGEX != "null":
                translated_content = filter_json_by_keys(translated_content, KEYS_FILTER_REGEX)

            if MERGE_INTO_STRUCTURE:
                translated_content = merge_translated_content(source_content, translated_content)

            # Save the translated JSON content
            with open(output_file_path, "w", encoding='utf-8') as output_file:
                json.dump(translated_content, output_file, ensure_ascii=False, indent=4)
            print(f"Translation complete for new file. File saved to: {output_file_path}")
        else:
            # Handle non-JSON content
            translated_content = translate(source_content_raw, source_language, target_language)
            with open(output_file_path, "w", encoding='utf-8') as output_file:
                output_file.write(translated_content)
            print(f"Translation complete. File saved to: {output_file_path}")





            
    if UPDATE_SOURCE:
        os.replace(output_file_path, src_path)  # Replace the original file with the updated one
        print(f"Original source file updated: {src_path}")

def filter_json_by_keys(data, regex):
    """Recursively filter JSON data based on regex matching on the keys."""
    if isinstance(data, dict):
        new_dict = {}
        for key, value in data.items():
            if re.match(regex, key):
                new_dict[key] = value
            elif isinstance(value, (dict, list)):
                result = filter_json_by_keys(value, regex)
                if result:
                    new_dict[key] = result
        return new_dict
    elif isinstance(data, list):
        new_list = [filter_json_by_keys(item, regex) for item in data]
        new_list = [item for item in new_list if item]  # Remove empty results
        return new_list if new_list else None
    return None

    
def merge_translated_content(original_data, translated_data):
    """Merges the translated data back into the original JSON structure."""
    for key, value in translated_data.items():
        if key in original_data and isinstance(original_data[key], dict) and isinstance(value, dict):
            original_data[key].update(value)
        else:
            original_data[key] = value
    return original_data

def monitor_input_folder():
    print(f"Script started. Monitoring the input folder: {INPUT_FOLDER}")

    while True:
        if SOURCE_FILE:
            # Process only the specified source file
            files_to_process = [SOURCE_FILE] if SOURCE_FILE in os.listdir(INPUT_FOLDER) else []
        else:
            # Process all files in the input folder
            files_to_process = os.listdir(INPUT_FOLDER)

        print(f"Files to process: {files_to_process}")

        for file_name in files_to_process:
            print(f"Processing file: {file_name}")
            src_path = os.path.join(INPUT_FOLDER, file_name)
            file_extension = os.path.splitext(file_name)[1][1:]
            if os.path.isfile(src_path) and file_extension in ACCEPTED_EXTENSIONS:
                if(SOURCE_LANGUAGE == "null"):
                    source_language = file_name.split("_")[-1].split(".")[0]
                else:
                    source_language = SOURCE_LANGUAGE
                    
                for target_language in TARGET_LANGUAGE:
                    translate_and_save(src_path, source_language, target_language)
                
                if DELETE_INPUT:
                    os.remove(src_path)
                    print(f"Input file deleted: {src_path}")

        if not CONTINUOUS_MONITORING:
            print("Continuous monitoring is disabled. Stopping script.")
            break

        time.sleep(10)

if __name__ == "__main__":
    monitor_input_folder()
