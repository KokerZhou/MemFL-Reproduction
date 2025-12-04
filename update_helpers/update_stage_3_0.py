from helper.request_llm import request_api
from helper.collect_covered_classes import collect_covered_classes
import shutil
import json
import re

model = "gpt-4o-mini"
def summarize_debugging_results(results):
    """
    Generate a natural language summary of debugging results.
    """
    total_bugs = len(results)
    not_found = sum(1 for r in results if r == [-1])
    found = total_bugs - not_found
    
    total_predictions = sum(r[0] for r in results if r != [-1])
    avg_predictions = total_predictions / found if found > 0 else 0
    
    rank_positions = [r[1] for r in results if r != [-1]]
    
    if found > 0:
        avg_rank = sum(rank_positions) / found
        best_rank = min(rank_positions)
        worst_rank = max(rank_positions)
    else:
        avg_rank, best_rank, worst_rank = None, None, None
    
    summary = [
        f"Total number of bugs analyzed: {total_bugs}.",
        f"Bugs successfully located: {found} ({found / total_bugs * 100:.2f}%).",
        f"Bugs not found: {not_found} ({not_found / total_bugs * 100:.2f}%).",
        f"Average number of predictions made: {avg_predictions:.2f}."
    ]
    
    if found > 0:
        summary.extend([
            f"Average rank of identified bugs: {avg_rank:.2f}.",
            f"Best rank achieved: {best_rank}.",
            f"Worst rank recorded: {worst_rank}."
        ])
    
    return " \n".join(summary)


def update_memory(results, memory_content, summary_content, basic_info,verbose):

    if memory_content:
        
        summary_result = summarize_debugging_results(results)
        prompt = {"role": "user",
        "content": f"""
You are a debugging assistant. After revewing tha previous debugging results, create or update the existing debugging guidance for the recommendation of right number of classes to be analyzed.
The previous debugging results conists of how successful previous debugging attemts were. You have to recommend the optimal number of classes to be analyzed by that debugging module.
If previous debugging attempts were not successful, consider increasing the amount of recommendation and vise versa.
To ensure efficiency, keep the recommended number of classes within the range of 2 to 5.
adjust the recommendation gradually by increasing or decreasing the number by only 1 class at a time to maintain consistency and prevent abrupt shifts.

This is the Examples describing the recommended update strategy depending on previous debugging results.

{basic_info}




 Here is the Previous Debugging Results, that you should read and analyze if update on the memory is necessary
-----------------------
{summary_result}
-----------------------


After analyzing the example given above, reading the above previous debugging result and analyzing on the % of bugs successfully located in that previous debugging results, update the existing debugging guidance below.

 <<{memory_content}>>

Maintain the number of recommended classes within an appropriate range (e.g., minimum of 2 and maximum of 5).
Adjust the number of recommended classes gradually, increasing or decreasing by only 1 at a time, to avoid sudden changes

Use simple sentence, as short as you can, only including the guideline related to the number of recommendation, not the previous history. Only update the debugging guidance if necessary.
If the existing debugging guidance is close enough to new guidance, do not update the memory.
If no update is needed, output STRICTLY and ONLY 'no_updated_required' since your answer will be handled automatically.
Now, proceed with generating the updated single-line debugging guidance about the number of classes to recommend as simple as possible if an update is required."""
         
    }
        _, response = request_api([prompt], model, True)
        if verbose:
            print(prompt["content"])
            print(response)
        return response
    else:
        return "Recommend around 3 classes"


def update_stage_3(project_name,logs, memory_input_path, memory_output_path, answer_path_list,verbose):

    project_path = f"/home/##/ttr/mem/data/{project_name}/"

    summary_file_path = f"{project_path}summary.txt"
    basic_info_path = f"{project_path}memory/basic_info/Stage_3_info_0.txt"

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
        if len(log)<=1:
            review_list.append([-1])
        else:
            cleaned_s = re.sub(r"[^a-zA-Z\n]", "", log[2][1][0])
            review_list.append([len(cleaned_s.strip().split("\n")),log[2][1][1]])

    #for r in review_list:
    #     print(r)
    #     print()
    #print()
    
    updated_memory = update_memory(review_list, memory_content, summary_content, basic_info, verbose)
    if "no_update" in updated_memory or "No_update" in updated_memory or "NO_UPDATE" in updated_memory:
        shutil.copy(memory_input_path, memory_output_path)
        print("stage 3 not updated")
        return 1
    else:
        with open(memory_output_path, 'w', encoding='utf-8') as file:
            file.write(updated_memory)
        print("stage 3 updated")
        return 2

