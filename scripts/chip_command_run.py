import os
import subprocess
import re
import argparse
from dataclasses import dataclass, fields
from datetime import datetime
import yaml

@dataclass
class Cluster:
    
    TVOCCONC : str = "../commands/Total_Volatile_Organic_Compounds_Concentration_Measurement.txt"
    NDOCONC : str = "../commands/Nitrogen_Dioxide_Concentration_Measurement.txt"
    CC : str = "../commands/Color_Control.txt"
    LUNIT : str = "../commands/Unit_localization.txt"
    FLDCONC : str = "../commands/Formaldehyde_Concentration_Measurement.txt"
    SWTCH : str = "../commands/Switch.txt"
    BRBINFO : str = "../commands/Bridged_Device_Basic_Information.txt"
    BIND : str = "../commands/Binding.txt"
    ULABEL : str = "../commands/User_Lable.txt"
    PMICONC : str = "../commands/PM2.5_Concentration_Measurement.txt"
    SMOKECO : str = "../commands/Smoke_and_CO_Alarm.txt"
    DISHM : str = "../commands/Dishwasher_Mode_Cluster.txt"
    FLABEL : str = "../commands/Fixed_Lable.txt"
    DRLK : str = "../commands/Door_lock.txt"
    ACFREMON : str = "../commands/Activated_Carbon_Filter_Monitoring.txt"
    TSTAT : str = "../commands/Thermostat.txt"
    DESC : str = "../commands/Descriptor_Cluster.txt"
    MC : str = "../commands/Media.txt"
    CDOCONC : str = "../commands/Carbon_Dioxide_Concentration_Measurement.txt"
    PSCFG : str = "../commands/Power_Source_Configuration.txt"
    DGETH : str = "../commands/Ethernet_Diag.txt"
    DGSW : str = "../commands/Software_Diag.txt"
    HEPAFREMON : str = "../commands/HEPA_Filter_Monitoring.txt"
    RVCCLEANM : str = "../commands/RVC_Clean_Mode.txt"
    PRS : str = "../commands/Pressure_measurement.txt"
    I : str = "../commands/Identify.txt"
    DGTHREAD : str = "../commands/Thread_diag.txt"
    BOOL : str = "../commands/Boolean.txt"
    TSUIC : str = "../commands/Thermostat_User.txt"
    LCFG : str = "../commands/Localization_Configuration_cluster.txt"
    WNCV : str = "../commands/Window_Covering.txt"
    BINFO : str = "../commands/Basic_Information.txt"
    OCC : str = "../commands/OccupancySensing.txt"
    DGWIFI : str = "../commands/Wifi_Diag.txt"
    GRPKEY : str = "../commands/Group_Communication.txt"
    RH : str = "../commands/Relative_Humidity_Measurement_Cluster.txt"
    PS : str = "../commands/Power_Source_Cluster.txt"
    LTIME : str = "../commands/Time_Format_localization.txt"
    G : str = "../commands/Groups.txt"
    LWM : str = "../commands/Laundry_Washer_Mode.txt"
    PMHCONC : str = "../commands/PM1_Concentration_Measurement.txt"
    PCC : str = "../commands/pump_configuration.txt"
    ACL : str = "../commands/Access_Control.txt"
    RVCRUNM : str = "../commands/RVC_Run_Mode.txt"
    RNCONC : str = "../commands/Radon_Concentration_Measurement.txt"
    FLW : str = "../commands/Flow_Measurement_Cluster.txt"
    MOD : str = "../commands/Mode_Select.txt"
    LVL : str = "../commands/Level_Control.txt"
    AIRQUAL : str = "../commands/Air_Quality.txt"
    PMKCONC : str = "../commands/PM10_Concentration_Measurement.txt"
    TMP : str = "../commands/Temperature_Measurement_Cluster.txt"
    OZCONC : str = "../commands/Ozone_Concentration_Measurement.txt"
    FAN : str = "../commands/Fan_Control.txt"
    OO : str = "../commands/OnOff.txt"
    CMOCONC : str = "../commands/Carbon_Monoxide_Concentration_Measurement.txt"
    TCCM : str = "../commands/Refrigerator_And_Temperature_Controlled_Cabinet_Mode.txt"
    DGGEN: str = "../commands/Gendiag.txt"
    ILL : str = "../commands/Illuminance_Measurement_Cluster.txt"

clusters = fields(Cluster)
cluster_name = [field.name for field in clusters]

# Parse command-line arguments
parser = argparse.ArgumentParser(description='Cluster name')
parser.add_argument('-c', '--cluster', nargs='+', help='Name of the cluster', choices=cluster_name, default=False)
args = parser.parse_args()

# Load configuration from YAML file
config_path = os.path.join(os.path.expanduser('~'), "chip_command_run", "config.yaml")
with open(config_path, 'r') as config_file:
    yaml_info = yaml.safe_load(config_file)
    build = yaml_info.get("chip_tool_directory")

# Define regular expressions
pattern1 = re.compile(r'(CHIP:DMG|CHIP:TOO)(.*)')
pattern2 = re.compile(r'^\./chip-tool')

# Folder Paths
input_dir = "../commands"
logs_dir = os.path.join(os.path.expanduser('~'), "chip_command_run", "Logs", "BackendLogs")
execution_logs_dir = os.path.join(os.path.expanduser('~'), "chip_command_run", "Logs", "ExecutionLogs")

# Function to get cluster names
def get_cluster_names():
    if args.cluster:
        selected_clusters = args.cluster
    else:
        selected_clusters = []
        for clus in cluster_name:
            e = yaml_info.get(clus)
            if e in ['Y', 'Yes']:
                selected_clusters.append(clus)
    return selected_clusters

# Function to run chip commands in terminal and save the log
def run_command(commands, testcase):
    file_path = os.path.join(os.path.expanduser('~'), build)
    os.chdir(file_path)

    date = datetime.now().strftime("%m_%Y_%d-%I:%M:%S_%p")
    while "" in commands:
        commands.remove("")

    # Create log files for both backend and execution logs
    backend_log_file_path = os.path.join(logs_dir, f"{testcase}-{date}.txt")
    execution_log_file_path = os.path.join(execution_logs_dir, f"{testcase}-{date}.txt")

    with open(backend_log_file_path, 'a') as backend_log_file, open(execution_log_file_path, 'a') as execution_log_file:
        for i in commands:
            print(testcase, i)
            backend_log_file.write('\n' + '\n' + i + '\n' + '\n')

            # Run the command and capture the output
            process = subprocess.Popen(i, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            stdout, _ = process.communicate()

            # Convert stdout to a string before writing it to the log
            stdout_str = stdout.decode('utf-8')
            backend_log_file.write(stdout_str)

            # Include pattern matching in the execution log
            match1 = pattern1.search(i)
            match2 = pattern2.search(i)
            if match1:
                chip_text = match1.group(1).strip()
                trailing_text = match1.group(2).strip()
                execution_log_file.write(f"{chip_text} {trailing_text}\n")
            if match2:
                execution_log_file.write(f'\nCHIP:CMD : {i}\n\n')

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
    idx_list = [idx + 1 for idx, val in enumerate(newcommand) if val.lower() == "end"]
    res = [newcommand[i: j] for i, j in zip([0] + idx_list, idx_list + ([size] if idx_list[-1] != size else []))]
    newRes = []
    for i in res:
        i.pop()
        newRes.append(i)
    return newRes

# Function to process all files
def process_all_files():
    for file in os.listdir(input_dir):
        if file.endswith(".txt"):
            file_path = os.path.join(input_dir, file)
            read_text_file(file_path)

if __name__ == "__main__":
    # Load configuration from YAML file
    config_path = os.path.join(os.path.expanduser('~'), "chip_command_run", "config.yaml")
    with open(config_path, 'r') as config_file:
        yaml_info = yaml.safe_load(config_file)
        build = yaml_info.get("chip_tool_directory")

    selected_clusters = get_cluster_names()

    if not selected_clusters:
        process_all_files()

    for cluster_name in selected_clusters:
        file = vars(Cluster)[cluster_name]
        file_path = os.path.join(input_dir, file)
        read_text_file(file_path)
