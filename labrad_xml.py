import labrad
import labrad.units
import numpy as np
from labrad.units import Value,Complex
try:
    from pyle.util.structures import ValueArray
except:
    ValueArray = type(None)

import labrad.units
import xml.etree.ElementTree as ET

def lr_to_element(data):
    if isinstance(data, Value):
        el = ET.Element("Value", attrib={"unit": data.units})
        el.text = str(data.value)
        return el
    elif isinstance(data, float):
        el = ET.Element("Value")
        el.text = str(data)
        return el
    elif isinstance(data, labrad.units.Complex):
        el = ET.Element("Complex", attrib={"unit": data.units})
        el.text = str(data.value)
        return el
    elif isinstance(data, complex):
        el = ET.Element("Complex")
        el.text = str(data)
        return el
    elif isinstance(data, int):
        el = ET.Element("Integer")
        el.test = str(data)
        return el
    elif isinstance(data, long):
        el = ET.Element("Word")
        el.test = str(data)
        return el
    elif isinstance(data, bool):
        el = ET.Element("Bool")
        el.text = str(data)
        return el
    elif isinstance(data, str):
        el = ET.Element("String")
        el.text = data
        return el
    elif isinstance(data, tuple):
        el = ET.Element("Cluster")
        for x in data:
            el.append(lr_to_element(x))
        return el
    elif isinstance(data, np.ndarray): # or isinstance(data,ValueArray):
        shapestr = ",".join([str(x) for x in data.shape])
        el = ET.Element("List", attrib={"dim": str(data.ndim),
                                        "shape": shapestr})
        for item in data.flat:
            el.append(lr_to_element(item))
        return el
    elif isinstance(data, list):
        # This does *not* currently verify that the list is a valid
        # labrad list.  labrad lists must be rectangular and
        # homogeneous, although the elements can be clusters or other
        # compound types.  Python lists can be heterogeneous, and if
        # nested can have different length sublists.
        depth = 0
        shape = []
        tmp = data
        while isinstance(tmp, list):
            shape.append(len(tmp))
            tmp = tmp[0]
            depth += 1
        shape = tuple(shape)
        shapestr = ",".join([str(x) for x in shape])
        el = ET.Element("List", attrib={"dim": str(depth),
                                        "shape": shapestr})
        def flatten_list(sublist):
            for item in sublist:
                if isinstance(item, list):
                    flatten_list(item)
                else:
                    sub_el = lr_to_element(item)
                    el.append(sub_el)
        flatten_list(data)
        return el

def element_to_lr(el):
    if el.tag.lower() == "value":
        if "unit" in el.attrib:
            return Value(float(el.text), el.attrib["unit"])
        else:
            return float(el.text)
    elif el.tag.lower() == "complex":
        if "unit" in el.attrib:
            return labrad.units.Complex(complex(el.text), el.attrib["unit"])
        else:
            return complex(el.text)
        pass
    elif el.tag.lower() == "word":
        return long(el.text)
    elif el.tag.lower() == "integer":
        return int(el.text)
    elif el.tag.lower() == "bool":
        return bool(el.text)
    elif el.tag.lower() == "string":
        return el.text
    elif el.tag.lower() == "cluster":
        data = []
        for x in el:
            data.append(element_to_lr(x))
        return tuple(data)
    elif el.tag.lower() == "list":
        # OK, we need to check the data type of the first element.
        # If it is a value/complex type, we make an ndarray or a valuearray.
        # If it is something else, we make nested lists.
        ndim = el.attrib["dim"]
        shape = [int(x) for x in el.attrib["shape"].split(",")]
        if el[0].tag.lower() == "value":
            array = np.zeros(shape, dtype=float)
            if "unit" in el[0].attrib and ValueArray is not type(None):
                array = ValueArray(array, el[0].attrib["unit"])
            for idx,item in enumerate(el):
                array.flat[idx] = element_to_lr(item)
            return array
        elif el[0].tag.lower() == "complex":
            array = np.zeros(shape, dtype=complex)
            if "unit" in el[0].attrib and ValueArray is not type(None):
                array = ValueArray(array, el[0].attrib["unit"])
            for idx,item in enumerate(el):
                array.flat[idx] = element_to_lr(item)
            return array
        else:
            def get_nested_list(subarray_shape, iter_):
                if len(subarray_shape) > 1:
                    l = []
                    for l in subarray_shape[0]:
                        l.append(get_nested_list(subarray_shape[1:], iter_))
                        return l
                else:
                    l = []
                    for l in subarray_shape[0]:
                        l.append(element_to_lr(iter_.next()))
                        return l
            return get_nested_list(shape, iter(el))
