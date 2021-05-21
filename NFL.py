import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from GeneticAlgorithm import GeneticAlgorithm

class NFL_GA():
    def __init__(self, week, population_size, positions, salary_cap):
        self.week_number = week
        self.population_size = population_size
        self.positions = positions
        self.salary_cap = salary_cap
        self.week = self.pullWeekData(week)
        self.file = None
        self.filters = self.getFilters()
        self.rank_criteria = {
            'Cat 1' : ['Proj FP', 4],
            'Cat 2' : ['Salary', 4], 
            'Cat 3' : ['Proj Att', 4]
        }
        self.expected_values = {
            'QB' : .565,
            'WR' : .649,
            'TE' : .487,
            'RB' : .514,
            'D' : .15
        }
        
    def createBestLineupsWithModel(self, generations):
        self.file = self.cleanFilterRankWeek()
        util_pos = set(['WR', 'TE', 'RB'])
        util_file = self.file[self.file['Pos'].isin(util_pos)]
        GA = GeneticAlgorithm(self.file, self.population_size, self.positions,  self.salary_cap, 9,"Total", generations, util_file)
        GA.runMainGA()
        GA.saveBestLineupstoCSV('E_BestCreatedLineups/NFL/{}', self.week_number)
        
    def cleanFilterRankWeek(self):
        df = self.filterPlayerPool()
        df = self.conductRankings(df.copy())
        final_df = self.assignExpectedValues(df.copy())
        return final_df
        
    def filterPlayerPool(self):
        groups = self.week.groupby(by='Pos')
        filtered_positions = []
        for position in self.filters: 
            for category in self.filters[position]:
                for key in category:
                    drop_level = category[key]
                    frame = groups.get_group(position)
                    filtered =  frame[frame[key] >  drop_level]
                    filtered_positions.append(filtered)
        cleaned = pd.concat(filtered_positions)
        cleaned = cleaned[~cleaned.index.duplicated(keep='first')]
        return cleaned
    
    
    def filterPlayerPoolRe(self,df):
        groups = df.groupby(by='Pos')
        filtered_positions = []
        for position in self.filters: 
            for category in self.filters[position]:
                for key in category:
                    drop_level = category[key]
                    frame = groups.get_group(position)
                    filtered =  frame[frame[key] >  drop_level]
                    filtered_positions.append(filtered)
        cleaned = pd.concat(filtered_positions)
        cleaned = cleaned[~cleaned.index.duplicated(keep='first')]
        return cleaned
    
    def createRanking(self, df, category, to_be_ranked, weight):
        print(category)
        df[category] = df.groupby(by='Pos')[to_be_ranked].transform(
                     lambda x: pd.qcut(x.rank(method='first'), weight, labels=False))
        return df

    def conductRankings(self, df): 
        for criteria in self.rank_criteria:
            df = self.createRanking(df, criteria, self.rank_criteria[criteria][0], self.rank_criteria[criteria][1])
        df['Total'] = df['Cat 1'] + df['Cat 2'] + df['Cat 3']
        return df
    
    def assignExpectedValues(self, df):
        groups = df.groupby(by='Pos')
        frames = []
        for position in self.expected_values:
            frame = groups.get_group(position)
            frame['Total'] = frame['Total'] * self.expected_values[position]
            frames.append(frame)
        return pd.concat(frames)
           
    def getFilters(self):
        season = self.pullFullSeasonData()
        filters = None
        filters = self.getPositionFilters(season) 
        return filters
    
    
    def pullFullSeasonData(self):
        offense = self.pullFullOffenseSeasonData()
        defense = self.pullFullDefenseSeasonData()
        offense = self.formatOffenseForMerge(offense)
        defense = self.formatDefenseForMerge(defense)
        return pd.concat([offense, defense])
    
    def pullWeekData(self, week):
        offense_file = 'A_UncleanedData/NFL/DFN NFL Offense DK Week {}.csv'.format(week)
        defense_file = 'A_UncleanedData/NFL/DFN NFL Defense DK Week {}.csv'.format(week)
        offense = pd.read_csv(offense_file)
        defense = pd.read_csv(defense_file)
        teams = set(['MIA','DEN', 'NYJ', 'LAC','GB', 'IND', 'DAL', 'MIN'])
        offense = offense[offense['Team'].isin(teams)]
        defense = defense[defense['Team'].isin(teams)]
        offense = self.formatOffenseForMerge(offense)
        defense = self.formatDefenseForMerge(defense)
        return pd.concat([offense, defense])
    

    def pullFullDefenseSeasonData(self):
        weeks= [2,3,4,5,6,7,8,9,10]
        dates = pd.date_range(start='9/20/2020', periods=9, freq="W")
        weekly_data = []
        for week in weeks:
            stats = 'A_UncleanedData/NFL/DFN NFL Defense DK Week {}.csv'.format(week)
            file = pd.read_csv(stats)
            file['Week'] = pd.to_datetime(dates[week-2])
            weekly_data.append(file)

        season = pd.concat(weekly_data)
        season = season.set_index(['Week', 'Player Name'])
        return season

    def pullFullOffenseSeasonData(self):
        weeks= [2,3,4,5,6,7,8,9, 10]
        dates = pd.date_range(start='9/20/2020', periods=9, freq="W")
        weekly_data = []
        for week in weeks:
            stats = 'A_UncleanedData/NFL/DFN NFL Offense DK Week {}.csv'.format(week)
            file = pd.read_csv(stats)
            file['Week'] = pd.to_datetime(dates[week-2])
            weekly_data.append(file)

        season = pd.concat(weekly_data)
        season = season.set_index(['Week', 'Player Name'])
        return season
    
    def formatOffenseForMerge(self, df):
        df=df[df['Proj FP'] > 0]
        df['Inj'].fillna('G', inplace=True)
        df['Likes'].fillna(0, inplace=True)
        df['Proj Pass Att'].fillna(0, inplace=True)
        df['Proj Rush Att'].fillna(0, inplace=True)
        df['Proj Targets'].fillna(0, inplace=True)
        df['Projected Usage'].fillna(0, inplace=True)
        df['Proj Att'] = df['Proj Pass Att'] + df['Proj Rush Att'] + df['Proj Targets']
        df = df[df['Inj'] == 'G']
        drop_attribs=[
            'Defense Pass Yds/G', 
            'Defense Rush Yds/G',
            'DvP', 
            'L3 Pass Att', 
            'S Pass Att', 
            'L3 Rush Att', 
            'S Rush Att',
            'Yards Per Rush Att',
            'L3 Targets',
            'S Targets', 
            'Red Zone Targets',
            'Yards Per Target', 
            'L16 FP', 
            'S FP',
            'Inj',
            'Opp',
            'Vegas Pts',
            'Vegas Spread',
            'Red Zone Pass Att',
            'Yards Per Pass Att',
            'Red Zone Rush Att',
            'Projected Usage', 
            'L3 FP', 
            'Floor FP', 
            'Ceil FP',
            'Proj Pass Att',
            'Proj Rush Att', 
            'Proj Targets',
            'Inj'
        ]
        df.drop(drop_attribs, inplace=True, axis=1)
        return df
    
    def formatDefenseForMerge(self, df):
        df=df[df['Proj FP'] > 0]
        df['Likes'].fillna(0, inplace=True)
        df['Proj Att'] = 1/df['Vegas PtsA'] * 100
        drop_attribs = [
            'Vegas PtsA',
            'Opp',
            'Vegas Spread',
            'Sacks Allowed by Offense', 
            'Fumbles Allowed by Offense',
            'Ints Allowed by Offense', 
            'Offense Pass Yds/G', 'Offense Rush Yds/G',
            'Points Scored by Offense', 
            'FP Allowed by Offense', 
            'L3 FP', 
            'L16 FP',
            'S FP', 
            'Floor FP', 
            'Ceil FP', 

        ]
        df.drop(drop_attribs, inplace=True, axis=1)
        return df
    
    def getPositionFilters(self, df):
        positional_filters = {
        'QB' : ['Proj FP', 'Salary', 'Proj Val',  'Proj Att'],
        'WR' : ['Proj FP', 'Salary', 'Proj Val', 'Proj Att'],
        'TE' : ['Proj FP', 'Salary', 'Proj Val', 'Proj Att'],
        'RB' : ['Proj FP', 'Salary', 'Proj Val', 'Proj Att'],
        'D' : ['Proj FP', 'Salary', 'Proj Val', 'Proj Att'], 
        }
        df['Pos Quants'] = df.groupby(by='Pos')['Actual FP'].transform(
                     lambda x: pd.qcut(x.rank(method='first'), 5, labels=False))
        groups = df.groupby(by='Pos')
        filter_levels = dict()
        for position in positional_filters: 
            drop_levels = []
            for category in positional_filters[position]:
                category_level = dict()
                drop_level = groups.get_group(position).groupby(by='Pos Quants').get_group(4)[category].describe()['25%']
                category_level[category] = drop_level
                drop_levels.append(category_level)
            filter_levels[position] = drop_levels
        return filter_levels

    

        

            
