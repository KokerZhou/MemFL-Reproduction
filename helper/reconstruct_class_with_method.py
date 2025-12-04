import json
import os
import re

def reconstruct_class_with_method(project_name: str, bug_id: str, class_name: str, response: str):
    """
    Reconstructs a Java class using the selected methods from the response.

    :param project_name: Name of the project.
    :param bug_id: ID of the bug.
    :param class_name: Fully qualified Java class name.
    :param response: LLM output containing selected methods and their line numbers in the format "MethodName@LineNumber".
    :return: The reconstructed Java class as a string.
    """

    # Extract method names and line numbers from the response
    extracted_methods = []
    extracted_lines = []

    response_lines = response.strip().split("\n")

    for line in response_lines:
        match = re.match(r'(.+?)@(\d+)', line.strip())
        if match:
            method_name = match.group(1).strip()
            line_number = int(match.group(2))
            extracted_methods.append(method_name)
            extracted_lines.append(line_number)

    if len(extracted_methods)==0:
        print("No valid Methods found")
        return -1, -1, -1  # No valid methods found

    # Define JSON file path
    json_path = f"/home/##/ttr/mem/data/{project_name}/data/{project_name}_{bug_id}/snippet.json"

    if not os.path.exists(json_path):
        print("File does not exist")
        return -1, -1, -1  # File does not exist

    with open(json_path, "r", encoding="utf-8") as file:
        data = json.load(file)

    # Collect methods belonging to the specified class
    class_methods = [entry for entry in data if entry.get("class_name") == class_name]

    if not class_methods:
        print("No matching Class Found, reconstruct_class_with_method")
        return -1, -1, -1  # No matching class found

    # Sort methods by their beginning line number
    class_methods.sort(key=lambda x: x["begin_line"])
    
    cleaned_class_name = class_name.split('.')[-1]

    # Start reconstructing the Java class
    reconstructed_class = []
    reconstructed_class.append(f"public class {cleaned_class_name} {{\n")
    
    recap = []
    result = []

    selected_methods = []
    print("-----------")
    print(extracted_methods)
    print(extracted_lines)
    #print(len(method_line_map))
    #print()
    #print(class_methods)

    print("-----------")
    for method in class_methods:
        method_name = method["name"]

        # Extract the actual method name (removing package/class prefixes)
        dot_index = method_name.find(".")
        hash_index = method_name.find("#")

        if dot_index != -1 and hash_index != -1:
            method_name = method_name[dot_index + 1:hash_index]

        # Check if this method is in the selected list (exact name and line number match)
        #if method_name in extracted_methods and method["begin_line"] == extracted_lines:
        if (method_name, method["begin_line"]) in zip(extracted_methods, extracted_lines):
            selected_methods.append((method_name, method["begin_line"], method.get("comment", ""), method.get("snippet", "")))

    if not selected_methods:
        print( "no matching methods in json, reconstruct_class_with_method")
        return -1, -1, -1  # No matching methods found in JSON

    # Sort selected methods by their line numbers (to preserve original order)
    selected_methods.sort(key=lambda x: x[1])

    # Add selected methods to the class reconstruction
    #print(selected_methods)
    for i, (method_name, line_number, comment, snippet) in enumerate(selected_methods, start=1):

        reconstructed_class.append("\n\n   /*==============================================")
        reconstructed_class.append(f"    *Method {i}: <{method_name}> (line {line_number})")
        reconstructed_class.append("    *==============================================")

        if comment.strip():
            reconstructed_class.append("    " + comment.replace("\n", "\n "))

        reconstructed_class.append("    */")  # Closing comment block

        if snippet.strip():
            reconstructed_class.append("    " + snippet.replace("\n", "\n    "))

        reconstructed_class.append("")  # Blank line for readability

        recap.append(f"Class : <{cleaned_class_name}>,\tMethod : <{method_name}>,\tline : ({line_number})")
        temp = []
        temp.append(cleaned_class_name)
        temp.append(method_name)
        temp.append(line_number)
        result.append(temp)
    reconstructed_class.append("}\n\n")

    return "\n".join(reconstructed_class), "\n".join(recap), result


#reconstructed_class, recap,result = reconstruct_class_with_method("Math","1","org.apache.commons.math3.fraction.BigFraction", "```\nBigFraction@269\nBigFraction@354\n```") #"com.google.javascript.jscomp.RemoveUnusedVars",'\nprocess@152\napply@883\nmaybeCreateAssign@936')
#print(reconstructed_class)
#print(recap)
#print(result)
