# -*- coding: utf-8 -*-

import bottle
from datetime import datetime

from aiohttp import web

from hapic.error.marshmallow import MarshmallowDefaultErrorBuilder
from hapic.ext.aiohttp.context import AiohttpContext

try:  # Python 3.5+
    from http import HTTPStatus
except ImportError:
    from http import client as HTTPStatus
import json
import time

from hapic import Hapic, MarshmallowProcessor
from hapic.data import HapicData

from example.usermanagement.schema import AboutSchema
from example.usermanagement.schema import NoContentSchema
from example.usermanagement.schema import UserDigestSchema
from example.usermanagement.schema import UserIdPathSchema
from example.usermanagement.schema import UserSchema

from example.usermanagement.userlib import User
from example.usermanagement.userlib import UserLib
from example.usermanagement.userlib import UserNotFound

hapic = Hapic(async_=True)
hapic.set_processor_class(MarshmallowProcessor)

class AiohttpController(object):
    @hapic.with_api_doc()
    @hapic.output_body(AboutSchema())
    async def about(self):
        """
        This endpoint allow to check that the API is running. This description
        is generated from the docstring of the method.
        """
        return {
            'version': '1.2.3',
            'datetime': datetime.now(),
        }

    @hapic.with_api_doc()
    @hapic.output_body(UserDigestSchema(many=True))
    async def get_users(self):
        """
        Obtain users list.
        """
        return UserLib().get_users()

    @hapic.with_api_doc()
    @hapic.handle_exception(UserNotFound, HTTPStatus.NOT_FOUND)
    @hapic.input_path(UserIdPathSchema())
    @hapic.output_body(UserSchema())
    async def get_user(self, id, hapic_data: HapicData):
        """
        Return a user taken from the list or return a 404
        """
        return UserLib().get_user(int(hapic_data.path['id']))

    @hapic.with_api_doc()
    # TODO - G.M - 2017-12-5 - Support input_forms ?
    # TODO - G.M - 2017-12-5 - Support exclude, only ?
    @hapic.input_body(UserSchema(exclude=('id',)))
    @hapic.output_body(UserSchema())
    async def add_user(self, hapic_data: HapicData):
        """
        Add a user to the list
        """
        print(hapic_data.body)
        new_user = User(**hapic_data.body)
        return UserLib().add_user(new_user)

    @hapic.with_api_doc()
    @hapic.handle_exception(UserNotFound, HTTPStatus.NOT_FOUND)
    @hapic.output_body(NoContentSchema(), default_http_code=204)
    @hapic.input_path(UserIdPathSchema())
    async def del_user(self, id, hapic_data: HapicData):
        UserLib().del_user(int(hapic_data.path['id']))
        return NoContentSchema()

    def bind(self, app: web.Application):
        app.add_routes([
            web.get('/about', self.about),
            web.get('/users', self.get_users),
            web.get(r'/users/{id}', self.get_user),
            web.post('/users/', self.add_user),
            web.delete('/users/{id}', self.del_user),
        ])


if __name__ == "__main__":
    app = web.Application()
    controllers = AiohttpController()
    controllers.bind(app)
    hapic.set_context(
        AiohttpContext(
            app,
            default_error_builder=MarshmallowDefaultErrorBuilder(),
        ),
    )
    doc_title = 'Demo API documentation'
    doc_description = 'This documentation has been generated from ' \
                       'code. You can see it using swagger: ' \
                       'http://editor2.swagger.io/'
    hapic.add_documentation_view('/doc/', doc_title, doc_description)
    print('')
    print('')
    print('GENERATING OPENAPI DOCUMENTATION')
    openapi_file_name = 'api-documentation.json'
    with open(openapi_file_name, 'w') as openapi_file_handle:
        openapi_file_handle.write(
            json.dumps(
                hapic.generate_doc(
                    title=doc_title,
                    description=doc_description
                )
            )
        )

    print('Documentation generated in {}'.format(openapi_file_name))
    time.sleep(1)

    print('')
    print('')
    print('RUNNING AIOHTTP SERVER NOW')
    # Run app
    web.run_app(app=app, host='127.0.0.1', port=8081)