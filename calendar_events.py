import pandas as pd
import streamlit as st

def schedule_df_to_calendar_events(schedule: pd.DataFrame) -> list[dict[str: str]]:
    new_schedule = schedule[['Start', 'End', 'Program']].copy()
    new_schedule[['Start', 'End']] = new_schedule[['Start', 'End']].map(lambda t: t.isoformat())
    new_schedule.rename(columns={'Program': 'title', 'Start':'start', 'End':'end'}, inplace=True)

    return new_schedule.to_dict(orient='records')