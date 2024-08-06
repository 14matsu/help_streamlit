import io
import pandas as pd
from reportlab.lib import colors
from reportlab.lib.colors import HexColor
from reportlab.lib.pagesizes import landscape, A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.colors import Color
from constants import STORE_COLORS, WEEKDAY_JA, SATURDAY_BG_COLOR, SUNDAY_BG_COLOR,EMPLOYEES,HOLIDAY_BG_COLOR
from io import BytesIO
from utils import parse_shift  # parse_shift関数をutils.pyからインポート
from datetime import datetime

def hex_to_rgb(hex_color):
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i+2], 16) / 255.0 for i in (0, 2, 4))



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
    
    normal_style = ParagraphStyle('Normal', parent=styles['Normal'], fontName='NotoSansJP', fontSize=8, alignment=1)

    def format_shift_for_pdf(shift_type, times, stores):
        if shift_type in ['-', 'AM', 'PM', '1日', '休み', '鹿屋']:
            if shift_type in ['休み', '鹿屋']:
                return Paragraph(shift_type, ParagraphStyle('Holiday', parent=normal_style, backColor=colors.HexColor(HOLIDAY_BG_COLOR), alignment=1))
            return shift_type
        
        formatted_parts = []
        for time, store in zip(times, stores):
            color = STORE_COLORS.get(store, "#000000")
            formatted_parts.append(f'<font color="{color}">{time}@{store}</font>')
        
        content = f"{shift_type}<br/>{', '.join(formatted_parts)}" if formatted_parts else shift_type
        return Paragraph(content, ParagraphStyle('Shift', parent=normal_style, alignment=1))

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
        formatted_shifts = [format_shift_for_pdf(shift_type, times, stores)]
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
        if '土' in row[1]:
            base_style.append(('BACKGROUND', (0, i), (-1, i), colors.HexColor(SATURDAY_BG_COLOR)))
        elif '日' in row[1]:
            base_style.append(('BACKGROUND', (0, i), (-1, i), colors.HexColor(SUNDAY_BG_COLOR)))

    t.setStyle(TableStyle(base_style))

    elements.append(t)
    doc.build(elements)
    return buffer


def generate_help_table_pdf(data, year, month):
    # フォントの登録
    pdfmetrics.registerFont(TTFont('NotoSansJP', 'NotoSansJP-VariableFont_wght.ttf'))
    pdfmetrics.registerFont(TTFont('NotoSansJP-Bold', 'NotoSansJP-Bold.ttf'))

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=landscape(A4), rightMargin=30, leftMargin=30, topMargin=30, bottomMargin=18)
    elements = []

    # スタイルの設定
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle('Title', parent=styles['Heading1'], fontName='NotoSansJP-Bold', fontSize=16)
    normal_style = ParagraphStyle('Normal', parent=styles['Normal'], fontName='NotoSansJP', fontSize=9, alignment=1)
    bold_style = ParagraphStyle('Bold', parent=normal_style, fontName='NotoSansJP-Bold', textColor=colors.white)  # テキスト色を白に変更


    # テーブルスタイルのフォントサイズも調整
    table_style = TableStyle([
        ('FONT', (0, 0), (-1, -1), 'NotoSansJP', 9),
        ('FONT', (0, 0), (-1, 0), 'NotoSansJP-Bold', 9),  # ヘッダー行を太字に
        # 他のスタイル設定は変更なし
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('LEFTPADDING', (0, 0), (-1, -1), 2),
        ('RIGHTPADDING', (0, 0), (-1, -1), 2),
    ])

    # タイトル
    title = Paragraph(f"{year}年{month}月 ヘルプ表", title_style)
    elements.append(title)
    elements.append(Spacer(1, 12))

    def format_shift_for_pdf(shift):
        if pd.isna(shift) or shift == '-':
            return '-'
        if shift in ['休み', '鹿屋']:
            return Paragraph(shift, ParagraphStyle('Holiday', parent=normal_style, backColor=colors.HexColor(HOLIDAY_BG_COLOR)))
        
        shift_parts = shift.split(',')
        shift_type = shift_parts[0]
        formatted_parts = []
        
        for part in shift_parts[1:]:
            if '@' in part:
                time, store = part.split('@')
                color = STORE_COLORS.get(store, "#000000")
                formatted_parts.append(f'<font color="{color}">{time}@<b>{store}</b></font>')  # 店舗名を太字に
            else:
                formatted_parts.append(part)
        
        if shift_type in ['AM可', 'PM可', '1日可']:
            if formatted_parts:
                content = f"{shift_type}<br/>{', '.join(formatted_parts)}"
            else:
                content = shift_type
        else:
            content = ', '.join(formatted_parts)
        
        return Paragraph(content, normal_style)

    # データの準備
    table_data = [['日付', '曜日'] + [Paragraph(f'<font color="white">{emp}</font>', bold_style) for emp in EMPLOYEES]]  # スタッフ名を白色に

    for _, row in data.iterrows():
        date = row['日付']
        weekday = row['曜日']
        employee_shifts = [format_shift_for_pdf(row[emp]) for emp in EMPLOYEES]
        table_data.append([date, weekday] + employee_shifts)

    # テーブルの作成
    table = Table(table_data, repeatRows=1)
    table_style = TableStyle([
        ('FONT', (0, 0), (-1, -1), 'NotoSansJP', 8),
        ('FONT', (0, 0), (-1, 0), 'NotoSansJP-Bold', 8),  # ヘッダー行を太字に
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('LEFTPADDING', (0, 0), (-1, -1), 2),
        ('RIGHTPADDING', (0, 0), (-1, -1), 2),
    ])

    # 土曜日と日曜日の背景色を設定
    for i, row in enumerate(table_data[1:], start=1):
        if row[1] == '土':
            table_style.add('BACKGROUND', (0, i), (-1, i), colors.HexColor(SATURDAY_BG_COLOR))
        elif row[1] == '日':
            table_style.add('BACKGROUND', (0, i), (-1, i), colors.HexColor(SUNDAY_BG_COLOR))

    table.setStyle(table_style)
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
    normal_style = ParagraphStyle('Normal', parent=styles['Normal'], fontName='NotoSansJP', fontSize=8, alignment=1)

    title = Paragraph(f"{employee}さん {year}年{month}月 シフト表", title_style)
    elements.append(title)
    elements.append(Spacer(1, 10))

    start_date = pd.Timestamp(year, month, 16)
    end_date = start_date + pd.DateOffset(months=1) - pd.Timedelta(days=1)
    filtered_data = data[(data.index >= start_date) & (data.index <= end_date)]

    max_shifts = max(len(str(shift).split(',')) - 1 for shift in filtered_data if not pd.isna(shift))
    
    col_widths = [20*mm, 15*mm] + [30*mm] * max_shifts
    
    table_data = [['日付', '曜日'] + [f'シフト{i+1}' for i in range(max_shifts)]]
    
    def format_shift_for_individual_pdf(shift_type, times, stores):
        if shift_type in ['-', 'AM', 'PM', '1日', '休み', '鹿屋']:
            return [shift_type]
        return [f'{time}@{store}' for time, store in zip(times, stores) if time and store]

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
        ('FONTNAME', (0, 0), (-1, 0), 'NotoSansJP-Bold'),
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
            if cell in ['休み', '鹿屋']:
                style.add('BACKGROUND', (j, i), (j, i), colors.HexColor(HOLIDAY_BG_COLOR))
            elif '@' in cell:
                time, store = cell.split('@')
                if store in STORE_COLORS:
                    color = colors.HexColor(STORE_COLORS[store])
                    style.add('TEXTCOLOR', (j, i), (j, i), color)

    t.setStyle(style)
    elements.append(t)
    doc.build(elements)
    buffer.seek(0)
    return buffer


def time_to_minutes(time_str):
    if '-' in time_str:
        start_time = time_str.split('-')[0]
    else:
        start_time = time_str
    if '半' in start_time:
        start_time = start_time.replace('半', ':30')
    else:
        start_time += ':00'
    time_obj = datetime.strptime(start_time, '%H:%M')
    return time_obj.hour * 60 + time_obj.minute


def generate_store_pdf(store_data, store_name, year, month):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=30, leftMargin=30, topMargin=30, bottomMargin=18)
    elements = []

    # スタイルの設定
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle('Title', parent=styles['Heading1'], fontName='NotoSansJP', fontSize=16)
    normal_style = ParagraphStyle('Normal', parent=styles['Normal'], fontName='NotoSansJP', fontSize=10)

    # タイトル
    title = Paragraph(f"{year}年{month}月 {store_name}", title_style)
    elements.append(title)
    elements.append(Spacer(1, 12))

    # 注意書き
    note = Paragraph("*大田さんは1人のときは18時まで\nそれ以外は17時まで", normal_style)
    elements.append(note)
    elements.append(Spacer(1, 12))

 # テーブルデータの準備
    data = [['日にち', '時間', 'ヘルプ担当', '備考']]
    row_colors = [('BACKGROUND', (0, 0), (-1, 0), colors.grey)]  # ヘッダー行の背景色

    for i, (date, row) in enumerate(store_data.iterrows(), start=1):
        day_of_week = WEEKDAY_JA.get(date.strftime('%a'), date.strftime('%a'))
        date_str = f"{date.strftime('%m月%d日')} {day_of_week}"
        help_request = row.get(store_name, '-')
        shifts = []
        for emp in EMPLOYEES:
            shift = row.get(emp, '-')
            if shift != '-':
                _, shift_times, stores = parse_shift(shift)
                for time, store in zip(shift_times, stores):
                    if store == store_name:
                        shifts.append((time_to_minutes(time), time, emp))
        
        # 時間でソート
        shifts.sort(key=lambda x: x[0])
        
        if shifts:
            time_str = '\n'.join([shift[1] for shift in shifts])
            helper_str = '\n'.join([shift[2] for shift in shifts])
        else:
            time_str = '-'
            helper_str = '-'
        
        data.append([date_str, time_str, helper_str, ''])

        # 土曜日と日曜日の背景色を設定
        if day_of_week == '土':
            row_colors.append(('BACKGROUND', (0, i), (-1, i), colors.HexColor(SATURDAY_BG_COLOR)))
        elif day_of_week == '日':
            row_colors.append(('BACKGROUND', (0, i), (-1, i), colors.HexColor(SUNDAY_BG_COLOR)))

    # テーブルの作成
    table = Table(data, colWidths=[80, 80, 80, 80])
    table.setStyle(TableStyle([
        ('FONT', (0, 0), (-1, -1), 'NotoSansJP', 10),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('WORDWRAP', (0, 0), (-1, -1), True),
    ] + row_colors))  # row_colors を追加

    elements.append(table)

    # PDFの生成
    doc.build(elements)

    buffer.seek(0)
    return buffer