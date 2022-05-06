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
    
def day_of_year(year, month, day):
    # validate date input
    if day > days_in_month(year, month):
        return None

    dayz = 0    
    for m in range(1, month):
        qz = days_in_month(year, m)
        dayz += qz

    print(dayz + day)  
    return dayz + day


tzt_time = [ [2000,7,23], [2020,12,21], [1987,5,23], [1988, 4, 8] ]
tzt_rez = [205, 356, 143,99]

for q in range(len(tzt_time)):
    tzt = day_of_year(tzt_time[q][0],tzt_time[q][1],tzt_time[q][2])
    if tzt == tzt_rez[q]:
        print("OK")
    else:
        print("Failed")

