import json
import os
from helper.construct_path import construct_path
import javalang
from helper.get_bug_info import get_bug_info
from helper.get_answer import get_answer

def count_methods_in_class(java_file_path, class_name):
    """
    Counts the number of methods and constructors in a specified class (including nested classes if desired).
    """
    try:
        with open(java_file_path, 'r', encoding='utf-8', errors = 'ignore') as file:
            java_code = file.read()

        tree = javalang.parse.parse(java_code)

        method_count = 0
        # Walk the entire tree
        for path, node in tree:
            # Check for method or constructor declarations
            if isinstance(node, (javalang.tree.MethodDeclaration, javalang.tree.ConstructorDeclaration)):
                # Check all ancestors to see if we're inside the target class
                for ancestor in reversed(path):
                    if isinstance(ancestor, javalang.tree.ClassDeclaration) and ancestor.name == class_name:
                        method_count += 1
                        break

        return method_count if method_count > 0 else -1
    except Exception as e:
        print(f"Error in count_methods_in_class: {e}")
        return -1




def convert_dots_to_slashes(s):
    parts = s.rsplit('.', 1)  # Split into two parts from the right (only once)
    return parts[0].replace('.', '/') + ('.' + parts[1] if len(parts) > 1 else '')


def count_covered_method(p,b,c):
    base_path = construct_path("/home/##/ttr/",p,b)
    if p == "Closure":
        base_path += "/com/google/"
    elif p=="Chart":
        base_path += "/org/jfree/"
    elif p=="Lang" or p=="Math":
        base_path += "/org/apache/"
    elif p=="Time":
        base_path+="/org/joda/"
    file_path = base_path + convert_dots_to_slashes(c)
    
    if not os.path.exists(file_path):
        print("file doex not exist, count_covered_method, collect_covered_classes")
        return -1

    parts = c.split(".")

    if len(parts) > 1:
        second_last = parts[-2]
    else:
        print("wrong c, count_covered_method, collect_covered_classes")
        return -1

    result = count_methods_in_class(file_path,second_last)
    
    return result

def collect_covered_classes(project_name: str, bug_id: str, num=60) -> list:
    json_path = f"/home/##/ttr/mem/data/{project_name}/data/{project_name}_{bug_id}/snippet.json"

    # Check if the file exists
    if not os.path.exists(json_path):
        raise FileNotFoundError(f"JSON file not found: {json_path}")

    # Read the JSON file
    with open(json_path, 'r', encoding='utf-8') as file:
        data = json.load(file)

    # Collect unique class names while preserving order
    class_counts = {}
    num_test = 0
    buggy_class,buggy_method,_ = get_answer(project_name,bug_id)
    for entry in data:
        if "class_name" in entry:
            if entry["num_failing_tests"] > num_test:
                num_test = entry["num_failing_tests"]
            
            parts = entry["class_name"].split('.')
            class_name = ".".join(parts[min(2, len(parts)):]) + ".java"
            

            if class_name in class_counts:
                class_counts[class_name] += entry["num_failing_tests"]
            else:
                class_counts[class_name] = entry["num_failing_tests"]

    unique_classes = []
    covered_class_counts = {class_name: 0 for class_name in class_counts}

    for class_name in covered_class_counts:
        result = count_covered_method(project_name,bug_id,class_name)
        covered_class_counts[class_name] = result * num_test  # Update the dictionary
    
    sorted_classes = sorted(
        class_counts.keys(), 
        key=lambda x: class_counts[x] / covered_class_counts[x] if covered_class_counts.get(x, 0) != 0 else 0,
        reverse=True
    )

    result = [cls for cls in sorted_classes]

    lowest = 1000
    for b in buggy_class:
        try:
            index = result.index(b)
        except ValueError:
            index = 1000
        if index<lowest:
            lowest = index
    #return lowest
    if lowest>=num:
        return -1
    
    return result[:num]

