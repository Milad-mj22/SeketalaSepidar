import jdatetime

def persian_to_gregorian(persian_date_str,ret_full = True):
    # Split the date
    parts = persian_date_str.split('/')
    year = int(parts[0])
    month = int(parts[1])
    day = int(parts[2])
    
    # Create Jalali date
    jalali_date = jdatetime.date(year, month, day)
    
    # Convert to Gregorian
    gregorian_date = jalali_date.togregorian()
    if ret_full:
        return gregorian_date
    return gregorian_date.strftime('%Y-%m-%d')


if __name__=='__main__':
    # Example
    persian_date = '۱۴۰۵/۰۵/۰۲'
    gregorian_date = persian_to_gregorian(persian_date)
    print(gregorian_date)  # Output: 2026-07-24