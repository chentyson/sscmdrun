import json

def _decode_list(data):
    rv = []
    for item in data:
        if hasattr(item, 'encode'):
            item = item.encode('utf-8')
        elif isinstance(item, list):
            item = _decode_list(item)
        elif isinstance(item, dict):
            item = _decode_dict(item)
        rv.append(item)
    return rv


def _decode_dict(data):
    rv = {}
    for key, value in data.items():
        if hasattr(value, 'encode'):
            value = value.encode('utf-8')
        elif isinstance(value, list):
            value = _decode_list(value)
        elif isinstance(value, dict):
            value = _decode_dict(value)
        rv[key] = value;
    return rv;

def jsondumps(config,sort=True,space=4):
    return json.dumps(config,sort_keys=sort,indent=space)

def parse_json_in_str(data):
    # parse json and convert everything from unicode to str
    #print( data );
    return json.loads(data, object_hook=_decode_dict)
