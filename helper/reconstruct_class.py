import json
import os

def reconstruct_class(project_name: str, bug_id: str, class_name: str) -> str:
    json_path = f"/home/##/ttr/mem/data/{project_name}/data/{project_name}_{bug_id}/snippet.json"
    
    if not os.path.exists(json_path):
        print("not a right json path..., helper.reconstruct_class")
        return -1
    
    with open(json_path, "r", encoding="utf-8") as file:
        data = json.load(file)
    
    # Collect methods belonging to the specified class
    class_methods = [entry for entry in data if entry.get("class_name") == class_name]
    
    if not class_methods:
        return -1
    
    # Sort methods by their beginning line
    class_methods.sort(key=lambda x: x["begin_line"])
    
    # Start class reconstruction
    reconstructed_class = []
    #reconstructed_class.append(f"package {package_name};\n")
    reconstructed_class.append(f"public class {class_name.split('.')[-1]} {{\n")
    i = 1
    all_methods = []
    all_lines = []
    for method in class_methods:
        begin_line = method["begin_line"]
        input_string = method["name"]

        dot_index = input_string.find(".")
        hash_index = input_string.find("#")

        if dot_index != -1 and hash_index != -1:
            input_string = input_string[dot_index + 1:hash_index]
        all_methods.append(input_string)
        all_lines.append(begin_line)
        reconstructed_class.append("\n\n   /*==============================================")
        reconstructed_class.append(f"    *Method {i} : <{input_string}> ,    (line {begin_line})")
        reconstructed_class.append("    *==============================================\n")
        i+=1
        comment = method.get("comment", "").strip()
        snippet = method.get("snippet", "").strip()
        
        if comment:
            reconstructed_class.append("    " + comment.replace("\n", "\n "))
        reconstructed_class.append("    */")
        if snippet:
            reconstructed_class.append("    " + snippet.replace("\n", "\n    "))
        
        reconstructed_class.append("")  # Add a blank line for readability
    
    reconstructed_class.append("}\n\n")
    i = 1
    reconstructed_class.append("<Existing Methods>")
    for m in all_methods:
        reconstructed_class.append(f"##Method {i} : <{m}>,   (line {all_lines[i-1]})")
        i+=1
    return "\n".join(reconstructed_class)

