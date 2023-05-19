
def is_year_leap(year):
    if year % 400 == 0:
        return True
    elif year % 100 == 0:
        return False
    elif year % 4 == 0:
        return True
    else:
        return False
    

def days_in_month(year, month):
    m31 = [1,3,5,7,8,10,12]
    m30 = [2,4,6,9,11]
    if month in m31:
        return 31
    elif month in m30:
        if is_year_leap(year) and month == 2:
            return 29
        elif month == 2:
            return 28
        else:
            return 30
        
