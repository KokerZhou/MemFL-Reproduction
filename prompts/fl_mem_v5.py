from helper.request_llm import request_api
import json
import os
import re
import csv
import pprint

from helper.get_answer import get_answer
from helper.reconstruct_class import reconstruct_class
from helper.collect_covered_classes import collect_covered_classes
from helper.reconstruct_class_with_method import reconstruct_class_with_method
from helper.helpers import format_test_info, format_test_info_exclude_related, extract_class_from_response, get_review, process_response,check_if_exist_class, check_if_exist_method, count_test_occurrences, process_response_simple
base_path = "/home/##/ttr/"

model = "gpt-4o-mini"


#V0

def refine_3(project_name, bug_id ,mem_path, stage_2_simple = True, stage_3_simple = False, request = True,verbose = True):

    print("begin : ", project_name, bug_id)

    # Define the directories
    base_path = f"/home/##/ttr/mem/data/{project_name}/"
    summary_dir = f"{base_path}class_summaries/"
    data_dir = f"{base_path}data/{project_name}_{bug_id}/"
    #memory_path = f"{base_path}memory/{mem_path}/"

    # Define the file path
    summary_file_path = f"{base_path}summary.txt"
    class_file_path = f"{base_path}classes.csv"
    test_info_path = f"{data_dir}failed_test.json"

    covered_class_file_path = f"{data_dir}covered_classes.txt"

    # Define the memory files
    memory_1_path = f"{mem_path}memory_1.txt"
    memory_2_path = f"{mem_path}memory_2.txt"
    memory_3_path = f"{mem_path}memory_3.txt"
    memory_4_path = f"{mem_path}memory_4.txt"
    memory_5_path = f"{mem_path}memory_5.txt"
    

    # Read and store file contents
    file_names = []
    summaries = []
    try:
        with open(memory_1_path, 'r') as f:
            memory_1_content = f.read()
        with open(memory_2_path, 'r') as f:
            memory_2_content = f.read()
        with open(memory_3_path, 'r') as f:
            memory_3_content = f.read()
        with open(memory_4_path, 'r') as f:
            memory_4_content = f.read()
        with open(memory_5_path, 'r') as f:
            memory_5_content = f.read()
        
        with open(covered_class_file_path, 'r') as f:
            covered_classes = f.read()

        with open(summary_file_path, 'r') as f:
            summary_content = f.read()
        
        with open(class_file_path, 'r') as csvfile:
            reader = csv.reader(csvfile)
            next(reader)
            for row in reader:
                file_names.append(row[0].strip())
                summaries.append(row[1].strip())

        with open(test_info_path, 'r') as f:
            test_info_content = json.load(f)  # Load JSON data as a Python dictionary

    except FileNotFoundError as e:
        print(f"File not found: {e}")
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON: {e}")
    except Exception as e:
        print(f"An error occurred: {e}")
    
    ## gets top <60> classes
    #covered_classes = collect_covered_classes(project_name,bug_id)
    


    if covered_classes == '-1':
        print("bug does not exist on top 60 classes...",project_name,bug_id)
        return 0, model,["Not_on_50"],[]
    else:
        covered_classes = covered_classes.split('\n')

    class_name_set = set()
    duplicates = set()

    covered_classes_for_prompt = ""####
    for i, covered_class in enumerate(covered_classes,start=1):
        if covered_class in file_names:
            index = file_names.index(covered_class)
            class_name = covered_class.split(".")[-2]
            if class_name in class_name_set:
                duplicates.add(class_name)  # Store duplicates
            else:
                class_name_set.add(class_name)

            if stage_2_simple:
                summary = summaries[index]
            else:
                if project_name == "Chart":
                    summary_file_name = "org.jfree." +covered_class.rsplit(".java", 1)[0] +"_summary.txt"
                elif project_name == "Closure":
                    summary_file_name = "com.google." +covered_class.rsplit(".java", 1)[0] +"_summary.txt"
                elif project_name == "Lang" or project_name=="Math":
                    summary_file_name = "org.apache." +covered_class.rsplit(".java", 1)[0] +"_summary.txt"
                elif project_name == "Time":
                    summary_file_name = "org.joda." +covered_class.rsplit(".java", 1)[0] +"_summary.txt"
                summary_path = os.path.join(summary_dir, summary_file_name)

                if os.path.exists(summary_path):
                    with open(summary_path, 'r') as f:
                        summary = f.read().strip()
                else:
                    summary = "Summary not found"

            covered_classes_for_prompt += f"  Class {i} : <{class_name}>, summary : {summary}\n"
        else:
            continue
    
    class_length = len(covered_classes)
    if duplicates:
        print("duplicated class names...")
        
    test_info = count_test_occurrences(project_name, bug_id)

    #Log that will be saved
    log = []
    
    #Prepare test information
    formatted_test = format_test_info(test_info_content)
    simple_formatted_test = format_test_info_exclude_related(test_info_content)
    
    ##Stage One
    ##----------
    prompt1 = {
            "role" : "user",
            "content" : f"""You are a debugging assistant. After reviewing the project summary and failing test case detail i want you to generate a review of the test function that includes potential reasons for failure,and fuctionalities related to the bug, You do not have to provide debugging guidance. 

Project summary :{summary_content}

Failing test case : {formatted_test}
"""
    }
    if memory_1_content:
        prompt1["content"]+=f"""
Debugging Guidance for the bug found by tests {test_info}:
{memory_1_content}
"""
    #rv_1, response_1 = request_api([prompt1], model, request)
    
    temp = []
    #log.append(temp)
    

    
    if(class_length>15):

    ##SECOND PART
    ##-----------

        prompt2 = {
        "role": "user",
        "content": f"""You are a debugging assistant. After reviewing project summary, failing test case that exposed the bug, and a list of class summary, i want you to decide few classes that might have caused the bug and  need further investigation. And output ONLY the name of the classes, since your answer will be handled automatically.

Project summary :{summary_content}

The failing test case that exposed the bug in the classes below (note: the bug is not in the test function itself): {simple_formatted_test}

Summary of each path in the project: 
{covered_classes_for_prompt}
"""
        }
    
        if memory_2_content:
            prompt2["content"]+=f"""
Debugging Guidance for the bug found by tests {test_info}:
{memory_2_content}
"""
        prompt2["content"]+="""
    
Now let's start.
Remember that your answer will be automatically handled.
Therefore, output your answer STRICTLY in format below, only with the name of the class
'''
classA
classB
classC
classD
'''
"""
        rv_2, response_2 = request_api([prompt2], model, request)

    
        if verbose:
            print("\nInteraction 2:")
            pprint.pprint(prompt2)
            print()
            print("response_2")
            pprint.pprint(response_2)

        rank = check_if_exist_class(response_2,project_name,bug_id)
    
        temp = []
        temp.append(prompt2)
        temp.append([response_2,rank])
        log.append(temp)
        
        if rv_2==-1:
            print("Error from API")
            return -2, model, [log], ""

        if rank==None:
            print("response 2 did not contain the answer")
            return -2, model,[log], ""
        if stage_3_simple:
            detailed_review = process_response_simple(project_name, response_2, covered_classes, file_names, summaries)
        else:
            detailed_review = process_response(project_name,response_2,covered_classes,summary_dir)###
    else:
        if verbose:
            print("Interaction2 skipped!")
        response_2 = ""
        for c in covered_classes:
            response_2+=c.split(".")[-2]
            response_2+="\n"
        rank = check_if_exist_class(response_2, project_name, bug_id)
        temp = []
        temp.append("Skipped")
        temp.append([response_2,rank])
        log.append(temp)
        if stage_3_simple:
            detailed_review = process_response_simple(project_name, response_2, covered_classes, file_names, summaries)
        else:
            detailed_review = process_response(project_name, response_2, covered_classes, summary_dir)###

    ##THIRD PART
    ##---------
    if(class_length>3):


        prompt3 = {
        "role": "user",
        "content": f"""You are a debugging assistant. After reviewing project summary. failing test case that exposed the bug, and list of class summary, i want you to decide few classes that might have caused the bug and need further investigation. And output ONLY the name of the classes, since your answer will be handled automatically.

Project summary :{summary_content}

The failing test case that exposed the bug in the classes below (note: the bug is not in the test function itself): {simple_formatted_test}

Summary of each path in the project: 
{detailed_review}
"""
        }
        if memory_3_content:
            prompt3["content"] +=f"""
Debugging Guidance for the bug found by tests {test_info}:
{memory_3_content}
"""
        prompt3["content"]+="""
Now let's start.
Remember that your answer will be automatically handled, and that you should determine the appropriate number of classes within the classes existing above
Therefore, output your answer STRICTLY in format below, only with the name of the class. 
'''
classA
classB
classC
'''

"""

        rv_3, response_3 = request_api([prompt3], model, request)
    
        if verbose:
            print("\nInteraction 3:")
            pprint.pprint(prompt3)
            print("\nresponse_3 :")
            pprint.pprint(response_3)

        rank = check_if_exist_class(response_3,project_name,bug_id)
    

        extracted_classes = extract_class_from_response(response_3,covered_classes,project_name)

        temp = []
        temp.append(prompt3)
        temp.append([response_3,rank])
        log.append(temp)
    
        if rank==None:
            print("response 3 did not contain the answer")
            return -3, model,[log], ""
        if rv_3==-1:
            print("Error from api")
            return -3, model, [log], ""
    else:
        response_3 = ""
        for c in covered_classes:
            response_3+=c.split(".")[-2]
            response_3+="\n"
        if verbose:
            print("\nInteraction 3 skipped")

        rank = check_if_exist_class(response_3, project_name,bug_id)

        extracted_classes=extract_class_from_response(response_3, covered_classes, project_name)
        temp = []
        temp.append("skipped")
        temp.append([response_3, rank])
        log.append(temp)



    print(response_3)
    classes = []
    total_recap = ""
    i = 1
    results = []

    for ex_class in extracted_classes:
        print(ex_class)
        
        class_code = reconstruct_class(project_name,bug_id,ex_class)
        review_of_class = get_review(ex_class,covered_classes,summary_dir,project_name)

        prompt4 = {
                "role":"user",
                "content": f""" You are a debugging assistant. After reviewing the project summary, failing test case that exposed the bug, and the source code, i want you to decide few methods that might have caused the bug and need further investigation. And output ONLY the name and the line number of the methods, since your answer will be handled automatically.

Project summary : {summary_content}

The failing test case that exposed the bug in the classes below (note: the bug is not in the test function itself): {simple_formatted_test}

{review_of_class}

Source code : {class_code}
"""
        }
        if memory_4_content:
            prompt4["content"] +=f"""
Debugging Guidance for the bug found by tests {test_info}:
{memory_4_content}
"""
        prompt4["content"] +="""
Now let's start.
Remember that your answer will be automatically handled, and that you should determine the appropriate number of methods within the methods existing above
Therefore, output your answer STRICTLY in format below, with Method_Name@Line_Number
'''
MethodA@123
MethodB@253
MethodC@335
MethodD@812
'''
"""
            
        rv_4, response_4 = request_api([prompt4], model, request)


        if verbose:
            print("Interaction 4 :")
            pprint.pprint(prompt4)

            print("response:")
            pprint.pprint(response_4)

        temp = []
        temp.append(prompt4)
        temp.append(ex_class)
        temp.append(response_4)
        log.append(temp)






        class_name = ex_class.split(".")[-1]
        classes.append(f"\n\n########Class {i} : <{class_name}>\n\n")
        classes.append(f"Review of target Class : {review_of_class}\n\n")
        classes.append(f"Source Code of the target class <{ex_class}>\n")
        reconstructed_class, recap, result = reconstruct_class_with_method(project_name,bug_id,ex_class,response_4)
        if reconstructed_class==-1 and recap==-1:
            continue
        classes.append(reconstructed_class)
        total_recap+=recap
        i+=1
        results.extend(result)

    if not check_if_exist_method(results,project_name,bug_id):
        c,m,l = get_answer(project_name,bug_id)
        if not "@@" in m:
            print(results)
            print()
            print(c,m,l)
            print("response 4 did not contain the answer")
            return -4, model,[log], ""

    #for c in classes:
    #    print(c)

    class_prompt = "\n".join(classes)
    ## FL PART
    ##--------
    prompt_FL = {
            "role" : "user",
            "content":f"""You are a debugging assistant. After reviewing the project summary, failing test case that exposed the bug, and the source code, I want you to identify the most relevant methods that are responsible for the issue. Output ONLY the Class name, Method name, line number in the given format that are most likely to contain a bug.

##Project summary : {summary_content}

##The failing test case that exposed the bug in the classes below (note: the bug is not in the test function itself): {simple_formatted_test}

"""
    }
    if memory_5_content:
        prompt_FL["content"] +=f"""
Debugging Guidance for the bug found by tests {test_info}:
{memory_5_content}
"""
    prompt_FL["content"] +=f"""
##Source Code : {class_prompt}

{total_recap}

with this available information, output Methods that are most likely to contain the bug ordered from most likely to buggy to least likely to be buggy. 
Since the answer will be automatically handled, output only the method signatures in the format Class_Name@Method_Name@Line_number, one per line. Do not provide any additional information.

Remember that your answer will be automatically processed. You should determine the appropriate number of class@method@lines pairs, optimally around 6~7.
Therefore, output your answer STRICTLY in format below, with the most suspicious item first:
'''
ClassA@MethodA@123
ClassA@MethodB@538
ClassB@MethodC@251
'''

Now, let's begin. 
"""
            
    rv_5, response_5 = request_api([prompt_FL], model, request)
    if verbose:
        print("Final Interaction :")
        pprint.pprint(prompt_FL)

    print("response :")
    pprint.pprint(response_5)
    if duplicates:
        log.append(["duplicate.."])
    temp = []
    temp.append(prompt_FL)
    temp.append(response_5)
    log.append(temp)

    return 1, model, log,response_5


