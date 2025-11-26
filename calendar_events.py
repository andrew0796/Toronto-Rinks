import pandas as pd

def schedule_df_to_calendar_events(schedule: pd.DataFrame) -> list[dict[str: str]]:
    new_schedule = schedule[['start', 'end', 'program', 'backgroundColor', 'borderColor']].copy()
    new_schedule[['start', 'end']] = new_schedule[['start', 'end']].map(lambda t: t.isoformat())
    new_schedule.rename(columns={'program': 'title'}, inplace=True)

    return new_schedule.to_dict(orient='records')