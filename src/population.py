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

def generate_validation_rows(case_week, countries, years) -> list:
    """Generates the 5 validation dictionaries for audit logging."""
    results = []
    for y in [2007, 1997]:
        var1 = asia_pop_life(case_week, y)
        var2 = asia_pop_total(case_week, year_arr=y)[0]
        var3 = asia_pop_total(case_week, year_arr=y)[1]

        pop1 = var1["pop_millions"].sum()
        pop2 = pop1 * 1000000
        length1 = len(var1)

        valid1 = np.isclose(var2, pop2, rtol=0, atol=1.0)
        valid2 = length1 == var3

        diction = {
            "check": f"Asia total {y}",
            "expected": float(var1["pop"].sum()),
            "actual": float(pop2),
            "tolerance": 1.0,
            "pass": bool(valid1),
        }
        diction2 = {
            "check": f"Asia row count {y}",
            "expected": int(var3),
            "actual": int(length1),
            "tolerance": 0,
            "pass": bool(valid2),
        }
        results.append(diction)
        results.append(diction2)

    pop_matrix = build_population_matrix(case_week, countries, years)
    pop_idx = population_index(pop_matrix)
    stored = pop_ind(pop_matrix)
    valid3 = np.allclose(stored, pop_idx, atol=1e-8, rtol=0)
    differ = stored - pop_idx
    absol = np.abs(differ)
    maxi = absol.max()

    diction3 = {
        "check": "Broadcast Result versus Loop Result",
        "expected": float(0),
        "actual": float(maxi),
        "tolerance": 1e-8,
        "pass": bool(valid3),
    }
    results.append(diction3)

    first_col = pop_idx[:, 0]
    valid4 = np.allclose(first_col, 100, atol=1e-8, rtol=0)

    diction4 = {
        "check": "1982 Column equals 100",
        "expected": 0.0,
        "actual": float(np.abs(first_col - 100).max()),
        "tolerance": 1e-8,
        "pass": bool(valid4),
    }
    results.append(diction4)

    countried = case_week["country"].to_numpy()
    yeared = case_week["year"].to_numpy()
    pops = case_week["pop"].to_numpy()

    call = phil_pop_life(case_week)
    call2 = call["year"].to_numpy()
    call3 = call["pop"].to_numpy()

    call_mask = call2 == 2007
    phil_mask = (countried == "Philippines") & (yeared == 2007)
    varia = pops[phil_mask].sum()
    expects = call3[call_mask].sum()
    valid5 = np.allclose(varia, expects, atol=1.0, rtol=0)

    diction5 = {
        "check": "Philippine Population in 2007",
        "expected": float(varia),
        "actual": float(expects),
        "tolerance": 1.0,
        "pass": bool(valid5),
    }
    results.append(diction5)

    return results
