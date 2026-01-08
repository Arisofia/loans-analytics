from scripts import load_secrets


def test_redact_dict_masks_keys():
    d = {"password": "s1", "username": "u", "token_value": "t"}
    redacted = load_secrets.redact_dict(d)
    assert redacted["password"] == "<redacted>"
    assert redacted["token_value"] == "<redacted>"
    assert redacted["username"] == "u"
