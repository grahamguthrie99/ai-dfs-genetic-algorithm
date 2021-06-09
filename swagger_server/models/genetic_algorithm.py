import random

class GeneticAlgorithm():
    def __init__(self, parameters, player_list):
        self.configuration = self.configure(parameters)
        self.player_position_table = self.mapPlayersToPosition(player_list)
    
    def configure(self, parameters):
        sports = {
            "nba" : {
                "draftkings": {
                    "positions" : ["PG", "SG", "SF", "PF", "C", "G", "F", "Util"], 
                    "salary_cap" : 500000
                },
                "fanduel" : {
                    "positions" : ["PG", "PG", "SG", "SG", "SF", "SF", "PF", "PF", "C"], 
                    "salary_cap" : 600000

                }
            }, 
            "mlb" : {
                "draftkings": {
                    "positions" : ["P", "P", "C", "1B", "2B", "3B", "SS", "OF", "OF","OF"], 
                    "salary_cap" : 500000
                },
                "fanduel" : {
                    "positions" : ["P", "C/1B", "2B", "SS", "3B", "OF", "OF", "OF", "Util"], 
                    "salary_cap" : 35000

                }
            }, 
        }    
        params = {}
        params = sports[parameters.sport.lower()][parameters.platform.lower()]
        params['population_size'] = parameters.population_size
        params['generation_count'] = parameters.generation_count
        return params

    def mapPlayersToPosition(self, player_list):
        position_table = {}
        for position in self.configuration['positions']: 
            if(position != 'Util'):
                position_table[position] = list(filter(lambda player: position in player._pos, player_list))
            else: 
                position_table['Util'] = player_list
        return position_table 

    def createLineup(self):
        lineup = []
        for position in self.player_position_table.keys():
            lineup.append(random.choice(self.player_position_table[position]))
        return lineup

    def validateLineup(self, lineup):
        all_unique_players = len(list(set([player._name for player in lineup]))) == len(lineup)
        teams_represented = len(list(set([player._team for player in lineup]))) > 1
        salary_under_cap = sum([int(player._salary) for player in lineup]) < self.configuration['salary_cap']
        return all_unique_players and teams_represented and salary_under_cap

    def createPopulation(self, limit):
        lineups = []
        while(len(lineups) < limit):
            lineup = self.createLineup()
            if(self.validateLineup(lineup)):
                lineups.append(lineup)
        return lineups

    def evaluateFitness(self, lineup):
        return sum([float(player._ppg_proj) for player in lineup])

    def performSelection(self, population):
        selected_population = population[:10]
        return selected_population

    def createChildren(self, selected_population):
        parents = [player for lineup in selected_population for player in lineup]
        master_position_table = self.player_position_table
        self.player_position_table = self.mapPlayersToPosition(parents)
        children = self.createPopulation(10)
        self.player_position_table = master_position_table
        return children

    def run(self):
        initial_population = self.createPopulation(self.configuration['population_size'])
        return self.performGeneration(self.configuration['generation_count'], initial_population)
    
    def performGeneration(self, generation_count, population):
        if(generation_count == 0):
            return population
        sorted_population = sorted(population, key=lambda lineup: self.evaluateFitness(lineup), reverse=True)
        selected_population = self.performSelection(sorted_population)
        children = self.createChildren(selected_population)
        random_population = self.createPopulation(len(population) - len(selected_population) - len(children))
        return self.performGeneration(generation_count-1, selected_population + children + random_population)