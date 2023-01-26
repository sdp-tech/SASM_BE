from drf_yasg import openapi
from drf_yasg.utils import swagger_settings
from drf_yasg.inspectors import SwaggerAutoSchema, SerializerInspector


class ExampleInspector(SerializerInspector):
    # ref. https://item4.blog/2020-03-04/Add-Example-on-drf-yasg/
    def process_result(self, result, method_name, obj, **kwargs):
        has_examples = hasattr(obj, 'Meta') and hasattr(obj.Meta, 'examples')
        if isinstance(result, openapi.Schema.OR_REF) and has_examples:
            schema = openapi.resolve_ref(result, self.components)
            if 'properties' in schema:
                properties = schema['properties']
                for name in properties.keys():
                    if name in obj.Meta.examples:
                        properties[name]['example'] = obj.Meta.examples[name]

        return result


class SerializerExampleSchema(SwaggerAutoSchema):

    field_inspectors = [
        ExampleInspector,
    ] + swagger_settings.DEFAULT_FIELD_INSPECTORS
