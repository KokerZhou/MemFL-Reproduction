from helper.request_llm import request_api
from helper.collect_covered_classes import collect_covered_classes

import shutil
import json
import re

model = "gpt-4o-mini"
def summarize_debugging_results(results):
    total_attempts = len(results)
    total_predictions = sum(sum(attempt) for attempt in results)
    total_classes = sum(len(attempt) for attempt in results)
    avg_classes_per_attempt = total_classes / total_attempts if total_attempts > 0 else 0
    avg_methods_per_attempt = total_predictions / total_attempts if total_attempts > 0 else 0
    avg_methods_per_class = total_predictions / total_classes if total_classes > 0 else 0
    
    summary = (
        f"A total of {total_attempts} debugging attempts were made. \n"
        f"On average, each attempt predicted {avg_classes_per_attempt:.1f} classes, \n"
        f"with a total of {avg_methods_per_attempt:.1f} methods per attempt. \n"
        f"Each class contained an average of {avg_methods_per_class:.1f} methods. \n"
        f"Overall, {total_predictions} method predictions were made.\n"
    )
    
    return summary

def update_memory(results, memory_content, summary_content, basic_info,verbose):
    if memory_content:
        summary_result = summarize_debugging_results(results)
        prompt = {
                "role": "user",
                "content": f"""
You are a debugging assistant. After revewing tha previous debugging results, create or update the existing debugging guidance for the recommendation of right number of methods to be analyzed.
The previous debugging results conists of how successful previous debugging attemts were. You have to recommend the optimal number of methods to be analyzed by that debugging module.
if previous debugging attempts were not successful, consider increasing the amount of recommendation and vise versa.
To ensure efficiency, keep the recommended number of methods within the range of 2 to 5
adjust the recommendation gradually by increasing or decreasing the number by only 1 to 2 methods at a time to maintain consistency and prevent abrupt shifts.

This is the Examples describing the recommended update strategy depending on previous debugging results.

{basic_info}


Here is the Previous Debugging Results, that you should read and analyze if update on the memory is necessary

-----------------------
{summary_result}
-----------------------


After analyzing the example given above, reading the above previous debugging result and analyzing on the % of bugs successfully located in that previous debugging results, update the existing debugging guidance below.

<<{memory_content}>>


Maintain the number of recommended methods within an appropriate range (e.g., minimum of 2 and maximum of 5).
Adjust the number of recommended methods gradually, increasing or decreasing by only 1 or 2 at a time, to avoid sudden changes

Use simple sentence, as short as you can, only including the guideline related to the number of recommendation, not the previous history. Only update the debugging guidance if necessary.
If the existing debugging guidance is close enough to new guidance, do not update the memory.
if no update is needed, output STRICTLY and ONLY 'no_updated_required' since your answer will be handled automatically.
Now, proceed with generating the updated single-line debugging guidance about the number of classes to recommend as simple as possible if an update is required."""
         }
        _, response = request_api([prompt], model, True)
        if verbose:
            print(prompt["content"])
            print(response)
        return response
    else:
        return "Recommend around 3 methods per class"



def update_stage_4(project_name,logs, memory_input_path, memory_output_path, answer_path_list,verbose):

    project_path = f"/home/##/ttr/mem/data/{project_name}/"

    summary_file_path = f"{project_path}summary.txt"
    basic_info_path = f"{project_path}memory/basic_info/Stage_4_info_0.txt"

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


    for log, answer in zip(logs, answer_list):
        if not len(log)<=1:
            temp = []
            for n in range(3, len(log) - 1):  # Iterate over all n > 2 except the last one
                import re

                if isinstance(log, list) and 0 <= n < len(log) and isinstance(log[n], (list, tuple)) and len(log[n]) > 2:
                    value = log[n][2] if isinstance(log[n][2], str) else str(log[n][2])  # Ensure it's a string
                    cleaned_s = re.sub(r"[^a-zA-Z\n]", "", value)
                else:
                    cleaned_s = ""  # Fallback for out-of-bounds or invalid data

                temp.append(len(cleaned_s.strip().split("\n")))
            review_list.append(temp)
    
    updated_memory = update_memory(review_list, memory_content, summary_content, basic_info,verbose)
    if "no_update" in updated_memory or "No_update" in updated_memory or "NO_UPDATE" in updated_memory:
        shutil.copy(memory_input_path, memory_output_path)
        print("stage 4 not updated")
        return 1
    else:
        with open(memory_output_path, 'w', encoding='utf-8') as file:
            file.write(updated_memory)
        print("Stage 4 updated")
        return 2

