import collections
import inspect

import chainer
from chainer import optimizer


class OptimizerInspector(object):
    def __init__(self):
        self.members = collections.OrderedDict()
        sorted_members = sorted(inspect.getmembers(chainer.optimizers),
                                key=lambda x:x[0])
        for name, member in sorted_members:
            if inspect.isclass(member) and issubclass(member, optimizer.Optimizer):
                self.members[name] = member

    def get_signature(self, name):
        signature = inspect.signature(self.members[name]).parameters
        signature_dict = {}
        for value in signature.values():
            signature_dict['opt_' + value.name] = value.default
        order_signature_dict = collections.OrderedDict()
        for name in sorted(signature_dict.keys()):
            order_signature_dict[name] = signature_dict[name]
        return order_signature_dict

    def get_members(self):
        return self.members.keys()


# from chainer import link
# print('links')
# for name, member in inspect.getmembers(chainer.links):
#     if inspect.isclass(member):
#         if issubclass(member, link.Chain) or issubclass(member, link.Link):
#             print(member)
#             print(inspect.signature(member))
#             for key, value in inspect.signature(member).parameters.items():
#                 print(key, value.default)
#
#
#
# print('functions')
# for name, member in inspect.getmembers(chainer.functions):
#     if inspect.isfunction(member):
#         print(member)
#         for key, value in inspect.signature(member).parameters.items():
#             print(key, value.default)
