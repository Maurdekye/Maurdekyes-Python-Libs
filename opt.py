import re

class OptionDefinitionException(Exception):
  pass

class OptionExtractionError(Exception):
  pass

class OptionTemplate:
  def __init__(my, *, short_name=None, long_name=None, default=False, default_accept=None):
    if not short_name and not long_name:
      raise OptionDefinitionException("Option must have at least a short_name or a long_name")
    if short_name != None:
      if type(short_name) != str:
        raise OptionDefinitionException(f"short_name must be a string, not {type(short_name)}")    
      elif len(short_name) != 1:
        raise OptionDefinitionException(f"short_name can only be a single character, {short_name} is too long")
      elif short_name == "-":
        raise OptionDefinitionException("short_name can not be a hyphen character")
    if long_name != None and type(long_name) != str:
      raise OptionDefinitionException(f"long_name must be a string, not {type(long_name)}")
    if default_accept != None:
      if type(default) == bool:
        raise OptionDefinitionException(f"default_accept should only be provided for non-boolean options")
      if type(default_accept) != default:
        raise OptionDefinitionException(f"default_accept type must be the same as default type")

    my.short_name = short_name
    my.long_name = long_name
    my.default = default
    my.default_accept = default_accept
    my.opt_type = type(default)
    my.value = default

  def get_active_name(my):
    '''Gets the name that the programmer would use to reference this option'''
    if long_name != None:
      return long_name
    return short_name
  
  def get_matching_name(my, other):
    '''Retrieves the name that was used to reference this option from the argument passed'''
    if my.short_name != None and other.startswith("-" + my.short_name):
      return "-" + my.short_name
    if my.long_name != None and other.startswith("--" + my.long_name):
      return "--" + my.long_name
    return None

  def __eq__(my, other):
    if type(other) == list:
      if len(other) == 0:
        return False
      else:
        return my.__eq__(other[0])
    if type(other) == str:
      return my.get_matching_name(other) != None
    else:
      return super().__eq__(other)

  def retrieve_conjoined_argument(my, other):
    if my != other:
      return None
    used_name = my.get_matching_name(other)
    remaining_option = other[len(used_name):]
    if remaining_option == "":
      return None
    if remaining_option.startswith("="):
      return remaining_option[1:]
    return remaining_option

  def extract(my, optlist):
    if my != optlist:
      return optlist
    else:
      used_name = my.get_matching_name(optlist[0])
      arg = my.retrieve_conjoined_argument(optlist[0])
      if my.opt_type == bool:
        if arg != None:
          raise OptionExtractionError(f"{used_name} passed with conjoined argument {arg}, but does not require one")
        else:
          my.value = not my.default
          return optlist[1:]
      else:
        if arg != None:
          try:
            arg = my.opt_type(arg)
          except ValueError:
            raise OptionExtractonError(f"Argument passed to option {used_name} is {arg}, but cannot be coerced to expected type {my.opt_type}")
          my.value = arg
          return optlist[1:]
        else:
          if my.default_accept != None:
            my.value = my.default_accept
            return optlist[1:]
          else:
            if len(optlist) == 1:
              raise OptionExtractionError(f"Option {used_name} requires an argument")
            else:
              try:
                arg = my.opt_type(optlist[1])
              except ValueError:
                raise OptionExtractionError(f"Option {used_name} took {optlist[1]} as its argument, but {optlist[1]} cannot be coerced to the expected type, {my.opt_type}")
              my.value = arg
              return optlist[2:]

''' Cases for extracting option from arg list:
Relevant elements: first two items in list, current option

Case: List has no elements
  Result: Do nothing, return arg list unmodified
Case: List has at least one element
  Subcase: First element does not match current option
    Result: Do nothing, return arg list unmodified
  Subcase: First element matches current option
    Subcase: current option is a boolean, and does not require an argument
      Subcase: Option is given in conjoined-argument form
        Result: Raise exception, citing unnecessary argument
      Subcase: Option is not given with a conjoined argument
        Result: Accept option and return list without element
    Subcase: current option is not a boolean, and can accept an argument
      Subcase: Option is given in conjoined-argument form
        Subcase: Type of conjoined argument does not match the expected argument type
          Result: Raise exception, cite wrong argument type
        Subcase: Type of conjoined argument does match the expected argument type
          Result: Accept option and argument, return list without first element
      Subcase: Option is not given in conjoined-argument form
        Subcase: Option can go without argument
          Result: Accept option and set to default accept value, return list without first element
        Subcase: Option cannot go without argument
          Subcase: List contains only a single element
            Result: Raise exception, cite missing argument
          Subcase: List contains at least two elements
            Subcase: Type of second element does not match the expected argument type
              Result Raise exception, cite argument consumed and wrong argument type
            Subcase: Type of second element does match the expected argument type
              Result: Accept option and argument, return list without first two elements

An option cannot both require no argument, and use one if it is given at the same time, 
AND also be able to use the next element in the list as an argument. This would create
ambiguity as to whether or not the next element should be consumed as an option argument.
'''

def name_type(name):
  sht, lng = None, None
  if name.startswith("--"):
    lng = name[2:]
  elif name.startswith("-"):
    sht = name[1:]
  elif len(name) > 1:
    lng = name
  else:
    sht = name
  return sht, lng

def rem_hyphens(name, c="-"):
  while name.startswith(c):
    name = name[1:]
  return name

def create_option_suite(optlist):
  suite = []
  for o in optlist:
    sht, lng, deft, deft_acc = None, None, False, None
    if type(o) == str:
      if len(rem_hyphens(o)) == 1:
        sht = rem_hyphens(o)
      else:
        lng = rem_hyphens(o)
    elif type(o) in [list, tuple]:
      o = list(o)
      if len(o) == 1:
        if type(o[0]) == str:
          sht, lng = name_type(o[0])
        else:
          continue
      if len(o) >= 2:
        if type(o[0]) == str:
          if type(o[1]) == str:
            if len(rem_hyphens(o[1])) == 1:
              lng, sht = rem_hyphens(o[0]), rem_hyphens(o[1])
            else:
              sht, lng = rem_hyphens(o[0]), rem_hyphens(o[1])
            o = o[2:]
          else:
            if len(rem_hyphens(o[0])) == 1:
              sht = rem_hyphens(o[0])
            else:
              lng = rem_hyphens(o[0])
            o = o[1:]
        if len(o) > 0:
          deft = o[0]
          o = o[1:]
        if len(o) > 0:
          deft_acc = o[0]
    elif type(o) == dict:
      if "short_name" in o:
        sht = rem_hyphens(o["short_name"])
      if "long_name" in o:
        lng = rem_hyphens(o["long_name"])
      if "default" in o:
        deft = o["default"]
      if "default_accept" in o:
        deft_acc = o["default_accept"]
    elif type(o) == OptionTemplate:
      sht = o.short_name
      lng = o.long_name
      deft = o.default
      deft_acc = o.default_accept
    else:
      continue
    suite.append(OptionTemplate(sht, lng, deft, deft_acc))
  return suite

def extract_all(arglist, options):
  if type(arglist) == str:
    arglist = arglist.split()
  suite = create_option_suite(options)
  optionless_args = []
  while len(arglist) > 0:
    for o in suite:
      startlen = len(arglist)
      arglist = o.extract(arglist)
      if len(arglist) != startlen:
        break
    else:
      optionless_args.append(arglist.pop(0))
  option_dict = {}
  for o in suite:
    option_dict[o.get_active_name()] = o.value

  return optionless_args, option_dict
