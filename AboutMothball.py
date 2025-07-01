"""
The about window of Mothball, using `RenderViewer` to display text.
"""
import sys
from PyQt5.QtWidgets import (
    QApplication, QMainWindow
)

from TextCell import MDLinter, RenderViewer

class MainWindow(QMainWindow):
    def __init__(self, generalOptions: dict, colorOptions: dict, textOptions: dict):
        super().__init__()
        self.generalOptions = generalOptions
        self.colorOptions = colorOptions
        self.textOptions = textOptions
        self.setWindowTitle("About")
        self.setGeometry(100, 100, 900, 600)

        self.pages = {}

        self.current_doc = None  # Track which document is currently loaded

        # QTextBrowser for the document viewer
        self.text_browser = RenderViewer(generalOptions,colorOptions,textOptions,self)

        # Set main layout
        # container = QWidget()
        # layout = QVBoxLayout(container)
        # layout.addWidget(splitter)
        self.setCentralWidget(self.text_browser)

        self.loadDocument()

    def loadDocument(self):
        md = """# About Mothball
A Minecraft movement/parkour calculator, complete with an IDE.

Mothball is an efficient tool for stratfinding Minecraft parkour. You are using the GUI version of Mothball, which is a graphical user interface for Mothball providing a user-friendly experience which includes syntax highlighting and a file save system. If you have any questions or need help, please refer to the help pages.

The GUI version of Mothball is still in development, so there may be bugs, missing features or performance issues, though performance shouldn't be a major concern for most tasks. If you encounter any issues, please report them to anonnoob.

## Discord Bot Version
Original Mothball Concept (in the form of a discord bot) by CyrenArkade: [https://github.com/CyrenArkade/mothball](https://github.com/CyrenArkade/mothball)

Updated Discord Bot by anonnoob (forked from CyrenArkade): [https://github.com/anon-noob/mothball](https://github.com/anon-noob/mothball)

## Contacts
Email: theanonnoob@gmail.com
GitHub: [https://github.com/anon-noob/mothballapp](https://github.com/anon-noob/mothballapp)

# Similar Tools
Other parkour related tools: 
    - [https://github.com/drakou111/MBS](https://github.com/drakou111/MBS) To check if a pixel pattern is constructable, supports all versions of Minecraft
    - [https://github.com/drakou111/OMF](https://github.com/drakou111/OMF) To find inputs that give optimal movement given constraints. Obviously optimal does not mean human doable, so be aware of its limitations.
    - [https://github.com/Leg0shii/ParkourCalculator](https://github.com/Leg0shii/ParkourCalculator) If abstraction and efficiency is too hard, this is a tool to simulate movement with an actual minecraft-world-like interface. Comes with AI pathfinding for general naviagation purposes, or trying to get the fastest times. As of right now, specializes in 1.8, 1.12, and 1.20 parkour.
    
Lastly, if you haven't already, download MPK/CYV to enhance your in game parkour abilities. A quick google search will take you to the right place. We recommend MPK for 1.8 - 1.12 parkour, and CYV for 1.20+ parkour.

# Credits
To CyrenArkade for the original Mothball concept in the form of a discord bot
To anonnoob (myself) for updating Mothball and creating the GUI version
To hammsamichz for helping with mothball help pages
To Erasmian (youtube: [https://www.youtube.com/@3rasmian](https://www.youtube.com/@3rasmian)) for helping us notify Mojang to retain good movement mechanics. 
To everyone else who has contributed to Mothball, whether it be through code, suggestions, or bug reports
And to you for using Mothball!
"""
        self.text_browser.renderTextfromMarkdown(MDLinter(self.generalOptions, self.colorOptions, self.textOptions), md)



if __name__ == "__main__":
    import FileHandler
    a=FileHandler.getCodeColorSettings()
    b=FileHandler.getGeneralSettings()
    c=FileHandler.getTextColorSettings()
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
