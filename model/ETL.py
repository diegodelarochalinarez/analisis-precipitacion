from datetime import datetime, date, timedelta

class ETL:
    def parse_dates(date_strings):
        valid_dates = []
        invalid_dates = []

        for date_str in date_strings:
            try:
                parsed_date = datetime.strptime(date_str, "%Y-%m-%d").date()
                valid_dates.append(parsed_date)
            except ValueError:
                invalid_dates.append(date_str)
        
        return valid_dates, invalid_dates

    def find_missing_dates(dates):
        if not dates:
            return []

        start_date = min(dates)
        print(start_date)
        end_date = max(dates)
        print(end_date)
        expected_dates = set(start_date + timedelta(days=x) for x in range((end_date - start_date).days + 1))

        missing_dates = sorted(expected_dates - set(dates))
        return missing_dates
