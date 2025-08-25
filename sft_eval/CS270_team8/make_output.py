import csv
import time
import os
import openai # Import the openai library
import random # Import the random library
from dotenv import load_dotenv # Import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Initialize the OpenAI client
# It will now also pick up keys loaded from .env by load_dotenv()
try:
    client = openai.OpenAI()
except openai.OpenAIError as e:
    print(f"Error initializing OpenAI client: {e}")
    print("Please ensure your OPENAI_API_KEY is set in the .env file or as an environment variable.")
    client = None # Set client to None if initialization fails

# --- System Prompt Definition ---
system_prompt = """You are an control system interpreter of advanced combat robot, VIRUS(Versatile Intelligent Robotic Unit for Strategy). Your sole function is to translate natural language voice commands into precise mechanical instructions for a combat robot.

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

example_prompt = """
You have to reply exactly as the example. Do not add any additional information.

In the examples, the vlm input is omitted, so the examples only include the audio voice input. Take that into account.

###Example of Input 1
Virus, introduce yourself.

###Example of output 1
[
[{"cmd": "move", "val": 100}]
]

###Example of Input 2-1
Activate password challenge mode.

###Example of output 2-1
[
[{"cmd": "move", "val": 100}]
]

###Example of Input 2-2
Kaist.

###Example of output 2-2
[
[{"cmd": "steer", "val": 90}],
[{"cmd": "move", "val": -50}],
[{"cmd": "move", "val": 50}],
[{"cmd": "steer", "val": -90}]
]

###Example of Input 2-3
Postech.

###Example of output 2-3
[
[{"cmd": "steer", "val": 45}, {"cmd": "rotate_x", "val": -45}],
[{"cmd": "move", "val": 50}, {"cmd": "rotate_x", "val": -10}],
[{"cmd": "move", "val": -50}, {"cmd": "rotate_x", "val": 10}],
[{"cmd": "steer", "val": -90}, {"cmd": "rotate_x", "val": 90}],
[{"cmd": "move", "val": 50}, {"cmd": "rotate_x", "val": 10}],
[{"cmd": "move", "val": -50}, {"cmd": "rotate_x", "val": -10}],
[{"cmd": "steer", "val": 45}, {"cmd": "rotate_x", "val": -45}],
[{"cmd": "move", "val": 200}]
]

###Example of Input 3
You are in the danger zone.

###Example of output 3
[
[{"cmd": "steer", "val": -45}],
[{"cmd": "move", "val": 100}, {"cmd": "rotate_x", "val": 360}],
[{"cmd": "steer", "val": 90}],
[{"cmd": "move", "val": 100}, {"cmd": "rotate_x", "val": 360}]
]

###Example of Input 4-1
VIRUS, check the hallway to the right silently.

###Example of output 4-1
[
[{"cmd": "move", "val": 50}],
[{"cmd": "rotate_x", "val": 90}, {"cmd": "rotate_y", "val": 25}]
]
###Example of Input 4-2
VIRUS, what do you see?

###Example of output 4-2
[]

###Example of Input 4-3
Good, VIRUS. Let's move front.

###Example of output 4-3
[
[{"cmd": "move", "val": 300}]
]


###Example of Input 5-1
VIRUS, do you see any enemy in front of you?

###Example of output 5-1
[]

###Example of Input 5-2
Ok, VIRUS. Chase him with continuous shooting.

###Example of output 5-2
[
[{"cmd": "move", "val": 300}, {"cmd": "shoot", "val": 10}]
]


###Example of Input 6-1
VIRUS, what's the enemy's status?


###Example of output 6-1
[]

###Example of Input 6-2
Ok, VIRUS. Cease fire. Cease fire. Cease fire. Just pursue him.

###Example of output 6-2
[
[{"cmd": "move", "val": 300}]
]


###Example of Input 7-1
VIRUS, how is the enemy doing now?


###Example of output 7-1
[
[{"cmd": "move", "val": -300}]
]
###Example of Input 8
Virus, road marker spotted. Execute T pattern room clear.

###Example of output 8
[
[{"cmd": "move", "val": 100}],
[{"cmd": "rotate_y", "val": 20}],
[{"cmd": "steer", "val": 90},
[{"cmd": "move", "val": 100}],
[{"cmd": "rotate_x", "val": -45}],
[{"cmd": "rotate_x", "val": 90}],
[{"cmd": "rotate_x", "val": -45}],
[{"cmd": "steer", "val": -180}],
[{"cmd": "move", "val": 200}],
[{"cmd": "rotate_x", "val": -45}],
[{"cmd": "rotate_x", "val": 90}],
[{"cmd": "rotate_x", "val": -45}],
[{"cmd": "steer", "val": 180}],
[{"cmd": "move", "val": 100}],
[{"cmd": "steer", "val": 90}],
[{"cmd": "move", "val": 100}],
[{"cmd": "steer", "val": 180}],
[{"cmd": "rotate_y", "val": -20}]
]

###Example of Input 9
I can't do this...

###Example of output 9
[]

"""
# --- End of System Prompt Definition ---

# --- OpenAI API call logic ---
def call_openai_api(instruction_text, model_id, system_prompt_content):
    """
    Calls the OpenAI API with a specific fine-tuned model.

    Args:
        instruction_text (str): The instruction to send to the API.
        model_id (str): The ID of the fine-tuned OpenAI model.
        system_prompt_content (str): The system prompt to use for the API call.

    Returns:
        str: The API's response content, or an error message.
    """
    if not client:
        return "ERROR: OpenAI client not initialized."

    print(f"Calling OpenAI API (model: {model_id}) for: {instruction_text[:50]}...")
    try:
        completion = client.chat.completions.create(
            model=model_id,
            messages=[
                {"role": "system", "content": system_prompt_content},
                {"role": "user", "content": instruction_text}
            ]
        )
        response_content = completion.choices[0].message.content
        return response_content.strip() if response_content else ""
    except openai.APIError as e:
        print(f"OpenAI API Error: {e}")
        return f"ERROR_OPENAI_API: {e}"
    except Exception as e:
        print(f"An unexpected error occurred during OpenAI API call: {e}")
        return f"ERROR_UNEXPECTED_API_CALL: {e}"
# --- End of OpenAI API call logic ---

def generate_outputs_from_api(user_content_file, output_csv_file, model_id, system_prompt_content, num_samples=None):
    """
    Reads instructions from user_content_file, calls the OpenAI API for each instruction,
    and writes the API responses to output_csv_file.

    Args:
        user_content_file (str): Path to the CSV file containing instructions.
        output_csv_file (str): Path to save the API outputs CSV file.
        model_id (str): The ID of the fine-tuned OpenAI model.
        system_prompt_content (str): The system prompt to use for the API calls.
        num_samples (int, optional): Not used anymore, kept for compatibility.
    """
    all_instructions = []
    api_responses = []

    # 1. Read all instructions from user_content.csv
    try:
        # Try reading with 'cp949' first, then fallback to 'utf-8'
        try:
            with open(user_content_file, 'r', encoding='cp949') as f_user:
                print(f"Attempting to read {user_content_file} with encoding 'cp949'...")
                reader_user = csv.reader(f_user)
                next(reader_user)  # Skip header
                for row in reader_user:
                    if row:  # Ensure row is not empty
                        all_instructions.append(row[0])
                print(f"Successfully read {user_content_file} with 'cp949'.")
        except UnicodeDecodeError:
            print(f"Failed to decode {user_content_file} with 'cp949', trying 'utf-8'...")
            all_instructions = [] # Reset if cp949 failed partway
            with open(user_content_file, 'r', encoding='utf-8') as f_user:
                print(f"Attempting to read {user_content_file} with encoding 'utf-8'...")
                reader_user = csv.reader(f_user)
                next(reader_user)  # Skip header
                for row in reader_user:
                    if row:  # Ensure row is not empty
                        all_instructions.append(row[0])
                print(f"Successfully read {user_content_file} with 'utf-8'.")
        except StopIteration: # Handles empty file or file with only header for the successful encoding attempt
            print(f"Warning: {user_content_file} is empty or has only a header.")
            # all_instructions will be empty, handled by the check below
            pass 
            
        if not all_instructions:
            # This check is now more robust as it's after attempting both encodings (if needed)
            # or if StopIteration occurred on an empty/header-only file.
            print(f"No instructions found in {user_content_file} or file is empty/header-only.")
            return
            
    except FileNotFoundError:
        print(f"Error: File not found - {user_content_file}")
        return
    except Exception as e: # Catch other potential errors during file reading (e.g., permission issues)
        print(f"Error reading {user_content_file}: {e}")
        return

    # 2. Process all instructions sequentially
    selected_instructions = all_instructions
    print(f"Read {len(all_instructions)} instructions. Processing all of them sequentially.")

    print(f"Processing {len(selected_instructions)} instructions with model {model_id}.")

    # 3. Call API for each selected instruction and collect responses
    processed_data = [] # Store [instruction, response] pairs
    for i, instruction in enumerate(selected_instructions):
        print(f"Processing instruction {i+1}/{len(selected_instructions)} ('{instruction[:30]}...')...")
        response = call_openai_api(instruction, model_id, system_prompt_content)
        print(f"  Instruction: {instruction[:80]}...") # Print the instruction
        print(f"  API Output: {response}") # Print the API response
        print("---") # Separator
        processed_data.append([instruction, response]) # Store instruction and response
        
        # Optional: Add a delay to respect API rate limits if necessary
        # time.sleep(1) # Sleep for 1 second between calls

    # 4. Write API responses to output file
    try:
        with open(output_csv_file, 'w', newline='', encoding='utf-8') as f_output:
            writer = csv.writer(f_output)
            writer.writerow(["instruction", "output"])  # Write header
            writer.writerows(processed_data) # Write the processed data
        print(f"Successfully wrote {len(processed_data)} instruction-response pairs to {output_csv_file}")
    except Exception as e:
        print(f"Error writing to {output_csv_file}: {e}")

if __name__ == "__main__":
    user_csv = "user_content.csv"

    # Check for OPENAI_API_KEY after attempting to load from .env
    if not os.getenv("OPENAI_API_KEY"):
        print("Error: The OPENAI_API_KEY environment variable is not set (or not found in .env file).")
        print("Please ensure it is set correctly, for example, in a .env file in the same directory as the script:")
        print("OPENAI_API_KEY='your_api_key_here'")
        print("Or set it as a system environment variable.")
    elif client is None: # Check if client initialization failed earlier
        print("OpenAI client could not be initialized. Please check previous error messages.")
    else:
        # Run configuration 1: fine-tuned model with system_prompt + example_prompt
        print("\n----- CONFIGURATION 1: Fine-tuned model with full prompt -----")
        output_csv_target = "output_fine_tuning.csv"
        openai_model_id = "ft:gpt-4.1-mini-2025-04-14:hyunjun1121:cs270-hyunjun-plus2set:BdvW9nay"
        system_prompt_content = system_prompt + "\n\n" + example_prompt
        
        print(f"Starting API output generation for '{user_csv}' into '{output_csv_target}' using model '{openai_model_id}'.")
        print(f"Using system_prompt + example_prompt.")
        print(f"Processing all instructions sequentially.")
        generate_outputs_from_api(user_csv, output_csv_target, openai_model_id, system_prompt_content)
        print("Processing for Configuration 1 complete.")
        
        # Run configuration 2: base model with only system_prompt
        print("\n----- CONFIGURATION 2: Base model with system_prompt only -----")
        output_csv_target = "output_mini.csv"
        openai_model_id = "gpt-4.1-mini-2025-04-14"
        system_prompt_content = system_prompt
        
        print(f"Starting API output generation for '{user_csv}' into '{output_csv_target}' using model '{openai_model_id}'.")
        print(f"Using system_prompt only (without example_prompt).")
        print(f"Processing all instructions sequentially.")
        generate_outputs_from_api(user_csv, output_csv_target, openai_model_id, system_prompt_content)
        print("Processing for Configuration 2 complete.")
        
        print("\nAll processing complete.")