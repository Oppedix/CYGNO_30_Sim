"""Historical contribution scale; preserve multiplication order."""
from study.source_matrix import quantity_for, require

def scale_for(row, quantities, generated):
    require(type(generated) is int and generated > 0, 'Invalid actual generated count')
    # Preserve C++ multiplication order, including the 365-day year.
    return row['activity']*quantity_for(row, quantities)*60*60*24*365/generated


