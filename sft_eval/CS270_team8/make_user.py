import csv
import os
import openai
import random
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Initialize the OpenAI client
try:
    client = openai.OpenAI()
except openai.OpenAIError as e:
    print(f"Error initializing OpenAI client: {e}")
    print("Please ensure your OPENAI_API_KEY is set in the .env file or as an environment variable.")
    client = None

def generate_similar_sentences(original_sentence, num_similar=19, model_id="gpt-4.1-mini-2025-04-14"):
    """
    Generates a specified number of sentences similar to the original sentence using OpenAI API.
    """
    if not client:
        return [f"ERROR: OpenAI client not initialized."] * num_similar

    similar_sentences = []
    # Updated prompt to English
    prompt_message = (
        f"Please generate exactly {num_similar} new sentences that are semantically similar to the original sentence below, "
        f"but use varied vocabulary, expressions, and sentence structures. "
        f"Respond with each new sentence on a separate line. Do not include any additional explanations, only the sentences.\n\n"
        f"Original sentence: \"{original_sentence}\""
    )

    print(f"Generating {num_similar} similar sentences for: \"{original_sentence[:50]}...\" using model {model_id}")
    try:
        completion = client.chat.completions.create(
            model=model_id,
            messages=[
                {"role": "system", "content": "You are a helpful assistant skilled in rephrasing sentences while keeping their core meaning."},
                {"role": "user", "content": prompt_message}
            ],
            temperature=0.7, # Allow some creativity for variations
            n=1
        )
        response_content = completion.choices[0].message.content
        if response_content:
            generated_lines = response_content.strip().split('\n')
            if len(generated_lines) >= num_similar:
                similar_sentences = [line.strip() for line in generated_lines[:num_similar] if line.strip()]
            else:
                similar_sentences = [line.strip() for line in generated_lines if line.strip()]
                print(f"Warning: Expected {num_similar} sentences, but got {len(similar_sentences)} for '{original_sentence}'. Using what was generated.")
            
            if len(similar_sentences) < num_similar:
                 print(f"  --> API generated {len(similar_sentences)} sentences. Required {num_similar}. Consider adjusting temperature or prompt if consistently low.")
            return similar_sentences
        else:
            return [f"ERROR: Empty response for {original_sentence}"] * num_similar
    except openai.APIError as e:
        print(f"OpenAI API Error for '{original_sentence}': {e}")
        return [f"ERROR_OPENAI_API: {e}"] * num_similar
    except Exception as e:
        print(f"An unexpected error occurred for '{original_sentence}': {e}")
        return [f"ERROR_UNEXPECTED_API_CALL: {e}"] * num_similar

def create_user_content_csv(original_inputs, output_csv_file="user_content.csv", num_variations_per_input=19):
    """
    Generates variations for each original input and saves them to a CSV file.
    Each original input will result in (1 original + num_variations_per_input) rows.
    """
    if not client:
        print("OpenAI client not initialized. Cannot proceed.")
        return

    all_instructions_for_csv = []

    for original_input_sentence in original_inputs: # Renamed for clarity
        all_instructions_for_csv.append(original_input_sentence) # Add the original sentence first
        print(f"\nProcessing original: \"{original_input_sentence}\"")
        
        # Get similar sentences
        similar_ones = generate_similar_sentences(original_input_sentence, 
                                                  num_similar=num_variations_per_input)
        
        count_successful_generations = 0
        for s_sentence in similar_ones:
            if not s_sentence.startswith("ERROR:"):
                all_instructions_for_csv.append(s_sentence)
                count_successful_generations += 1
            else:
                print(f"  Skipping error sentence: {s_sentence}")
        print(f"  Added original and {count_successful_generations} successfully generated similar sentences.")

    # Write to CSV
    try:
        with open(output_csv_file, 'w', newline='', encoding='utf-8') as f_csv:
            writer = csv.writer(f_csv)
            writer.writerow(["instruction"])  # Write header
            for instruction_to_write in all_instructions_for_csv:
                writer.writerow([instruction_to_write])
        print(f"\nSuccessfully wrote {len(all_instructions_for_csv)} instructions to {output_csv_file}")
    except Exception as e:
        print(f"Error writing to {output_csv_file}: {e}")

if __name__ == "__main__":
    original_user_inputs = [
        'You are in the danger zone.',
        'VIRUS, check the hallway to the right silently.',
        "Good, VIRUS. Let's move front.",
        'Ok, VIRUS. Chase him with continuous shooting.',
        'Ok, VIRUS. Cease fire. Cease fire. Cease fire. Just pursue him.',
        'Virus, road marker spotted. Execute T pattern room clear.'
    ]

    output_file_name = "user_content.csv"  # Renamed for clarity
    num_sentence_variations = 19 # Number of similar sentences to generate for each original

    # Check for API key and client initialization
    if not os.getenv("OPENAI_API_KEY"):
        print("Error: The OPENAI_API_KEY environment variable is not set (or not found in .env file).")
        print("Please ensure it is set correctly, for example, in a .env file in the same directory as the script:")
        print("OPENAI_API_KEY='your_api_key_here'")
        print("Or set it as a system environment variable.")
    elif client is None:
        print("OpenAI client could not be initialized. Please check previous error messages.")
    else:
        print(f"Starting generation of similar sentences for {len(original_user_inputs)} base inputs.")
        print(f"Each input will have 1 original + {num_sentence_variations} variations, aiming for {1 + num_sentence_variations} total per input.")
        print(f"Output will be saved to: {output_file_name}")
        
        create_user_content_csv(
            original_inputs=original_user_inputs,
            output_csv_file=output_file_name,
            num_variations_per_input=num_sentence_variations
        )
        print("Processing complete.")