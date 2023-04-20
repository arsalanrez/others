import os
import sys
import threading
import yt_dlp
from PyQt5.QtWidgets import (
    QApplication,
    QLabel,
    QLineEdit,
    QPushButton,
    QCheckBox,
    QGridLayout,
    QMainWindow,
    QStatusBar,
    QProgressBar,
    QWidget,
    QFrame
)
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import Qt, QObject, pyqtSignal


class DownloadWorker(QObject):
    downloadFinished = pyqtSignal()
    downloadFailed = pyqtSignal(str)
    downloadProgress = pyqtSignal(float, float)

    def __init__(self, options):
        super(DownloadWorker, self).__init__()
        self.options = options
        self.isCanceled = False

    def _onProgress(self, progress):
        if progress['status'] == 'finished':
            self.downloadFinished.emit()
            return
        if progress['status'] == 'error':
            errorMsg = progress.get('error', {}).get('message', 'Download failed')
            self.downloadFailed.emit(errorMsg)
            return
        totalBytes = progress.get('total_bytes', 0)
        downloadedBytes = progress.get('downloaded_bytes', 0)
        self.downloadProgress.emit(totalBytes, downloadedBytes)

    def run(self):
        try:
            with yt_dlp.YoutubeDL(self.options) as ydl:
                ydl.add_progress_hook(self._onProgress)
                ydl.download([self.options.get('url')])
        except Exception as e:
            if not self.isCanceled:
                self.downloadFailed.emit(f'Download failed: {str(e)}')
    

class MainWindow(QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()
        self.setWindowTitle('yt-dlp GUI')
        #self.setFixedSize(500, 225)
        self.setWindowIcon(QIcon('icon.png'))
        self.downloadWorker = None
        self.darkTheme = False
        self.setupUi()

    def setupUi(self):
        centralWidget = QWidget(self)

        gridLayout = QGridLayout(centralWidget)
        gridLayout.setSpacing(10)

        self.urlLabel = QLabel('Video URL:', centralWidget)
        self.urlLineEdit = QLineEdit(centralWidget)

        self.proxyCheckBox = QCheckBox('Use Proxy', centralWidget)
        self.proxyCheckBox.stateChanged.connect(self.toggleProxyFields)
        
        self.proxyLabel = QLabel('Proxy URL:', centralWidget)
        self.proxyLabel.setEnabled(False)
        self.proxyLineEdit = QLineEdit(centralWidget)
        self.proxyLineEdit.setEnabled(False)
        
        self.proxyPortLabel = QLabel('Proxy Port:', centralWidget)
        self.proxyPortLabel.setEnabled(False)
        self.proxyPortLineEdit = QLineEdit(centralWidget)
        self.proxyPortLineEdit.setEnabled(False)

        self.downloadProgressBar = QProgressBar(centralWidget)
        self.downloadProgressBar.setTextVisible(False)
        self.downloadProgressBar.setMaximum(0)

        self.downloadButton = QPushButton('Download', centralWidget)
        self.downloadButton.clicked.connect(self.startDownload)
        self.cancelButton = QPushButton('Cancel', centralWidget)
        self.cancelButton.setEnabled(False)
        self.cancelButton.clicked.connect(self.cancelDownload)
        
        self.themeButton = QPushButton('Light Theme', centralWidget)
        self.themeButton.clicked.connect(self.changeTheme)
        
        gridLayout.addWidget(self.urlLabel, 0, 0)
        gridLayout.addWidget(self.urlLineEdit, 0, 1)
        
        gridLayout.addWidget(self.proxyCheckBox, 1, 0)
        gridLayout.addWidget(self.proxyLabel, 2, 0)
        gridLayout.addWidget(self.proxyLineEdit, 2, 1)
        gridLayout.addWidget(self.proxyPortLabel, 3, 0)
        gridLayout.addWidget(self.proxyPortLineEdit, 3, 1)
        
        buttonBoxLayout = QGridLayout()
        buttonBoxLayout.setSpacing(10)
        buttonBoxLayout.addWidget(self.downloadButton, 0, 0)
        buttonBoxLayout.addWidget(self.cancelButton, 0, 1)
        buttonBoxLayout.addWidget(self.themeButton, 0, 2)
        buttonBox = QFrame(centralWidget)
        buttonBox.setLayout(buttonBoxLayout)
        gridLayout.addWidget(buttonBox, 4, 1)

        gridLayout.addWidget(self.downloadProgressBar, 5, 0, 1, -1)

        self.setCentralWidget(centralWidget)

        self.statusBar = QStatusBar(self)
        self.setStatusBar(self.statusBar)
        self.statusBar.showMessage('Ready.')
        self.setStyleSheet(self.getStyleSheet())

    def getStyleSheet(self):
        darkTheme = '''
            QMainWindow{
                background-color: #121212;
                color: #c2c2c2;
            }
            QLabel{
                color: #c2c2c2;
            }
            QPushButton{
                background-color: #1db954;
                padding: 10px;
                color: #c2c2c2;
                border: 2px solid #1db954;
                border-radius: 5px;
            }
            QPushButton:hover{
                background-color: #1ed760;
                border: 2px solid #1ed760;
            }
            QPushButton:pressed{
                background-color: #19b24d;
                border: 2px solid #19b24d;
            }
            QCheckBox, QLineEdit{
                background-color: #2b2b2b;
                color: #c2c2c2;
                padding: 5px;
                border: 1px solid #202020;
                border-radius: 5px;
            }
            QProgressBar{
                background-color: #2b2b2b;
                border: 2px solid #151515;
            }
        '''
        lightTheme = '''
            QMainWindow{
                background-color: #ffffff;
                color: #404040;
            }
            QLabel{
                color: #404040;
            }
            QPushButton{
                background-color: #1db954;
                padding: 10px;
                color: #ffffff;
                border: 2px solid #1db954;
                border-radius: 5px;
            }
            QPushButton:hover{
                background-color: #1ed760;
                border: 2px solid #1ed760;
            }
            QPushButton:pressed{
                background-color: #19b24d;
                border: 2px solid #19b24d;
            }
            QCheckBox, QLineEdit{
                background-color: #f2f2f2;
                color: #404040;
                padding: 5px;
                border: 1px solid #e5e5e5;
                border-radius: 5px;
            }
            QProgressBar{
                background-color: #f2f2f2;
                border: 2px solid #e5e5e5;
            }
        '''
        return darkTheme if self.darkTheme else lightTheme

    def toggleProxyFields(self, state):
        self.proxyLabel.setEnabled(state)
        self.proxyLineEdit.setEnabled(state)
        self.proxyPortLabel.setEnabled(state)
        self.proxyPortLineEdit.setEnabled(state)
    
    def startDownload(self):
        url = self.urlLineEdit.text().strip()
        if url.strip() == '':
            self.statusBar.showMessage('Video URL is required.')
            return
        self.downloadButton.setEnabled(False)
        self.cancelButton.setEnabled(True)
        self.downloadProgressBar.setMaximum(0)
        
        options = {'url': url}
        if self.proxyCheckBox.isChecked():
            options['proxy'] = self.proxyLineEdit.text().strip()
            options['proxy_port'] = self.proxyPortLineEdit.text().strip()

        self.downloadWorker = DownloadWorker(options)
        self.downloadWorker.downloadFinished.connect(self.onDownloadFinished)
        self.downloadWorker.downloadFailed.connect(self.onDownloadFailed)
        self.downloadWorker.downloadProgress.connect(self.onDownloadProgress)
        self.downloadThread = threading.Thread(target=self.downloadWorker.run)
        self.downloadThread.start()

    def cancelDownload(self):
        if self.downloadWorker:
            self.downloadWorker.isCanceled = True
        self.downloadButton.setEnabled(True)
        self.cancelButton.setEnabled(False)
        self.downloadProgressBar.reset()
        self.downloadProgressBar.setMaximum(0)
        self.statusBar.showMessage('Download canceled.')

    def onDownloadFinished(self):
        self.downloadButton.setEnabled(True)
        self.cancelButton.setEnabled(False)
        self.downloadProgressBar.setValue(100)
        self.downloadProgressBar.setMaximum(0)
        self.statusBar.showMessage('Download successful.')
    
    def onDownloadFailed(self, errorMsg):
        self.downloadButton.setEnabled(True)
        self.cancelButton.setEnabled(False)
        self.downloadProgressBar.reset()
        self.downloadProgressBar.setMaximum(0)
        self.statusBar.showMessage(errorMsg)
    
    def onDownloadProgress(self, totalBytes, downloadedBytes):
        if totalBytes > 0:
            progressPercentage = downloadedBytes * 100 / totalBytes
            self.downloadProgressBar.setMaximum(100)
            self.downloadProgressBar.setValue(progressPercentage)
        else:
            self.downloadProgressBar.setMaximum(0)

    def changeTheme(self):
        self.darkTheme = not self.darkTheme
        self.setStyleSheet(self.getStyleSheet())
        if self.darkTheme:
            self.themeButton.setText('Dark Theme')
        else:
            self.themeButton.setText('Light Theme')
            

if __name__ == '__main__':
    app = QApplication(sys.argv)
    mainWindow = MainWindow()
    mainWindow.show()
    sys.exit(app.exec_())
