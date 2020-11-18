from __future__ import print_function
import os

class CoreWrapper:

  def __init__(self, mbed_path):
    self.mbed_path = mbed_path

  def configure(self, arduino_variant, board_name):
    self.arduino_variant = arduino_variant
    self.board_name = board_name

  def generate_defines (self):
    print("Generating defines...")
    macros_path = os.path.join(self.mbed_path, self.board_name + ".macros.txt")
    with open(macros_path, "r") as macros_file:
      macros = macros_file.read()
      macros = macros.replace("\"", "\\" + "\"")
      macros_list = macros.split()
      macros_list.remove("Macros:")
      macros_list.append("-DMBED_NO_GLOBAL_USING_DIRECTIVE=1")
      if os.path.isfile(self.arduino_variant + "/variant.cpp"):
        macros_list.append("-DUSE_ARDUINO_PINOUT")
      macros_list.sort()
      with open(self.arduino_variant + "/defines.txt", "w") as output_file:
        for macro in macros_list:
          output_file.write("%s\n" % macro)
      print(macros_list)

  def generate_includes (self):
    pass

  def generate_flags (self):
    pass 

  def generate_libs (self):
    pass

  def copy_core_files (self):
    pass
