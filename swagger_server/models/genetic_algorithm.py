import random

class GeneticAlgorithm():
    def __init__(self, parameters, player_list):
        self.configuration = self.configure(parameters)
        self.player_position_table = self.mapPlayersToPosition(self.normalizeProjectionValues(player_list))
    
    def configure(self, parameters):
        sports = {
            "nba" : {
                "draftkings": {
                    "positions" : ["PG", "SG", "SF", "PF", "C", "G", "F", "Util"], 
                    "salary_cap" : 500000
                },
                "fanduel" : {
                    "positions" : ["PG1", "PG2", "SG1", "SG2", "SF1", "SF2", "PF1", "PF2", "C"], 
                    "salary_cap" : 600000

                }
            }, 
            "mlb" : {
                "draftkings": {
                    "positions" : ["P1", "P2", "C", "1B", "2B", "3B", "SS", "OF1", "OF2","OF3"], 
                    "salary_cap" : 500000
                },
                "fanduel" : {
                    "positions" : ["P", "C/1B", "2B", "SS", "3B", "OF1", "OF2", "OF3", "Util"], 
                    "salary_cap" : 35000

                }
            }, 
        }    
        params = {}
        params = sports[parameters.sport.lower()][parameters.platform.lower()]
        params['population_size'] = parameters.population_size
        params['generation_count'] = parameters.generation_count
        return params

    def normalizeProjectionValues(self, player_list): 
        positions = list({player._pos for player in player_list})
        min_max_pos_lookup = {} 
        for position in positions: 
            position_min_max = {} 
            position_list  = list(filter(lambda player: player._pos in position, player_list))
            position_min_max["min"] = min(float(player._ppg_proj) for player in position_list)
            position_min_max["max"] = max(float(player._ppg_proj) for player in position_list)
            min_max_pos_lookup[position] = position_min_max
        for player in player_list: 
                player._fitness_score = ( float(player._ppg_proj) - min_max_pos_lookup[player._pos]["min"] ) / (min_max_pos_lookup[player._pos]["max"] - min_max_pos_lookup[player._pos]["min"])
        return player_list
        

    def mapPlayersToPosition(self, player_list):
        position_table = {}
        for position in self.configuration['positions']: 
            if(position != 'Util'):
                position_table[position] = list(filter(lambda player: player._pos in position or position in player._pos, player_list))
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
        return sum([float(player._fitness_score) for player in lineup])

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