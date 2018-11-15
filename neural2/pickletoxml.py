#!/usr/bin/env python
import xml.dom.minidom as dom
import sys

class PickleToXML(object): pass

# helper function

def getType(obj):
    """ generates string representation of class of obj 
        discarding decoration """
    return obj.__class__.__name__
def getModule(obj):
    return obj.__class__.__module__


_easyToPickle = [ "int", "float", "str", "unicode" ]

_isCallable = lambda o: hasattr(o, "__call__")

# 
#   pickling 
# 

def _pickleDictItems(root, node, fabric):
    for key, value in root.items():
        tempnode = fabric.createElement("item")
        tempnode.appendChild(_pickle(key, fabric, "key"))
        tempnode.appendChild(_pickle(value, fabric, "value"))
        node.appendChild(tempnode)

def _pickleListItems(root, node, fabric):
    for idx, obj in enumerate(root):
        tempnode = _pickle(obj, fabric, "item")
        tempnode.attributes["index"] = str(idx)
        node.appendChild(tempnode)

_pickleTupleItems = _pickleListItems

_pickle_id = 0
def _getNextPickleID():
    global _pickle_id
    temp = _pickle_id
    _pickle_id += 1
    return temp

def pickle(obj, elementName="root", fabric=dom.Document()):
    global _pickle_id
    _pickle_id=0
    root = _pickle(obj, fabric, elementName)
    _remove_ref_ids(obj)
    fabric.unlink()
    return root
    
def _pickle(root, fabric, elementName="root"):

    node = fabric.createElement(elementName)
    typeStr = getType(root)
    node.attributes["type"]=typeStr
    moduleStr = getModule(root)
    if not moduleStr == '__builtin__':
        node.attributes["module"]=moduleStr

    if isinstance(root, PickleToXML):
        node = _pickleObjectWithAttributes(node, root, fabric, elementName)
    elif typeStr in _easyToPickle:
        node.appendChild(fabric.createTextNode(str(root)))
    elif isinstance(root, dict):
        _pickleDictItems(root, node, fabric)
    elif isinstance(root, list):
        _pickleListItems(root, node, fabric)
    elif isinstance(root, tuple):
        _pickleTupleItems(root, node, fabric)
    else:
        # fallback handler
        node.appendChild(fabric.createTextNode(repr(root)))
    return node

def _remove_ref_ids(root):
    if isinstance(root, PickleToXML):
        _remove_ref_ids_from_object(root)
    elif isinstance(root, dict):
        _remove_ref_ids_from_dict(root)
    elif isinstance(root, list):
        _remove_ref_ids_from_list(root)
    elif isinstance(root, tuple):
        _remove_ref_ids_from_tuple(root)

def _remove_ref_ids_from_object(root):
    if not hasattr(root, "__pickle_reference_id__"):
        return
    del root.__pickle_reference_id__
    if hasattr(root, "__pickle_to_xml__"):
        attributesToPickle = root.__pickle_to_xml__
    else:
        attributesToPickle = [ name for name in dir(root) if not name.startswith("__") ]
    for name in attributesToPickle: 
        obj = getattr(root, name)
        if _isCallable(obj): continue
        _remove_ref_ids(obj)

def _remove_ref_ids_from_dict(root):
    for key, value in root.items():
        _remove_ref_ids(key)
        _remove_ref_ids(value)

def _remove_ref_ids_from_list(root):
    for obj in root:
        _remove_ref_ids(obj)

_remove_ref_ids_from_tuple = _remove_ref_ids_from_list

def _pickleObjectWithAttributes(node, root, fabric, elementName):

    # if it's already been pickled, store a reference
    if hasattr(root, "__pickle_reference_id__"):
        node.attributes["objectid"]=repr(root.__pickle_reference_id__)
        return node
    # otherwise add an object id tag and store it as an attribute
    root.__pickle_reference_id__ = _getNextPickleID()
    node.attributes["objectid"]=repr(root.__pickle_reference_id__)

    # pickle all members or just a subset ???
    if hasattr(root, "__pickle_to_xml__"):
        attributesToPickle = root.__pickle_to_xml__
    else:
        # avoid members which are python internal
        attributesToPickle = [ name for name in dir(root) if not name.startswith("__") ]

    for name in attributesToPickle: 
        obj = getattr(root, name)

        # do not pickle member functions
        if _isCallable(obj): continue

        # is there some special encoding method ??
        if hasattr(root, "_xml_encode_%s" % name):
            value = getattr(root, "_xml_encode_%s" % name)()
            node.appendChild(fabric.createTextNode(value))
        else:
            node.appendChild(_pickle(obj, fabric, name))
    return node

#
#   unpickling 
#

# helper functions

def _getElementChilds(node, doLower = False):
    """ returns list of (tagname, element) for all element childs of node """

    dolow = doLower and (lambda x:x.lower()) or (lambda x:x)
    return [ (dolow(no.tagName), no) for no in node.childNodes if no.nodeType != no.TEXT_NODE ]

def _getText(nodelist):
    """ returns collected and stripped text of textnodes among nodes in nodelist """
    rc = ""
    for node in nodelist:
        if node.nodeType == node.TEXT_NODE:
            rc = rc + node.data
    return rc.strip()

def _getClassFullSearch(modname, classname):
    "Get a class, importing if necessary"
    if modname is not None:
        __import__(modname)
    mod = sys.modules[modname]
    if hasattr(mod,classname):
        return getattr(mod,classname)
    return classname

# main unpickle function
visited={}
def unpickle(node):
    global visited
    visited={}
    result = _unpickle(node)
    visited={} # clear out visited list so we don't prevent garbage collection
    return result
    
def _unpickle(node):
    global visited
    typeName = node.attributes["type"].value
    moduleName = None
    if "module" in node.attributes.keys():
        moduleName = node.attributes["module"].value
    id = -1
    if "objectid" in node.attributes.keys():
        id = node.attributes["objectid"].value

    if typeName in _easyToPickle:
        initValue = _getText(node.childNodes)
        if typeName == "unicode":   # strings are always unicode in p3
            typeName = "str"
        value = eval("%s(%r)" % (typeName, initValue))
        return value
    elif typeName=="tuple":
        return _unpickleTuple(node)
    elif typeName=="list":
        return _unpickleList(node)
    elif typeName=="dict":
        return _unpickleDict(node)
    elif typeName=="NoneType":
        return None
    else:
        classType = _getClassFullSearch(moduleName, typeName)
        if id == -1:
            raise XMLUnpicklingException()

        if id in visited:
            obj = visited[id]
        else:
            #print( "type: '%s.%s' class: '%s'" % (moduleName, typeName, classType))
            obj = classType() #eval('%s()' % typeName)
            visited[id] = obj

            for name, element in _getElementChilds(node):
                setattr(obj, name, _unpickle(element))
        return obj

class XMLUnpicklingException(Exception): pass

def _unpickleList(node):
    li = []
    # collect entries, you can not assume that the
    # members of the list appear in the right order !
    for name, element in _getElementChilds(node):
        if name != "item":
            raise XMLUnpicklingException()
        idx = int(element.attributes["index"].value)
        obj = _unpickle(element)
        li.append((idx, obj))

    # rebuild list with right order
    li.sort()
    return [ item[1] for item in li ]

def _unpickleTuple(node):
    return tuple(_unpickleList(node))

def _unpickleDict(node):
    dd = dict()
    for name, element in _getElementChilds(node):
        if name != "item":
            raise XMLUnpicklingException()
        childList = _getElementChilds(element)
        if len(childList) != 2:
            raise XMLUnpicklingException()
        for name, element in childList:
            if name=="key":
                key = _unpickle(element)
            elif name=="value":
                value = _unpickle(element)
        dd[key]=value
    return dd

if __name__=="__main__":

    # build some nested data structures for testing purposes

    class RootObject(PickleToXML):

        counter = 3
        def __init__(self):
            self.sub = SubObject()
            self.data = dict(xyz=4711)
            self.objlist = [ 1, 2, SubObject(), DetailObject() ]

    class SubObject(PickleToXML):

        __pickle_to_xml__ = ["values", "detail"]

        def __init__(self):
            self.values = (3.12, 4711, 8.15)
            self.z = "uwe"
            self.detail = DetailObject()

    class DetailObject(PickleToXML):

        statement = "1 < 2 is true"
        blablaliste = ["a", "b", "c"]

        def _xml_encode_statement(self):
            # encrypt attribute 'statement'
            return self.statement[::-1]

        def _xml_decode_statement(self, value):
            # decrypt value
            self.statement = value[::-1]

    # testing procedure:
    # convert objects -> xml -> objects -> xml

    obj = RootObject()
    node = pickle(obj)
    print(node)
    print( node.toprettyxml())

    x = unpickle(node)
    node = pickle(x)
    print( node.toprettyxml())
