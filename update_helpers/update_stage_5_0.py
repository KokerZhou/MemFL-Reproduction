from helper.request_llm import request_api
import shutil
import random
import json

model = "gpt-4o-mini"

def review_interaction(interaction_content, answer_content,verbose):
    prompt = {
    "role": "user",
    "content": f"""You are a debugging review assistant. Your task is to evaluate the debugging attempt and the bug report answer generated in the previous debugging step, and then produce a very short review 

Please follow these guidelines:

1.Check for Accuracy: Compare the debugging attempt with the bug report answer. Ensure that the provided explanation matches the actual bug described in the report. For example, if the report discusses bug B but the debugging attempt focuses on bug A, highlight this inconsistency.

2.Concise Evaluation:

    If the explanation is accurate and covers the key points, provide a brief confirmation (e.g., "Factually correct" or "Accurate interaction").
    If there are errors, missing details, or discrepancies, clearly point them out and suggest corrections.

3.Actionable Feedback: If the debugging attempt is incorrect, offer short and practical suggestions to improve the debugging process.

**## Interaction History:**

- ** debugging attempt:**
{interaction_content}

**## Actual Bug Report):**
{answer_content}

Please provide your short review focused on suggestions for improvement <only if needed>. in less than 2 sentences"""
}
    _, response = request_api([prompt],model,True)
    if verbose:
        print(prompt["content"])
        print(response)
    return response

def update_memory(review_list, memory_content, summary_content, basic_info,verbose):
    prompt = {
        "role": "user",
        "content": f"""
You are a debugging review assistant. Your task is to analyze the previous debugging reviews, 
the summary of the target project, and the basic bug information. Based on this analysis, update 
the existing debugging guidance or create a new one if necessary. Ensure that the update improves clarity while retaining
all existing relevant information, and be very concise.

Project Summary:
{summary_content}

Debugging Information:
{basic_info}
"""}

    if memory_content:
        prompt["content"]+=f"""
Previous Debugging Reviews:
{'\n'.join(review_list)}

Existing Debugging Guidance (to be updated):
<<{memory_content}>>


Only update the debugging guidance if necessary.
If no update is needed, output STRICTLY and ONLY 'no_updated_required' since your answer will be handled automatically
Now, proceed with generating the concise updated debugging guidance if an update is required, keep your guidance less than 2 sentences long

Do not mention any of the name of classes or methods
"""
    else:
        prompt["content"]+="""
No debugging guidance is present, create a new and concise debugging guidance, under 2 sentences

Do not mention any of the name of classes or methods"""

    if verbose:
        print(prompt["content"])
        print()
    _, response = request_api([prompt], model, True)
    if verbose:
        print(response)
    return response

def update_stage_5(project_name,logs, memory_input_path, memory_output_path, answer_path_list,verbose):
    
    project_path = f"/home/##/ttr/mem/data/{project_name}/"

    summary_file_path = f"{project_path}summary.txt"
    basic_info_path = f"{project_path}memory/basic_info/Stage_5_info_0.txt"

    interaction_list = []
    answer_list = []
    #print(memory_input_path)
    #print()
    #print(answer_path_list)
    try:
        with open(memory_input_path) as f:
            memory_content = f.read()
        with open(summary_file_path) as f:
            summary_content = f.read()
        with open(basic_info_path) as f:
            basic_info = f.read()
        for answer_path in answer_path_list:
            with open(answer_path) as f:
                answer_list.append(f.read())                                                                       
    except Exception as e:
        print(f"Error : {e}")
        return -1
    

    review_list = []


    if memory_content:
        selected_indices = random.sample(range(len(logs)), min(5, len(logs)))
        for i in selected_indices:
            log, answer = logs[i], answer_list[i]
            if len(log) <= 1:
                review_list.append(review_interaction(log[-1][-1], answer,verbose))

    
    #for r in review_list:
    #    print(r)
    #    print()
    #print()
    updated_memory = update_memory(review_list, memory_content, summary_content, basic_info,verbose)
    # print(updated_memory)
    if not "no_update" in updated_memory or "No_update" in updated_memory or "NO_UPDATE" in updated_memory:
        with open(memory_output_path, 'w', encoding='utf-8') as file:
            file.write(updated_memory)
            print("stage_5 updated")
        return 2
    else:
        shutil.copy(memory_input_path, memory_output_path)
        print("stage_5 not updated")
        return 1

