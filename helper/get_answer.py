from helper.get_bug_info import get_bug_info

import os
import json


def get_answer(p,b):
    json_path = f"/home/##/ttr/mem/data/{p}/data/{p}_{b}/snippet.json"
    with open(json_path, 'r', encoding='utf-8') as file:
        data = json.load(file)

    buggy_class = []
    buggy_method = []
    buggy_line = []

    for entry in data:
        if "class_name" in entry:

            parts = entry["class_name"].split('.')
            class_name = ".".join(parts[min(2, len(parts)):]) + ".java"

            if entry["is_bug"]:
                buggy_class.append(class_name)

                input_string = entry["name"]
                
                dot_index = input_string.find(".")
                hash_index = input_string.find("#")

                if dot_index != -1 and hash_index != -1:
                    input_string = input_string[dot_index + 1:hash_index]

                buggy_method.append(input_string)
                buggy_line.append(entry["begin_line"])

       
    
    if len(buggy_class) == 0:
        bug_file_path = f"/home/##/ttr/mem/data/{p}/modified_classes/{b}.src"
        try:
            with open(bug_file_path, "r") as file:
                for line in file:
                    line = line.strip()
                    parts = line.split(".")
                    line = ".".join(parts[min(2,len(parts)):])
                    line += ".java"  # Add ".java" at the end
                    buggy_class.append(line)
                    buggy_method.append("@@")
                    buggy_line.append("@@")

        except FileNotFoundError:
            print(f"Error: File not found at {bug_file_path}")
        except Exception as e:
            print(f"Unexpected error: {e}")

    return buggy_class, buggy_method,buggy_line

#re = get_answer("Chart","1")
#print(re)
