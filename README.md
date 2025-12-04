# MemFL: Memory-Enhanced Fault Localization with Project-Specific Knowledge

##Update 1 : added MemFL Results.xlsx
##Update 1 : added SoapFL result

## Overview
**MemFL** is a Memory-Enhanced Fault Localization approach that utilizes project-specific knowledge to improve debugging efficiency. While the current version is functional, future updates will focus on better organization and reproducibility upon publication.

## Installation & Setup

### System Requirements
- **Operating System**: Ubuntu
- **Python**: Ensure Python 3.x is installed with all necessary dependencies (to be updated in the final release).

### Directory Structure
Before running MemFL, ensure that the `mem` folder is correctly placed at:
```sh
/home/##/ttr/{mem}

Note: The ## placeholder was used for double-blind review. 
To run MemFL successfully, update all instances of /home/##/ttr to match your local directory path.

```

### gpt model
You can modify the used model by altering model = "" field on prompts/fl_mem_v#.py

## Dataset & 5-Fold Cross-Validation
MemFL supports 5-fold cross-validation using JSON-formatted dataset files structured as follows:

- Each project contains separate fold files: `projectname_fold_n.json`
- The folds use different batch sizes:
  - **Fold 1**: `batch size = 5` (discussion)
  - **Fold 2**: `batch size = 10`
  - **Fold 3**: `batch size = 1`
  - **Fold 4**: `batch size = 2`
  - **Fold 5**: `batch size = 5`
- Each JSON file specifies the test dataset for the corresponding fold and includes a memory path with debugging guidance for each iteration.

### Customizing Folds
You can:
- Create new fold files
- Extract debugging guidance
- Use existing folds for 5-fold validation with MemFL

## Running MemFL

### OpenAI API Setup
Before running MemFL, configure your OpenAI API credentials in:
```sh
mem/helper/request_llm.py
```

### Execution Command
To run MemFL, use the following command format inside the `/mem/` directory:
```sh
python3 -m fl --mode # --fold_file_name # --target_project # \
  --mem_input_dir # --mem_log_dir # --iteration # --batch_size # \
  --test_log_dir # --target_iteration_num #
```

#### Example 1: Running MemFL with Pre-Extracted Debugging Guidance
This command runs MemFL using previously extracted debugging guidance with `batch_size=1` and `iteration=1`:
```sh
python3 -m fl --mode 3 --fold_file_name fold_3 --target_project ALL \
  --mem_input_dir fl_test_3 --mem_log_dir mem_logs --iteration 1 \
  --batch_size 1 --test_log_dir logs/new_batch1/iteration_1 \
  --target_iteration_num 1
```

#### Example 2: Running Debugging Extraction on a New Fold
To extract debugging guidance for `batch_size=1` and `iteration=3` on a new fold:
```sh
python -m fl --mode 2 --fold_file_name new_fold --target_project ALL \
  --mem_input_dir fl_new --mem_log_dir mem_logs --iteration 3 \
  --batch_size 1 --test_log_dir logs/new_batch1/iteration_3 \
  --target_iteration_num 3
```

## Scoring and Evaluation
To check correctness and score results, run the following command:
```sh
python3 -m logs.check_correctness logs/batch#/iteration_#
```
This will output scores in the order of:
- Chart
- Closure
- Lang
- Math
- Time

# data
All the result data is at /logs/
