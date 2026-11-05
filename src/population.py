import numpy as np
import pandas as pd

def asia_pop_life(df, year: int = 2007) -> pd.DataFrame:
    '''Selects Asia based on the selected year, Creates a separate table, and Rank the life Expectancy'''
    asia_sel = df.loc[(df['continent'] == 'Asia') & (df['year'] == year)].copy()

    asia_sel['pop_millions'] = asia_sel['pop']/1000000

    lifeExp_rank = asia_sel['lifeExp'].rank(ascending = False, method = 'min')
    asia_sel['lifeExp_rank'] = lifeExp_rank.astype(int)

    final_part1 = asia_sel.sort_values(by = ['lifeExp_rank', 'country'], ascending = [True, True]) 
    return final_part1
    
def phil_pop_life(df, country: str = 'Philippines') -> pd.DataFrame:
    '''Selects Philippines from the table, Sorts by year, and Adds pop_millions & lifeExp_change'''
    phil_sel = df.loc[(df['country'] == country)].copy()

    phil_sel['pop_millions'] = phil_sel['pop']/1000000

    phil_sel = phil_sel.sort_values(by = 'year', ascending = True)
    
def build_population_matrix(df, countries: list, years: list) -> np.ndarray:

def population_index(matrix: np.ndarray) -> np.ndarray:

def asia_pop_total(df, cont_arr: str = 'Asia', year_arr: int = 2007) -> tuple:

def pop_ind(matrix: np.ndarray) -> np.ndarray:
  
def population_index_table(index_matrix: np.ndarray, countries: list[str], years: list[int]) -> pd.DataFrame:
