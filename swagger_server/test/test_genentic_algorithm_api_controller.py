# coding: utf-8

from __future__ import absolute_import

from flask import json
from six import BytesIO

from swagger_server.models.context import Context  # noqa: E501
from swagger_server.models.lineup_list import LineupList  # noqa: E501
from swagger_server.test import BaseTestCase


class TestGenenticAlgorithmAPIController(BaseTestCase):
    """GenenticAlgorithmAPIController integration test stubs"""

    def test_run_genetic_algorithm(self):
        """Test case for run_genetic_algorithm

        Optimize daily fantasy sports lineups through the use of a genetic algorithm
        """
        body = Context()
        response = self.client.open(
            '/v1/runGeneticAlgorithm',
            method='POST',
            data=json.dumps(body),
            content_type='application/json')
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))


if __name__ == '__main__':
    import unittest
    unittest.main()
