import sys
import os

sys.path.append(os.path.abspath("."))
sys.dont_write_bytecode = True

__author__ = "bigfatnoob"

from utils.lib import O
from utils import cache, lib
from store import json_store, mongo_store
import properties


def get_store(dataset):
  if properties.STORE == "json":
    return json_store.InputStore(dataset)
  elif properties.STORE == "mongo":
    return mongo_store.InputStore(dataset)
  raise RuntimeError("Invalid configuration: %s" % properties.STORE)



class InputCache(O):
  _cache = {}
  _store = None

  @staticmethod
  def load(dataset, key):
    if key in InputCache._cache:
      return InputCache._cache[key]
    if not InputCache._store or InputCache._store.dataset != dataset:
      InputCache._store = get_store(dataset)
    arguments = InputCache._store.load_inputs(key)
    InputCache._cache[key] = arguments
    return arguments


class Function(O):
  _id = 0

  def __init__(self, **kwargs):
    Function._id += 1
    self.id = Function._id
    self.name = None
    self.body = None
    self.dataset = None
    self.package = None
    self.className = None
    self.source = None
    self.lines_touched = None
    self.span = None
    self.input_key = None
    self.return_attribute = None
    self.outputs = None
    # Meta-info
    self.useful = None
    self.source = None
    O.__init__(self, **kwargs)

  def clone(self):
    new = Function()
    for key in self.has().keys():
      if key == "id": continue
      new[key] = self[key]
    return new

  def is_useful(self):
    # TODO: check usefulness of function
    if self.useful is not None:
      return self.useful
    inputs = InputCache.load(self.dataset, self.input_key)
    if inputs is None:
      self.useful = False
      return self.useful
    only_none = True
    for retrn in self.outputs.returns:
      if retrn is not None:
        only_none = False
        break
    if only_none:
      self.useful = False
      return self.useful
    return_not_nones_indices = []
    for i in range(len(self.outputs.returns)):
      if self.outputs.returns[i] is not None:
        return_not_nones_indices.append(i)
    if len(return_not_nones_indices) == 0:
      self.useful = False
      return self.useful
    for input_arg in inputs:
      is_valid_input = False
      for i in return_not_nones_indices:
        if input_arg[i] != self.outputs.returns[i]:
          is_valid_input = True
          break
      if not is_valid_input:
        self.useful = False
        return self.useful
    self.useful = True
    return self.useful


class Outputs(O):
  def __init__(self, outputs_json=None, **kwargs):
    O.__init__(self, **kwargs)
    self.returns = []
    self.errors = []
    self.durations = []
    if outputs_json is not None:
      for output_json in outputs_json:
        self.returns.append(output_json["return"] if "return" in output_json else None)
        self.errors.append(output_json["errorMessage"] if "errorMessage" in output_json else None)
        self.durations.append(output_json["duration"] if "duration" in output_json else None)

  def clone(self):
    new = Outputs()
    new.returns = self.returns[:]
    new.errors = self.errors[:]
    new.durations = self.durations[:]
    return new
