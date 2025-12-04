import json
import os

from helper.get_answer import get_answer


def reconstruct_class_builder(project_name: str, bug_id: str, class_name: str,limit=7) -> str:
    json_path = f"/home/##/ttr/mem/data/{project_name}/data/{project_name}_{bug_id}/snippet.json"
    
    if not os.path.exists(json_path):
        return -1
    
    with open(json_path, "r", encoding="utf-8") as file:
        data = json.load(file)
    
    # Collect methods belonging to the specified class
    class_methods = [entry for entry in data if entry.get("class_name") == class_name]

    # Split the string by "."
    parts = class_name.split(".")
    
    # Remove the first two parts and join the rest
    class_name = ".".join(parts[2:]) + ".java"


    buggy_class, buggy_method,l = get_answer(project_name,bug_id)

    matching_methods = [buggy_method[i] for i in range(len(buggy_class)) if buggy_class[i] == class_name]

    #print(matching_methods)
    if not class_methods:
        return -1
    reconstructed_class = []
    reconstructed_class.append(f"public class {class_name.split('.')[-2]} {{\n")
    count = 0
    bug_count = 0

    target_classes = []
    for method in class_methods:
        


        input_string = method["name"]

        dot_index = input_string.find(".")
        hash_index = input_string.find("#")

        if dot_index != -1 and hash_index != -1:
            input_string = input_string[dot_index + 1:hash_index]
        
        if count>=limit:
            if bug_count<len(matching_methods):
                if method["is_bug"]:
                    pass
                else:
                    continue
            else:
                break
        count+=1
        if method["is_bug"]:
            bug_count+=1
        
        target_classes.append(method)
    target_classes.sort(key=lambda x: x["begin_line"])
    for method in target_classes:
        comment = method.get("comment", "").strip()
        snippet = method.get("snippet", "").strip()
        
        if comment:
            reconstructed_class.append("    " + comment.replace("\n", "\n    "))
        if snippet:
            reconstructed_class.append("    " + snippet.replace("\n", "\n    "))
        
        reconstructed_class.append("")  # Add a blank line for readability
    
    reconstructed_class.append("}\n\n")
    return "\n".join(reconstructed_class)

