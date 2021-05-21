import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy.stats import norm
from math import floor
from random import sample
from sklearn.linear_model import LinearRegression
    

class GeneticAlgorithm():
    def __init__(self, file, population_size, positions, salary_cap, players, fitness_key, generations, util_file):
        self.file = file
        self.util = util_file
        self.population_size = population_size
        self.positions = positions #array
        self.players = players
        self.salary_cap = salary_cap
        self.player_dict = self.createPlayerDict()
        self.population = []
        self.fitness_key = fitness_key
        self.generations = generations
        
    def createPlayerDict(self):
        player_dict = dict()
        for position in self.positions:
            player_dict[position] =  self.file.loc[self.file['Pos'].str.contains(self.positions[position])]
        player_dict['util'] = self.util
        return player_dict
        
    def runMainGA(self):
        self.population = self.createRandomPopulation(self.population_size)  
        counter = 0
        while(counter<self.generations):
            
            self.sortFitest()
            print(len(self.population))
            self.createNextGeneration() 
            
            self.population.extend(self.createRandomPopulation(self.population_size - len(self.population)))
            counter = counter+1
            print(len(self.population))
        
        self.sortFitest()
        print("*****************")
        
    def createRandomPopulation(self, limit):
        counter = 0
        lineups = []
        while(counter<limit):
            lineup = pd.DataFrame()
            for position in self.player_dict.values():
                lineup = lineup.append(position.sample(n=1))
           
            if(self.verifyLineup(lineup)):
                lineups.append(lineup)
                counter = counter + 1
        return lineups


    def verifyLineup(self, lineup):
        enough_represented_teams = len(set(lineup['Team'].tolist()))>=2
        under_salary_cap = lineup['Salary'].sum() <= self.salary_cap
        all_unique_players = len(set(lineup['Player Name'].tolist())) == self.players
        if enough_represented_teams and under_salary_cap and all_unique_players:
            return True
        else:
            return False
    
    def fitnessFunction(self, lineup):
        return lineup[self.fitness_key].sum() 
    
    def sortFitest(self): 
        self.population = sorted(self.population,key=lambda lineup: lineup[self.fitness_key].sum(), reverse=True)
        self.eliminateDuplicates()
    
    def eliminateDuplicates(self):
        unique_lineups = set()
        unique_population = []
        for lineup in self.population:
            lineup_set = set()
            for player in lineup['Player Name'].tolist():
                lineup_set.add(player)

            if(not lineup_set.issubset(unique_lineups)):  
                unique_population.append(lineup)
                unique_lineups = unique_lineups.union(lineup_set)
        self.population = unique_population
        
            
    def createNextGeneration(self):
        selected_population = self.performSelection()
        children = self.performCrossover(selected_population)
        new_generation = self.population[:len(self.population)-10]
        new_generation.extend(children)
        self.population = new_generation
    
    def performSelection(self):
        selected_population = self.population[:1]
#         selected_population.extend(sample(self.population[1:5], 3))
#         selected_population.extend(sample(self.population[10:20], 4))
        selected_population.extend(sample(self.population, 2))
        return selected_population
    
    def performCrossover(self, selected_population):
        children = []
        parents = selected_population
        children = self.mate(parents) 
        return children

    def mate(self, _parents):
        parents = pd.concat(sample(_parents, 3))
        parent_dict = dict()
        for position in self.positions:
            parent_dict[position] = parents.loc[parents['Pos'].str.contains(self.positions[position])]
        util_pos = set(self.util['Pos'].to_list())
        parent_dict['util'] = parents[parents['Pos'].isin(util_pos)]
        children = []
        while(len(children) < 10):
            child_lineup = _parents[0].append(_parents[1])
            while(not self.verifyLineup(child_lineup)):
                child_lineup = pd.DataFrame()
                for position in parent_dict.values():
                    child_lineup = child_lineup.append(position.sample(n=1))
            children.append(child_lineup)
        return children
    
    def resetIndicies(self, file):
        for lineup in file:
            lineup.reset_index(drop=True, inplace=True)
        return file

    def dropLowScoringLineups(self, file):
        drop_level = file.groupby(['Lineup Num'])[self.fitness_key].sum().mean() - file.groupby(['Lineup Num'])[self.fitness_key].sum().std()
       
        group = file.groupby(['Lineup Num'])
#         return group.filter(lambda x: x[self.fitness_key].sum() > drop_level)
        return file
    
    def saveBestLineupstoCSV(self, file_name, date):
        key = np.arange(len(self.resetIndicies(self.population)))
        file_name = file_name.format(date)
        new_file = self.dropLowScoringLineups(pd.concat(self.population, keys=key, names=['Lineup Num']))
        new_file.to_csv(file_name)

    def randomlyCreateLineups(self):
        self.population = self.createRandomPopulation(self.population_size)
        














        








