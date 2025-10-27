import sys
import traceback
import datetime
import FileHandler
import os
import json
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QScrollArea, QSizePolicy, QLabel, QGridLayout, QMessageBox

class CrashHandler:
    def __init__(self, mothball_instance):
        self.mothabll_instance = mothball_instance

    def f(self, exctype, value, trace_back):
        now = datetime.datetime.now()
        s = f"-----===== < Crash Log at {now.date()} {now.hour:>02d}:{now.minute:>02d}:{now.second:>02d} > =====-----"
        with open(FileHandler.getPathtoLogs(),'a') as f:
            print(s, file=f)
            last_traceback_string = "".join(traceback.format_exception(exctype, value, trace_back))
            print(last_traceback_string, file=f)

            if self.mothabll_instance.name:
                p = FileHandler.getPathToLastState()
                print(f"Getting path: {p}", file=f)
                with open(os.path.join(p, "LastState.json"), 'w') as file:
                    json.dump({"crashed":True, "tempfile":False, "log": last_traceback_string}, file)
                self.mothabll_instance.saveFile()
            else:
                p = FileHandler.getPathToLastState()
                with open(os.path.join(p, "tempfile.json"), 'w') as file:
                    json.dump(self.mothabll_instance.getAllCellData(), file)
                with open(os.path.join(p, "LastState.json"), 'w') as file:
                    json.dump({"crashed":True, "tempfile":True, "log": last_traceback_string}, file)
            print("Report this issue to @anonnoob over at https://github.com/anon-noob/mothballapp2 and be sure to copy and paste the entire log.", file=f)
            print("-----===== < END of Crash Log > =====-----\n", file=f)
        
        ErrorLogMessageBox.showlogs("A Crash has Occured!", "Mothball has encountered an unhandled error. See the logs below. You can also view these at Documents/Mothball/Logs.", last_traceback_string)
        sys.exit(-1)


class ErrorLogMessageBox(QMessageBox):
    def __init__(self, icon, title, message1, buttons, logs, message2 = None, *args, **kwargs):
        super().__init__(icon, title, message1, buttons, *args, **kwargs)

        self.setIcon(icon)
        self.setWindowTitle(title)
        self.setText(message1)

        grd = self.findChild(QGridLayout)
        if grd is not None:
            scrll = QScrollArea(self)
            scrll.setWidgetResizable(True)
            scrll.setMinimumSize(450, 300)
            scrll.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

            lbl = QLabel(logs)
            lbl.setWordWrap(True)
            lbl.setAlignment(Qt.AlignmentFlag.AlignTop)
            lbl.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse | Qt.TextInteractionFlag.TextSelectableByKeyboard)
            scrll.setWidget(lbl)
            grd.addWidget(scrll, 1, 1, 1, 2)

            if message2:
                a = QLabel(message2)
                grd.addWidget(a, 2,1)
        else:
            self.setDetailedText(logs)
            
    @staticmethod
    def showlogs(title, message, logs):
        return ErrorLogMessageBox(QMessageBox.Icon.Critical, title, message, QMessageBox.StandardButton.Ok, logs).exec_()