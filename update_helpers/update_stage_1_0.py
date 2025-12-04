from helper.request_llm import request_api
import shutil
import random

import json

model = "gpt-4o-mini"

def review_interaction(interaction_content, answer_content):
    prompt = {
    "role": "user",
    "content": f"""You are a debugging review assistant. Your task is to evaluate the interaction history and the bug report answer generated in the previous debugging step, and then produce a concise review focusing on factual correctness.

Please follow these guidelines:
1. **Review Scope:** Focus only on the initial part of the bug report answer—the section that explains the test case failure and identifies potential reasons for the bug. Ignore any detailed method-level analysis or root cause in the source code.
2. **Assessment of Factual Accuracy:** Compare the information provided in the interaction history (both the query and the LLM's initial answer) with the bug report answer. Verify whether the interaction factually aligns with the explanation in the bug report answer. For example, if the bug report answer discusses bug B but the interaction details bug A, clearly note this discrepancy.
3. **Concise Review:**
   - If the interaction is factually correct and accurately covers the key points from the bug report answer, provide a very concise review (e.g., "Interaction was factually correct" or "Interaction was fine").
   - If there are discrepancies, missing details, or incorrect information, clearly identify them and explain what is wrong, along with suggestions for improvement.
4. **Actionable Feedback:** Provide actionable suggestions that could improve the debugging process if needed.

**## Interaction History:**

- **Query (Initial Request):**
{interaction_content[0]["content"]}

- **LLM's Initial Answer:**
{interaction_content[1]}

**## Bug Report Answer (Test Failure Explanation Focus):**
{answer_content}

Please provide your short review focused on suggestions for improvement <only if needed>."""
}
    _, response = request_api([prompt],model,True)
    return response

def update_memory(review_list, memory_content, summary_content, basic_info,verbose):
    prompt = {
        "role": "user",
        "content": f"""
You are a debugging review assistant. Your task is to analyze the previous debugging reviews, 
the summary of the target project, and the basic bug information. Based on this analysis, update 
the existing debugging guidance if necessary. Ensure that the update improves clarity while retaining
all existing relevant information.

Project Summary:
{summary_content}

Debugging Information:
{basic_info}
"""}

    if memory_content:
        prompt["content"]+=f"""
Previous Debugging Reviews:
{'\n'.join(review_list)}

Existing Debugging Guidance that you should update ( if needed ):
<<{memory_content}>>


Only update the debugging guidance if necessary.
If no update is needed, output STRICTLY and ONLY 'no_updated_required' since your answer will be handled automatically
Now, proceed with generating the updated debugging guidance if an update is required."""
    else:
        prompt["content"]+="""
No debugging guidance is present, create a new debugging guidance"""

    if verbose:
        print(prompt["content"])
        print()
    _, response = request_api([prompt], model, True)
    if verbose:
        print(response)
    return response

def update_stage_1(project_name,logs, memory_input_path, memory_output_path, answer_path_list,verbose):
    
    project_path = f"/home/##/ttr/mem/data/{project_name}/"

    summary_file_path = f"{project_path}summary.txt"
    basic_info_path = f"{project_path}memory/basic_info/Stage_1_info_0.txt"

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
                                                                
                review_list.append(review_interaction(log[0][0], answer))
                                                                        
            else:
                                                                                        
                review_list.append(review_interaction(log[0], answer))

    #for r in review_list:
    #    print(r)
    #    print()
    #print()
    updated_memory = update_memory(review_list, memory_content, summary_content, basic_info,verbose)
    # print(updated_memory)
    if not "no_update" in updated_memory or "No_update" in updated_memory or "NO_UPDATE" in updated_memory:
        with open(memory_output_path, 'w', encoding='utf-8') as file:
            file.write(updated_memory)
            print("stage_1 updated")
        return 2
    else:
        shutil.copy(memory_input_path, memory_output_path)
        print("stage_1 not updated")
        return 1

