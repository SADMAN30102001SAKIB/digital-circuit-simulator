from PySide6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTextBrowser,
    QVBoxLayout,
)


class HelpDialog(QDialog):
    """Custom help dialog with scrollable content"""

    def __init__(self, title, content, parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setModal(True)
        self.resize(600, 500)

        # Layout
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)

        # Title
        title_label = QLabel(title)
        title_label.setProperty("class", "title")
        layout.addWidget(title_label)

        # Content content
        browser = QTextBrowser()
        browser.setHtml(content)
        browser.setOpenExternalLinks(True)
        # Style the browser to match theme
        browser.setStyleSheet(
            """
            QTextBrowser {
                background-color: #28292E;
                color: #DCDCE1;
                border: 2px solid #3C3E44;
                border-radius: 6px;
                padding: 12px;
                font-size: 14px;
            }
        """
        )
        layout.addWidget(browser)

        # Close button
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        btn_close = QPushButton("Close")
        btn_close.setProperty("class", "success")
        btn_close.clicked.connect(self.accept)
        btn_layout.addWidget(btn_close)

        layout.addLayout(btn_layout)
        self.setLayout(layout)
