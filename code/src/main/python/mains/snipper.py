import sys
import os

sys.path.append(os.path.abspath("."))
sys.dont_write_bytecode = True

__author__ = "bigfatnoob"

from analysis.helpers import constants as a_consts
from analysis import generate
from utils import cache
import properties


def execute(dataset, root_folder):
  for file_path in cache.list_files(root_folder, check_nest=True, is_absolute=True):
    file_name = cache.get_file_name(file_path)
    if file_name == "input": continue
    if file_name == "__init__" or file_name.startswith(a_consts.GENERATED_PREFIX):
      continue
    generate.generate_for_file(dataset, file_path)


def execute_dataset(dataset):
  root_folder = os.path.join(properties.PYTHON_PROJECTS_HOME, dataset)
  execute(dataset, root_folder)


def execute_problem(dataset, problem):
  root_folder = os.path.join(properties.PYTHON_PROJECTS_HOME, dataset, problem)
  execute(dataset, root_folder)


def export_methods(dataset):
  root_folder = os.path.join(properties.PYTHON_PROJECTS_HOME, dataset, problem)
  for file_path in cache.list_files(root_folder, check_nest=True, is_absolute=True):
    file_name = cache.get_file_name(file_path)
    if file_name == "__init__" or file_name.startswith(a_consts.GENERATED_PREFIX):
      continue
    generate.generate_for_file(dataset, file_path)


if __name__ == "__main__":
  args = sys.argv
  if len(args) < 2:
    print("Use: python mains/snipper.py <dataset> <?problem_id>")
    exit(0)
  elif len(args) > 2:
    execute_problem(args[1], args[2])
  else:
    execute_dataset(args[1])
