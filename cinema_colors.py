# cinema_colors.py - Cinematic Color Scheme for Movie Collection Manager
"""
Netflix/Cinema-inspired dark theme color palette
"""

# Cinematic Color Palette
CINEMA = {
    # Backgrounds
    'bg_dark': '#0F0F0F',           # Deep black - main background
    'bg_medium': '#1A1A1A',         # Medium black - dialogs, secondary areas
    'bg_light': '#252525',          # Light black - cards, containers
    'bg_hover': '#2D2D2D',          # Hover state background
    
    # Accent Colors
    'gold': '#D4AF37',              # Gold - primary buttons, titles, highlights
    'gold_dark': '#8B6914',         # Dark gold - borders, secondary accents
    'red': '#C41E3A',               # Red - danger/delete buttons
    'green': '#4A7C59',             # Green - watched status
    
    # Text Colors
    'text': '#E8E8E8',              # Primary text - bright white
    'text_dim': '#A0A0A0',          # Secondary text - dimmed
    'text_muted': '#6B6B6B',        # Muted text - very dim
    
    # Borders
    'border': '#333333',            # Standard borders
    'border_bright': '#555555',     # Highlighted/hover borders
}


def get_button_style(primary=False, danger=False):
    """Generate button stylesheet based on type"""
    if danger:
        bg = CINEMA['red']
        hover = "#A01828"
        txt = CINEMA['text']
    elif primary:
        bg = CINEMA['gold']
        hover = CINEMA['gold_dark']
        txt = "#0F0F0F"
    else:
        bg = CINEMA['bg_light']
        hover = CINEMA['bg_hover']
        txt = CINEMA['text']
    
    return f"""
        QPushButton {{
            background-color: {bg};
            color: {txt};
            border: 1px solid {CINEMA['border']};
            border-radius: 4px;
            padding: 6px 16px;
            font-size: 13px;
            font-weight: 600;
            min-height: 28px;
        }}
        QPushButton:hover {{
            background-color: {hover};
            border: 1px solid {CINEMA['border_bright']};
        }}
        QPushButton:pressed {{
            background-color: {hover};
        }}
        QPushButton:disabled {{
            background-color: {CINEMA['bg_medium']};
            color: {CINEMA['text_muted']};
            border: 1px solid {CINEMA['border']};
        }}
    """


def get_card_style():
    """Generate card/frame stylesheet"""
    return f"""
        QFrame {{
            background-color: {CINEMA['bg_light']};
            border-radius: 6px;
            border: 1px solid {CINEMA['border']};
        }}
    """


def get_dialog_style():
    """Generate dialog stylesheet"""
    return f"""
        QDialog {{
            background-color: {CINEMA['bg_medium']};
        }}
        QLineEdit {{
            background-color: {CINEMA['bg_dark']};
            border: 1px solid {CINEMA['border']};
            border-radius: 4px;
            padding: 8px;
            color: {CINEMA['text']};
        }}
        QLineEdit:focus {{
            border: 1px solid {CINEMA['gold']};
        }}
        QTableWidget {{
            background-color: {CINEMA['bg_dark']};
            border: 1px solid {CINEMA['border']};
            border-radius: 4px;
            gridline-color: {CINEMA['border']};
            color: {CINEMA['text']};
        }}
        QTableWidget::item {{
            padding: 8px;
        }}
        QTableWidget::item:selected {{
            background-color: {CINEMA['gold_dark']};
            color: {CINEMA['text']};
        }}
        QTableWidget::item:hover {{
            background-color: {CINEMA['bg_hover']};
        }}
        QHeaderView::section {{
            background-color: {CINEMA['bg_light']};
            color: {CINEMA['text']};
            padding: 8px;
            border: none;
            border-bottom: 1px solid {CINEMA['border']};
            font-weight: 700;
        }}
        QLabel {{
            color: {CINEMA['text']};
        }}
    """


def get_main_window_style():
    """Generate main window stylesheet"""
    return f"""
        QMainWindow {{
            background-color: {CINEMA['bg_dark']};
        }}
        QMenuBar {{
            background-color: {CINEMA['bg_medium']};
            color: {CINEMA['text']};
            border-bottom: 1px solid {CINEMA['border']};
            padding: 3px;
        }}
        QMenuBar::item {{
            padding: 6px 14px;
            background-color: transparent;
            color: {CINEMA['text']};
            font-weight: 600;
        }}
        QMenuBar::item:selected {{
            background-color: {CINEMA['bg_hover']};
            border-radius: 4px;
        }}
        QMenu {{
            background-color: {CINEMA['bg_light']};
            color: {CINEMA['text']};
            border: 1px solid {CINEMA['border']};
            border-radius: 4px;
        }}
        QMenu::item {{
            padding: 8px 30px;
            color: {CINEMA['text']};
        }}
        QMenu::item:selected {{
            background-color: {CINEMA['gold']};
            color: {CINEMA['bg_dark']};
        }}
        QLineEdit {{
            background-color: {CINEMA['bg_dark']};
            border: 1px solid {CINEMA['border']};
            border-radius: 4px;
            padding: 8px;
            font-size: 12px;
            color: {CINEMA['text']};
        }}
        QLineEdit:focus {{
            border: 1px solid {CINEMA['gold']};
        }}
        QScrollBar:vertical {{
            border: none;
            background: {CINEMA['bg_medium']};
            width: 12px;
            border-radius: 6px;
        }}
        QScrollBar::handle:vertical {{
            background: {CINEMA['bg_hover']};
            border-radius: 6px;
            min-height: 30px;
        }}
        QScrollBar::handle:vertical:hover {{
            background: {CINEMA['border_bright']};
        }}
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
            height: 0px;
        }}
        QLabel {{
            color: {CINEMA['text']};
        }}
    """


def get_movie_card_style():
    """Generate movie card stylesheet"""
    return f"""
        QFrame {{
            background-color: {CINEMA['bg_medium']};
            border: 1px solid {CINEMA['border']};
            border-radius: 6px;
        }}
        QFrame:hover {{
            border: 2px solid {CINEMA['gold']};
            background-color: {CINEMA['bg_hover']};
        }}
    """


def get_status_bar_style():
    """Generate status bar stylesheet"""
    return f"""
        QStatusBar {{
            background-color: {CINEMA['bg_medium']};
            color: {CINEMA['text_dim']};
            border-top: 1px solid {CINEMA['border']};
            padding: 4px;
            font-weight: 600;
        }}
    """