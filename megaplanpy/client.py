#-------------------------------------------------------------------------------
# Name:        client
# Purpose:
#
# Author:      Sergey Pikhovkin (s@pikhovkin.ru)
#
# Created:     10.02.2011
# Copyright:   (c) Sergey Pikhovkin 2011
# Licence:     <MIT>
#-------------------------------------------------------------------------------
#!/usr/bin/env python
# -*- coding: UTF-8 -*-

import httplib
from urlparse import urlparse, ParseResult
from urllib import urlencode


class UnsupportedScheme(httplib.HTTPException):
    pass


class APIClient(object):
    """
    """
    debug = False

    HEADERS = {
        'User-Agent': 'Mozilla/5.0 (Windows; U; Windows NT 6.0; ru; rv:1.9.1.7) Gecko/20091221 Firefox/3.5.7',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'ru,en-us;q=0.7,en;q=0.3',
        'Accept-Encoding': 'deflate',
        'Accept-Charset': 'utf-8;q=0.7,*;q=0.7',
        'Keep-Alive': '300',
        'Connection': 'keep-alive'
    }

    def __init__(self):
        self.Status = int(0)
        self.Reason = str()
    # /

    def _get_scheme(self, uri):
        if not uri.scheme or (uri.scheme == 'http'):
            return 'http'
        elif uri.scheme == 'https':
            return 'https'
        else:
            raise UnsupportedScheme(
                '"{0}" is not supported.'.format(uri.scheme))
    # /

    def _get_port(self, uri):
        host = ''
        port = None
        host_parts = uri.netloc.split(':')
        if host_parts[0]:
            host = host_parts[0]
        if len(host_parts) > 1:
            port = int(host_parts[1])
            if not port:
                port = None
        return (host, port)
    # /

    def _get_connection(self, uri):
        """Opens a socket connection to the server to set up an HTTP request.

        Args:
          uri: The full URL for the request as a Uri object.
        """
        scheme = self._get_scheme(uri)
        host, port = self._get_port(uri)
        connection = None
        if scheme == 'https':
            connection = httplib.HTTPSConnection(host, port=port)
        else:
            connection = httplib.HTTPConnection(host, port)
        return connection
    # /

    def _http_request(self, uri, params='', headers={}):
        if isinstance(uri, (str, unicode)):
            uri = urlparse(uri)
        else:
            raise TypeError('Invalid URL')

        method = 'GET'
        if params:
            method = 'POST'

        connection = self._get_connection(uri)

        if self.debug:
            connection.debuglevel = 1

        query = uri.path
        if uri.query:
            query += '?{0}'.format(uri.query)
        connection.putrequest(method, query)

        # Send the HTTP headers.
        for name, value in headers.iteritems():
            connection.putheader(name, value)

        if params: # POST
            if 'Content-type' not in headers:
                connection.putheader('Content-type',
                    'application/x-www-form-urlencoded')
            if 'Content-length' not in headers:
                connection.putheader('Content-length', str(len(params)))

        connection.endheaders()

        if params:
            connection.send(params)

        return connection.getresponse()
    # /

    def Request(self, url, params={}, headers={}):
        """
        """
        if not headers:
            headers = self.HEADERS

        if params:
            params = urlencode(params)

        response = self._http_request(url, params, headers)
        self.Status = response.status
        self.Reason = response.reason

        return response.read()
    # /

# / class APIClient(object):


def main():
    pass

if __name__ == '__main__':
    main()
