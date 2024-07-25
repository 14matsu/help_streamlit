import io
import pandas as pd
from reportlab.lib import colors
from reportlab.lib.colors import HexColor
from reportlab.lib.pagesizes import landscape, A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.colors import Color
from constants import STORE_COLORS, WEEKDAY_JA, SATURDAY_BG_COLOR, SUNDAY_BG_COLOR
from io import BytesIO
from utils import parse_shift  # parse_shift関数をutils.pyからインポート

def hex_to_rgb(hex_color):
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i+2], 16) / 255.0 for i in (0, 2, 4))

def format_shift_for_pdf(shift):
    if pd.isna(shift) or shift == '-':
        return '-'
    parts = str(shift).split(',')
    formatted = [f'<font name="NotoSansJP-Bold">{parts[0]}</font>']  # シフトタイプ（AM可、PM可、1日可など）
    for part in parts[1:]:
        if '@' in part:
            time, store = part.split('@')
            color = STORE_COLORS.get(store, '#000000')
            formatted.append(f'<font color="{color}">{time}@{store}</font>')
        else:
            formatted.append(part)
    return '<br/>'.join(formatted)

def format_shift_for_individual_pdf(shift_type, times, stores):
    if shift_type in ['-', 'AM', 'PM', '1日', '休み']:
        return [shift_type]
    return [f'{time}@{store}' for time, store in zip(times, stores) if time and store]

def generate_pdf(data, employee, year, month):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=10*mm, leftMargin=10*mm, topMargin=10*mm, bottomMargin=10*mm)
    elements = []

    pdfmetrics.registerFont(TTFont('NotoSansJP', 'NotoSansJP-VariableFont_wght.ttf'))
    pdfmetrics.registerFont(TTFont('NotoSansJP-Bold', 'NotoSansJP-Bold.ttf'))

    styles = getSampleStyleSheet()
    title_style = styles['Title']
    title_style.fontName = 'NotoSansJP'
    title_style.fontSize = 14
    
    start_date = pd.Timestamp(year, month, 16)
    end_date = start_date + pd.DateOffset(months=1) - pd.Timedelta(days=1)
    title = f"{employee} {start_date.strftime('%Y年%m月%d日')}～{end_date.strftime('%Y年%m月%d日')} シフト表"
    elements.append(Paragraph(title, title_style))
    elements.append(Spacer(1, 10))

    filtered_data = data[(data.index >= start_date) & (data.index <= end_date)]

    max_shifts = max(len(parse_shift(shift)[1]) for shift in filtered_data if not pd.isna(shift))
    
    col_widths = [20*mm, 15*mm] + [30*mm] * max_shifts
    
    table_data = [['日付', '曜日'] + [f'シフト{i+1}' for i in range(max_shifts)]]
    for date, shift in filtered_data.items():
        weekday = WEEKDAY_JA[date.strftime('%a')]
        shift_type, times, stores = parse_shift(shift)
        formatted_shifts = format_shift_for_pdf(shift_type, times, stores)
        row = [date.strftime('%m/%d'), weekday] + formatted_shifts + [''] * (max_shifts - len(formatted_shifts))
        table_data.append(row)

    t = Table(table_data, colWidths=col_widths)
    base_style = [
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, -1), 'NotoSansJP'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
        ('BACKGROUND', (0, 1), (-1, -1), colors.white),
        ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
        ('FONTSIZE', (0, 1), (-1, -1), 8),
        ('TOPPADDING', (0, 1), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 3),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.black)
    ]
    
    for i, row in enumerate(table_data[1:], start=1):
        for j, cell in enumerate(row[2:], start=2):
            if cell in ['AM', 'PM', '1日', '-', '休み']:
                base_style.append(('TEXTCOLOR', (j, i), (j, i), colors.black))
            elif '@' in cell:
                time, store = cell.split('@')
                if store in STORE_COLORS:
                    color = STORE_COLORS[store]
                    rgb_color = hex_to_rgb(color)
                    base_style.append(('TEXTCOLOR', (j, i), (j, i), Color(*rgb_color, alpha=1)))

    t.setStyle(TableStyle(base_style))

    elements.append(t)
    doc.build(elements)
    return buffer

def generate_help_table_pdf(data, year, month):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=landscape(A4), rightMargin=30, leftMargin=30, topMargin=30, bottomMargin=30)
    elements = []

    # フォントの登録
    pdfmetrics.registerFont(TTFont('NotoSansJP', 'NotoSansJP-VariableFont_wght.ttf'))

    # タイトルの追加
    styles = getSampleStyleSheet()
    title_style = styles['Title']
    title_style.fontName = 'NotoSansJP'
    title = Paragraph(f"{year}年{month}月 ヘルプ表", title_style)
    elements.append(title)

    # データの準備
    data['日付'] = pd.to_datetime(data['日付']).dt.strftime('%m/%d')
    data_list = [data.columns.tolist()] + data.values.tolist()

    # テーブルの作成
    table = Table(data_list, repeatRows=1)

    # テーブルのスタイル
    style = TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.grey),
        ('TEXTCOLOR',(0,0),(-1,0),colors.whitesmoke),
        ('ALIGN',(0,0),(-1,-1),'CENTER'),
        ('FONTNAME', (0,0), (-1,-1), 'NotoSansJP'),
        ('FONTSIZE', (0,0), (-1,-1), 8),
        ('BOTTOMPADDING', (0,0), (-1,0), 12),
        ('GRID', (0,0), (-1,-1), 1, colors.black)
    ])

    # 土曜日と日曜日の背景色を変更
    for i, row in enumerate(data_list[1:], start=1):
        if row[1] == '土':
            style.add('BACKGROUND', (0, i), (-1, i), HexColor(SATURDAY_BG_COLOR))
        elif row[1] == '日':
            style.add('BACKGROUND', (0, i), (-1, i), HexColor(SUNDAY_BG_COLOR))

    # シフトの色分け
    for i, row in enumerate(data_list[1:], start=1):
        for j, cell in enumerate(row[2:], start=2):
            if '@' in str(cell):
                parts = str(cell).split(',')
                for part in parts:
                    if '@' in part:
                        store = part.split('@')[1]
                        if store in STORE_COLORS:
                            color = HexColor(STORE_COLORS[store])
                            style.add('TEXTCOLOR', (j, i), (j, i), color)

    table.setStyle(style)
    elements.append(table)

    # PDFの生成
    doc.build(elements)
    buffer.seek(0)
    return buffer

def generate_individual_pdf(data, employee, year, month):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=10*mm, leftMargin=10*mm, topMargin=10*mm, bottomMargin=10*mm)
    elements = []

    pdfmetrics.registerFont(TTFont('NotoSansJP', 'NotoSansJP-VariableFont_wght.ttf'))
    pdfmetrics.registerFont(TTFont('NotoSansJP-Bold', 'NotoSansJP-VariableFont_wght.ttf'))

    styles = getSampleStyleSheet()
    title_style = styles['Title']
    title_style.fontName = 'NotoSansJP-Bold'
    title = Paragraph(f"{employee}さん {year}年{month}月 シフト表", title_style)  # ここを修正
    elements.append(title)
    elements.append(Spacer(1, 10))

    start_date = pd.Timestamp(year, month, 16)
    end_date = start_date + pd.DateOffset(months=1) - pd.Timedelta(days=1)
    filtered_data = data[(data.index >= start_date) & (data.index <= end_date)]

    max_shifts = max(len(str(shift).split(',')) - 1 for shift in filtered_data if not pd.isna(shift))
    
    col_widths = [20*mm, 15*mm] + [30*mm] * max_shifts
    
    table_data = [['日付', '曜日'] + [f'シフト{i+1}' for i in range(max_shifts)]]
    for date, shift in filtered_data.items():
        weekday = WEEKDAY_JA[date.strftime('%a')]
        shift_parts = str(shift).split(',') if pd.notna(shift) else ['-']
        shift_type = shift_parts[0]
        times_stores = [part.strip().split('@') for part in shift_parts[1:] if '@' in part]
        times, stores = zip(*times_stores) if times_stores else ([], [])
        formatted_shifts = format_shift_for_individual_pdf(shift_type, times, stores)
        row = [date.strftime('%m/%d'), weekday] + formatted_shifts + [''] * (max_shifts - len(formatted_shifts))
        table_data.append(row)

    t = Table(table_data, colWidths=col_widths)
    
    style = TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('FONTNAME', (0, 0), (-1, -1), 'NotoSansJP'),
        ('FONTNAME', (0, 0), (-1, 0), 'NotoSansJP-Bold'),  # カラム名を太字に
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('FONTSIZE', (0, 1), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.black)
    ])

    for i, row in enumerate(table_data[1:], start=1):
        if '土' in row[1]:
            style.add('BACKGROUND', (0, i), (-1, i), colors.HexColor(SATURDAY_BG_COLOR))
        elif '日' in row[1]:
            style.add('BACKGROUND', (0, i), (-1, i), colors.HexColor(SUNDAY_BG_COLOR))

        for j, cell in enumerate(row[2:], start=2):
            if '@' in cell:
                time, store = cell.split('@')
                if store in STORE_COLORS:
                    color = colors.HexColor(STORE_COLORS[store])
                    style.add('TEXTCOLOR', (j, i), (j, i), color)
                    

    t.setStyle(style)
    elements.append(t)
    doc.build(elements)
    buffer.seek(0)
    return buffer