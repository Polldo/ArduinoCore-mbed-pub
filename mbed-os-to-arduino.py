from __future__ import print_function
from argparse import ArgumentParser
import os
import tempfile
import script.mbed_wrapper
import script.core_wrapper

CURRENT_DIR = os.getcwd()
TMP_PATH = tempfile.gettempdir() 

valid_complete_variants = ["ARDUINO_NANO33BLE:ARDUINO_NANO33BLE", "PORTENTA_H7_M4:PORTENTA_H7_M4", "PORTENTA_H7_M7:PORTENTA_H7_M7"]
valid_incomplete_variants = ["ARDUINO_NANO33BLE", "PORTENTA_H7_M4", "PORTENTA_H7_M7"]


# TODO: Check validity of passed arguments
# check if the path are actually accessible // path must be absolute
parser = ArgumentParser()
# Flags
parser.add_argument("-c", "--clean", dest="clean_flag", action="store_true", help="Clean Mbed application BUILD directory")
parser.add_argument("-u", "--update", dest="update_flag", action="store_true", help="Update to latest mbed-os release")
parser.add_argument("-a", "--apply-patches", dest="apply_patches", action="store_true", help="Apply patches")
# Optional path
parser.add_argument("-r", "--local-repo", type=str, dest="local_repo", help="Specify local mbed-os directory to link")
parser.add_argument("-b", "--remote-branch", type=str, dest="remote_branch", help="Specify remote mbed-os branch to checkout")
parser.add_argument("-p", "--core-location", type=str, dest="core_path", default=CURRENT_DIR, help="Specify local mbed core directory (defaults to PWD)")
parser.add_argument("--profile", type=str, dest="profile", choices=["debug","develop","release"], help="Specify a build profile")
# Mandatory arguments
parser.add_argument("variants", type=str, nargs="+", help="List of variant boards for which mbed is recompiled")
args = parser.parse_args()

# Summary passed arguments and flags
#if (args.clean_flag):
  #print ("c ")
#if (args.update_flag):
  #print ("u ")
#for board in args.variants:
  #print (board)
#print (args.core_path)

#print (args.local_repo)


# return tuple (variant, board)
def get_variant_and_board(variant_argument):
  for complete_item in valid_complete_variants:
    if variant_argument == complete_item:
      return (variant_argument.split(":")[0], variant_argument.split(":")[1])
  for incomplete_item in valid_incomplete_variants:
    if variant_argument == incomplete_item:
      return (variant_argument, variant_argument)
  # raise error, variant not valid
  raise Exception("Provided variant is not valid") 


def get_profile_and_flag(arduino_variant, args_profile):
  profile = ""
  profile_flag = ""
  if args_profile != None:
    profile = "-" + args_profile.upper()
    profile_flag = "--profile=" + args_profile
  elif os.path.isfile(arduino_variant + "/conf/profile/custom.json"):
    profile = "-CUSTOM"
    profile_flag = "--profile=" + arduino_variant + "/conf/profile/custom.json"
  #TODO: get also exported variables from the environment
  return (profile, profile_flag)


def main():
  mbed_path = TMP_PATH + "/test-mbed-os-program"
  core_cmd_exec = script.core_wrapper.CoreWrapper(mbed_path)

  mbed_cmd_exec = script.mbed_wrapper.MbedWrapper(args, mbed_path)
  mbed_cmd_exec.mbed_new()
  mbed_cmd_exec.mbed_revision()

  for item in args.variants:
    variant, board_name = get_variant_and_board(item)
    arduino_variant = args.core_path + "/variants/" + variant
    arduino_core_mbed = args.core_path + "/cores/arduino/mbed"
    profile, profile_flag = get_profile_and_flag(arduino_variant, args.profile)

    mbed_cmd_exec.configure(arduino_variant, board_name, profile, profile_flag)
    mbed_cmd_exec.create_mbed_program()
    mbed_cmd_exec.apply_patches()
    mbed_cmd_exec.mbed_compile()

    core_cmd_exec.configure(arduino_variant, board_name)
    core_cmd_exec.generate_defines()
    core_cmd_exec.generate_includes()
    core_cmd_exec.generate_flags()
    core_cmd_exec.generate_libs()
    core_cmd_exec.copy_core_files()

if __name__ == "__main__":
  main()
