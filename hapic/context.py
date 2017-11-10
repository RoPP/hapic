# -*- coding: utf-8 -*-
import typing
from http import HTTPStatus

from hapic.processor import RequestParameters
from hapic.processor import ProcessValidationError

if typing.TYPE_CHECKING:
    from hapic.decorator import DecoratedController


class RouteRepresentation(object):
    def __init__(
        self,
        rule: str,
        method: str,
    ) -> None:
        self.rule = rule
        self.method = method


class ContextInterface(object):
    def get_request_parameters(self, *args, **kwargs) -> RequestParameters:
        raise NotImplementedError()

    def get_response(
        self,
        response: dict,
        http_code: int,
    ) -> typing.Any:
        raise NotImplementedError()

    def get_validation_error_response(
        self,
        error: ProcessValidationError,
        http_code: HTTPStatus=HTTPStatus.BAD_REQUEST,
    ) -> typing.Any:
        raise NotImplementedError()

    def find_route(
        self,
        decorated_controller: 'DecoratedController',
    ) -> RouteRepresentation:
        raise NotImplementedError()

    def get_swagger_path(self, contextualised_rule: str) -> str:
        """
        Return OpenAPI path with context path
        :param contextualised_rule: path of original context
        :return: OpenAPI path
        """
        raise NotImplementedError()
