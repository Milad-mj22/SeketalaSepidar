from dataclasses import dataclass

@dataclass
class urlAction:
    url:str
    type='url'

@dataclass
class postAction:
    url:str
    type='post'

# @dataclass
# class getAction:
#     url:str
#     type='get'

@dataclass
class jsAction:
    func_name:str
    type='js'