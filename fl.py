import os
import json
import random
from concurrent.futures import ThreadPoolExecutor, as_completed
import argparse

# Assume these functions/modules are available from your codebase:
from helper.get_bug_info import get_bug_info
from update_memory import update_memory
from prompts.fl_mem_v3 import refine
from prompts.fl_mem_v5 import refine_3
from prompts.fl_mem_v6 import refine_4
from helper.helpers import create_log_directory

from fault_localization_main import fault_localization_main

base_dir = "/home/##/ttr/"

def create_folds_json(target_project,  output_file):
    """
    Creates a 5-fold split for the bugs in target_project.
    Each fold consists of:
      - test: a unique subset of bugs (each bug appears in test exactly once)
      - train: a random sample (of given batch_size) from the remaining bugs
      - memory_path: (to be filled later after update_memory)
    The fold information is written to a JSON file.
    """
    # Retrieve bug information
    p, b, _, _, _ = get_bug_info()
    # Filter for the target project bugs
    project_bugs = [b[i] for i in range(len(p)) if p[i] == target_project]
    
    # Shuffle the bug list randomly
    random.shuffle(project_bugs)
    n = len(project_bugs)
    
    # Compute sizes for 5 folds (distributing remainder evenly)
    fold_size = n // 5
    remainder = n % 5
    folds = []
    start = 0
    
    for fold in range(5):
        extra = 1 if fold < remainder else 0
        end = start + fold_size + extra
        test_set = project_bugs[start:end]
        # Training set is selected randomly from bugs not in test_set
        remaining = [bug for bug in project_bugs if bug not in test_set]
        folds.append({
            "fold": fold + 1,
            "test": test_set,
            #"train": training_set,
            "memory_path": []  # To be updated after memory update
        })
        start = end
    
    fold_json = {
        "project": target_project,
        "folds": folds
    }
    
    with open(output_file, "w") as f:
        json.dump(fold_json, f, indent=4)
    print(f"Folds created and saved to {output_file}")

def update_memory_for_folds(target_project, folds_file, mem_input_dir, iteration, log_dir,batch_size, verbose=False):
    # Load the fold configuration
    p,b,_,_,_ = get_bug_info()
    with open(folds_file, "r") as f:
        data = json.load(f)
    
    folds = data["folds"]
    
    project_bugs = [b[i] for i in range(len(p)) if p[i] == target_project]

    memory_base_path = f"{base_dir}mem/data/{target_project}/memory/{mem_input_dir}/"
    new_mem_paths = []
    for fold in folds:
        # new memory path to be saved in json file
        new_memory_path = []
        fold_num = fold["fold"]
        fold_mem_path = f"{memory_base_path}fold_{fold_num}/"
        os.makedirs(fold_mem_path, exist_ok = True)
        
        ### Initiating with empty files
        path = os.path.join(fold_mem_path, "stage_0")
        os.makedirs(path, exist_ok=True)  # Ensure the folder exists
        
        new_memory_path.append(path)

        mem_files = [os.path.join(path, f"memory_{i}.txt") for i in range(1, 6)]
        for file in mem_files:
            open(file, "w").close()
        
        ## Update memory begins
        for i in range(iteration):
            mem_path = f"{fold_mem_path}stage_{i}/"
            os.makedirs(mem_path, exist_ok = True)
            mem_output_path = f"{fold_mem_path}stage_{i+1}/"
            os.makedirs(mem_output_path, exist_ok=True)
    
            test_batch = fold["test"]
            remaining = [bug for bug in project_bugs if bug not in test_batch]
            
            batch = random.sample(remaining,batch_size)

            print("Traning start..")
            last_log_dir = fault_localization_main(target_project, batch, 1, 1, mem_path, log_dir, False)#1,2 -> 1,5
            last_log_dir+="/"
            update_memory(target_project, batch, last_log_dir, mem_path, mem_output_path, False)
            new_memory_path.append(mem_output_path)
        new_mem_paths.append(new_memory_path)
    
    if len(new_mem_paths)!=len(folds):
        print("Length of new_mem_paths does not match")
        return -1

    for i, fold in enumerate(folds):
        fold["memory_path"] = new_mem_paths[i]  # Assign the list

     # Save the updated JSON file
    with open(folds_file, "w") as f:
        json.dump(data, f, indent=4) 

def process_single_fl(project_name, bug_id, repeat_index, mem_path, log_dir, verbose):
    return_value, model_used, log_data, result = refine(project_name, bug_id, mem_path, verbose=verbose)
 
    # Write the result to a JSON log file
    file_name = os.path.join(log_dir, f"log_{repeat_index}.json")

    with open(file_name, "w") as file:
        json.dump(log_data, file, indent=4)
    #print(file_name)
    return return_value


def fault_localization_for_folds(target_project, folds_file, log_dir, iteration_num, num_bugs=1,repeat=1, verbose=False):
    """
    For each fold defined in folds_file:
      - Retrieve the test set and the memory_path (from update_memory)
      - Create a dedicated log directory and run fault localization on the test set using fault_localization_main.
      - Runs each fold concurrently.
    """
    max_workers = 1

    log_dir = create_log_directory(log_dir)
    if log_dir is None:
        return -1

    # Load the fold configuration
    with open(folds_file, "r") as f:
        data = json.load(f)
    
    folds = data["folds"]
    
    for fold in folds:
        batch = fold["test"]
        memory_paths = fold["memory_path"]

        memory_path = memory_paths[iteration_num]
        
        fold_num = fold["fold"]
        print(f"batch {fold_num} begins..")
        i = 0
        while i < len(batch):

                batch_bugs = batch[i:i+num_bugs]
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
                                process_single_fl, target_project, bug_id, _, memory_path, sub_log_path,verbose
                            )
                            futures.append(future)

                    for future in as_completed(futures):
                        result = future.result()
                        # You can process result here if needed

                i += num_bugs  # Move to the next batch

def process_single_fl_2(project_name, bug_id, repeat_index, mem_path, log_dir, verbose, no_step_1):
    if no_step_1:
        return_value, model_used, log_data, result = refine_3(project_name, bug_id, mem_path, verbose=verbose)
    else:
        return_value, model_used, log_data, result = refine_4(project_name, bug_id, mem_path, verbose=verbose)

    #refine_3 = without test summary
    #refine_4 = without code condensation

    # Write the result to a JSON log file
    file_name = os.path.join(log_dir, f"log_{repeat_index}.json")

    with open(file_name, "w") as file:
        json.dump(log_data, file, indent=4)
    #print(file_name)
    return return_value


def fault_localization_for_folds_2(target_project, folds_file, log_dir, iteration_num, no_step_1,num_bugs=1,repeat=1, verbose=False):
    """
    For each fold defined in folds_file:
      - Retrieve the test set and the memory_path (from update_memory)
      - Create a dedicated log directory and run fault localization on the test set using fault_localization_main.
      - Runs each fold concurrently.
    """
    max_workers = 6

    log_dir = create_log_directory(log_dir)
    if log_dir is None:
        return -1

    # Load the fold configuration
    with open(folds_file, "r") as f:
        data = json.load(f)
    
    folds = data["folds"]
    
    for fold in folds:
        batch = fold["test"]
        memory_paths = fold["memory_path"]

        memory_path = memory_paths[iteration_num]
        
        fold_num = fold["fold"]
        print(f"batch {fold_num} begins..")
        i = 0
        while i < len(batch):

                batch_bugs = batch[i:i+num_bugs]
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
                                process_single_fl_2, target_project, bug_id, _, memory_path, sub_log_path,verbose, no_step_1
                            )
                            futures.append(future)

                    for future in as_completed(futures):
                        result = future.result()
                        # You can process result here if needed

                i += num_bugs  # Move to the next batch

def five_fold_validation_pipeline(target_project, batch_size, mem_input_dir, mem_log_dir, test_log_dir, iteration,iteration_num,mode,fold_file_name,  verbose=False):
    """
    5-fold validation
      1. Creates the fold splits and saves them as JSON.
      2. For each fold, updates memory using the training set.
      3. For each fold, runs fault localization on the test set.

    Variable for FL
        Repeat : how many times each bugs be tested
        Num_bugs : how many times each bugs be tested simultaneously, using multithread
    """
    if ',' in target_project:
        target_projects = [t_p.strip() for t_p in target_project.split(',')]
    elif target_project == "ALL":
        target_projects = ["Chart","Closure","Lang","Math","Time"]
    else:
        target_projects = [target_project]

    # Step 1: Create the fold splits
    if mode==1:
        for tp in target_projects:
            folds_file = f"{tp}_{fold_file_name}.json"
            create_folds_json(tp,folds_file)
    
    # Step 2: Update memory using training data for each fold
    elif mode==2:
        for tp in target_projects:
            folds_file = f"{tp}_{fold_file_name}.json"
            update_memory_for_folds(tp, folds_file, mem_input_dir, iteration,mem_log_dir,batch_size, verbose)
    
    # Step 3: Run fault localization on test data for each fold
    elif mode==3:
        for tp in target_projects:
            folds_file = f"{tp}_{fold_file_name}.json"
            fault_localization_for_folds(tp, folds_file, test_log_dir,  iteration_num)
    
    # ablation study
    else:
        if mode==4:
            no_step_1 = True
        else:
            no_step_1 = False
        for tp in target_projects:
            folds_file = f"{tp}_{fold_file_name}.json"
            fault_localization_for_folds_2(tp, folds_file, test_log_dir,  iteration_num,no_step_1)

def main():
    parser = argparse.ArgumentParser(description="Five-fold validation pipeline for fault localization.")
    parser.add_argument("--mode", type=int, required=True,
                        help="Mode selection: 1 (generate new fold), 2 (debugging guidance extraction), 3 (FL), 4 (ablation study), 5 (ablation study)")
    parser.add_argument("--fold_file_name", type=str, required=True, help="Fold file name")
    parser.add_argument("--target_project", type=str, required=True,
                        help="Target project: Chart, Closure, Lang, Math, Time, or ALL")
    parser.add_argument("--mem_input_dir", type=str, required=True, help="Directory for initial memory files")
    parser.add_argument("--mem_log_dir", type=str, required=True, help="Base directory for fault localization logs for training")
    parser.add_argument("--iteration", type=int, required=True, help="Number of training iterations")
    parser.add_argument("--batch_size", type=int, required=True, help="Number of training bugs to sample for each fold")
    parser.add_argument("--test_log_dir", type=str, required=True, help="Directory for test logs")
    parser.add_argument("--target_iteration_num", type=int, required=True,
                        help="Target memory iteration number for FL testing")

    args = parser.parse_args()

    five_fold_validation_pipeline(args.target_project, args.batch_size, args.mem_input_dir,
                                  args.mem_log_dir, args.test_log_dir, args.iteration,
                                  args.target_iteration_num, args.mode, args.fold_file_name)

if __name__ == "__main__":
    main()
