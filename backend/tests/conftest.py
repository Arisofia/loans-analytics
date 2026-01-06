# Minimal local requests_mock fixture for backend tests when requests-mock plugin is unavailable
#
# TODO: Temporary shim - remove once `requests-mock` is available in the
# developer environment and added to `requirements.txt`. The shim mirrors a
# subset of the plugin's behavior so backend tests run reliably in broken
# venvs or during local development.import requests
from types import SimpleNamespace
import pytest


class _SimpleRequestsMock:
    def __init__(self):
        self._routes = []

    def register(self, method: str, url, **kwargs):
        self._routes.append((method.upper(), url, kwargs))

    def get(self, url, **kwargs):
        self.register("GET", url, **kwargs)

    def put(self, url, **kwargs):
        self.register("PUT", url, **kwargs)

    def _handle(self, method: str, url: str, **kwargs) -> requests.Response:
        for mth, matcher, route_kwargs in self._routes:
            if mth != method.upper():
                continue
            if hasattr(matcher, "match"):
                if matcher.match(url):
                    route = route_kwargs
                    break
            else:
                if matcher == url:
                    route = route_kwargs
                    break
        else:
            resp = requests.Response()
            resp.status_code = 404
            resp._content = b"Not Found"
            return resp

        if "json" in route and callable(route["json"]):
            ctx = SimpleNamespace()
            ctx.status_code = 200

            class _Req:
                def __init__(self, method, url, headers, body):
                    self.method = method
                    self.url = url
                    self.headers = headers or {}
                    self.body = body

                @property
                def text(self):
                    if self.body is None:
                        return ""
                    if isinstance(self.body, bytes):
                        return self.body.decode("utf-8")
                    return str(self.body)

                def json(self_inner):
                    import json as _json

                    return _json.loads(self_inner.text)

            req_obj = _Req(method=method, url=url, headers=kwargs.get("headers", {}), body=kwargs.get("data"))
            res = route["json"](req_obj, ctx)
            resp = requests.Response()
            resp.status_code = getattr(ctx, "status_code", 200)
            if isinstance(res, dict):
                import json as _json

                resp._content = _json.dumps(res).encode("utf-8")
                resp.headers["Content-Type"] = "application/json"
            elif isinstance(res, str):
                resp._content = res.encode("utf-8")
            return resp

        resp = requests.Response()
        resp.status_code = int(route.get("status_code", 200))
        if "json" in route:
            import json as _json

            resp._content = _json.dumps(route["json"]).encode("utf-8")
            resp.headers["Content-Type"] = "application/json"
        elif "text" in route:
            resp._content = str(route["text"]).encode("utf-8")
        else:
            resp._content = b""
        return resp


@pytest.fixture
def requests_mock(monkeypatch):
    stub = _SimpleRequestsMock()

    def _patched(self, method, url, *args, **kwargs):
        resp = stub._handle(method, url, **kwargs)
        return resp

    monkeypatch.setattr(requests.Session, "request", _patched)
    return stub
