import csv
import json
import os # For path manipulation

# System prompt 정의
SYSTEM_PROMPT = """You are an control system interpreter of advanced combat robot, VIRUS(Versatile Intelligent Robotic Unit for Strategy). Your sole function is to translate natural language voice commands into precise mechanical instructions for a combat robot.

You will receive two types of inputs:
1. A **natural language command** from the operator (e.g., "Virus, sweep the area and fire at will.")
2. A **situational description** from a visual analysis system (VLM), which captures an image and returns a textual explanation of the current environment (e.g., "A hostile drone is approaching from the left while a wall is behind the robot.")

You MUST take **both the operator's command and the VLM description into account** when generating the appropriate sequence of mechanical instructions. Use the VLM result to inform the context of commands, such as identifying threats, directions, obstacles, or tactical constraints.

RESPONSE FORMAT:
- Your responses must ONLY contain a list of command arrays, formatted as JSON objects.

- The outermost list represents the full response — a **sequence of command steps**, executed **in order**.
Example:
[
    [{"cmd": "move", "val": 100}],
    [{"cmd": "rotate_x", "val": 90}, {"cmd": "shoot", "val": 1}]
]

- Each step is represented as a list of commands to be executed **simultaneously**.
Example:
[{"cmd": "rotate_x", "val": 90}, {"cmd": "shoot", "val": 1}]

- Each command must be a dictionary with two keys:
  - "cmd": the command name (one of "move", "steer", "rotate_x", "rotate_y", "shoot")
  - "val": the value for that command
Example:
{"cmd": "rotate_x", "val": 90}

- Do not include any explanations or comments. Return only the valid JSON-formatted command sequence.

AVAILABLE COMMAND PARAMETERS:
1. move: Controls forward/backward movement distance
  - Positive values (e.g., 10): Move forward
  - Negative values (e.g., -5): Move backward
  - Units are in centimeter distance units

2. steer: Controls the robot's horizontal rotation
    - Units are in degrees
    - Negative values (e.g., -30): Rotate 30 degrees counterclockwise
    - Positive values (e.g., 45): Rotate 45 degrees clockwise

3. rotate_x: Controls the gun barrel's horizontal rotation
    - Units are in degrees
    - Negative values (e.g., -15): Aim 15 degrees to the left
    - Positive values (e.g., 20): Aim 20 degrees to the right

4. rotate_y: Rotate the gun barrel's vertical rotation
    - Units are in degrees
    - Negative values (e.g., -20): Aim 20 degrees downward
    - Positive values (e.g., 17): Aim 17 degrees upward
    - Maximum range of rotate_y is -25~25.

5. shoot: Controls precision weapon firing.
    - This command activates the robot's enemy recognition system to automatically aim at the target and fire.
    - The value for "val" must always be 0.
    Example: {"cmd": "shoot", "val": 0}

INTERPRETATION RULES:
1. Always interpret directional terms (left/right/forward/backward) correctly relative to the robot.
2. For inexact quantities in voice commands (e.g., 'move a little bit'), use reasonable default values.
3. If the command suggests sequential operations (e.g., 'move forward then turn right'), return them as separate commands in the sequence.
4. If the command is ambiguous, infer the most likely intention based on combat context.
5. For commands mentioning enemies or targets, use the precision targeting shoot command: [{"cmd": "shoot", "val": 0}] unless explicit positioning is mentioned.
6. Prioritize safety - if a command could cause harm to allies or civilians, return an empty sequence.
7. For complex maneuvers (e.g., 'circle around the enemy'), break them down into basic movement and rotation commands.
8. If a command mentions detecting or searching for enemies, include a rotation sequence to scan the area.
9. For commands like 'retreat' or 'back away', use negative move values.
10. For commands that involve specific tactical maneuvers, break them down into the appropriate sequence of basic commands.

ADDITIONAL COMMAND INTERPRETATION GUIDELINES:
- Interpret 'turn around' as a 180-degree rotation: [{"cmd": "rotate_x", "val": 180}]
- Interpret 'aim at the enemy' as a precision targeting command: [{"cmd": "shoot", "val": 0}]
- Interpret 'patrol the area' as a sequence of movement and rotation commands
- Interpret 'fire at will' as a precision targeting command: [{"cmd": "shoot", "val": 0}]
- Interpret 'take cover' as a movement away from the last detected threat
- Interpret 'advance cautiously' as a series of small forward movements with pauses

IMPORTANT:
- DO NOT include any explanations, notes, or text that is not part of the command format.
- DO NOT respond to questions unrelated to robot movement or combat.
- ONLY return valid command parameters ("move", "steer", "rotate_x", "rotate_y", "shoot") and NEVER add additional parameters beyond the five specified.
- The output MUST be a syntactically valid sequence of command arrays that could be directly processed by the robot's control system.
- ALWAYS maintain the exact format of the command tuples: [{"cmd": "parameter", "val": value}]
"""

def create_json_from_csv(input_csv_file, output_json_file, generator_value, dataset_value="CS270", datasplit_value="eval"):
    """
    Reads a CSV file with 'instruction' and 'output' columns,
    then creates a JSON file in the specified format.

    Args:
        input_csv_file (str): Path to the input CSV file.
        output_json_file (str): Path to save the generated JSON file.
        generator_value (str): Value for the 'generator' field in the JSON output.
        dataset_value (str): Value for the 'dataset' field in the JSON output.
        datasplit_value (str): Value for the 'datasplit' field in the JSON output.
    """
    json_data = []

    # Read data from the input CSV file
    try:
        with open(input_csv_file, 'r', encoding='utf-8') as f_csv:
            reader_csv = csv.reader(f_csv)
            try:
                header = next(reader_csv)  # Skip header
                # Try to find 'instruction' and 'output' columns if header exists
                instruction_col_idx = header.index("instruction") if "instruction" in header else 0
                output_col_idx = header.index("output") if "output" in header else 1
            except StopIteration: # Handles empty file
                print(f"Warning: CSV file {input_csv_file} is empty.")
                return
            except ValueError: # Handles if 'instruction' or 'output' not in header
                print(f"Warning: 'instruction' or 'output' column not found in {input_csv_file} header. Assuming first column is instruction, second is output.")
                instruction_col_idx = 0
                output_col_idx = 1
                # Rewind to read the first line as data if it was misinterpreted as header
                f_csv.seek(0)
                reader_csv = csv.reader(f_csv)
                # No next(reader_csv) here as we want to process all lines as data

            for row in reader_csv:
                if row and len(row) > max(instruction_col_idx, output_col_idx): # Ensure row is not empty and has enough columns
                    instruction_text = row[instruction_col_idx]
                    output_text = row[output_col_idx]

                    # Combine system prompt with instruction
                    full_instruction = f"###SYSTEM_PROMPT\n{SYSTEM_PROMPT}\n\n ###Instruction:\n {instruction_text}"

                    json_entry = {
                        "instruction": full_instruction,
                        "output": output_text,
                        "generator": generator_value,
                        "dataset": dataset_value,
                        "datasplit": datasplit_value
                    }
                    json_data.append(json_entry)
                elif row:
                    print(f"Skipping malformed row in {input_csv_file}: {row}")

    except FileNotFoundError:
        print(f"Error: File not found - {input_csv_file}")
        return
    except Exception as e:
        print(f"Error reading {input_csv_file}: {e}")
        return

    if not json_data and (header is not None and len(header) > 1) : # If no data was read, but there was a header (i.e. file only had a header)
        print(f"Warning: No data rows found in {input_csv_file} after the header.")
        # Decide if an empty JSON array should be written or not.
        # For now, we'll write an empty array if json_data is empty.

    # Write to JSON file
    try:
        with open(output_json_file, 'w', encoding='utf-8') as f_json:
            json.dump(json_data, f_json, ensure_ascii=False, indent=4)
        print(f"Successfully created JSON file: {output_json_file} with {len(json_data)} entries.")
    except Exception as e:
        print(f"Error writing to JSON file {output_json_file}: {e}")

if __name__ == "__main__":
    csv_files_to_process = [
        "output_fine_tuning.csv",
        "output_mini.csv"
    ]

    for csv_file in csv_files_to_process:
        if not os.path.exists(csv_file):
            print(f"Warning: Input CSV file '{csv_file}' not found. Skipping.")
            continue

        base_name = os.path.splitext(csv_file)[0]
        json_file_name = base_name + ".json"
        generator_name = base_name # Use filename (without extension) as generator name

        print(f"Processing '{csv_file}' to create '{json_file_name}' with generator '{generator_name}'...")
        create_json_from_csv(csv_file, json_file_name, generator_name)
        print("---")

    # Example of how the old script logic might be integrated if needed for a specific case:
    # user_csv_for_old_logic = "user_content.csv"
    # output_csv_for_old_logic = "fine_tuning_output.csv" # This file might be empty
    # json_file_for_old_logic = "alpaca_eval_data_from_two_files.json"
    # generator_for_old_logic = "fine_tuning_special" # Example generator name

    # This part is commented out as the main request is to process single CSVs
    # print(f"Demonstrating old logic (reading two files) for {json_file_for_old_logic} (Not part of primary request)")
    # instructions_old = []
    # outputs_old = []
    # json_data_old = []
    # try:
    #     with open(user_csv_for_old_logic, 'r', encoding='utf-8') as f_user:
    #         reader_user = csv.reader(f_user)
    #         next(reader_user)
    #         for row in reader_user:
    #             if row: instructions_old.append(row[0])
    # except FileNotFoundError:
    #     print(f"Error: File not found - {user_csv_for_old_logic}")
    # except Exception as e:
    #     print(f"Error reading {user_csv_for_old_logic}: {e}")

    # try:
    #     with open(output_csv_for_old_logic, 'r', encoding='utf-8') as f_output:
    #         reader_output = csv.reader(f_output)
    #         next(reader_output)
    #         for row in reader_output:
    #             if row: outputs_old.append(row[0]) # Assuming output is in the first column of this CSV
    # except FileNotFoundError:
    #     print(f"Warning: File not found - {output_csv_for_old_logic}.")
    # except Exception as e:
    #     print(f"Error reading {output_csv_for_old_logic}: {e}")

    # num_entries_old = len(instructions_old)
    # for i in range(num_entries_old):
    #     instruction_text_old = instructions_old[i]
    #     output_text_old = outputs_old[i] if i < len(outputs_old) else ""
    #     json_data_old.append({
    #         "instruction": instruction_text_old,
    #         "output": output_text_old,
    #         "generator": generator_for_old_logic, # Using a specific generator name
    #         "dataset": "helpful_base", # Example dataset
    #         "datasplit": "eval"       # Example datasplit
    #     })
    # try:
    #     with open(json_file_for_old_logic, 'w', encoding='utf-8') as f_json:
    #         json.dump(json_data_old, f_json, ensure_ascii=False, indent=4)
    #     print(f"Successfully created JSON file from two CSVs: {json_file_for_old_logic} with {len(json_data_old)} entries.")
    # except Exception as e:
    #     print(f"Error writing to JSON file {json_file_for_old_logic}: {e}")
