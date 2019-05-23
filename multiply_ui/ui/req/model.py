from typing import Dict, Any, Tuple, Optional, List

from ..params.model import TIME_RANGE_TYPE
from ...util.html import html_element, html_table
from ...util.schema import PropertyDef, TypeDef

INPUT_IDENTIFIERS_TYPE = TypeDef(dict,
                                 key_type=TypeDef(str),
                                 item_type=TypeDef(list, item_type=TypeDef(str)))

INPUT_REQUEST_TYPE = TypeDef(object, properties=[
    PropertyDef('name', TypeDef(str)),
    PropertyDef('bbox', TypeDef(str)),
    PropertyDef('timeRange', TIME_RANGE_TYPE),
    PropertyDef('inputTypes', TypeDef(list, item_type=TypeDef(str))),
])

PROCESSING_REQUEST_TYPE = TypeDef(object, properties=[
    PropertyDef('name', TypeDef(str)),
    PropertyDef('bbox', TypeDef(str)),
    PropertyDef('timeRange', TIME_RANGE_TYPE),
    PropertyDef('inputTypes', TypeDef(list, item_type=TypeDef(str))),
    PropertyDef('inputIdentifiers', INPUT_IDENTIFIERS_TYPE),
])


class InputIdentifiers:
    def __init__(self, data: Dict):
        INPUT_IDENTIFIERS_TYPE.validate(data)
        self._data = data

    def _repr_html_(self):
        data_rows = []
        for input_type, prod_ids in self._data.items():
            for prod_id in prod_ids:
                data_rows.append([input_type, prod_id])
        return html_table(data_rows, header_row=['Input Type', 'Product Identifier'], title='Inputs')


class InputRequestMixin:

    @property
    def name(self) -> str:
        # noinspection PyUnresolvedReferences
        return self._data['name']

    @property
    def bbox(self) -> Tuple[float, float, float, float]:
        # noinspection PyUnresolvedReferences
        x1, y1, x2, y2 = tuple(map(float, self._data['bbox'].split(',')))
        return x1, y1, x2, y2

    @property
    def time_range(self) -> Tuple[Optional[str], Optional[str]]:
        # noinspection PyUnresolvedReferences
        start, stop = self._data['timeRange']
        return start, stop

    @property
    def input_types(self) -> List[str]:
        # noinspection PyUnresolvedReferences
        return self._data['inputTypes']

    def as_dict(self) -> Dict:
        # noinspection PyUnresolvedReferences
        return self._data

    def _repr_html_(self):
        # TODO: make it look nice
        return f'<p>' \
            f'Name: {self.name}<br/>' \
            f'Time range: {self.time_range}<br/>' \
            f'Region box: {self.bbox}' \
            f'Input types: {", ".join(self.input_types)}' \
            f'</p>'


class InputRequest(InputRequestMixin):
    def __init__(self, data: Dict[str, Any]):
        INPUT_REQUEST_TYPE.validate(data)
        self._data = data


class ProcessingRequest(InputRequestMixin):
    def __init__(self, data: Dict[str, Any] = None):
        PROCESSING_REQUEST_TYPE.validate(data)
        self._data = data

    @property
    def input_identifiers(self) -> InputIdentifiers:
        return InputIdentifiers(self._data['inputIdentifiers'])

    def _repr_html_(self):
        input_request_html = super()._repr_html_()
        # noinspection PyProtectedMember
        input_identifiers_html = self.input_identifiers._repr_html_()
        # TODO: make it look nice
        return html_element('div',
                            f'{input_request_html}'
                            f'{input_identifiers_html}')
