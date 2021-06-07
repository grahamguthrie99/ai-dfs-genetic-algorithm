import random

class GeneticAlgorithm():
    def __init__(self, population_size, generation_count, positions, fitness_key, player_list):
        self.population_size = population_size
        self.generation_count = generation_count
        self.positions = positions 
        self.fitness_key = fitness_key
        self.player_position_table = self.mapPlayersToPosition(player_list)

    def mapPlayersToPosition(self, player_list):
        position_table = {}
        for position in self.positions: 
            if(position != 'Util'):
                position_table[position] = list(filter(lambda player: position in player['pos'], player_list))
            else: 
                position_table['Util'] = player_list
        return position_table 

    def createLineup(self):
        lineup = []
        for position in self.player_position_table.keys():
            lineup.append(random.choice(self.player_position_table[position]))
        return lineup

    def validateLineup(self, lineup):
        all_unique_players = len(list(set([player['name'] for player in lineup]))) == len(lineup)
        teams_represented = len(list(set([player['team'] for player in lineup]))) > 1
        salary_under_cap = sum([int(player['salary']) for player in lineup]) < 50000
        return all_unique_players and teams_represented and salary_under_cap

    def createPopulation(self, limit):
        lineups = []
        while(len(lineups) < limit):
            lineup = self.createLineup()
            if(self.validateLineup(lineup)):
                lineups.append(lineup)
        return lineups

    def evaluateFitness(self, lineup):
        return sum([float(player[self.fitness_key]) for player in lineup])

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
        initial_population = self.createPopulation(self.population_size)
        return self.performGeneration(self.generation_count, initial_population)
    
    def performGeneration(self, generation_count, population):
        if(generation_count == 0):
            return population
        sorted_population = sorted(population, key=lambda lineup: self.evaluateFitness(lineup), reverse=True)
        print(sum([float(player[self.fitness_key]) for player in sorted_population[0]]))
        selected_population = self.performSelection(sorted_population)
        children = self.createChildren(selected_population)
        random_population = self.createPopulation(len(population) - len(selected_population) - len(children))
        return self.performGeneration(generation_count-1, selected_population + children + random_population)















        








