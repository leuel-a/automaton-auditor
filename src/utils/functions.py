from dataclasses import asdict

def as_dict(obj) -> dict:
    if hasattr(obj, "__dataclass_fields__"):
        return asdict(obj)
    raise TypeError(f"Not a dataclass: {type(obj)}")
