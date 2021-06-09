import connexion
import six

from swagger_server.models.context import Context  # noqa: E501
from swagger_server.models.lineup_list import LineupList  # noqa: E501
from swagger_server.models.genetic_algorithm import GeneticAlgorithm  # noqa: E501
from swagger_server import util


def run_genetic_algorithm(body=None):  # noqa: E501
    """Optimize daily fantasy sports lineups through the use of a genetic algorithm

    Run genetic optimization algorithm # noqa: E501

    :param body: Context schema
    :type body: dict | bytes

    :rtype: LineupList
    """
    if connexion.request.is_json:
        context = Context.from_dict(connexion.request.get_json())  # noqa: E501
    return GeneticAlgorithm(context._parameters, context._player_list).run()
