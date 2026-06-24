def valid_date(dt, sep="."):

    def is_year_leap(year):
        if year % 400 == 0 and (
            year % 100 != 0 and year % 4 == 0
        ):
            return True
        else:
            return False

    def days_in_month(year, month):
        month_num = { 
            31: [1,3,5,7,8,10,12],
            30: [2,4,6,9,11]
        }
        if month == 2:
            if is_year_leap(year):
                return 29
            return 28
        for days, months in month_num.items():
            if month in months:
                return days

    dd, mm, yyyy = dt.split(sep)
    mm = int(mm.lstrip("0"))
    dd = int(dd.lstrip("0"))
    if dd <= days_in_month(mm) and len(yyyy) == 4:
        return True
    return False
