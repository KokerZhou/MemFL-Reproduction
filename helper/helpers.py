import json
import os
import re
import csv

from datetime import datetime

from helper.get_answer import get_answer

from collections import Counter

def count_test_occurrences(project_name, bug_id):
    file_path = f"/home/##/ttr/mem/data/{project_name}/data/{project_name}_{bug_id}/test_info.json"
    
    if not os.path.exists(file_path):
        return "File not found"
    
    with open(file_path, "r", encoding="utf-8") as f:
        test_data = json.load(f)
    
    # Extract first element from each sublist, split by '/', and get last part
    extracted_names = [entry[0].split("/")[-1] for entry in test_data if entry]
    
    # Count occurrences
    count_dict = Counter(extracted_names)
    
    # Format result
    formatted_result = " , ".join(f"{count}<{name}>" if count > 1 else f"<{name}>" for name, count in count_dict.items())
    
    return formatted_result


def create_log_directory(log_dir):
    # Ensure base log directory exists
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    for i in range(1000):
        dir_name = f"log_{i:03}"
        full_path = os.path.join(log_dir, dir_name)
        if not os.path.exists(full_path):
            os.makedirs(full_path)
            print(f"Created directory: {full_path}")
            log_file_path = os.path.join(full_path, "log.txt")
            with open(log_file_path, "w") as log_file:
                log_file.write(f"Log created on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            return full_path
    print("all directory exist")
    return None

def check_if_exist_class(response, project_name, bug_id):
    c, m, l = get_answer(project_name, bug_id)

    cleaned_lines = [''.join(filter(str.isalpha, line)) for line in response.split('\n') if line.strip()]
    cleaned_lines = [line for line in cleaned_lines if line]  # Remove empty strings
    
    for rank, class_name in enumerate(c, start=1):
        if any(cleaned in class_name for cleaned in cleaned_lines):
            return rank  # Return True and rank if found
    
    return None  # Return False and None if not found

def check_if_exist_method(results, project_name, bug_id):
    c, m, l = get_answer(project_name, bug_id)
    for a, b, c_val in results:
        for i in range(len(c)):
            if a in c[i] and b in m[i] and c_val == l[i]:
                return True
    return False


def format_test_info(test_info_content):
    test_name = test_info_content[0]
    failure_reason = test_info_content[1]
    stack_trace = test_info_content[2]
    test_function_code = test_info_content[3]
    related_functions = test_info_content[4:]

    formatted_string = f"""
==== TEST FAILURE REPORT ====

Test Name: {test_name}

--- Failure Reason ---
{failure_reason.strip()}

--- Stack Trace ---
{stack_trace.strip()}

--- Test Function Code ---
{test_function_code.strip()}

--- Related Functions ---
{'\n\n'.join(f.strip() for f in related_functions)}

===========================
"""
    return formatted_string

def format_test_info_exclude_related(test_info_content):
    test_name = test_info_content[0]
    failure_reason = test_info_content[1]
    stack_trace = test_info_content[2]
    test_function_code = test_info_content[3]

    formatted_string = f"""
==== TEST FAILURE REPORT ====

Test Name: {test_name}

--- Failure Reason ---
{failure_reason.strip()}

--- Stack Trace ---
{stack_trace.strip()}

--- Test Function Code ---
{test_function_code.strip()}

===========================
"""
    return formatted_string

def extract_class_from_response(response,covered_classes,p):

    # Extract only alphabetic characters from each line in response and remove empty strings
    cleaned_lines = [''.join(filter(str.isalpha, line)) for line in response.split('\n') if line.strip()]
    cleaned_lines = [line for line in cleaned_lines if line]  # Remove empty strings


    # Keep only cleaned_lines that are part of an element in covered_classes
    matching_classes = [cls for cls in covered_classes if any(cls.endswith(line + ".java") for line in cleaned_lines)]
    if p=="Closure":
        matching_classes = ["com.google." + cls.removesuffix(".java") for cls in matching_classes]  # Remove ".java" from each element
    elif p=="Chart":
        matching_classes = ["org.jfree." + cls.removesuffix(".java") for cls in matching_classes]  # Remove ".java" from each element
    elif p=="Lang" or p=="Math":
        matching_classes = ["org.apache." + cls.removesuffix(".java") for cls in matching_classes]  # Remove ".java" from each element
    elif p=="Time":
        matching_classes = ["org.joda." + cls.removesuffix(".java") for cls in matching_classes]  # Remove ".java" from each element
    else:
        print("something wrong,,, extract_class_from_response")
    return matching_classes


def get_review(ex_class,covered_classes,summary_dir,p):
    
    original = ex_class.split('.')[-1]
    parts = ex_class.split('.')
    ex_class = '.'.join(parts[2:]) + '.java'
    summary_content = ""   
    if ex_class in covered_classes:
        if p=="Closure":
            summary_filename = "com.google." + ex_class.rsplit(".java", 1)[0] + "_summary.txt"
        elif p=="Chart":
            summary_filename = "org.jfree." + ex_class.rsplit(".java", 1)[0] + "_summary.txt"
        elif p=="Lang" or p=="Math":
            summary_filename = "org.apache." + ex_class.rsplit(".java", 1)[0] + "_summary.txt"
        elif p=="Time":
            summary_filename = "org.joda." + ex_class.rsplit(".java", 1)[0] + "_summary.txt"
        else:
            print("something wrong... get_review")

        summary_path = os.path.join(summary_dir, summary_filename)
        
        # Read summary file content
        if os.path.exists(summary_path):
            with open(summary_path, "r", encoding="utf-8") as f:
                summary_content = f.read().strip()
        else:
            summary_content = "Summary not found"
        
    return (f"Summary of Class <{original}> :\n{summary_content}")
    
import random

def select_random_numbers(low,high,count):
    return [str(num) for num in random.sample(range(low,high), count)]  # Ensures unique numbers



def process_response(project,response, covered_classes, summary_dir):#Function that [ Response -->  Detailed Summaries]
    # Normalize response: Remove non-alphabet characters from each line
    cleaned_lines = [''.join(filter(str.isalpha, line)) for line in response.split('\n') if line.strip()]
    cleaned_lines = [line for line in cleaned_lines if line]
    # Find matching elements in covered_classes
    matching_classes = [cls for cls in covered_classes if any(cls.endswith(line + ".java") for line in cleaned_lines)]
    # Sort matching_classes based on the order in covered_classes
    #matching_classes.sort(key=lambda x: covered_classes.index(x))
    
    # Process filenames and collect summaries
    formatted_results = []

    for i, cls in enumerate(matching_classes):
        if project == "Closure":
            summary_filename = "com.google." + cls.rsplit(".java", 1)[0] + "_summary.txt"
        elif project=="Chart":
            summary_filename = "org.jfree." + cls.rsplit(".java", 1)[0] + "_summary.txt"
        elif project=="Lang" or project=="Math":
            summary_filename = "org.apache." + cls.rsplit(".java", 1)[0] + "_summary.txt"
        elif project=="Time":
            summary_filename = "org.joda." + cls.rsplit(".java", 1)[0] + "_summary.txt"
        summary_path = os.path.join(summary_dir, summary_filename)
        
        # Read summary file content
        if os.path.exists(summary_path):
            with open(summary_path, "r", encoding="utf-8") as f:
                summary_content = f.read().strip()
        else:
            summary_content = "Summary not found"
        
        # Format result
        parts = matching_classes[i].split(".")
        class_name = parts[-2]
        formatted_results.append(f"class {i+1} : <{class_name}>\nsummary : {summary_content}")
    
    return '\n'.join(formatted_results)


def process_response_simple(project,response, covered_classes, file_names, summaries): #Function that [ Response -->  Detailed Summaries]
    # Normalize response: Remove non-alphabet characters from each line
    cleaned_lines = [''.join(filter(str.isalpha, line)) for line in response.split('\n') if line.strip()]
    cleaned_lines = [line for line in cleaned_lines if line]
    # Find matching elements in covered_classes
    matching_classes = [cls for cls in covered_classes if any(cls.endswith(line + ".java") for line in cleaned_lines)]
    # Sort matching_classes based on the order in covered_classes
    #matching_classes.sort(key=lambda x: covered_classes.index(x))
    
    # Process filenames and collect summaries
    formatted_results = []

    for i, cls in enumerate(matching_classes):
        """
        if project == "Closure":
            summary_filename = "com.google." + cls.rsplit(".java", 1)[0] + "_summary.txt"
        elif project=="Chart":
            summary_filename = "org.jfree." + cls.rsplit(".java", 1)[0] + "_summary.txt"
        elif project=="Lang" or project=="Math":
            summary_filename = "org.apache." + cls.rsplit(".java", 1)[0] + "_summary.txt"
        elif project=="Time":
            summary_filename = "org.joda." + cls.rsplit(".java", 1)[0] + "_summary.txt"
        summary_path = os.path.join(summary_dir, summary_filename)
        
        
        
        # Read summary file content
        if os.path.exists(summary_path):
            with open(summary_path, "r", encoding="utf-8") as f:
                summary_content = f.read().strip()
        else:
            summary_content = "Summary not found"
        """
        index = file_names.index(cls) if cls in file_names else -1
        
        if index==-1:
            summary_content = "Summary not found"
        else:
            summary_content = summaries[index]

        
        # Format result
        parts = matching_classes[i].split(".")
        class_name = parts[-2]
        formatted_results.append(f"class {i+1} : <{class_name}>\nsummary : {summary_content}")
    
    return '\n'.join(formatted_results)
