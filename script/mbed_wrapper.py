from __future__ import print_function
import shutil
import os
import subprocess
import json
import sys

DEFAULT_APP_JSON = {"macros" : ["MBED_HEAP_STATS_ENABLED=1", "MBED_STACK_STATS_ENABLED=1", "MBED_MEM_TRACING_ENABLED=1"],
                    "target_overrides" : {"*" : {
                      "platform.stdio-buffered-serial": True,
                      "platform.stdio-baud-rate": 115200,
                      "platform.default-serial-baud-rate": 115200,
                      "rtos.main-thread-stack-size": 32768
                    }}}

DEFAULT_MBED_MAIN = "#include \"mbed.h\"\nint main() {}"


#mbed commands wrapper
class MbedWrapper:

  def __init__(self, params, mbed_path):
    self.mbed_path = mbed_path
    self.params = params


  # TODO: not all really needed. prune them
  def configure(self, arduino_variant, board_name, profile, profile_flag):
    self.arduino_variant = arduino_variant
    self.board_name = board_name
    self.profile = profile
    self.profile_flag = profile_flag
    

  def __execute_cmd(self, cmd):
    process = subprocess.Popen(cmd.split(), stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
    log, error = process.communicate()
    if error:
      print("Error while executing command:  " + cmd)
      print(error)
      sys.exit()
    else:
      print(log, end='')
    

  def mbed_new(self):
    if not os.path.exists(self.mbed_path):
      self.__execute_cmd("mbed new " + self.mbed_path)
      os.chdir(self.mbed_path)


  def mbed_revision(self):
    os.chdir(self.mbed_path)
    print("Checking out preferred 'mbed-os' version...")

    if self.params.update_flag:
      print(" Updating to latest...")
      self.__execute_cmd("mbed update")

    if self.params.remote_branch != None:
      print(" Checking out remote branch " + self.params.remote_branch + "...")
      os.chdir(self.mbed_path + "/mbed-os")
      self.__execute_cmd("git checkout --track " + self.params.remote_branch)
      os.chdir(self.mbed_path)

    if self.params.local_repo != None:
      print(" Linking local repo " + self.params.local_repo + "...")
      if os.path.isdir("mbed-os") and not os.path.islink("mbed-os"):
        shutil.rmtree(self.mbed_path + "/mbed-os", ignore_errors=True)
        os.symlink(self.params.local_repo, self.mbed_path + "/mbed-os")
    print(" done.")


  def create_mbed_program(self):
    print("Setting up Mbed Application...")
    shutil.rmtree(".mbedignore", ignore_errors=True)
    #self.__exec("mbed target " + self.board_name)
    #os.system("mbed toolchain GCC_ARM")
    self.__execute_cmd("mbed target " + self.board_name)
    self.__execute_cmd("mbed toolchain GCC_ARM")

    with open("main.cpp", "w") as outfile:
      outfile.write(DEFAULT_MBED_MAIN)

    # If config file does not exist, then put a default one
    app_json = self.arduino_variant + "/conf/mbed_app.json"
    if not os.path.isfile(app_json):
      with open(app_json, "w") as outfile:
        json.dump(DEFAULT_APP_JSON, outfile, indent=4)

    # Copy config files preserving metadata
    config_path = self.arduino_variant + "/conf"
    for filename in os.listdir(config_path):
      file_path = os.path.join(config_path, filename)
      if os.path.isfile(file_path):
        # same as cp -p
        shutil.copy2(file_path, self.mbed_path)
    print(" done.")


  def apply_patches(self):
    if self.params.apply_patches:
      print("Applying patches...")
      patch_path = self.params.core_path + "/patches"
      for filename in os.listdir(patch_path):
        file_path = os.path.join(patch_path, filename)
        if os.path.isfile(file_path):
          #TODO: doesn't work
          self.__execute_cmd("git apply -p1 -t -d mbed-os -i " + file_path)
          #os.system("git apply -p1 mbed-os " + file_path)
      print(" done.")


  def mbed_compile(self):
    os.chdir(self.mbed_path)
    print("Compiling Mbed Application...")

    if self.params.clean_flag:
      print("Cleaning...")
      shutil.rmtree(self.mbed_path + "/BUILD", ignore_errors=True)  

    compile_cmd = ("mbed compile " + self.profile_flag + " --source . -v").split()
    print(compile_cmd)
    compile_process = subprocess.Popen(compile_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
    # run-time iteration of process output
    for line in iter(compile_process.stdout.readline, '') :
      # Print compilation status 
      if "Compile [" in line:
        print(line, end='')
      # Save macros in a file
      elif "Macros:" in line:
        with open(self.mbed_path + "/" + self.board_name + ".macros.txt", "w") as outfile:
          outfile.write(line)

    # Check final status of the execution
    _, error = compile_process.communicate()
    if error:
      print(error)
      sys.exit()
    print(" done.")
