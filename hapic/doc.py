# -*- coding: utf-8 -*-
import typing

import bottle
from apispec import APISpec
from apispec import Path
from apispec.ext.marshmallow.swagger import schema2jsonschema

from hapic.context import ContextInterface, RouteRepresentation
from hapic.decorator import DECORATION_ATTRIBUTE_NAME
from hapic.decorator import DecoratedController
from hapic.description import ControllerDescription
from hapic.exception import NoRoutesException
from hapic.exception import RouteNotFound


def find_bottle_route(
    decorated_controller: DecoratedController,
    app: bottle.Bottle,
):
    if not app.routes:
        raise NoRoutesException('There is no routes in yout bottle app')

    reference = decorated_controller.reference
    for route in app.routes:
        route_token = getattr(
            route.callback,
            DECORATION_ATTRIBUTE_NAME,
            None,
        )

        match_with_wrapper = route.callback == reference.wrapper
        match_with_wrapped = route.callback == reference.wrapped
        match_with_token = route_token == reference.token

        if match_with_wrapper or match_with_wrapped or match_with_token:
            return route
    # TODO BS 20171010: Raise exception or print error ? see #10
    raise RouteNotFound(
        'Decorated route "{}" was not found in bottle routes'.format(
            decorated_controller.name,
        )
    )


def bottle_generate_operations(
    spec,
    route: RouteRepresentation,
    description: ControllerDescription,
):
    method_operations = dict()

    # schema based
    if description.input_body:
        schema_class = type(description.input_body.wrapper.processor.schema)
        method_operations.setdefault('parameters', []).append({
            'in': 'body',
            'name': 'body',
            'schema': {
                '$ref': '#/definitions/{}'.format(schema_class.__name__)
            }
        })

    if description.output_body:
        schema_class = type(description.output_body.wrapper.processor.schema)
        method_operations.setdefault('responses', {})\
            [int(description.output_body.wrapper.default_http_code)] = {
                'description': str(description.output_body.wrapper.default_http_code),  # nopep8
                'schema': {
                    '$ref': '#/definitions/{}'.format(schema_class.__name__)
                }
            }

    if description.errors:
        for error in description.errors:
            schema_class = type(error.wrapper.schema)
            method_operations.setdefault('responses', {})\
                [int(error.wrapper.http_code)] = {
                    'description': str(error.wrapper.http_code),
                    'schema': {
                        '$ref': '#/definitions/{}'.format(schema_class.__name__)  # nopep8
                    }
                }

    # jsonschema based
    if description.input_path:
        schema_class = type(description.input_path.wrapper.processor.schema)
        # TODO: look schema2parameters ?
        jsonschema = schema2jsonschema(schema_class, spec=spec)
        for name, schema in jsonschema.get('properties', {}).items():
            method_operations.setdefault('parameters', []).append({
                'in': 'path',
                'name': name,
                'required': name in jsonschema.get('required', []),
                'type': schema['type']
            })

    if description.input_query:
        schema_class = type(description.input_query.wrapper.processor.schema)
        jsonschema = schema2jsonschema(schema_class, spec=spec)
        for name, schema in jsonschema.get('properties', {}).items():
            method_operations.setdefault('parameters', []).append({
                'in': 'query',
                'name': name,
                'required': name in jsonschema.get('required', []),
                'type': schema['type']
            })

    operations = {
        route.method.lower(): method_operations,
    }

    return operations


class DocGenerator(object):
    def get_doc(
        self,
        controllers: typing.List[DecoratedController],
        context: ContextInterface,
    ) -> dict:
        spec = APISpec(
            title='Swagger Petstore',
            version='1.0.0',
            plugins=[
                # 'apispec.ext.bottle',
                'apispec.ext.marshmallow',
            ],
        )

        schemas = []
        # parse schemas
        for controller in controllers:
            description = controller.description

            if description.input_body:
                schemas.append(type(
                    description.input_body.wrapper.processor.schema
                ))

            if description.input_forms:
                schemas.append(type(
                    description.input_forms.wrapper.processor.schema
                ))

            if description.output_body:
                schemas.append(type(
                    description.output_body.wrapper.processor.schema
                ))

            if description.errors:
                for error in description.errors:
                    schemas.append(type(error.wrapper.schema))

        for schema in set(schemas):
            spec.definition(schema.__name__, schema=schema)

        # add views
        # with app.test_request_context():
        paths = {}
        for controller in controllers:
            route = context.find_route(controller)
            swagger_path = context.get_swagger_path(route.rule)

            operations = bottle_generate_operations(
                spec,
                route,
                controller.description,
            )

            path = Path(path=swagger_path, operations=operations)

            if swagger_path in paths:
                paths[swagger_path].update(path)
            else:
                paths[swagger_path] = path

            spec.add_path(path)

        return spec.to_dict()
