import os
import inspect
import yaml

def write_output(*args):
    print(*args)

class CallLogger(object):
    def __init__(self, namespace, class_obj):
        self.namespace = namespace
        self.class_obj = class_obj

    def logcall(self, method_name, args, kwargs):
        output = "namespace:{} class: {} call: {}".format(self.namespace, self.class_obj.__name__, method_name)
        output += ("(")
        if args or kwargs:

            if len(args) == 1:
                output += str(args)[1:-2]
            elif len(args) > 1:
                output += str(args)[1:-1]
            if kwargs:
                if args:
                    output += ", "
                output += "**{}".format(kwargs)
        output += (")")
        write_output(output)
        return output


class MockClass(object):
    configuration_file = "mock.yaml"
    mock_class = None
    namespace = "generic"
    predefined_return = "Nothing"

    def __init__(self, *args, **kwargs):
        self.logger = CallLogger(self.namespace, self.mock_class or object)
        self.logger.logcall("__init__", args, kwargs)

    def __getattr__(self, name):
        stored_value = self.__return_from_config(name)

        def method(*args, **kwargs):
            self.logger.logcall(name, args, kwargs)
            return MockClass()
        
        output = method
        if self.mock_class is not None:
            if any([name in foo for foo in inspect.getmembers(self.mock_class, predicate=inspect.ismethod)]) or any([name in foo for foo in inspect.getmembers(self.mock_class, predicate=inspect.isfunction)]):
                output = method
            elif any([name in foo for foo in inspect.getmembers(self.mock_class)]):
                output = self.predefined_return
            else:
                raise NotImplementedError("function:{} is not supported by {} class".format(name, self.mock_class))
        return stored_value if stored_value is not None else output

    def __return_from_config(self, name):
        output = None
        function_suffix="()"
        filename = self.configuration_file
        if os.path.exists(filename):
            with open(filename, "r") as yaml_file:
                whole_config = yaml.safe_load(yaml_file)
            if whole_config.get(self.namespace):
                if whole_config[self.namespace].get(name):
                    output = whole_config[self.namespace].get(name)
                elif whole_config[self.namespace].get(name + function_suffix):
                    func_ret = whole_config[self.namespace].get(name + function_suffix)

                    def method(*args, **kwargs):
                        return func_ret
                    return method
        return output

    @staticmethod
    def mock_return(expected):
        return expected

    @staticmethod
    def mock_return_list(cls, amount=10, input_object=None):
        return [input_object or cls] * amount
