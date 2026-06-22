import datetime
import unittest

from asyagent.sigv4 import (
    ALGORITHM,
    canonical_query_string,
    derive_signing_key,
    presign_url,
    sha256_hex,
    sign_request,
    uri_encode,
)

SECRET = "wJalrXUtnFEMI/K7MDENG+bPxRfiCYEXAMPLEKEY"
ACCESS = "AKIDEXAMPLE"

FIXED_DATE = datetime.datetime(2015, 8, 30, 12, 36, 0, tzinfo=datetime.timezone.utc)
EXPECTED_SIGNING_KEY = "938127b5336810ddb6a5d6af445fcac9e371f9ed418ed386b022aed82901be75"
EXPECTED_SIGNATURE = "726c5c4879a6b4ccbbd3b24edbd6b8826d34f87450fbbf4e85546fc7ba9c1642"


class TestUriEncode(unittest.TestCase):
    def test_keeps_slash(self):
        self.assertEqual(uri_encode("a/b", keep_slash=True), "a/b")

    def test_encodes_slash(self):
        self.assertEqual(uri_encode("a/b", keep_slash=False), "a%2Fb")

    def test_encodes_space(self):
        self.assertEqual(uri_encode("a b"), "a%20b")

    def test_encodes_plus(self):
        self.assertEqual(uri_encode("a+b"), "a%2Bb")

    def test_unicode(self):
        self.assertEqual(uri_encode("\u4e2d"), "%E4%B8%AD")


class TestCanonicalQuery(unittest.TestCase):
    def test_empty(self):
        self.assertEqual(canonical_query_string({}), "")

    def test_sorted(self):
        result = canonical_query_string({"b": "2", "a": "1"})
        self.assertEqual(result, "a=1&b=2")

    def test_encoded_values(self):
        result = canonical_query_string({"prefix": "foo bar"})
        self.assertEqual(result, "prefix=foo%20bar")


class TestSha256(unittest.TestCase):
    def test_empty(self):
        self.assertEqual(
            sha256_hex(b""),
            "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
        )


class TestDeriveSigningKey(unittest.TestCase):
    def test_known_answer(self):
        key = derive_signing_key(SECRET, "20150830", "us-east-1", "service")
        self.assertEqual(key.hex(), EXPECTED_SIGNING_KEY)


class TestSignRequest(unittest.TestCase):
    def test_known_answer(self):
        headers, signature, sts, canonical = sign_request(
            method="GET",
            host="example.amazonaws.com",
            port=None,
            path="/",
            query={},
            extra_headers={},
            body=b"",
            access_key=ACCESS,
            secret_key=SECRET,
            security_token=None,
            region="us-east-1",
            service="service",
            date=FIXED_DATE,
        )
        self.assertEqual(signature, EXPECTED_SIGNATURE)
        self.assertEqual(headers["authorization"][: len(ALGORITHM)], ALGORITHM)
        self.assertIn(f"Credential={ACCESS}/20150830/us-east-1/service/aws4_request", headers["authorization"])
        self.assertEqual(headers["x-amz-date"], "20150830T123600Z")
        self.assertEqual(
            headers["x-amz-content-sha256"],
            "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
        )

    def test_signs_body(self):
        body = b'{"key": "value"}'
        headers, sig, _, _ = sign_request(
            method="PUT",
            host="s3.amazonaws.com",
            port=None,
            path="/bucket/key",
            query={},
            extra_headers={"content-type": "application/json"},
            body=body,
            access_key=ACCESS,
            secret_key=SECRET,
            security_token=None,
            region="us-east-1",
            service="s3",
            date=FIXED_DATE,
        )
        expected_hash = sha256_hex(body)
        self.assertEqual(headers["x-amz-content-sha256"], expected_hash)
        self.assertIn("content-type", headers)
        self.assertIn("content-type", headers["authorization"].split("SignedHeaders=")[1])

    def test_security_token_included(self):
        headers, _, _, _ = sign_request(
            method="GET",
            host="s3.amazonaws.com",
            port=None,
            path="/bucket/key",
            query={},
            extra_headers={},
            body=b"",
            access_key=ACCESS,
            secret_key=SECRET,
            security_token="session-token-123",
            region="us-east-1",
            service="s3",
            date=FIXED_DATE,
        )
        self.assertEqual(headers["x-amz-security-token"], "session-token-123")
        self.assertIn("x-amz-security-token", headers["authorization"].split("SignedHeaders=")[1])

    def test_different_dates_produce_different_signatures(self):
        _, sig1, _, _ = sign_request(
            method="GET", host="h", port=None, path="/", query={}, extra_headers={},
            body=b"", access_key=ACCESS, secret_key=SECRET, security_token=None,
            region="r", service="s", date=datetime.datetime(2024, 1, 1, tzinfo=datetime.timezone.utc),
        )
        _, sig2, _, _ = sign_request(
            method="GET", host="h", port=None, path="/", query={}, extra_headers={},
            body=b"", access_key=ACCESS, secret_key=SECRET, security_token=None,
            region="r", service="s", date=datetime.datetime(2024, 1, 2, tzinfo=datetime.timezone.utc),
        )
        self.assertNotEqual(sig1, sig2)

    def test_non_standard_port_in_host(self):
        headers, _, _, _ = sign_request(
            method="GET", host="localhost", port=9000, path="/", query={}, extra_headers={},
            body=b"", access_key=ACCESS, secret_key=SECRET, security_token=None,
            region="us-east-1", service="s3", use_tls=False, date=FIXED_DATE,
        )
        self.assertEqual(headers["host"], "localhost:9000")

    def test_default_port_omitted(self):
        headers, _, _, _ = sign_request(
            method="GET", host="localhost", port=80, path="/", query={}, extra_headers={},
            body=b"", access_key=ACCESS, secret_key=SECRET, security_token=None,
            region="us-east-1", service="s3", use_tls=False, date=FIXED_DATE,
        )
        self.assertEqual(headers["host"], "localhost")


class TestPresignUrl(unittest.TestCase):
    def test_structure(self):
        url = presign_url(
            method="GET",
            host="s3.amazonaws.com",
            port=None,
            path="/bucket/key",
            query={},
            headers_to_sign={},
            access_key=ACCESS,
            secret_key=SECRET,
            security_token=None,
            region="us-east-1",
            service="s3",
            expires=3600,
            date=FIXED_DATE,
        )
        self.assertTrue(url.startswith("https://s3.amazonaws.com/bucket/key?"))
        self.assertIn("X-Amz-Algorithm=AWS4-HMAC-SHA256", url)
        self.assertIn("X-Amz-Expires=3600", url)
        self.assertIn("X-Amz-Credential=AKIDEXAMPLE%2F20150830%2Fus-east-1%2Fs3%2Faws4_request", url)
        self.assertIn("X-Amz-Signature=", url)

    def test_unsigned_payload(self):
        import hashlib

        url = presign_url(
            method="GET", host="h", port=None, path="/k", query={}, headers_to_sign={},
            access_key=ACCESS, secret_key=SECRET, security_token=None,
            region="r", service="s3", expires=300, date=FIXED_DATE,
        )
        self.assertIn("X-Amz-SignedHeaders=host", url)

    def test_different_expires_different_url(self):
        u1 = presign_url(
            method="GET", host="h", port=None, path="/k", query={}, headers_to_sign={},
            access_key=ACCESS, secret_key=SECRET, security_token=None,
            region="r", service="s3", expires=300, date=FIXED_DATE,
        )
        u2 = presign_url(
            method="GET", host="h", port=None, path="/k", query={}, headers_to_sign={},
            access_key=ACCESS, secret_key=SECRET, security_token=None,
            region="r", service="s3", expires=600, date=FIXED_DATE,
        )
        self.assertNotEqual(u1, u2)


if __name__ == "__main__":
    unittest.main()
