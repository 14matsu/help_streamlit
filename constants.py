EMPLOYEES = ['佐渡', '大塚', '和田', '新門', '大田', '山下', '大久保', '石田', '米山']
#STORES = ['本店', '武店', '任天堂', '市役所前', 'クローバー', '郡元店', 'ケンコー堂', '宇宿店', 'ジャック']
AREAS = {
    'なし': [],  # シフト登録/修正で使用
    '中央エリア': ['本店', '武店', '任天堂', '市役所前', 'クローバー', '郡元店', 'ケンコー堂', '宇宿店', 'ジャック'],
    '西エリア': ['郡山店','大王店','市比野店','天辰店','出水店'],
    '北エリア': ['ピッコロ','加治木店', '霧島店'],
    '南薩エリア': ['チェリー','ひかり','屋久島店','南さつま店'],
    '宮崎エリア': ['東町店','早鈴店','三股店','とだか','さくら']
}
SHIFT_TYPES = ['AM可', 'PM可', '1日可', '時間指定', '-', '休み']
STORE_COLORS = {
    # 中央エリア
    '本店': '#0070C2', 
    '宇宿店': '#00B0F0', 
    '武店': '#D2A000', 
    '任天堂': '#FF7C80', 
    '市役所前': '#FF6600', 
    'クローバー': '#00B050', 
    '郡元店': '#0000FF', 
    'ケンコー堂': '#7030A0',
    'ジャック': '#FF3399',
    
    # 西エリア
    '郡山店': '#4472C4',
    '大王店': '#ED7D31',
    '市比野店': '#A5A5A5',
    '天辰店': '#FFC000',
    '出水店': '#5B9BD5',
    
    # 北エリア
    'ピッコロ': '#70AD47',
    '加治木店': '#264478',
    '霧島店': '#9E480E',
    
    # 南薩エリア
    'チェリー': '#BF8F00',
    'ひかり': '#43682B',
    '屋久島店': '#698ED0',
    '南さつま店': '#A6A6A6',
    
    # 宮崎エリア
    '東町店': '#8497B0',
    '早鈴店': '#F2A104',
    '三股店': '#305496',
    'とだか': '#C55A11',
    'さくら': '#548235'
}
WEEKDAY_JA = {'Mon': '月', 'Tue': '火', 'Wed': '水', 'Thu': '木', 'Fri': '金', 'Sat': '土', 'Sun': '日'}
FILLED_HELP_BG_COLOR = 'background-color: #D9D9D9'
SATURDAY_BG_COLOR = '#E6F2FF'  # 薄い青色
SUNDAY_BG_COLOR = '#FFE6E6'    # 薄い赤色
HOLIDAY_BG_COLOR = '#FFE6E6'  # 休み用の背景色