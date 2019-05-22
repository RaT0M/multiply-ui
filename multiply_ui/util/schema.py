from typing import Any, Type, List, Optional


class TypeDef:
    def __init__(self,
                 data_type: Type[Any] = str,
                 optional: bool = False,
                 item_type: 'TypeDef' = None,
                 num_items: int = None,
                 num_items_min: int = None,
                 num_items_max: int = None,
                 properties: List['PropertyDef'] = None):
        self._data_type = data_type
        self._optional = optional
        self._item_type = item_type
        self._num_items_min = num_items_min if num_items_min is not None else num_items
        self._num_items_max = num_items_max if num_items_max is not None else num_items
        self._properties = properties

    @property
    def data_type(self) -> Type[Any]:
        return self._data_type

    @property
    def optional(self) -> bool:
        return self._optional

    @property
    def item_type(self) -> Optional['TypeDef']:
        return self._item_type

    @property
    def properties(self) -> Optional[List['PropertyDef']]:
        return self._properties

    def validate(self, value: Any, prefix: str = ''):

        if value is None:
            if self.optional:
                return
            raise ValueError(f'{prefix}value is not optional, but found null')

        if value is not None and not self._optional and not isinstance(value, self._data_type):
            raise ValueError(f'{prefix}value is expected to have type {self._data_type.__name__!r}, '
                             f'but found type {type(value).__name__!r}')

        if isinstance(value, list) and self._item_type is not None:
            self._validate_list(value, prefix)
        elif isinstance(value, dict) and self._properties is not None:
            self._validate_dict(value, prefix)

    def _validate_list(self, value: List[Any], prefix):
        if self._num_items_min is not None or self._num_items_max is not None:
            num_items = len(value)
            if self._num_items_min == self._num_items_max and num_items != self._num_items_min:
                raise ValueError(f'{prefix}number of items must be {self._num_items_min}, '
                                 f'but was {num_items}')
            if self._num_items_min is not None and len(value) < self._num_items_min:
                raise ValueError(f'{prefix}number of items must not be less than {self._num_items_min}, '
                                 f'but was {num_items}')
            if self._num_items_max is not None and len(value) > self._num_items_max:
                raise ValueError(f'{prefix}number of items must not be greater than {self._num_items_max}, '
                                 f'but was {num_items}')

        index = 0
        for item in value:
            self._item_type.validate(item, prefix=prefix + f'index {index}: ')
            index += 1

    def _validate_dict(self, value, prefix):

        for p in self._properties:
            if p.name not in value and not p.optional:
                raise ValueError(f'{prefix}missing property {p.name!r}')
            p.validate(value[p.name], prefix=prefix + f'property {p.name!r}: ')

        illegal_property_names = set(value.keys()).difference(set(p.name for p in self._properties))
        if len(illegal_property_names) == 1:
            raise ValueError(f'{prefix}unexpected property {list(illegal_property_names)[0]!r} found')
        elif len(illegal_property_names) > 1:
            raise ValueError(f'{prefix}unexpected properties found: {sorted(list(illegal_property_names))!r}')


class PropertyDef:
    def __init__(self, name: str, prop_type: TypeDef):
        self._name = name
        self._type = prop_type

    @property
    def name(self) -> str:
        return self._name

    @property
    def data_type(self) -> Type[Any]:
        return self._type.data_type

    @property
    def optional(self) -> bool:
        return self._type.optional

    @property
    def item_type(self) -> Optional['TypeDef']:
        return self._type.item_type

    @property
    def properties(self) -> Optional[List['PropertyDef']]:
        return self._type.properties

    def validate(self, value: Any, prefix: str = ''):
        self._type.validate(value, prefix=prefix)