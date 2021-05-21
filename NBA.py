import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy.stats import norm
from math import floor
from random import sample
from GeneticAlgorithm import GeneticAlgorithm
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import cross_val_score


class NBA_GA():
    def __init__(self, population_size, positions, salary_cap):
        self.population_size = population_size
        self.positions = positions
        self.salary_cap = salary_cap
        
    def mergeAllDates(self):
        for game_day in dates:
            dfn_date = 'A_UncleanedData/NBA/HistoricalData_DFN/DFN NBA DK {}.csv'.format(game_day[0])
            ff_date = 'A_UncleanedData/NBA/HistoricalData_FantasyFuel/DFF_NBA_cheatsheet_{}.csv'.format(game_day[1])
            daily_fantasy_nerd_data = pd.read_csv(dfn_date)
            fantasy_fuel_data = pd.read_csv(ff_date)
            merged_file = self.mergeSources(daily_fantasy_nerd_data, fantasy_fuel_data)
            self.saveMergedFile_toCSV(merged_file)
    
    def mergeSources(self, fantasy_nerd, fantasy_fuel):
        fantasy_fuel['Player Name'] = fantasy_fuel['first_name'] + " " + fantasy_fuel['last_name']
        fantasy_fuel.drop(['first_name', 'last_name', 'ppg_actual', 'value_actual', 'slate'] , axis=1, inplace=True)
        fantasy_nerd.drop(['Likes', 'Opp', 'Team', 'Inj', 'PS' ], axis=1, inplace=True)
        merged = pd.merge(left=fantasy_fuel, right=fantasy_nerd, left_on="Player Name", right_on='Player Name')
        merged.set_index('Player Name', inplace=True)
        return merged
    
    def saveMergedFile_toCSV(self, file):
        game_date = file['game_date'].iloc[0]
        file_name = 'B_CleanedData/NBA/{}'.format(game_date)
        file.to_csv(file_name)  
        
    def reduceForProjectionAnalysis(self, file):
        file = file[file['injury_status'] != 'O']
        file = file[file['injury_status'] != 'Q']
        file['FantasyFuelPPGProj'] = file['ppg_projection']
        file['FantasyFuelValueProj'] = file['value_projection']
        file['DFN_PPGProj'] = file['Proj FP']
        file['DFN_ValueProj'] = file['Proj Val']

        cleaned_file = pd.DataFrame()
        cleaned_file['Player Name'] = file['Player Name']
        cleaned_file['Actual FP'] = file['Actual FP']
        cleaned_file['team'] = file['team']
        cleaned_file['Pos'] = file['Pos']
        cleaned_file['Salary'] = file['Salary']
        cleaned_file['DFN_MinProj'] = file['Proj Min']
        cleaned_file['Avg Proj'] = (file['DFN_PPGProj']+file['FantasyFuelPPGProj'])/2
        cleaned_file['Avg Value Proj'] = ((file['DFN_ValueProj']+file['FantasyFuelValueProj'])/2)
        cleaned_file['Avg Skewed Min'] = ((file['L2 Min']+file['L5 Min']+file['S Min'])/3)
        cleaned_file['Avg Skewed FP'] = ((file['L5 FP']+file['S FP']+file['Ceil FP']+file['Floor FP']+cleaned_file['Avg Proj'])/5)
        cleaned_file['Proj Min Enhanced'] = (cleaned_file['Avg Proj'] / cleaned_file['Avg Skewed Min'] ) * cleaned_file['DFN_MinProj']
        cleaned_file = cleaned_file.replace([np.inf, -np.inf], 0)
        cleaned_file = cleaned_file.fillna(0)
#         file.drop(drop_attribs, axis=1, inplace=True)
#         file = file.loc[file['Actual FP'] > 0]
        return cleaned_file
    
    def createBestLineupsForBacktest(self, generations):
        for game_day in dates:
            file_name = 'B_CleanedData/NBA/{}'.format(game_day[1])
            file = self.reduceForProjectionAnalysis(pd.read_csv(file_name))
            GA = GeneticAlgorithm(file, self.population_size, self.positions, self.salary_cap, "Actual FP", generations)
            GA.runMainGA()
            GA.saveBestLineupstoCSV('C_Backtest/NBA/{}', game_day[1])
            
    def createRandomLineupSample(self):
        for game_day in dates:
            file_name = 'B_CleanedData/NBA/{}'.format(game_day[1])
            file = self.reduceForProjectionAnalysis(pd.read_csv(file_name))
            GA = GeneticAlgorithm(file, self.population_size, self.positions, self.salary_cap, "Actual FP", 0)
            GA.randomlyCreateLineups()
            GA.saveBestLineupstoCSV('D_RandomLineups/NBA/{}', game_day[1])
            
            
    def createBestLineupsWithModel(self, generations):
        build_limit = 0
        master_training_data = pd.DataFrame()
        dates.reverse()
        for game_day in dates:
            print(game_day[1])
            file_name = 'B_CleanedData/NBA/{}'.format(game_day[1])
            file = self.reduceForProjectionAnalysis(pd.read_csv(file_name))
            categories = ['Avg Proj', 'DFN_MinProj', 'Proj Min Enhanced', 'Avg Skewed FP', 'Avg Value Proj', 'Actual FP']
            cleaned_file = self.standardize(file, categories)
            if(build_limit > 3):
                file_with_predictions = self.buildRegressionModel(master_training_data, cleaned_file)
                master_training_data = master_training_data.append(cleaned_file.drop(['predictions'], axis=1), sort=False)
                GA = GeneticAlgorithm(file_with_predictions, self.population_size, self.positions, self.salary_cap, "predictions", generations)
                GA.runMainGA()
                GA.saveBestLineupstoCSV('E_BestCreatedLineups/NBA/{}', game_day[1])
            else:
                master_training_data = master_training_data.append(cleaned_file, sort=False)
            build_limit = build_limit + 1
            
            
    def standardize(self, df, categories):
        result = df.copy()
        for feature_name in categories:
            mean_value = df[feature_name].mean()
            std_value = df[feature_name].std()
            result[feature_name + ' Stan'] = ((df[feature_name] - mean_value) / (std_value))
        result = result.replace([np.inf, -np.inf], 0)
        result = result.fillna(0)
        return result
        
    def buildRegressionModel(self, master_training_data, cleaned_file):
        drop_attribs = ['Player Name','team','Pos','Salary', 'Actual FP', 'Actual FP Stan', 'Avg Proj', 'DFN_MinProj', 'Proj Min Enhanced', 'Avg Skewed FP', 'Avg Skewed Min', 'Avg Value Proj']
        features = master_training_data.drop(drop_attribs, axis=1).copy()
        labels = master_training_data['Actual FP Stan'].copy()
        reg = LinearRegression()
        reg.fit(features, labels)
        scores = cross_val_score( reg, features, labels, scoring='neg_mean_squared_error', cv=10)
        rmse_scores = np.sqrt(-scores)
        self.display_scores(rmse_scores, 'Actual FP')
        cleaned_file['predictions'] = reg.predict(cleaned_file.drop(drop_attribs, axis=1).copy())
        return cleaned_file
    
    def display_scores(self, scores, label_type):
        print("*", label_type)
        print('Scores:', scores)
        print('Mean:' ,scores.mean())
        print('Std:', scores.std()) 
            
dates = [
    ['3_11', '2020-03-11'],
    ['3_10', '2020-03-10'],
    ['3_9', '2020-03-09'],
    ['3_8', '2020-03-08'],
    ['3_7', '2020-03-07'],
    ['3_6', '2020-03-06'],
    ['3_5', '2020-03-05'],
    ['3_4', '2020-03-04'],
    ['3_3', '2020-03-03'],
    ['3_2', '2020-03-02'],
    ['3_1', '2020-03-01'],
    ['2_29', '2020-02-29'],
    ['2_28', '2020-02-28'],
    ['2_27', '2020-02-27'],
    ['2_26', '2020-02-26'],
    ['2_25', '2020-02-25'],
    ['2_24', '2020-02-24'],
    ['2_23', '2020-02-23'],
    ['2_22', '2020-02-22'],
    ['2_21', '2020-02-21'],
    ['2_20', '2020-02-20'],
    ['2_13', '2020-02-13'],
    ['2_12', '2020-02-12'],
    ['2_11', '2020-02-11'],
    ['2_10', '2020-02-10'],
    ['2_9', '2020-02-09'],
    ['2_8', '2020-02-08'],
    ['2_7', '2020-02-07'],
    ['2_6', '2020-02-06'],
    ['2_5', '2020-02-05'],
    ['2_4', '2020-02-04'],
    ['2_3', '2020-02-03'],
    ['2_2', '2020-02-02'],
    ['2_1', '2020-02-01'],
    ['1_31', '2020-01-31'],
    ['1_30', '2020-01-30'],
    ['1_29', '2020-01-29'],
    ['1_28', '2020-01-28'],
    ['1_27', '2020-01-27'],
    ['1_26', '2020-01-26'],
    ['1_25', '2020-01-25'],
    ['1_24', '2020-01-24'],
    ['1_23', '2020-01-23'],
    ['1_22', '2020-01-22'],
    ['1_20', '2020-01-20'],
    ['1_19', '2020-01-19'],
    ['1_18', '2020-01-18'],
    ['1_17', '2020-01-17'],
    ['1_16', '2020-01-16'],
    ['1_15', '2020-01-15'],
    ['1_14', '2020-01-14'],
    ['1_13', '2020-01-13'],
    ['1_12', '2020-01-12'],
    ['1_11', '2020-01-11'],
    ['1_10', '2020-01-10'],
    ['1_9', '2020-01-09'],
    ['1_8', '2020-01-08'],
    ['1_7', '2020-01-07'],
    ['1_6', '2020-01-06'],
    ['1_5', '2020-01-05'],
    ['1_4', '2020-01-04'],
    ['1_3', '2020-01-03'],
    ['1_2', '2020-01-02'],
    ['1_1', '2020-01-01'],
    ['12_31', '2019-12-31'],
    ['12_30', '2019-12-30'],
    ['12_29', '2019-12-29'],
    ['12_28', '2019-12-28'],
    ['12_27', '2019-12-27'],
    ['12_26', '2019-12-26'],
    ['12_25', '2019-12-25'],
    ['12_23', '2019-12-23'],
    ['12_22', '2019-12-22'],
    ['12_21', '2019-12-21'],
    ['12_20', '2019-12-20'],
    ['12_19', '2019-12-19'],
    ['12_18', '2019-12-18'],
    ['12_17', '2019-12-17'],
    ['12_16', '2019-12-16'],
    ['12_15', '2019-12-15'],
    ['12_14', '2019-12-14'],
    ['12_13', '2019-12-13'],
    ['12_12', '2019-12-12'],
    ['12_11', '2019-12-11'],
    ['12_10', '2019-12-10'],
    ['12_9', '2019-12-09'],
    ['12_8', '2019-12-08'],
    ['12_7', '2019-12-07'],
    ['12_6', '2019-12-06'],
    ['12_5', '2019-12-05'],
    ['12_4', '2019-12-04'],
    ['12_3', '2019-12-03'],
    ['12_2', '2019-12-02'],
    ['12_1', '2019-12-01'],
    ['11_30', '2019-11-30'],
    ['11_29', '2019-11-29'],
    ['11_27', '2019-11-27'],
    ['11_26', '2019-11-26'],
    ['11_25', '2019-11-25'],
    ['11_24', '2019-11-24'],
    ['11_23', '2019-11-23'],
    ['11_22', '2019-11-22'],
    ['11_21', '2019-11-21'],
    ['11_20', '2019-11-20'],
    ['11_19', '2019-11-19'],
    ['11_18', '2019-11-18'],
    ['11_17', '2019-11-17'],
    ['11_16', '2019-11-16'],
    ['11_15', '2019-11-15'],
    ['11_14', '2019-11-14'],
    ['11_13', '2019-11-13'],
    ['11_12', '2019-11-12'],
    ['11_11', '2019-11-11'],
    ['11_10', '2019-11-10'],
    ['11_9', '2019-11-09'],
    ['11_8', '2019-11-08'],
    ['11_7', '2019-11-07'],
    ['11_6', '2019-11-06'],
    ['11_5', '2019-11-05'],
    ['11_4', '2019-11-04'],
    ['11_3', '2019-11-03'],
    ['11_2', '2019-11-02'],
    ['11_1', '2019-11-01'],
    ['10_31', '2019-10-31'],
    ['10_30', '2019-10-30'],
    ['10_29', '2019-10-29'],
    ['10_28', '2019-10-28'],
    ['10_27', '2019-10-27'],
    ['10_26', '2019-10-26'],
    ['10_25', '2019-10-25'],
    ['10_24', '2019-10-24'],
    ['10_23', '2019-10-23'],
    ['10_22', '2019-10-22'],   
]
        
