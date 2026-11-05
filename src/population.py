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

    life_num = phil_sel['lifeExp'].iloc[0]
    phil_sel['lifeExp_change'] = phil_sel['lifeExp'] - life_num
    return phil_sel
    
def build_population_matrix(df, countries: list, years: list) -> np.ndarray:
    '''Creating a Matrix based on population from the selected countries and years'''
    numpy_asia = df.loc[df['country'].isin(countries) & df['year'].isin(years)]
    pop_list = []

    for c in countries:
        country_nump = numpy_asia.loc[numpy_asia['country'] == c]
        country_order = country_nump.sort_values(by = 'year', ascending = True)
        country_pop = country_order['pop']
        pop_list.append(np.array(country_pop))

    converted = np.vstack(pop_list)
    return converted
    
def population_index(matrix: np.ndarray) -> np.ndarray:
    '''Calculate the population index of the matrix'''
    sliced_select = matrix[:, [0]]
    divide = matrix / sliced_select
    result_product = divide * 100

    return result_product
    
def asia_pop_total(df, cont_arr: str = 'Asia', year_arr: int = 2007) -> tuple:
    '''Takes continent from original data and Returns a sum of population and counts of matching rows'''
    continent = df['continent'].to_numpy()
    year = df['year'].to_numpy()
    pop = df['pop'].to_numpy()

    mask = (continent == cont_arr) & (year == year_arr)
    val = pop[mask].sum()
    counts = mask.sum()

    return int(val), int(counts)
    
def pop_ind(matrix: np.ndarray) -> np.ndarray:
    '''Rebuilds the index with plain loops and Returns the result'''
    rows, cols = matrix.shape
    store = np.zeros((rows, cols))
    
    for i in range(rows):
        for j in range(cols):
            store[i, j] = (matrix[i, j] / matrix[i, 0]) * 100

    return store
    
def population_index_table(index_matrix: np.ndarray, countries: list[str], years: list[int]) -> pd.DataFrame:
    """Labels an index matrix with country names and string year column headers."""
    if index_matrix.shape != (len(countries), len(years)):
        raise ValueError(
            f"Matrix shape {index_matrix.shape} does not match "
            f"{len(countries)} countries x {len(years)} years"
        )
    table = pd.DataFrame(index_matrix, columns=[str(y) for y in years])
    table.insert(0, "country", countries)
    return table
