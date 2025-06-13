import sys
import json
import matplotlib.pyplot as plt
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import Qt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from pathlib import Path

# === 配置文件路径 ===
PROJECT_ROOT = Path("E:/Qwen_V2.5_CHN2LaTeX")
RESOURCE_FILE_FLODER = PROJECT_ROOT / "data/splits"
EXAMPLE_FILE = RESOURCE_FILE_FLODER / "data_splits_with_CHN_Example.jsonl"

# === QtPy UI定义 ===
class FormulaApp(QWidget):
    def __init__(self):
        super().__init__()
        # 1. 初始化UI
        self.setWindowTitle('简墨公式编辑器 - Present By MatrixDynamic')
        self.setGeometry(300, 300, 900, 600)
        
        # 深色主题样式
        self.apply_dark_theme()
        
        # 2. 设置窗口图标
        self.setWindowIcon(QIcon(r"E:\Qwen_V2.5_CHN2LaTeX\src\ui\resources\icon\logo_1995.png"))
        
        # 3. 加载数据
        self.formulas = self.load_data(EXAMPLE_FILE)
        
        # 4. 创建UI组件
        self.create_widgets()
        
        # 5. 默认显示第一个公式
        self.update_formula_preview(0)
        
        # 6. 添加快捷键支持
        self.setFocusPolicy(Qt.StrongFocus)

    def apply_dark_theme(self):
        """应用深色主题样式表"""
        self.setStyleSheet("""
            QWidget {
                background-color: #1F1E33;
                color: #E0E0FF;
                font-family: 'Microsoft YaHei';
            }
            QGroupBox {
                border: 1px solid #5B5A8F;
                border-radius: 8px;
                margin-top: 1ex;
                padding-top: 15px;
                font-weight: bold;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
            QComboBox, QLabel, QPushButton, QTextEdit {
                background-color: #3A395F;
                color: #FFFFFF;
                border-radius: 5px;
                padding: 8px;
                border: 1px solid #5B5A8F;
                font-family: 'Microsoft YaHei';
            }
            QPushButton {
                background-color: #6C63FF;
                font-weight: bold;
                min-width: 100px;
            }
            QPushButton:hover {
                background-color: #5B52E0;
                border: 1px solid #7A72FF;
            }
            QComboBox::drop-down {
                border: none;
            }
            QComboBox QAbstractItemView {
                background-color: #3A395F;
                color: #FFFFFF;
                selection-background-color: #6C63FF;
            }
            QTabWidget::pane {
                border: 1px solid #5B5A8F;
                border-radius: 5px;
                background: #2A2948;
            }
            QTabBar::tab {
                background: #3A395F;
                color: #E0E0FF;
                padding: 8px 15px;
                border-top-left-radius: 5px;
                border-top-right-radius: 5px;
                border: 1px solid #5B5A8F;
                margin-right: 2px;
            }
            QTabBar::tab:selected {
                background: #6C63FF;
                color: #FFFFFF;
                border-bottom: 2px solid #FFFFFF;
            }
        """)

    def load_data(self, file_path):
        """加载JSONL数据文件"""
        formulas = []
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                for line in f:
                    formulas.append(json.loads(line))
            return formulas
        except Exception as e:
            QMessageBox.critical(self, "数据加载错误", f"无法加载数据文件:\n{str(e)}")
            return []

    def create_widgets(self):
        """创建界面组件"""
        main_layout = QVBoxLayout()
        main_layout.setSpacing(15)
        main_layout.setContentsMargins(20, 20, 20, 20)
        
        # === 公式选择区域 ===
        selection_group = QGroupBox("公式选择")
        selection_layout = QVBoxLayout()
        
        selection_layout.addWidget(QLabel("选择中文描述："))
        self.combo = QComboBox()
        self.combo.setFont(QFont("Microsoft YaHei", 10))
        self.combo.addItems([item['CHINESE'] for item in self.formulas])
        self.combo.currentIndexChanged.connect(self.update_formula_preview)
        selection_layout.addWidget(self.combo)
        
        selection_group.setLayout(selection_layout)
        main_layout.addWidget(selection_group)
        
        # === 公式预览区域 ===
        preview_group = QGroupBox("公式预览与解释")
        preview_layout = QVBoxLayout()
        
        # 创建标签页容器
        self.tab_widget = QTabWidget()
        
        # 1. 公式预览标签页
        preview_tab = QWidget()
        preview_tab_layout = QVBoxLayout()
        self.figure = plt.figure()
        self.canvas = FigureCanvas(self.figure)
        preview_tab_layout.addWidget(self.canvas)
        preview_tab.setLayout(preview_tab_layout)
        self.tab_widget.addTab(preview_tab, "公式预览")
        
        # 2. LaTeX代码标签页
        latex_tab = QWidget()
        latex_tab_layout = QVBoxLayout()
        self.latex_label = QLabel("LaTeX代码将显示在这里")
        self.latex_label.setWordWrap(True)
        self.latex_label.setFont(QFont("Microsoft YaHei", 10))
        latex_tab_layout.addWidget(self.latex_label)
        latex_tab.setLayout(latex_tab_layout)
        self.tab_widget.addTab(latex_tab, "LaTeX代码")
        
        # 3. 公式意义标签页
        meaning_tab = QWidget()
        meaning_tab_layout = QVBoxLayout()
        self.meaning_text = QTextEdit()
        self.meaning_text.setReadOnly(True)
        self.meaning_text.setFont(QFont("Microsoft YaHei", 10))
        meaning_tab_layout.addWidget(self.meaning_text)
        meaning_tab.setLayout(meaning_tab_layout)
        self.tab_widget.addTab(meaning_tab, "公式意义")
        
        preview_layout.addWidget(self.tab_widget)
        preview_group.setLayout(preview_layout)
        main_layout.addWidget(preview_group)
        
        # === 操作按钮区域 ===
        button_layout = QHBoxLayout()
        button_layout.setAlignment(Qt.AlignCenter)
        
        self.export_btn = QPushButton("导出PNG图片")
        self.export_btn.setFont(QFont("Microsoft YaHei", 10))
        self.export_btn.clicked.connect(self.export_png)
        button_layout.addWidget(self.export_btn)
        
        self.copy_btn = QPushButton("复制LaTeX")
        self.copy_btn.setFont(QFont("Microsoft YaHei", 10))
        self.copy_btn.clicked.connect(self.copy_latex)
        button_layout.addWidget(self.copy_btn)
        
        main_layout.addLayout(button_layout)
        
        self.setLayout(main_layout)

    def update_formula_preview(self, index):
        """更新公式预览"""
        if not self.formulas:
            return
            
        # 获取当前公式数据
        current_data = self.formulas[index]
        latex_code = current_data['LaTeX']
        
        # 显示LaTeX代码
        self.latex_label.setText(latex_code)
        
        # 显示公式意义（如果存在）
        meaning = current_data.get('MEANING', '该公式暂无详细说明')
        self.meaning_text.setPlainText(meaning)
        
        # 渲染公式图像
        self.render_latex(latex_code)
        
        # 保存当前选择的公式
        self.current_latex = latex_code
        self.current_meaning = meaning
        self.current_index = index

    def render_latex(self, latex_str):
        """使用Matplotlib渲染LaTeX公式"""
        self.figure.clear()
        ax = self.figure.add_subplot(111)
        
        # 设置纯白背景
        ax.set_facecolor('white')
        self.figure.set_facecolor('white')
        
        try:
            # 显示公式（处理反斜杠）
            processed_latex = latex_str.replace("\\\\", "\\")
            ax.text(0.5, 0.5, f'${processed_latex}$', 
                    fontsize=20, ha='center', va='center')
            
            # 隐藏坐标轴
            ax.axis('off')
            
            # 刷新画布
            self.canvas.draw()
        except Exception as e:
            QMessageBox.warning(self, "渲染错误", f"无法渲染公式:\n{str(e)}")

    def export_png(self):
        """导出公式为PNG图片"""
        if not hasattr(self, 'current_latex'):
            return
            
        try:
            QApplication.setOverrideCursor(Qt.WaitCursor)
            
            # 生成智能默认文件名
            default_name = self.formulas[self.current_index]['CHINESE'][:10] + ".png"
            
            options = QFileDialog.Options()
            file_name, _ = QFileDialog.getSaveFileName(
                self, "保存公式图片", default_name, "PNG Images (*.png)", options=options)
            
            if file_name:
                # 确保文件以.png结尾
                if not file_name.lower().endswith('.png'):
                    file_name += '.png'
                
                # 使用Matplotlib保存高分辨率图片
                plt.figure(figsize=(4, 2), dpi=300)
                plt.text(0.5, 0.5, f'${self.current_latex.replace("\\\\", "\\")}$', 
                        fontsize=20, ha='center', va='center')
                plt.axis('off')
                plt.savefig(file_name, bbox_inches='tight', pad_inches=0.1, dpi=300)
                plt.close()
                
                QMessageBox.information(self, "导出成功", f"公式已保存到:\n{file_name}")
        except Exception as e:
            QMessageBox.critical(self, "导出错误", f"保存失败:\n{str(e)}")
        finally:
            QApplication.restoreOverrideCursor()
            
    def copy_latex(self):
        """复制LaTeX代码到剪贴板"""
        if hasattr(self, 'current_latex'):
            clipboard = QApplication.clipboard()
            clipboard.setText(self.current_latex)
            QMessageBox.information(self, "复制成功", "LaTeX代码已复制到剪贴板")
            
    def keyPressEvent(self, event):
        """键盘事件处理"""
        # 添加快捷键支持
        if event.key() == Qt.Key_Escape:
            self.close()
        elif event.key() == Qt.Key_Enter or event.key() == Qt.Key_Return:
            self.export_png()
        else:
            super().keyPressEvent(event)


# === 主程序 ===
if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # 设置全局字体
    font = QFont("Microsoft YaHei", 10)
    app.setFont(font)
    
    window = FormulaApp()
    window.show()
    sys.exit(app.exec_())