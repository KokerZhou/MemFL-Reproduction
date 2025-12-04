from concurrent.futures import ThreadPoolExecutor, as_completed
import os
import json

from helper.helpers import create_log_directory
from prompts.fl_mem_v3 import refine

from helper.get_bug_info import get_bug_info

p,b,_,_,_= get_bug_info()

def process_fault_localization(project_name, bug_id, repeat_index, mem_path, log_dir,verbose):
    """
    A helper function that runs FL and writes the log to file.
    This will be executed in a separate thread.
    """
    return_value, model_used, log_data, result = refine(project_name, bug_id, mem_path, verbose=verbose)
 
    file_name = os.path.join(log_dir, f"log_{repeat_index}.json")

    with open(file_name, "w") as file:
        json.dump(log_data, file, indent=4)
    return return_value

def fault_localization_main(target_project, new_b, repeat, num_bugs, mem_path, log_dir, verbose, max_workers = 5):
    log_dir = create_log_directory(log_dir)

    if log_dir is None:
        return -1

    if repeat * num_bugs > max_workers:
        raise ValueError(f"Total tasks ({repeat * num_bugs}) exceed max_workers ({max_workers}). Adjust num_bugs or repeat.")

    i = 0
    while i < len(new_b):
        batch_bugs = new_b[i:i+num_bugs]
        if not batch_bugs:
            break

        futures = []
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            for k in range(len(batch_bugs)):  # Loop through selected bugs
                bug_id = batch_bugs[k]

                sub_log_path = os.path.join(log_dir, f"{target_project}_{bug_id}")
                os.makedirs(sub_log_path, exist_ok=True)

                for _ in range(repeat):  # Run each bug `repeat` times
                    future = executor.submit(
                        process_fault_localization, target_project, bug_id, _, mem_path, sub_log_path,verbose
                    )
                    futures.append(future)

            for future in as_completed(futures):
                result = future.result()
                # You can process result here if needed

        i += num_bugs  # Move to the next batch
    return log_dir
