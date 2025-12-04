import os
import json

from helper.get_bug_info import get_bug_info
from helper.helpers import create_log_directory,select_random_numbers

from update_helpers.update_stage_1_0 import update_stage_1
from update_helpers.update_stage_2_0 import update_stage_2
from update_helpers.update_stage_3_0 import update_stage_3
from update_helpers.update_stage_4_0 import update_stage_4
from update_helpers.update_stage_5_0 import update_stage_5

p,b,_,_,_ = get_bug_info()
base_dir = "/home/##/ttr/"

def update_memory(p, b_list,log_dir,mem_input_path, mem_output_path,verbose=False):
    
    logs = []
    answer_path_list = []
    
    stage_1_input = f"{mem_input_path}memory_1.txt"
    stage_1_output = f"{mem_output_path}memory_1.txt"

    stage_2_input = f"{mem_input_path}memory_2.txt"
    stage_2_output = f"{mem_output_path}memory_2.txt"

    stage_3_input = f"{mem_input_path}memory_3.txt"
    stage_3_output = f"{mem_output_path}memory_3.txt"

    stage_4_input = f"{mem_input_path}memory_4.txt"
    stage_4_output = f"{mem_output_path}memory_4.txt"

    stage_5_input = f"{mem_input_path}memory_5.txt"
    stage_5_output = f"{mem_output_path}memory_5.txt"
    #print(stage_1_output)
    count = 0
    
    for b in  b_list:
        

        log_file = f"{log_dir}{p}_{b}/log_0.json"
        
        with open(log_file, "r") as file:
            log = json.load(file)

        if not isinstance(log[0], str):
            logs.append(log)
            answer_path_list.append(f"{base_dir}mem/data/{p}/data/{p}_{b}/answer.txt")
        else:
            print("skipped...")
        count+=1
    print("----------------------\n\n")
    update_stage_1(p, logs, stage_1_input, stage_1_output, answer_path_list,verbose)
    print("----------------------\n\n")
    update_stage_2(p, logs, stage_2_input, stage_2_output, answer_path_list,verbose)
    print("----------------------\n\n")
    update_stage_3(p, logs, stage_3_input, stage_3_output, answer_path_list,verbose)
    print("----------------------\n\n")
    update_stage_4(p, logs, stage_4_input, stage_4_output, answer_path_list,verbose)
    print("----------------------\n\n")
    update_stage_5(p, logs, stage_5_input, stage_5_output, answer_path_list,verbose)
    print("----------------------\n\n")
#rand_list = select_random_numbers(1,134,20)



