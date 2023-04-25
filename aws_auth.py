import binascii
import hmac
import hashlib
import time

import urequests as requests


def sign(key, msg):
    """
    Copied from https://docs.aws.amazon.com/general/latest/gr/sigv4-signed-request-examples.html
    """
    return hmac.digest(key, msg.encode('utf-8'), hashlib.sha256)


def getSignatureKey(key, dateStamp, regionName, serviceName):
    """
    Copied from https://docs.aws.amazon.com/general/latest/gr/sigv4-signed-request-examples.html
    """
    kDate = sign(('AWS4' + key).encode('utf-8'), dateStamp)
    kRegion = sign(kDate, regionName)
    kService = sign(kRegion, serviceName)
    kSigning = sign(kService, 'aws4_request')
    return kSigning


class AWSRequestsAuth:
    """
    Auth class that allows us to connect to AWS services
    via Amazon's signature version 4 signing process

    Adapted from https://docs.aws.amazon.com/general/latest/gr/sigv4-signed-request-examples.html
    """

    def __init__(self,
                 aws_access_key,
                 aws_secret_access_key,
                 aws_host,
                 aws_region,
                 aws_service,
                 aws_token=None):
        """
        Example usage for talking to an AWS Elasticsearch Service:

        AWSRequestsAuth(aws_access_key='YOURKEY',
                        aws_secret_access_key='YOURSECRET',
                        aws_host='search-service-foobar.us-east-1.es.amazonaws.com',
                        aws_region='us-east-1',
                        aws_service='es',
                        aws_token='...')

        The aws_token is optional and is used only if you are using STS
        temporary credentials.
        """
        self.aws_access_key = aws_access_key
        self.aws_secret_access_key = aws_secret_access_key
        self.aws_host = aws_host
        self.aws_region = aws_region
        self.service = aws_service
        self.aws_token = aws_token

    def get_aws_request_headers(self, method, url, rbody):
        return self._get_aws_request_headers(method=method, url=url, rbody=rbody,
                                            aws_access_key=self.aws_access_key,
                                            aws_secret_access_key=self.aws_secret_access_key,
                                            aws_token=self.aws_token)

    def _get_aws_request_headers(self, method, url, rbody, aws_access_key, aws_secret_access_key, aws_token):
        """
        Returns a dictionary containing the necessary headers for Amazon's
        signature version 4 signing process. An example return value might
        look like

            {
                'Authorization': 'AWS4-HMAC-SHA256 Credential=YOURKEY/20160618/us-east-1/es/aws4_request, '
                                 'SignedHeaders=host;x-amz-date, '
                                 'Signature=ca0a856286efce2a4bd96a978ca6c8966057e53184776c0685169d08abd74739',
                'x-amz-date': '20160618T220405Z',
            }
        """
        # Create a date for headers and the credential string
        t = time.gmtime()
        amzdate = f'{t[0]}{t[1]:02d}{t[2]:02d}T{t[3]:02d}{t[4]:02d}{t[5]:02d}Z'
        datestamp = f'{t[0]}{t[1]:02d}{t[2]:02d}'  # Date w/o time for credential_scope

        canonical_uri = '/' # AWSRequestsAuth.get_canonical_path(r)

        canonical_querystring = '' # AWSRequestsAuth.get_canonical_querystring(r)

        # Create the canonical headers and signed headers. Header names
        # and value must be trimmed and lowercase, and sorted in ASCII order.
        # Note that there is a trailing \n.
        canonical_headers = ('host:' + self.aws_host + '\n' +
                             'x-amz-date:' + amzdate + '\n')
        if aws_token:
            canonical_headers += 'x-amz-security-token:' + aws_token + '\n'

        # Create the list of signed headers. This lists the headers
        # in the canonical_headers list, delimited with ";" and in alpha order.
        # Note: The request can include any headers; canonical_headers and
        # signed_headers lists those that you want to be included in the
        # hash of the request. "Host" and "x-amz-date" are always required.
        signed_headers = 'host;x-amz-date'
        if aws_token:
            signed_headers += ';x-amz-security-token'

        # Create payload hash (hash of the request body content). For GET
        # requests, the payload is an empty string ('').
        body = rbody if rbody else bytes()
        try:
            body = body.encode('utf-8')
        except (AttributeError, UnicodeDecodeError):
            # On py2, if unicode characters in present in `body`,
            # encode() throws UnicodeDecodeError, but we can safely
            # pass unencoded `body` to execute hexdigest().
            #
            # For py3, encode() will execute successfully regardless
            # of the presence of unicode data
            body = body

        payload_hash = binascii.hexlify(hashlib.sha256(body).digest()).decode('utf-8')

        # Combine elements to create create canonical request
        canonical_request = (method + '\n' + canonical_uri + '\n' +
                             canonical_querystring + '\n' + canonical_headers +
                             '\n' + signed_headers + '\n' + payload_hash)

        # Match the algorithm to the hashing algorithm you use, either SHA-1 or
        # SHA-256 (recommended)
        algorithm = 'AWS4-HMAC-SHA256'
        credential_scope = (datestamp + '/' + self.aws_region + '/' +
                            self.service + '/' + 'aws4_request')
        string_to_sign = (algorithm + '\n' + amzdate + '\n' + credential_scope +
                          '\n' + binascii.hexlify(hashlib.sha256(canonical_request.encode('utf-8')).digest()).decode('utf-8'))

        # Create the signing key using the function defined above.
        signing_key = getSignatureKey(aws_secret_access_key,
                                      datestamp,
                                      self.aws_region,
                                      self.service)

        # Sign the string_to_sign using the signing_key
        string_to_sign_utf8 = string_to_sign.encode('utf-8')
        signature = binascii.hexlify(hmac.digest(signing_key,
                             string_to_sign_utf8,
                             hashlib.sha256)).decode('utf-8')

        # The signing information can be either in a query string value or in
        # a header named Authorization. This code shows how to use a header.
        # Create authorization header and add to request headers
        authorization_header = (algorithm + ' ' + 'Credential=' + aws_access_key +
                                '/' + credential_scope + ', ' + 'SignedHeaders=' +
                                signed_headers + ', ' + 'Signature=' + signature)

        headers = {
            'Authorization': authorization_header,
            'x-amz-date': amzdate,
            'x-amz-content-sha256': payload_hash
        }
        if aws_token:
            headers['X-Amz-Security-Token'] = aws_token
        return headers
