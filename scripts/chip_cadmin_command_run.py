import os
import sys
from datetime import datetime
import subprocess
import yaml
import re
from dataclasses import dataclass, fields
import threading
from fabric import Connection
import time
from invoke import UnexpectedExit
import invoke.exceptions

# Load configuration from YAML file
config_path = os.path.join(os.path.expanduser('~'), "chip_command_run", "config.yaml")
with open(config_path, 'r') as file:
    yaml_info = yaml.safe_load(file)
    build = yaml_info["chip_tool_directory"]

# Define regular expressions
pattern1 = re.compile(r'(CHIP:DMG|CHIP:TOO)(.*)')
pattern2 = re.compile(r'^\./chip-tool')
pattern3 = re.compile(r'avahi-browse')
testcase = ""

# Folder Path
path = os.path.join(os.getcwd(),"../commands")

# Change the directory
os.chdir(path)

# Function to factory reset the dut
def factory_reset( data ):

        ssh = Connection(host= data["host"], user=data["username"], connect_kwargs={"password": data["password"]})
        # Executing the  'ps aux | grep process_name' command to find the PID value to kill
        command = f"ps aux | grep {data['command']}"
        pid_val = ssh.run(command, hide=True)
        pid_output = pid_val.stdout
        pid_lines = pid_output.split('\n')
        for line in pid_lines:
            if data["command"] in line:
                pid = line.split()[1]
                conformance = line.split()[7]
                if conformance == 'Ssl':
                    kill_command = f"kill -9 {pid}"
                    ssh.run(kill_command)
        ssh.close()

#Function to advertise the dut
def advertise():
        
        cd = os.getcwd()
        data = yaml_info["Dut_data"]
        ssh = Connection(host= data["host"], user=data["username"], connect_kwargs={"password": data["password"]})
        path = data["path"]
        ssh.run('rm -rf /tmp/chip_*')
        try:
            log = ssh.run('cd ' + path + ' && ' + data["command"], warn=True, hide=True, pty=False)
        except UnexpectedExit as e:
            if e.result.exited == -1:
                None
            else:
                raise
        #self.start_logging(log)
        ssh.close()
        logpath = os.path.join(cd,"../logs/execution_logs") 
        date = datetime.now().strftime("%m_%Y_%d-%I:%M:%S_%p")
        with open(f"{logpath}/{testcase}dut-{date}.txt", 'a') as f:
            f.write(log.stdout)
        return True

# Function to assign the testcase name to the dut-side log
def testcasename(tc):
    global testcase
    testcase = tc
    return None
    
# Fn to process log files and save them
def process_log_file(input_file_path, output_directory):
    
    if not os.path.exists(output_directory):
        os.makedirs(output_directory)
        
    # Construct the output file path using the input file name
    output_file_path = os.path.join(output_directory, os.path.basename(input_file_path))
    avahi = False

    with open(input_file_path, 'r') as input_file, open(output_file_path, 'w') as output_file:
                for line in input_file:
                    line = line.strip()
                    match1 = pattern1.search(line)
                    match2 = pattern2.search(line)
                    match3 = pattern3.search(line)
                    if match1:
                        chip_text = match1.group(1).strip()
                        trailing_text = match1.group(2).strip()
                        output_line = f"{chip_text} {trailing_text}"
                        output_file.write(output_line + '\n')
                    elif match2:
                        output_file.write('\n' 'CHIP:CMD : ' + line + '\n\n')
                        avahi = False
                    elif match3:
                        output_file.write('\n' 'CHIP:CMD : ' + line + '\n')
                        avahi = True
                    elif avahi:
                        output_file.write( line + '\n')

# Function to scrap the manualcode from the log
def code():
    
    with open ("temp.txt", 'r') as f:
        for line in f:
            line = line.strip()
            match = re.search(r'Manual pairing code: \[(\d+)\]', line)
            if match:
                manualcode = match.group(1)
                return(str(manualcode))            
    return False
    
# Fn to run chip commands in terminal
def run_command(commands, testcase):
    file_path = os.path.join(os.path.expanduser('~'), build)
    save_path = os.path.join(os.path.expanduser('~'), "chip_command_run", "logs", "execution_logs")
    testcasename(testcase)
    cd = os.getcwd()
    date = datetime.now().strftime("%m_%Y_%d-%I:%M:%S_%p")
    manualcode = "34970112332"
    data = yaml_info["Dut_data"]
    factory_reset(data)
    thread = threading.Thread(target=advertise)
    thread.daemon = True
    thread.start()
    time.sleep(5)
    os.chdir(file_path)
    rebootcmd = "rm -rf /tmp/chip_*"
    subprocess.run(rebootcmd, shell=True, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    pairing_cmd = "./chip-tool pairing onnetwork 1 20202021"
    subprocess.run(pairing_cmd, shell=True, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    while "" in commands:
        commands.remove("")
    for i in commands:
        log_filename = f"{testcase}-{date}.txt"
        log_file_path = os.path.join(save_path, log_filename)
        with open(log_file_path, 'a') as cluster_textfile:
            print(testcase, i)
            # subprocess module is used to open, append logs and run command in the terminal
            if "open-commissioning-window" in i:
                cluster_textfile.write('\n' + '\n' + i + '\n' + '\n')

            elif "open-basic-commissioning-window" in i:
                manualcode = "34970112332"

            elif "{code}" in i:
                i = i.replace("{code}", manualcode)
                cluster_textfile.write('\n' + '\n' + i + '\n' + '\n')

            else:
                cluster_textfile.write('\n' + '\n' + i + '\n' + '\n')
        run = subprocess.run(i, shell=True, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        log = run.stdout
        with open("temp.txt", 'w') as f:
            f.write(log)
        if "open-commissioning-window" in i:
            cod = code()
            if cod == False:
                None
            else:
                manualcode = cod
        with open(log_file_path, 'a') as cluster_textfile:
            cluster_textfile.write(log)
    factory_reset(data)
    time.sleep(5)

    # Process the log file immediately after running the commands
    output_directory = os.path.join(os.path.expanduser('~'), "chip_command_run", "logs", "validation_logs")
    process_log_file(log_file_path, output_directory)
    os.chdir(cd)
    print(f"\n---------------------{testcase} - Executed----------------------")
    print(f"\nExecution log saved as {log_filename}")
    print(f"Validation log processed for {testcase}")
    print(f"\n****************************************************************")

# Function to read text files
def read_text_file(file_path):
    testsite_array = []
    filterCommand = []
    with open(file_path, 'r') as f:
        for line in f:
            testsite_array.append(line)
        filter_command = filter_commands(testsite_array)
        for command in filter_command:
            for com in command:
                # Separate testcase name from the array of commands
                if "#" in com:
                    testcase = com.split()[1]
                else:
                    filterCommand.append(com)
            run_command(filterCommand, testcase)
            filterCommand = []

# Function to filter only commands from txt file
def filter_commands(commands):
    newcommand = []
    for command in commands:
        if "\n" in command:
            command = command.replace("\n", "")
        if "$" not in command:
            newcommand.append(command)
    size = len(newcommand)
    # Remove all the "end" in the array
    idx_list = [idx + 1 for idx, val in
                enumerate(newcommand) if val.lower() == "end"]
    res = [newcommand[i: j] for i, j in
           zip([0] + idx_list, idx_list +
               ([size] if idx_list[-1] != size else []))]
    newRes = []
    for i in res:
        i.pop()
        newRes.append(i)
    return newRes

if __name__ == "__main__":
    selected_clusters = ["CADMIN"]
    build_confirmation = input(f"\nConfirm the Chip-Tool Build Path: {build} (Y/Yes to confirm): ").strip().lower()
    output_directory = os.path.join(os.path.expanduser('~'), "chip_command_run", "logs", "validation_logs")

    if build_confirmation in ['y', 'yes']:
        clusters_confirmation = input(f"\nProceed with selected Clusters {selected_clusters} for execution (Y/Yes to proceed): ").strip().lower()
        print(f"\n****************************************************************")
        if clusters_confirmation in ['y', 'yes']:
            for cluster_name in selected_clusters:
                file = "Cadmin.txt"
                file_path = os.path.join(os.path.expanduser('~'), "chip_command_run", "commands", file)
                read_text_file(file_path)
                print(f"\nExecution completed... Logs are ready for validation in {output_directory}")
        else:
            print(f"\nExecution Canceled With The User Input: {clusters_confirmation}")
    else:
        print(f"\nExecution Canceled With User The User Input: {build_confirmation}")
