import json
import unittest

from jsonrpcserver import (InvalidParametersError, InvalidRequestError,
                           MethodNotFoundError, Service)
from jsonrpcserver.introspection import introspect


class TestService(unittest.TestCase):
    def setUp(self):
        self.service = Service()

    def test_register_method(self):
        @self.service.method
        def add(a, b):
            return a + b

        self.assertIn("add", self.service._methods)

    def test_dispatch_success(self):
        @self.service.method
        def add(a, b):
            return a + b

        request = {"jsonrpc": "2.0", "method": "add", "params": [1, 2], "id": 1}
        response = self.service.dispatch(request)
        self.assertEqual(response.result, 3)

    def test_dispatch_invalid_params(self):
        @self.service.method
        def add(a, b):
            return a + b

        request = {"jsonrpc": "2.0", "method": "add", "params": [1], "id": 1}
        response = self.service.dispatch(request)
        self.assertIsInstance(response, InvalidParametersError)

    def test_dispatch_method_not_found(self):
        request = {"jsonrpc": "2.0", "method": "non_existent_method", "id": 1}
        response = self.service.dispatch(request)
        self.assertIsInstance(response, MethodNotFoundError)

    def test_dispatch_invalid_request(self):
        request = {"jsonrpc": "2.0", "id": 1}
        response = self.service.dispatch(request)
        self.assertIsInstance(response, InvalidRequestError)

    def test_dispatch_parse_error(self):
        request = "invalid json"
        response = self.service.handle_request_body(request)
        response_dict = json.loads(response)
        self.assertEqual(response_dict["error"]["code"], -32700)

    def test_handle_http_request(self):
        @self.service.method
        def add(a, b):
            return a + b

        class MockHttpRequest:
            body = json.dumps(
                {"jsonrpc": "2.0", "method": "add", "params": [1, 2], "id": 1}
            )

        response = self.service.handle_http_request(MockHttpRequest())
        response_dict = json.loads(response)
        self.assertEqual(response_dict["result"], 3)

    def test_method_decorator(self):
        @self.service.method
        def subtract(a, b):
            return a - b

        self.assertIn("subtract", self.service._methods)

    def test_public_methods(self):
        @self.service.method
        def public_method():
            pass

        def _private_method():
            pass

        self.service.register("_private_method", _private_method)
        public_methods = self.service.public_methods()
        self.assertIn("public_method", public_methods)
        self.assertNotIn("_private_method", public_methods)

    def test_trait_names(self):
        @self.service.method
        def method1():
            pass

        @self.service.method
        def method2():
            pass

        self.assertEqual(set(self.service.trait_names()), {"method1", "method2"})

    def test_get_attribute_names(self):
        self.assertEqual(self.service.get_attribute_names(), [])

    def test_introspection(self):
        @self.service.method
        def my_method(param1, param2):
            """This is a test method."""
            return f"test({param1}, {param2})"

        introspection_data = introspect(self.service, "http://localhost:5000")
        self.assertEqual(introspection_data["name"], "Service")
        self.assertEqual(len(introspection_data["methods"]), 1)
        method_info = introspection_data["methods"][0]
        self.assertEqual(method_info["name"], "my_method")
        self.assertEqual(method_info["description"], "This is a test method.")
        self.assertEqual(method_info["args"], ["param1", "param2"])


if __name__ == "__main__":
    unittest.main()
