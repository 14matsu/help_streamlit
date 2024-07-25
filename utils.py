import pandas as pd
import streamlit as st
from constants import  AREAS, SHIFT_TYPES, STORE_COLORS,FILLED_HELP_BG_COLOR


def parse_shift(shift_str):
    if pd.isna(shift_str) or shift_str == '-' or isinstance(shift_str, (int, float)):
        return '-', [], []
    try:
        parts = str(shift_str).split(',')
        shift_type = parts[0] if parts[0] in ['AM可', 'PM可', '1日可'] else ''
        times_stores = []
        for part in parts[1:]:
            if '@' in part:
                time, store = part.strip().split('@')
                times_stores.append((time, store))
            else:
                times_stores.append((part.strip(), ''))
        times, stores = zip(*times_stores) if times_stores else ([], [])
        return shift_type, list(times), list(stores)
    except:
        return '-', [], []
    


def format_shifts(val):
    if pd.isna(val) or val == '-' or isinstance(val, (int, float)):
        return '-'
    try:
        parts = str(val).split(',')
        shift_type = parts[0]
        formatted_shifts = []
        
        for part in parts[1:]:
            if '@' in part:
                time, store = part.strip().split('@')
                color = STORE_COLORS.get(store, "#000000")
                formatted_shifts.append(f'<span style="color: {color}">{time}@{store}</span>')
            else:
                formatted_shifts.append(part.strip())
        
        if shift_type in ['AM可', 'PM可', '1日可']:
            if formatted_shifts:
                return f'<div style="white-space: pre-line;">{shift_type}\n{chr(10).join(formatted_shifts)}</div>'
            else:
                return shift_type
        else:
            return f'<div style="white-space: pre-line;">{chr(10).join(formatted_shifts)}</div>' if formatted_shifts else '-'
    except Exception as e:
        print(f"Error formatting shift: {val}. Error: {e}")
        return str(val)
    

def update_session_state_shifts(shifts):
    for date, row in shifts.iterrows():
        if date in st.session_state.shift_data.index:
            for employee, shift in row.items():
                if pd.notna(shift):
                    st.session_state.shift_data.loc[date, employee] = str(shift)
                else:
                    st.session_state.shift_data.loc[date, employee] = '-'

def highlight_weekend(row):
    weekday = row['曜日']
    if weekday == '土':
        return ['background-color: #EEF9FF'] * len(row)
    elif weekday == '日':
        return ['background-color: #FFE9E9'] * len(row)
    return [''] * len(row)

def get_store_index(store):
    all_stores = [s for stores in AREAS.values() for s in stores]
    return all_stores.index(store) if store in all_stores else 0

def get_shift_type_index(shift_type):
    return SHIFT_TYPES.index(shift_type) if shift_type in SHIFT_TYPES else 0

def is_shift_filled(shift):
    if pd.isna(shift) or shift == '-':
        return False, []
    shift_type, times, stores = parse_shift(shift)
    return bool(times and stores), stores

def highlight_filled_shifts(row, shift_data):
    styles = [''] * len(row)
    date = pd.to_datetime(row['日付'])
    if date not in shift_data.index:
        return styles
    
    all_stores = [store for stores in AREAS.values() for store in stores]
    for i, store in enumerate(all_stores):
        if store in row.index:
            store_shifts = shift_data.loc[date]
            if any(is_shift_filled(shift) and store in shift for shift in store_shifts if pd.notna(shift)):
                styles[row.index.get_loc(store)] = FILLED_HELP_BG_COLOR
    return styles