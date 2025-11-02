import sys, re, os, unicodedata
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QColorDialog, QFileDialog, QListWidgetItem, QStyledItemDelegate, QMessageBox, QInputDialog
)
from PyQt6 import uic
from PyQt6.QtGui import QIcon, QColor, QPixmap, QImage, QPainter
from PyQt6.QtCore import Qt, QRect
from PIL import Image

class BorderDelegate(QStyledItemDelegate):
    def paint(self, painter, option, index):
        # Primeiro, deixe o item ser pintado normalmente (incluindo a cor de fundo)
        super().paint(painter, option, index)
        
        # Depois, desenhe as bordas
        painter.save()
        painter.setPen(QColor("#d0d0d0"))
        
        # Desenha borda superior apenas para o primeiro item
        if index.row() == 0:
            painter.drawLine(option.rect.topLeft(), option.rect.topRight())
        
        # Desenha borda inferior para todos os itens
        painter.drawLine(option.rect.bottomLeft(), option.rect.bottomRight())
        
        painter.restore()

class CenteredBoldDelegate(QStyledItemDelegate):
    def paint(self, painter, option, index):
        # Configurar o estilo de texto para centralizado e negrito
        option = option
        option.displayAlignment = Qt.AlignmentFlag.AlignCenter
        font = option.font
        font.setBold(True)
        option.font = font
        
        # Primeiro, deixe o item ser pintado normalmente (incluindo a cor de fundo)
        super().paint(painter, option, index)
        
        # Depois, desenhe as bordas
        painter.save()
        painter.setPen(QColor("#d0d0d0"))
        
        # Desenha borda superior apenas para o primeiro item
        if index.row() == 0:
            painter.drawLine(option.rect.topLeft(), option.rect.topRight())
        
        # Desenha borda inferior para todos os itens
        painter.drawLine(option.rect.bottomLeft(), option.rect.bottomRight())
        
        painter.restore()

def resource_path(relative_path):
    """ Obtém o caminho absoluto para o recurso. Funciona para desenvolvimento e para o PyInstaller. """
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    
    full_path = os.path.join(base_path, relative_path)
    # Debug: verificar se o arquivo existe
    if not os.path.exists(full_path):
        print(f"AVISO: Arquivo não encontrado: {full_path}")
        print(f"Base path: {base_path}")
        print(f"Relative path: {relative_path}")
    
    return full_path

def get_save_directory():
    """Retorna o diretório onde salvar arquivos (mesmo diretório do executável ou do script)"""
    if getattr(sys, 'frozen', False):
        # Se é um executável PyInstaller, usa o diretório do executável
        return os.path.dirname(sys.executable)
    else:
        # Se está rodando como script, usa o diretório do script
        return os.path.dirname(os.path.abspath(__file__))

class ColorEditor(QWidget):
    def __init__(self):
        super().__init__()
        
        # Nome da janela (verificar também na interface "windowTitle")
        self.setWindowTitle("Zero Palette Editor - Mega Man X8 Demake")
        
        # Obter o diretório do script
        self.save_dir = get_save_directory()
        
        # Carregar UI
        ui_path = resource_path(os.path.join("ui", "color_editor.ui"))
        print(f"Tentando carregar UI de: {ui_path}")
        
        try:
            uic.loadUi(ui_path, self)
        except Exception as e:
            QMessageBox.critical(None, "Erro", f"Erro ao carregar interface: {str(e)}")
            sys.exit(1)
        
        # Carregar ícone
        icon_path = resource_path(os.path.join("resources", "icone.ico"))
        print(f"Tentando carregar ícone de: {icon_path}")
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))
        else:
            print("AVISO: Ícone não encontrado")
        
        # Flag para controlar se uma paleta foi carregada
        self.palette_loaded = False
        
        # Armazenar o caminho da última paleta carregada
        self.last_loaded_palette_path = None

        # Dados
        self.palette = {}  # dict {parameter_name: "#HEX"}
        self.default_comment_lines = []
        self.plt_name = "Padrão"  # Nome da paleta
        
        # Mapeamento entre nomes de exibição e nomes internos
        self.display_to_internal = {
            'Outline_Color': 'Outln',
            'MainBody_Color1': 'Armr1',
            'MainBody_Color2': 'Armr2',
            'MainBody_Color3': 'Armr3',
            'MainBody_Color4': 'Armr4',
            'Hair_Color1': 'Hair1',
            'Hair_Color2': 'Hair2',
            'Hair_Color3': 'Hair3',
            'Hair_Color4': 'Hair4',
            'HeadCrystal_Color1': 'Crtl1',
            'HeadCrystal_Color2': 'Crtl2',
            'HeadCrystal_Color3': 'Crtl3',
            'ChestCrystal_Color1': 'Sphr1',
            'ChestCrystal_Color2': 'Sphr2',
            'ChestCrystal_Color3': 'Sphr3',
            'Armor_Color1': 'Detl1',
            'Armor_Color2': 'Detl2',
            'Armor_Color3': 'Detl3',
            'Grey_Color1': 'Grey1',
            'Grey_Color2': 'Grey2',
            'Grey_Color3': 'Grey3',
            'Grey_Color4': 'Grey4',
            'Skin_Color1': 'Skin1',
            'Skin_Color2': 'Skin2',
            'Skin_Color3': 'Skin3',
            'Saber_Color1': 'Sabr1',
            'Saber_Color2': 'Sabr2',
            'Saber_Color3': 'Sabr3',
            'Saber_Color4': 'Sabr4'
        }
        
        # Mapeamento reverso: nomes internos para nomes de arquivo
        self.internal_to_file = {
            'Outln': 'Outline_Color',
            'Armr1': 'MainBody_Color1',
            'Armr2': 'MainBody_Color2',
            'Armr3': 'MainBody_Color3',
            'Armr4': 'MainBody_Color4',
            'Hair1': 'Hair_Color1',
            'Hair2': 'Hair_Color2',
            'Hair3': 'Hair_Color3',
            'Hair4': 'Hair_Color4',
            'Crtl1': 'HeadCrystal_Color1',
            'Crtl2': 'HeadCrystal_Color2',
            'Crtl3': 'HeadCrystal_Color3',
            'Sphr1': 'ChestCrystal_Color1',
            'Sphr2': 'ChestCrystal_Color2',
            'Sphr3': 'ChestCrystal_Color3',
            'Detl1': 'Armor_Color1',
            'Detl2': 'Armor_Color2',
            'Detl3': 'Armor_Color3',
            'Grey1': 'Grey_Color1',
            'Grey2': 'Grey_Color2',
            'Grey3': 'Grey_Color3',
            'Grey4': 'Grey_Color4',
            'Skin1': 'Skin_Color1',
            'Skin2': 'Skin_Color2',
            'Skin3': 'Skin_Color3',
            'Sabr1': 'Saber_Color1',
            'Sabr2': 'Saber_Color2',
            'Sabr3': 'Saber_Color3',
            'Sabr4': 'Saber_Color4'
        }
        
        # Conectar sinais
        self.setup_connections()

        # Aplicar o delegate personalizado para as bordas
        self.colorList.setItemDelegate(BorderDelegate())
        self.colorEdit.setItemDelegate(CenteredBoldDelegate())
        
        # Inicializar palette com cores padrão
        self.initialize_default_palette()
        
        # Desenhar imagem do mapeamento
        self.draw_mapped_image()

    def setup_connections(self):
        # Conectar sinais da interface
        self.savePaletteButton.clicked.connect(self.save_palette)
        self.loadPaletteButton.clicked.connect(self.load_palette_dialog)
        self.colorList.itemDoubleClicked.connect(self.edit_color_from_name)
        self.colorEdit.itemDoubleClicked.connect(self.edit_color_from_hex)
        self.resetButton.clicked.connect(self.reset_palette)
        self.applyPaletteButton.clicked.connect(self.apply_palette)
        self.reloadButton.clicked.connect(self.reload_last_palette)
        
        # Substituir QLabel por QLineEdit ou usar método alternativo
        try:
            self.paletteName.editingFinished.connect(self.update_palette_name)
        except AttributeError:
            # Se paletteName for QLabel, usar método alternativo
            self.paletteName.mouseDoubleClickEvent = self.edit_palette_name_dialog

    def initialize_default_palette(self):
        """Inicializa a palette com as cores padrão definidas na classe"""
        # Limpa a paleta atual
        self.palette.clear()

        # Define os comentários padrão do arquivo
        self.default_comment_lines = [
            "# You can customize Zero's colors by changing the hex values below.",
            "# Format: ParameterName=HexColor",
            "# Lines starting with '#' are comments and ignored.",
            "",
            "# Custom palette name"
        ]

        # Define o nome padrão da paleta
        self.plt_name = 'Padrão'
        self.paletteName.setText(self.plt_name)

        # Outline color
        self.palette['Outln'] = '#202020'

        # Armor main colors (Red - light to dark)
        self.palette['Armr1'] = '#FD2D1E'
        self.palette['Armr2'] = '#F03000'
        self.palette['Armr3'] = '#A02100'
        self.palette['Armr4'] = '#612100'

        # Hair colors (light to dark)
        self.palette['Hair1'] = '#FFFBCD'
        self.palette['Hair2'] = '#F0C818'
        self.palette['Hair3'] = '#B17001'
        self.palette['Hair4'] = '#6B3018'

        # Head crystal colors (Blue - light to dark)
        self.palette['Crtl1'] = '#F7F8F9'
        self.palette['Crtl2'] = '#158FFE'
        self.palette['Crtl3'] = '#0545DC'

        # Chest sphere colors (Green - light to dark)
        self.palette['Sphr1'] = '#E8FFE9'
        self.palette['Sphr2'] = '#41E040'
        self.palette['Sphr3'] = '#21A120'

        # Armor details colors (Yellow - light to dark)
        self.palette['Detl1'] = '#F1C919'
        self.palette['Detl2'] = '#B17702'
        self.palette['Detl3'] = '#8B5A00'

        # Parts colors (Grey - light to dark)
        self.palette['Grey1'] = '#E0E0E0'
        self.palette['Grey2'] = '#A0A0A0'
        self.palette['Grey3'] = '#606060'
        self.palette['Grey4'] = '#303030'

        # Skin colors (light to dark)
        self.palette['Skin1'] = '#F8B080'
        self.palette['Skin2'] = '#B86048'
        self.palette['Skin3'] = '#6B3118'

        # Saber colors (light to dark)
        self.palette['Sabr1'] = '#DBF9DB'
        self.palette['Sabr2'] = '#9DE39C'
        self.palette['Sabr3'] = '#60DC60'
        # Also used for afterimage effects when dashing
        self.palette['Sabr4'] = '#3EC23B'

        # Eye colors (light to dark) - Unchangable
        self.palette['Eye01'] = '#E7E7E7'
        self.palette['Eye02'] = '#A5A5A5'
        
        # Transparência da imagem
        self.palette['_____'] = '#000000'

        # Atualizar a lista de cores
        self.update_color_lists()

    def reset_palette(self):
        """Reseta a paleta para as cores padrão"""
        self.default_comment_lines.clear()
        self.initialize_default_palette()
        self.plt_name = 'Padrão'
        self.paletteName.setText(self.plt_name)
        self.palette_loaded = False
        self.last_loaded_palette_path = None
        self.draw_mapped_image()

    def update_palette_name(self):
        """Atualiza o nome da paleta quando o usuário edita o campo"""
        self.plt_name = self.paletteName.text()

    def edit_palette_name_dialog(self, event):
        """Abre um diálogo para editar o nome da paleta quando o QLabel é clicado duas vezes"""
        new_name, ok = QInputDialog.getText(self, "Editar Nome da Paleta", "Nome da paleta:", text=self.plt_name)
        if ok and new_name.strip():
            self.plt_name = new_name.strip()
            self.paletteName.setText(self.plt_name)

    def reload_last_palette(self):
        """Recarrega a última paleta que foi carregada"""
        if self.last_loaded_palette_path and os.path.exists(self.last_loaded_palette_path):
            self.load_palette_from_file(self.last_loaded_palette_path)
        else:
            # Se nenhuma paleta foi carregada anteriormente, resetar para padrão
            self.reset_palette()

    # --------------------------------------------------
    # Métodos para carregar paletas (CORRIGIDOS)
    # --------------------------------------------------
    def load_palette_dialog(self):
        """Abre diálogo para selecionar arquivo de paleta"""
        path, _ = QFileDialog.getOpenFileName(self, "Carregar Paleta", self.save_dir, "Texto (*.txt)")
        if not path:
            return
        self.load_palette_from_file(path)

    def load_palette_from_file(self, path):
        """Carrega uma paleta a partir de um arquivo (método interno)"""
        try:
            # Limpa a paleta atual antes de carregar a nova
            self.palette.clear()
            
            # Define valores iniciais
            self.plt_name = ""
            found_palette_name = False
            
            # Mapeamento dos nomes das variáveis do arquivo para os nomes internos
            variable_mapping = {
                'Outline_Color': 'Outln',
                'MainBody_Color1': 'Armr1',
                'MainBody_Color2': 'Armr2',
                'MainBody_Color3': 'Armr3',
                'MainBody_Color4': 'Armr4',
                'Hair_Color1': 'Hair1',
                'Hair_Color2': 'Hair2',
                'Hair_Color3': 'Hair3',
                'Hair_Color4': 'Hair4',
                'HeadCrystal_Color1': 'Crtl1',
                'HeadCrystal_Color2': 'Crtl2',
                'HeadCrystal_Color3': 'Crtl3',
                'ChestCrystal_Color1': 'Sphr1',
                'ChestCrystal_Color2': 'Sphr2',
                'ChestCrystal_Color3': 'Sphr3',
                'Armor_Color1': 'Detl1',
                'Armor_Color2': 'Detl2',
                'Armor_Color3': 'Detl3',
                'Grey_Color1': 'Grey1',
                'Grey_Color2': 'Grey2',
                'Grey_Color3': 'Grey3',
                'Grey_Color4': 'Grey4',
                'Skin_Color1': 'Skin1',
                'Skin_Color2': 'Skin2',
                'Skin_Color3': 'Skin3',
                'Saber_Color1': 'Sabr1',
                'Saber_Color2': 'Sabr2',
                'Saber_Color3': 'Sabr3',
                'Saber_Color4': 'Sabr4'
            }

            with open(path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.rstrip("\n")
                    
                    # Verificar se é a linha do nome da paleta
                    if line.startswith("Palette_Name="):
                        self.plt_name = line.split("=", 1)[1]
                        self.paletteName.setText(self.plt_name)
                        found_palette_name = True
                        continue
                        
                    # Ignorar todas as linhas de comentário e linhas vazias ao carregar
                    if line.startswith("#") or not line.strip():
                        continue
                        
                    match = re.match(r"(\w+)=#([0-9A-Fa-f]{6})", line)
                    if match:
                        file_name, hexcolor = match.groups()
                        # Converter nome do arquivo para nome interno usando o mapeamento
                        internal_name = variable_mapping.get(file_name)
                        if internal_name:
                            self.palette[internal_name] = f"#{hexcolor}"

            # Se não encontrou nome da paleta, usar nome do arquivo
            if not found_palette_name:
                base_name = os.path.splitext(os.path.basename(path))[0]
                self.plt_name = base_name
                self.paletteName.setText(self.plt_name)

            # FORÇAR CORES IMUTÁVEIS (não são salvas no arquivo, sempre usam valores padrão)
            self.palette['Eye01'] = '#E7E7E7'
            self.palette['Eye02'] = '#A5A5A5'
            self.palette['_____'] = '#000000'

            # Marcar que uma paleta foi carregada
            self.palette_loaded = True
            
            # Armazenar o caminho da última paleta carregada
            self.last_loaded_palette_path = path

            # Atualizar a lista de cores e a imagem
            self.update_color_lists()
            self.draw_mapped_image()
            
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao carregar paleta: {str(e)}")
            # Em caso de erro, recarregar paleta padrão
            self.reset_palette()

    # --------------------------------------------------
    # Imagem a partir do mapeamento
    # --------------------------------------------------
    def draw_mapped_image(self):
        """Desenha a imagem usando o mapeamento de cores fornecido"""
        # Mapeamento de cores fornecido (mantido igual do código original)
        color_mapping = [
            #01
            ['_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', 'Outln', '_____', '_____', '_____', '_____', 'Outln', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____'],
            #02
            ['_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', 'Outln', 'Outln', '_____', '_____', '_____', 'Outln', 'Outln', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____'],
            #03
            ['_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', 'Outln', 'Armr3', 'Outln', '_____', '_____', 'Outln', 'Armr4', 'Outln', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____'],
            #04
            ['_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', 'Outln', '_____', '_____', 'Outln', 'Armr3', 'Armr2', 'Outln', 'Outln', 'Outln', 'Armr4', 'Armr4', 'Outln', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____'],
            #05
            ['_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', 'Outln', 'Outln', 'Outln', 'Armr4', 'Armr2', 'Armr2', 'Outln', 'Grey3', 'Grey1', 'Grey1', 'Grey2', 'Armr4', 'Outln', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____'],
            #06
            ['_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', 'Outln', 'Armr4', 'Outln', 'Armr3', 'Armr2', 'Armr2', 'Armr4', 'Outln', 'Grey1', 'Grey1', 'Grey1', 'Grey2', 'Outln', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____'],
            #07
            ['_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', 'Outln', 'Armr3', 'Armr4', 'Armr3', 'Armr2', 'Armr2', 'Armr2', 'Armr4', 'Grey2', 'Grey1', 'Grey1', 'Grey1', 'Grey3', 'Outln', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____'],
            #08
            ['_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', 'Outln', 'Armr4', 'Armr3', 'Armr3', 'Armr2', 'Armr2', 'Armr2', 'Armr2', 'Armr4', 'Grey1', 'Grey1', 'Crtl3', 'Crtl3', 'Crtl3', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____'],
            #09
            ['_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', 'Outln', 'Armr4', 'Armr4', 'Armr3', 'Armr2', 'Armr2', 'Armr3', 'Armr2', 'Armr4', 'Grey2', 'Grey1', 'Crtl2', 'Crtl1', 'Crtl2', 'Outln', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____'],
            #10
            ['_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', 'Outln', 'Armr4', 'Outln', 'Outln', 'Armr3', 'Armr2', 'Outln', 'Armr4', 'Armr2', 'Armr4', 'Grey2', 'Grey1', 'Crtl2', 'Crtl2', 'Outln', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____'],
            #11
            ['_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', 'Outln', 'Grey3', 'Grey1', 'Grey2', 'Armr2', 'Outln', 'Outln', 'Armr4', 'Armr2', 'Armr4', 'Grey3', 'Grey2', 'Crtl3', 'Outln', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____'],
            #12
            ['_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', 'Outln', 'Grey2', 'Crtl3', 'Grey1', 'Armr2', 'Outln', 'Skin3', 'Eye01', 'Outln', 'Armr3', 'Armr4', 'Outln', 'Outln', 'Outln', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____'],
            #13
            ['_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', 'Outln', 'Grey3', 'Outln', 'Grey1', 'Armr2', 'Outln', 'Skin3', 'Eye01', 'Eye02', 'Outln', 'Outln', 'Armr4', 'Outln', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____'],
            #14
            ['_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', 'Hair4', 'Outln', 'Outln', 'Grey2', 'Grey3', 'Armr2', 'Armr3', 'Outln', 'Skin2', 'Eye02', 'Outln', 'Skin3', 'Outln', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____'],
            #15
            ['_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', 'Hair2', 'Hair3', 'Outln', 'Crtl3', 'Outln', 'Outln', 'Armr3', 'Armr2', 'Armr4', 'Outln', 'Skin1', 'Skin1', 'Skin1', 'Skin2', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____'],
            #16
            ['_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', 'Hair2', 'Hair2', 'Outln', 'Armr4', 'Outln', 'Outln', 'Outln', 'Outln', 'Armr3', 'Armr4', 'Outln', 'Skin1', 'Outln', 'Skin1', 'Outln', 'Outln', 'Outln', 'Outln', 'Outln', 'Outln', '_____', '_____', '_____', '_____', '_____', '_____', '_____'],
            #17
            ['_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', 'Hair1', 'Hair2', 'Outln', 'Armr4', 'Grey3', 'Grey3', 'Outln', 'Detl2', 'Detl2', 'Outln', 'Outln', 'Skin2', 'Skin1', 'Skin1', 'Outln', 'Outln', 'Grey3', 'Grey2', 'Grey1', 'Grey1', 'Armr3', 'Outln', '_____', '_____', '_____', '_____', '_____', '_____'],
            #18
            ['_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', 'Hair3', 'Hair1', 'Hair2', 'Outln', 'Armr3', 'Grey2', 'Outln', 'Detl2', 'Detl1', 'Detl1', 'Detl1', 'Detl2', 'Outln', 'Outln', 'Outln', 'Outln', 'Armr3', 'Grey2', 'Grey1', 'Grey1', 'Armr2', 'Armr4', 'Armr4', 'Outln', '_____', '_____', '_____', '_____', '_____'],
            #19
            ['_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', 'Hair2', 'Hair2', 'Hair3', 'Outln', 'Armr4', 'Armr3', 'Sphr2', 'Armr3', 'Armr2', 'Detl1', 'Armr2', 'Armr2', 'Sphr2', 'Sphr2', 'Armr3', 'Outln', 'Armr3', 'Grey2', 'Grey1', 'Armr2', 'Armr4', 'Outln', 'Outln', 'Armr4', '_____', '_____', '_____', '_____', '_____'],
            #20
            ['_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', 'Hair3', 'Hair2', 'Hair3', 'Outln', 'Outln', 'Outln', 'Armr4', 'Sphr3', 'Armr3', 'Armr2', 'Armr2', 'Armr2', 'Armr2', 'Sphr1', 'Sphr3', 'Sphr3', 'Armr3', 'Armr4', 'Armr3', 'Armr2', 'Armr4', 'Outln', 'Outln', 'Outln', 'Outln', '_____', '_____', '_____', '_____', '_____'],
            #21
            ['_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', 'Hair3', 'Outln', 'Outln', 'Armr4', 'Outln', 'Outln', 'Outln', 'Sphr3', 'Armr3', 'Armr4', 'Armr4', 'Armr4', 'Armr3', 'Sphr2', 'Sphr3', 'Armr3', 'Armr4', 'Outln', 'Armr4', 'Outln', 'Outln', 'Outln', 'Outln', 'Outln', '_____', '_____', '_____', '_____', '_____', '_____'],
            #22
            ['_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', 'Outln', 'Armr4', 'Armr4', 'Armr3', 'Armr2', 'Outln', 'Outln', 'Outln', 'Armr4', 'Armr3', 'Armr2', 'Armr2', 'Armr4', 'Armr3', 'Armr3', 'Armr4', 'Armr4', 'Outln', 'Outln', 'Outln', 'Outln', 'Outln', 'Armr4', 'Armr4', 'Outln', '_____', '_____', '_____', '_____', '_____'],
            #23
            ['_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', 'Outln', 'Grey2', 'Grey3', 'Armr3', 'Armr2', 'Armr2', 'Armr4', 'Outln', 'Outln', 'Outln', 'Detl2', 'Detl1', 'Detl2', 'Armr4', 'Armr4', 'Armr4', 'Armr4', 'Outln', '_____', '_____', 'Outln', 'Outln', 'Armr4', 'Armr3', 'Armr2', 'Armr3', 'Outln', '_____', '_____', '_____', '_____'],
            #24
            ['_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', 'Outln', 'Grey2', 'Grey1', 'Grey3', 'Grey1', 'Armr2', 'Armr3', 'Armr4', 'Outln', 'Hair4', 'Outln', 'Grey3', 'Grey1', 'Grey1', 'Grey1', 'Grey2', 'Grey2', 'Outln', 'Outln', '_____', '_____', '_____', 'Outln', 'Armr3', 'Armr4', 'Grey2', 'Grey1', 'Grey3', 'Outln', '_____', '_____', '_____'],
            #25
            ['_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', 'Outln', 'Grey3', 'Grey1', 'Outln', 'Outln', 'Grey3', 'Grey2', 'Armr4', 'Outln', 'Hair3', 'Hair4', 'Outln', 'Outln', 'Outln', 'Outln', 'Outln', 'Outln', 'Outln', 'Outln', '_____', '_____', '_____', '_____', 'Outln', 'Armr4', 'Grey2', 'Outln', 'Outln', 'Grey2', 'Grey1', 'Outln', '_____', '_____'],
            #26
            ['_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', 'Outln', 'Outln', 'Grey2', 'Grey2', 'Outln', 'Outln', 'Grey3', 'Grey3', 'Outln', 'Hair4', 'Hair4', 'Outln', 'Grey2', 'Grey3', 'Outln', 'Outln', 'Grey3', 'Grey2', 'Outln', '_____', '_____', '_____', '_____', 'Outln', 'Grey3', 'Outln', 'Grey2', 'Grey1', 'Grey2', 'Grey1', 'Grey3', 'Outln', '_____'],
            #27
            ['_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', 'Outln', 'Grey2', 'Grey2', 'Grey1', 'Grey1', 'Grey2', 'Outln', 'Outln', 'Hair3', 'Hair4', 'Outln', 'Outln', 'Grey3', 'Grey2', 'Grey1', 'Grey1', 'Grey1', 'Grey3', 'Outln', 'Outln', '_____', '_____', '_____', '_____', 'Outln', 'Grey1', 'Grey1', 'Outln', 'Grey1', 'Outln', 'Grey3', 'Outln', '_____'],
            #28
            ['_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', 'Sabr2', 'Sabr2', 'Sabr3', 'Sabr3', 'Sabr4', 'Outln', 'Grey1', 'Grey1', 'Grey1', 'Grey2', 'Outln', 'Hair3', 'Outln', 'Outln', 'Outln', 'Outln', 'Grey3', 'Grey2', 'Grey1', 'Grey3', 'Outln', 'Outln', 'Outln', 'Outln', '_____', '_____', '_____', 'Outln', 'Grey1', 'Outln', 'Grey1', 'Grey1', 'Grey2', 'Outln', 'Outln', '_____'],
            #29
            ['_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', 'Sabr3', 'Sabr3', 'Sabr1', 'Sabr2', 'Sabr3', 'Outln', 'Grey1', 'Grey2', 'Outln', 'Outln', 'Outln', 'Outln', 'Outln', 'Outln', 'Outln', 'Outln', 'Grey3', 'Grey3', 'Outln', 'Outln', 'Outln', 'Outln', 'Outln', 'Outln', '_____', '_____', 'Outln', 'Grey2', 'Outln', 'Grey1', 'Grey2', 'Grey1', 'Grey2', 'Outln', '_____'],
            #30
            ['_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', 'Sabr3', 'Sabr2', 'Sabr2', 'Sabr1', 'Sabr2', 'Sabr2', 'Sabr4', 'Grey2', 'Outln', 'Outln', 'Grey2', 'Outln', 'Outln', 'Outln', 'Outln', 'Outln', 'Hair3', '_____', '_____', '_____', 'Outln', 'Outln', 'Outln', 'Outln', 'Outln', 'Outln', 'Outln', '_____', 'Outln', 'Outln', 'Outln', 'Grey2', 'Grey2', 'Outln', '_____', '_____'],
            #31
            ['_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', 'Sabr3', 'Sabr2', 'Sabr1', 'Sabr1', 'Sabr2', 'Sabr1', 'Sabr4', 'Sabr4', 'Outln', 'Outln', 'Grey2', 'Grey1', 'Outln', 'Outln', 'Outln', 'Outln', 'Outln', 'Hair3', '_____', '_____', '_____', 'Outln', 'Outln', 'Outln', 'Outln', 'Outln', 'Grey1', 'Grey2', 'Outln', '_____', '_____', 'Outln', 'Outln', 'Outln', '_____', '_____', '_____'],
            #32
            ['_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', 'Sabr4', 'Sabr2', 'Sabr1', 'Sabr1', 'Sabr1', 'Sabr1', 'Sabr2', 'Sabr4', 'Sabr3', 'Outln', 'Grey2', 'Grey1', 'Grey1', 'Armr4', 'Outln', 'Outln', 'Outln', 'Hair3', 'Hair2', '_____', '_____', '_____', '_____', 'Outln', 'Outln', 'Outln', 'Outln', 'Grey1', 'Grey1', 'Grey2', 'Outln', '_____', '_____', '_____', '_____', '_____', '_____', '_____'],
            #33
            ['_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', 'Sabr4', 'Sabr3', 'Sabr1', 'Sabr1', 'Sabr1', 'Sabr1', 'Sabr2', 'Sabr3', 'Sabr2', 'Sabr3', 'Outln', 'Grey2', 'Grey1', 'Grey2', 'Armr3', 'Armr4', 'Armr4', 'Outln', 'Hair3', 'Hair2', 'Hair3', '_____', '_____', '_____', 'Outln', 'Outln', 'Outln', 'Armr4', 'Grey1', 'Grey1', 'Grey2', 'Outln', '_____', '_____', '_____', '_____', '_____', '_____', '_____'],
            #34
            ['_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', 'Sabr3', 'Sabr2', 'Sabr1', 'Sabr1', 'Sabr1', 'Sabr1', 'Sabr2', 'Sabr4', 'Sabr3', '_____', 'Sabr2', 'Outln', 'Grey2', 'Armr4', 'Armr3', 'Armr2', 'Armr3', 'Armr4', 'Outln', 'Hair4', 'Hair2', 'Hair2', '_____', '_____', '_____', 'Outln', 'Armr4', 'Armr3', 'Armr3', 'Armr3', 'Grey1', 'Grey2', 'Armr4', 'Outln', '_____', '_____', '_____', '_____', '_____', '_____'],
            #35
            ['_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', 'Sabr4', 'Sabr3', 'Sabr1', 'Sabr1', 'Sabr1', 'Sabr2', 'Sabr3', 'Sabr4', '_____', '_____', '_____', 'Outln', 'Armr4', 'Armr4', 'Armr3', 'Armr2', 'Armr2', 'Armr3', 'Armr4', 'Outln', 'Hair4', 'Hair3', 'Hair2', 'Hair3', '_____', '_____', 'Outln', 'Armr4', 'Armr3', 'Armr2', 'Armr2', 'Armr3', 'Armr3', 'Armr3', 'Outln', '_____', '_____', '_____', '_____', '_____', '_____'],
            #36
            ['_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', 'Sabr3', 'Sabr2', 'Sabr1', 'Sabr1', 'Sabr2', 'Sabr3', 'Sabr4', '_____', '_____', '_____', '_____', '_____', 'Outln', 'Detl2', 'Armr3', 'Armr2', 'Armr2', 'Armr2', 'Armr3', 'Armr4', 'Outln', 'Hair4', 'Hair4', 'Hair4', 'Hair3', '_____', '_____', 'Outln', 'Armr4', 'Armr3', 'Armr2', 'Armr2', 'Armr2', 'Armr3', 'Detl2', 'Armr4', 'Outln', '_____', '_____', '_____', '_____', '_____'],
            #37
            ['_____', '_____', '_____', '_____', '_____', '_____', '_____', 'Sabr3', 'Sabr2', 'Sabr1', 'Sabr1', 'Sabr2', 'Sabr3', 'Sabr4', '_____', '_____', '_____', '_____', '_____', 'Outln', 'Armr4', 'Detl1', 'Detl2', 'Armr2', 'Armr2', 'Armr2', 'Armr3', 'Armr4', 'Outln', '_____', '_____', 'Hair4', 'Hair4', 'Hair4', '_____', 'Outln', 'Armr4', 'Armr3', 'Armr3', 'Armr2', 'Armr2', 'Armr3', 'Detl1', 'Detl2', 'Armr4', '_____', '_____', '_____', '_____', '_____'],
            #38
            ['_____', '_____', '_____', '_____', '_____', '_____', 'Sabr4', 'Sabr2', 'Sabr1', 'Sabr2', 'Sabr3', 'Sabr4', '_____', '_____', '_____', '_____', '_____', '_____', '_____', 'Outln', 'Detl2', 'Detl1', 'Detl1', 'Armr2', 'Armr2', 'Armr3', 'Armr4', 'Armr4', 'Outln', '_____', '_____', '_____', '_____', '_____', '_____', 'Outln', 'Armr4', 'Armr4', 'Armr3', 'Armr2', 'Armr2', 'Detl2', 'Detl1', 'Detl1', 'Detl2', 'Outln', '_____', '_____', '_____', '_____'],
            #39
            ['_____', '_____', '_____', '_____', '_____', 'Sabr4', 'Sabr3', 'Sabr2', 'Sabr3', 'Sabr3', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', 'Outln', 'Outln', 'Outln', 'Detl1', 'Detl2', 'Armr3', 'Armr3', 'Outln', 'Outln', 'Outln', '_____', '_____', '_____', '_____', '_____', '_____', '_____', 'Outln', 'Outln', 'Armr4', 'Armr3', 'Armr3', 'Detl1', 'Outln', 'Outln', 'Outln', 'Outln', '_____', '_____', '_____', '_____'],
            #40
            ['_____', '_____', '_____', '_____', 'Sabr4', 'Sabr2', 'Sabr2', 'Sabr4', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', 'Outln', 'Armr4', 'Armr3', 'Armr3', 'Outln', 'Detl1', 'Detl2', 'Detl2', 'Grey1', 'Grey2', 'Outln', '_____', '_____', '_____', '_____', '_____', '_____', '_____', 'Outln', 'Grey2', 'Outln', 'Armr4', 'Detl2', 'Outln', 'Armr4', 'Armr3', 'Armr4', 'Armr4', 'Outln', '_____', '_____', '_____'],
            #41
            ['_____', '_____', '_____', 'Sabr4', 'Sabr3', 'Sabr4', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', 'Outln', 'Armr4', 'Armr3', 'Armr2', 'Armr2', 'Armr3', 'Outln', 'Detl1', 'Outln', 'Grey2', 'Grey3', 'Outln', '_____', '_____', '_____', '_____', '_____', '_____', '_____', 'Outln', 'Grey3', 'Grey1', 'Detl2', 'Outln', 'Armr3', 'Armr2', 'Armr2', 'Armr3', 'Armr3', 'Armr4', 'Outln', '_____', '_____'],
            #42
            ['_____', '_____', 'Sabr4', 'Sabr3', 'Sabr4', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', 'Outln', 'Grey3', 'Grey2', 'Grey1', 'Grey2', 'Grey3', 'Armr2', 'Armr4', 'Outln', 'Outln', 'Grey3', 'Outln', 'Outln', '_____', '_____', '_____', '_____', '_____', '_____', '_____', 'Outln', 'Grey3', 'Grey2', 'Outln', 'Armr4', 'Armr2', 'Outln', 'Grey3', 'Grey2', 'Grey1', 'Grey2', 'Grey3', 'Outln', '_____'],
            #43
            ['_____', 'Sabr4', 'Sabr4', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', 'Outln', 'Grey3', 'Grey2', 'Grey1', 'Grey1', 'Grey1', 'Grey2', 'Outln', 'Armr3', 'Armr4', 'Armr4', 'Outln', 'Outln', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', 'Outln', 'Outln', 'Armr4', 'Armr4', 'Outln', 'Grey3', 'Grey2', 'Grey1', 'Grey1', 'Grey1', 'Grey2', 'Grey3', 'Outln'],
            #44
            ['Sabr4', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', 'Outln', 'Outln', 'Outln', 'Outln', 'Outln', 'Outln', 'Outln', 'Outln', 'Outln', 'Outln', 'Outln', 'Outln', 'Outln', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', '_____', 'Outln', 'Outln', 'Outln', 'Outln', 'Outln', 'Outln', 'Outln', 'Outln', 'Outln', 'Outln', 'Outln', 'Outln', 'Outln']
        ]

        # Criar imagem 50x44 com formato ARGB32 para suportar transparência
        width = 50
        height = 44
        image = QImage(width, height, QImage.Format.Format_ARGB32)
        image.fill(Qt.GlobalColor.transparent)

        # Preencher a imagem com as cores do mapeamento
        for y in range(min(height, len(color_mapping))):
            for x in range(min(width, len(color_mapping[y]))):
                color_hex = color_mapping[y][x]
                
                # Se for um nome de cor (não hexadecimal), buscar da palette
                if not color_hex.startswith('#'):
                    color_hex = self.palette.get(color_hex, '#000000')
                
                if color_hex != '#000000':
                    color = QColor(color_hex)
                    image.setPixelColor(x, y, color)
                else:
                    # Define como totalmente transparente para #000000
                    image.setPixelColor(x, y, QColor(0, 0, 0, 0))

        # Converter para QPixmap e exibir
        pixmap = QPixmap.fromImage(image).scaled(
            300, 264,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.FastTransformation
        )
        self.imageLabel.setPixmap(pixmap)

    # --------------------------------------------------
    # Paleta (métodos de salvamento permanecem iguais)
    # --------------------------------------------------
   
    def save_palette(self):
        """Salva a paleta no diretório do script com nome baseado no nome da paleta"""
        if not self.palette:
            return
            
        # Verificar se o nome da paleta está vazio
        if not self.plt_name.strip():
            QMessageBox.critical(self, "Erro", "O nome da paleta não pode estar vazio!")
            return
            
        # Gerar nome de arquivo sugerido
        suggested_filename = self.generate_suggested_filename()
        
        # Caminho para salvar no diretório do script
        path = os.path.join(self.save_dir, suggested_filename)
        
        # Verificar se o arquivo já existe
        if os.path.exists(path):
            reply = QMessageBox.question(
                self,
                "Arquivo Existente",
                f"O arquivo '{suggested_filename}' já existe. Deseja substituí-lo?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.No:
                return  # Cancela o salvamento
        
        # Salvar o arquivo
        self._save_palette_to_path(path)
            
        # Armazenar o caminho da última paleta carregada
        self.last_loaded_palette_path = path
        
        # Flag para controlar se uma paleta foi carregada
        self.palette_loaded = True
        
        # Mensagem de sucesso
        QMessageBox.information(self, "Sucesso", f"Paleta salva como: {suggested_filename}")

    def _save_palette_to_path(self, path):
        """Salva a paleta no caminho especificado"""
        with open(path, "w", encoding="utf-8") as f:
            # Preserva comentários originais ou usa os padrão
            for line in self.default_comment_lines:
                f.write(line + "\n")
            
            # Linha do nome da paleta
            f.write(f"Palette_Name={self.plt_name}\n\n")

            # Escreve as cores na ordem específica usando o mapeamento correto
            # Grupo: Outline color
            f.write("# Outline color\n")
            file_name = self.internal_to_file['Outln']
            f.write(f"{file_name}={self.palette.get('Outln', '#202020')}\n\n")
            
            # Grupo: Armor main colors
            f.write("# Armor main colors (light to dark)\n")
            for internal_name in ['Armr1', 'Armr2', 'Armr3', 'Armr4']:
                file_name = self.internal_to_file[internal_name]
                f.write(f"{file_name}={self.palette.get(internal_name, '#000000')}\n")
            f.write("\n")
            
            # Grupo: Hair colors
            f.write("# Hair colors (light to dark)\n")
            for internal_name in ['Hair1', 'Hair2', 'Hair3', 'Hair4']:
                file_name = self.internal_to_file[internal_name]
                f.write(f"{file_name}={self.palette.get(internal_name, '#000000')}\n")
            f.write("\n")
            
            # Grupo: Head crystal colors
            f.write("# Head crystal colors (light to dark)\n")
            for internal_name in ['Crtl1', 'Crtl2', 'Crtl3']:
                file_name = self.internal_to_file[internal_name]
                f.write(f"{file_name}={self.palette.get(internal_name, '#000000')}\n")
            f.write("\n")
            
            # Grupo: Chest crystal colors
            f.write("# Chest crystal colors (light to dark)\n")
            for internal_name in ['Sphr1', 'Sphr2', 'Sphr3']:
                file_name = self.internal_to_file[internal_name]
                f.write(f"{file_name}={self.palette.get(internal_name, '#000000')}\n")
            f.write("\n")
            
            # Grupo: Armor details colors
            f.write("# Armor details colors (light to dark)\n")
            for internal_name in ['Detl1', 'Detl2', 'Detl3']:
                file_name = self.internal_to_file[internal_name]
                f.write(f"{file_name}={self.palette.get(internal_name, '#000000')}\n")
            f.write("\n")
            
            # Grupo: Parts colors
            f.write("# Grey parts colors (light to dark)\n")
            for internal_name in ['Grey1', 'Grey2', 'Grey3', 'Grey4']:
                file_name = self.internal_to_file[internal_name]
                f.write(f"{file_name}={self.palette.get(internal_name, '#000000')}\n")
            f.write("\n")
            
            # Grupo: Skin colors
            f.write("# Skin colors (light to dark)\n")
            for internal_name in ['Skin1', 'Skin2', 'Skin3']:
                file_name = self.internal_to_file[internal_name]
                f.write(f"{file_name}={self.palette.get(internal_name, '#000000')}\n")
            f.write("\n")
            
            # Grupo: Saber colors
            f.write("# Saber colors (light to dark)\n")
            for internal_name in ['Sabr1', 'Sabr2', 'Sabr3']:
                file_name = self.internal_to_file[internal_name]
                f.write(f"{file_name}={self.palette.get(internal_name, '#000000')}\n")
            f.write("# Also used for afterimage effects when dashing\n")
            file_name = self.internal_to_file['Sabr4']
            f.write(f"{file_name}={self.palette.get('Sabr4', '#000000')}\n")
            
    def apply_palette(self):
        """Salva a paleta atual como 'custom_zero_palette.txt' no diretório do script"""
        if not self.palette:
            return
            
        # Verificar se o nome da paleta está vazio
        if not self.plt_name.strip():
            QMessageBox.critical(self, "Erro", "O nome da paleta não pode estar vazio!")
            return
            
        # Caminho fixo para salvar
        path = os.path.join(self.save_dir, "custom_zero_palette.txt")
        
        # Salvar o arquivo
        self._save_palette_to_path(path)
        
        # Mensagem de sucesso
        QMessageBox.information(self, "Sucesso", f"Paleta aplicada com sucesso!")

    def generate_suggested_filename(self):
        """Gera um nome de arquivo sugerido no formato custom_zero_palette_[sufixo].txt"""
        base_name = "custom_zero_palette"
        
        if self.plt_name and self.plt_name.strip():
            # Normalizar o nome: remover acentos, converter para minúsculas, substituir espaços por _
            suffix = unicodedata.normalize('NFKD', self.plt_name)
            suffix = ''.join(c for c in suffix if not unicodedata.combining(c))  # Remove diacríticos
            suffix = suffix.lower().strip()
            suffix = re.sub(r'[^a-z0-9]+', '_', suffix)  # Substitui caracteres não alfanuméricos por _
            suffix = suffix.strip('_')  # Remove _ no início e fim
            
            # Se o sufixo ficou vazio, usar "custom"
            if not suffix:
                suffix = "custom"
                
            return f"{base_name}_{suffix}.txt"
        else:
            return f"{base_name}_custom.txt"

    def get_text_color_based_on_bg(self, hexcolor):
        """Retorna a cor do texto baseado na claridade do fundo usando 3 tons de cinza."""
        color = QColor(hexcolor)
        # Fórmula de luminância relativa
        luminance = 0.299 * color.red() + 0.587 * color.green() + 0.114 * color.blue()
        
        if luminance <= 128:
            return QColor(255, 255, 255)
        elif luminance <= 255:
            return QColor(0, 0, 0)

    def update_color_lists(self):
        """Atualiza ambas as listas de cores"""
        self.colorList.clear()
        self.colorEdit.clear()
        
        # Ordem específica para exibição
        display_order = [
            'Outline_Color',
            'MainBody_Color1', 'MainBody_Color2', 'MainBody_Color3', 'MainBody_Color4',
            'Hair_Color1', 'Hair_Color2', 'Hair_Color3', 'Hair_Color4',
            'HeadCrystal_Color1', 'HeadCrystal_Color2', 'HeadCrystal_Color3',
            'ChestCrystal_Color1', 'ChestCrystal_Color2', 'ChestCrystal_Color3',
            'Armor_Color1', 'Armor_Color2', 'Armor_Color3',
            'Grey_Color1', 'Grey_Color2', 'Grey_Color3', 'Grey_Color4',
            'Skin_Color1', 'Skin_Color2', 'Skin_Color3',
            'Saber_Color1', 'Saber_Color2', 'Saber_Color3', 'Saber_Color4'
        ]
        
        for display_name in display_order:
            internal_name = self.display_to_internal[display_name]
            hexcolor = self.palette.get(internal_name, '#000000')
            
            # Lista esquerda - Nomes (SEM cor de fundo, COM bordas)
            item_name = QListWidgetItem(display_name)
            item_name.setData(Qt.ItemDataRole.UserRole, internal_name)  # Guarda o nome interno para referência
            self.colorList.addItem(item_name)
            
            # Lista direita - Valores HEX (COM cor de fundo)
            item_hex = QListWidgetItem(hexcolor)
            item_hex.setBackground(QColor(hexcolor))
            
            # Ajusta a cor do texto baseado na claridade do fundo
            text_color = self.get_text_color_based_on_bg(hexcolor)
            item_hex.setForeground(text_color)
            
            item_hex.setData(Qt.ItemDataRole.UserRole, internal_name)  # Guarda o nome interno para referência
            self.colorEdit.addItem(item_hex)
        
        # Aplica bordas usando um delegate customizado
        self.apply_item_borders()
        
    def apply_item_borders(self):
        """Aplica bordas entre os itens sem afetar as cores de fundo"""
        # Para colorList (apenas bordas)
        for i in range(self.colorList.count()):
            item = self.colorList.item(i)
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsEnabled)  # Garante que está habilitado
        
        # Para colorEdit (bordas + cores de fundo)
        for i in range(self.colorEdit.count()):
            item = self.colorEdit.item(i)
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsEnabled)  # Garante que está habilitado

    def edit_color_from_name(self, item):
        """Edita cor quando clicado na lista de nomes"""
        internal_name = item.data(Qt.ItemDataRole.UserRole)
        hexcolor = self.palette[internal_name]
        self.open_color_editor(internal_name, hexcolor)

    def edit_color_from_hex(self, item):
        """Edita cor quando clicado na lista de HEX"""
        internal_name = item.data(Qt.ItemDataRole.UserRole)
        hexcolor = self.palette[internal_name]
        self.open_color_editor(internal_name, hexcolor)

    def open_color_editor(self, internal_name, hexcolor):
        """Abre o diálogo de edição de cor"""
        color = QColor(hexcolor)
        new_color = QColorDialog.getColor(color, self, f"Editar cor de {internal_name}")
        if new_color.isValid():
            new_hex = new_color.name().upper()
            if new_hex != hexcolor:
                self.palette[internal_name] = new_hex
                
                # Limpar o nome da paleta
                if not self.palette_loaded or self.plt_name == "Padrão":
                    self.plt_name = ""
                    self.paletteName.setText("")
                    
                self.update_color_lists()
                self.draw_mapped_image()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ColorEditor()
    window.show()
    sys.exit(app.exec())
