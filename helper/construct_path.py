import os

def construct_path(base_dir,project_name,bug_id):
    buggy_base_dir = f"{base_dir}temp/{project_name}_{bug_id}/{project_name}_{bug_id}_buggy/"
    if project_name == "Chart":
        project_source_directory = "source"
    elif project_name == "Closure" or project_name == "Mockito":
        project_source_directory = "src"
    elif project_name == "Time" or project_name == "Lang" or project_name == "Math":
        project_source_directory = "src/main/java"
    else:
        print("wrong project_name")
        return -1
    
    buggy_dir = buggy_base_dir + project_source_directory
    if not os.path.isdir(buggy_dir):
        buggy_source_directory = "src/java"
        buggy_dir = buggy_base_dir + buggy_source_directory
        if not os.path.isdir(buggy_dir):
            print("wrong path")
            return -1
    
    return buggy_dir
