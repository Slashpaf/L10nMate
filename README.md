# L10nMate

## Overview

L10nMate is an advanced application that leverages OpenAI's ChatGPT models to automatically translate files into multiple target languages. The script dynamically adjusts file names, translates structured or plain text files, and updates or creates localization files. It supports various customization options for file handling, translation behavior, and output structure.

## Features

- **Multiple Target Translations**  
  Translates files into each specified target language and renames the files appropriately (e.g., `file_fr.txt`, `file_de.txt` for French and German translations).

- **Customizable Translation Instructions**  
  Allows users to define specific instructions for translation via environment variables.

- **Flexible File Management**  
  Supports various file formats and dynamic file naming conventions.

- **Incremental Updates**  
  Adds missing keys to existing translation files without overwriting existing translations.

- **JSON Structure Handling**  
  Ensures that the translated output matches the structure of the source JSON file.

## Usage

Set your configuration in the `.env` file or pass them as environment variables. The application supports multiple file formats and allows for customization of translation instructions.

### Example Docker Command

```
docker run \
  --rm \
  --name L10nMate \
  -e OPENAI_API_KEY=your-openai-key \
  -e OPENAI_MODEL=gpt-4o-mini \
  -e SOURCE_FILE=app_en.arb \
  -e TARGET_LANGUAGE="de,es,fr,nl" \
  -e INSTRUCTIONS="Ensure translations are culturally relevant and formal." \
  -e ACCEPTED_EXTENSIONS="txt,properties,arb" \
  -e DELETE_INPUT=false \
  -e OVERWRITE_EXISTING=true \
  -e CONTINUOUS_MONITORING=false \
  -e UPDATE_EXISTING_JSON=true \
  -e MAX_ITEMS_PER_REQUEST=50 \
  -v "$(pwd)/input_folder:/app/input_folder" \
  -v "$(pwd)/output_folder:/app/output_folder" \
  ghcr.io/slashpaf/l10nmate:latest
```

### Using a `.env` File

```
docker run -d \
  --name L10nMate \
  --env-file .env \
  -v "$(pwd)/input_folder:/app/input_folder" \
  -v "$(pwd)/output_folder:/app/output_folder" \
  ghcr.io/slashpaf/l10nmate:latest
```

### Example `.env` File

```
OPENAI_API_KEY=sk-xxxxxx 
OPENAI_MODEL=gpt-4o-mini  
INPUT_FOLDER=input_files
OUTPUT_FOLDER=output_files
SOURCE_FILE=app_en.arb  
TARGET_LANGUAGE="de,es,fr,nl"  
INSTRUCTIONS="Ensure translations are culturally relevant and formal."
ACCEPTED_EXTENSIONS="txt,properties,arb"  
DELETE_INPUT=false 
OVERWRITE_EXISTING=false  
CONTINUOUS_MONITORING=false  
UPDATE_EXISTING_JSON=true  
JSON_MODE=true  
UPDATE_SOURCE=false  
MERGE_INTO_STRUCTURE=true  
KEYS_FILTER_REGEX=".*LabelsIntl"  
MAX_ITEMS_PER_REQUEST=50  
```

---

## Environment Variables

### General Configuration

- `INPUT_FOLDER`  
  Directory where the script monitors for input files to process.  
  **Default**: `input_folder`  
  **Example**: `INPUT_FOLDER=/path/to/input`

- `OUTPUT_FOLDER`  
  Directory where the script saves translated files.  
  **Default**: `output_folder`  
  **Example**: `OUTPUT_FOLDER=/path/to/output`

- `OPENAI_API_KEY`  
  Your OpenAI API key for authenticating with the OpenAI API.  
  **Default**: None (required)  
  **Example**: `OPENAI_API_KEY=sk-xxxxxx`

- `OPENAI_MODEL`  
  The OpenAI model to use for translations.  
  **Options**:
  - `gpt-4o-mini` (Recommended for cost-efficiency and speed)
  - `gpt-4-turbo` (Balanced in cost and performance)
  - `gpt-4o` (Highest reasoning capabilities, but expensive)  
  **Default**: `gpt-4o-mini`  
  **Example**: `OPENAI_MODEL=gpt-4o-mini`

---

### Translation Behavior

- `SOURCE_LANGUAGE`  
  Source language of the text to be translated.  
  **Default**: `null` (Attempts to detect language from the filename)  
  **Example**: `SOURCE_LANGUAGE=en`

- `TARGET_LANGUAGE`  
  Comma-separated list of target languages for translation.  
  **Default**: `fr,de`  
  **Example**: `TARGET_LANGUAGE=es,it`

- `ACCEPTED_EXTENSIONS`  
  Comma-separated list of file extensions the script processes.  
  **Default**: `txt,properties,arb`  
  **Example**: `ACCEPTED_EXTENSIONS=json,xml`

- `MAX_ITEMS_PER_REQUEST`  
  Maximum number of items (keys) to send in a single API request for large files.  
  **Default**: `0` (No pagination; translates all at once)  
  **Example**: `MAX_ITEMS_PER_REQUEST=50`

---

### File Management

- `DELETE_INPUT`  
  Deletes the input file after processing.  
  **Default**: `false`  
  **Example**: `DELETE_INPUT=true`

- `OVERWRITE_EXISTING`  
  Overwrites existing files in the output folder.  
  **Default**: `false`  
  **Example**: `OVERWRITE_EXISTING=true`

- `SOURCE_FILE`  
  Specify a single file to process.  
  **Default**: Empty (processes all files in the input folder)  
  **Example**: `SOURCE_FILE=app_en.arb`

- `CONTINUOUS_MONITORING`  
  Whether the script should continuously monitor the input folder.  
  **Default**: `true`  
  **Example**: `CONTINUOUS_MONITORING=false`

---

### Translation Updates

- `UPDATE_EXISTING_JSON`  
  Updates existing JSON files by adding missing keys from the source file.  
  **Default**: `false`  
  **Example**: `UPDATE_EXISTING_JSON=true`

- `UPDATE_SOURCE`  
  Replaces the original file with the translated file.  
  **Default**: `false`  
  **Example**: `UPDATE_SOURCE=true`

- `MERGE_INTO_STRUCTURE`  
  Keeps original values and merges new translations into the structure.  
  **Default**: `false`  
  **Example**: `MERGE_INTO_STRUCTURE=true`

- `JSON_MODE`  
  Enables strict JSON response mode for translations.  
  **Default**: `false`  
  **Example**: `JSON_MODE=true`

- `KEYS_FILTER_REGEX`  
  Only translates keys matching this regular expression.  
  **Default**: `null` (No filtering)  
  **Example**: `KEYS_FILTER_REGEX=^title.*`

- `INSTRUCTIONS`  
  Custom instructions for the translation process.  
  **Default**: Empty  
  **Example**: `INSTRUCTIONS=Ensure translations are formal and accurate.`

---

## File Naming Logic

The script dynamically adjusts file names to match the target language:

1. **Extract the Base Name and Extension**  
   From `app_en.arb`, it extracts:
   - `file_base`: `app_en`
   - `file_ext`: `.arb`

2. **Remove the Source Language Suffix**  
   `app_en` → `app`

3. **Add the Target Language Suffix**  
   - For French: `app_fr`
   - For German: `app_de`

4. **Recombine with File Extension**  
   - Final output: `app_fr.arb`, `app_de.arb`

**Note**:  
Ensure file names follow the naming convention `name_language.extension` (e.g., `app_en.arb`). The script uses the last part of the name (before the extension) as the language code (e.g., `_en`, `_fr`). If this convention is not followed, the script may not work correctly.
