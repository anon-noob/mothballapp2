# Wordle
import sys, os, datetime
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton, QHBoxLayout, QMainWindow, QLabel, QSizePolicy
from typing import Literal, Union, Optional
from PyQt5.QtCore import Qt, QTimer, QVariantAnimation
from PyQt5.QtGui import QColor
import random

with open("Minigame_Files/Five Letter Words.txt") as f:
    l = f.read().split()

if getattr(sys, "frozen", False):
    base_path = sys._MEIPASS
else:
    base_path = os.path.abspath(".")

words_file_path = os.path.join(base_path, "Minigame_Files", "Five Letter Words.txt")
with open(words_file_path) as f:
    ALL_FIVE_LETTER_WORDS_SET = set(list(filter(lambda x: len(x) == 5, f.read().split("\n"))))
    

l = ['58541283804c', '5a24cd629f6b', '5dc81f9b3e54', '960b15c1feb', 'a781dac7e73', '68b076d38b8c', '585235332a05', 'a46503c0c7b', '68b19fe53e2c', 'a8f4da2aa2b', '593cabbbb42c', 'e8c375f0a0', '9498ca8666d', '94963bd16c3', '8ec41ea9e83', 'ae94bd7f1fa', '917a2047dbb', '5f98dae5217c', '593b45ed316c', '68afc34bfb24', '68b341b98d74', 'a78469df454', 'e8c8abd149', '90377a8d4d6', '10c024c6be3', '5a2278be24ec', '90377a8e478', '6b6a7d223c7b', '68b128ecde25', '5a241a923d74', 'a0076d76418', '65f581dc72f4', 'a78469de0da', 'a323d8a4bc5', '1105d6693c5', '8ec58eb3ed3', '91aa91aabe1', 'a3226914ca0', '6998d34efb03', '699aecb4063a', '585236180014', '98c0c84c893', 'a320eaf4b71', '68b0b1b73e6d', '593a92c13a33', '65f493253661', '977d019a653', 'e6c359a91d', '9493a0b90dd', 'a7841839a9c', '60835097dd33', '616d13f45c80', '9ec52626d7f', '6423d89252fb', '6422e9f98f33', '94975ac755d', '5eb041bc1881', '8ec1d505d63', 'a74e129f3eb', '68af1123b078', '1001122b17f', '67c63c6f1fbc']
def e():
    globals()['\x63\x68\x72'] = chr
    globals()['\x69\x6e\x74'] = int
    f = lambda n: (
        str(globals()['\x69\x6e\x74'](n, 16))
    )
    g = lambda s: (
        (lambda i=0, r="": 
            r if i >= len(s) else
            (lambda c: g._setitem(i + len(c), r + globals()['\x63\x68\x72'](int(s[i:i+len(c)]))) or g(s))
            (next(c for c in ('3', '2') if 97 <= int(s[i:i+globals()['\x69\x6e\x74'](c)]) <= 122))
        )()
    )
    globals()['\x65\x6e\x71'] = len
    g._setitem = lambda i, r: setattr(g, "_i", i) or setattr(g, "_r", r) or True
    g._i = 12-3+4-9-5+1
    g._r = ""
    def g(s):
        i = 0
        r = ""
        while i < globals()['\x65\x6e\x71'](s):
            for p in (6/2, 6/3):
                p = list(map(globals()['\x69\x6e\x74'], [p]))[0]
                if i + p <= len(s):
                    y = globals()['\x69\x6e\x74'](s[i:i+p])
                    if 3*(4**2-5)*3-2 <= y <= (10+1)**2+1:
                        r += globals()['\x63\x68\x72'](y)
                        i += p
                        break
            else:
                break
        return r

    return list(map(lambda x: g(f(x)), l))
PARKOUR_FIVE_LETTER_WORDS = e()
ALL_FIVE_LETTER_WORDS_SET = ALL_FIVE_LETTER_WORDS_SET.union(set(PARKOUR_FIVE_LETTER_WORDS))
ALL_FIVE_LETTER_WORDS_LIST = list(ALL_FIVE_LETTER_WORDS_SET)

GREEN = "#6aaa64"
YELLOW = "#F8E300"
GRAY = "#1F1F1F"
ORANGE = "#E75900"
BLUE = "#0099FF"
RED = "#ff0000"



class GUI(QMainWindow):
    # gameStates
    IN_PROGRESS = 0
    WIN = 1
    LOSE = 2

    # guesses
    UNKNOWN = 0
    CORRECT = 1
    PARTIAL_CORRECT = 2
    INCORRECT = 3

    def __init__(self):
        super().__init__()
        self.help_window = None
        random.seed(int(datetime.datetime.now(datetime.timezone.utc).toordinal()))
        self.sol = random.choice(PARKOUR_FIVE_LETTER_WORDS)
        self.gameState = self.IN_PROGRESS

        self.sol_letter_count = {}
        for i in self.sol:
            if i not in self.sol_letter_count:
                self.sol_letter_count[i] = 1
            else:
                self.sol_letter_count[i] += 1

        self.contrast_mode = False
        self.button_states: list[list[int]] = []

        self.acceptInput = True

        central_widget = QWidget()
        central_widget.setStyleSheet("background-color: #2e2e2e;color: white")
        central_widget.setMinimumWidth(800)

        self.main_layout = QHBoxLayout(central_widget)

        
        self.game_interface = QVBoxLayout()
        self.game_interface.setAlignment(Qt.AlignCenter)
        self.setCentralWidget(central_widget)

        self.info_label = QLabel("Good Luck!")
        self.info_label.setStyleSheet("font-size: 20pt")
        self.info_label.setAlignment(Qt.AlignCenter)
        self.game_interface.addWidget(self.info_label)

        # Word grid (6 rows x 5 columns)
        self.grid_layout = QVBoxLayout()
        self.grid_layout.setAlignment(Qt.AlignCenter)
        self.display_buttons: list[list[QPushButton]] = []
        for _ in range(6):
            row = QHBoxLayout()
            cells = []
            for _ in range(5):
                cell = QPushButton("")
                cell.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
                cell.setFixedSize(70,70)
                cell.setStyleSheet("background-color: #444; color: white; font-size: 24px; border: 2px solid #666;")
                cell.setEnabled(False)
                row.addWidget(cell)
                cells.append(cell)
            self.grid_layout.addLayout(row)
            self.display_buttons.append(cells)
        self.game_interface.addLayout(self.grid_layout)

        self.letter_pointer = 0
        self.guess_count = 0
        self.current_letter_guesses = []


        # Keyboard layout
        keyboard_layout = QVBoxLayout()
        keyboard_layout.setAlignment(Qt.AlignCenter)
        keys = [
            list("QWERTYUIOP"),
            list("ASDFGHJKL"),
            ["DEL"] + list("ZXCVBNM") + ["ENTER"]
        ]
        self.key_buttons = {}
        self.key_button_states = {}
        for row_keys in keys:
            row_layout = QHBoxLayout()
            row_layout.setAlignment(Qt.AlignCenter)
            for key in row_keys:
                btn = QPushButton(key)
                btn.clicked.connect(lambda _, k=key: self.pressedKey(k))
                btn.setStyleSheet(
                    "QPushButton {background-color: #555; color: white; font-size: 22px; border-radius: 6px; }" +
                    "QPushButton:pressed { background-color: #888; border: 2px inset #aaa; }"
                )
                row_layout.addWidget(btn)
                self.key_buttons[key] = btn
                self.key_button_states[key] = 0
            keyboard_layout.addLayout(row_layout)
        self.game_interface.addLayout(keyboard_layout)

        self.main_layout.addLayout(self.game_interface)

        self.right_sidebar = QVBoxLayout()

        self.help_button = QPushButton("Help")
        self.help_button.setStyleSheet("font-size: 20pt")
        self.help_button.clicked.connect(self.openHelp)
        self.right_sidebar.addWidget(self.help_button)

        self.contrast_button = QPushButton("Contrast")
        self.contrast_button.setStyleSheet("font-size: 20pt")
        self.contrast_button.clicked.connect(self.toggleContrastMode)
        self.right_sidebar.addWidget(self.contrast_button)

        self.share = QPushButton("Share")
        self.share.setStyleSheet("font-size: 20pt")
        self.share.clicked.connect(self.shareToClipboard)
        self.right_sidebar.addWidget(self.share)

        self.main_layout.addLayout(self.right_sidebar)

        QTimer.singleShot(0, lambda: self.resizeEvent(None))

    def shareToClipboard(self):
        if self.gameState == self.IN_PROGRESS:
            return
        
        if self.contrast_mode:
            correct = "🟧"
            partial = "🟦"
        else:
            correct = "🟩"
            partial = "🟨"
        incorrect = "⬛"

        rows = []
        for row in range(self.guess_count):
            squares = ""
            for col in range(5):
                state = self.button_states[row][col]
                if state == self.CORRECT:
                    squares += correct
                elif state == self.PARTIAL_CORRECT:
                    squares += partial
                else:
                    squares += incorrect
            rows.append(squares)

        guess_count = f"{self.guess_count}/6" if self.gameState==self.WIN else "Failed"
        result = f"Parkour Wordle {guess_count}\n" + "\n".join(rows)
        QApplication.clipboard().setText(result)
        self.info_label.setText("Copied to clipboard!")

    def toggleContrastMode(self):
        if not self.acceptInput:
            return
        if self.contrast_mode == False:
            self.contrast_button.setStyleSheet("background-color:" + "#752D00" + ";font-size: 20pt;")
            self.contrast_mode = True
        elif self.contrast_mode == True:
            self.contrast_button.setStyleSheet("font-size: 20pt;")
            self.contrast_mode = False

        for row in range(min(self.guess_count,6)):
            for button in range(5):
                if self.button_states[row][button] == self.CORRECT:
                    self.display_buttons[row][button].setStyleSheet(
                        "background-color:" + self.letterCorrectPositionColor() + "; color: black; font-size: 24pt; border: 2px solid #666;"
                    )
                elif self.button_states[row][button] == self.PARTIAL_CORRECT:
                    self.display_buttons[row][button].setStyleSheet(
                        "background-color:" + self.letterInWordColor() + "; color: black; font-size: 24pt; border: 2px solid #666;"
                    )
        
        for key, btn in self.key_buttons.items():
            btn.setStyleSheet(
                "QPushButton {background-color: " + self.intToColor(self.key_button_states[key]) + "; color: " + ('black' if self.intToColor(self.key_button_states[key]) in (GREEN, YELLOW, ORANGE, BLUE) else 'white') + "; font-size: 22px; border-radius: 6px; }" +
                "QPushButton:pressed { background-color: #888; border: 2px inset #aaa; }"
            )
        
        if self.help_window is not None and self.help_window.isVisible():
            self.help_window.changedContrastMode()

    def checkWord(self):
        if "".join(self.current_letter_guesses).lower() not in ALL_FIVE_LETTER_WORDS_SET:
            self.info_label.setText("Not a valid word!")
            g = self.guess_count
            for i in range(5):
                QTimer.singleShot(i*50, lambda x=i: self.animateCell(self.display_buttons[g][x], "#444", RED, duration=200))
                QTimer.singleShot(i*50 + 200, lambda x=i: self.animateCell(self.display_buttons[g][x], RED, "#444", duration=200))
            return

        self.acceptInput = False
        colored = [False, False, False, False, False]
        count = {} | self.sol_letter_count
        self.button_states.append(['', '', '', '', ''])

        # Check for greens
        for i, letter in enumerate(self.current_letter_guesses):
            letter = letter.lower()
            if letter == self.sol[i] and count[letter]:
                QTimer.singleShot(i*200, lambda g=self.guess_count, x=i: self.animateCell(self.display_buttons[g][x], "#444", self.letterCorrectPositionColor()))
                count[letter] -= 1
                colored[i] = True
                self.button_states[self.guess_count][i] = self.CORRECT
                if self.key_button_states[letter.upper()] != self.CORRECT:
                    curr = self.intToColor(self.key_button_states[letter.upper()])
                    self.key_button_states[letter.upper()] = self.CORRECT
                    QTimer.singleShot(i*200, lambda y=letter.upper(): self.animateKey(self.key_buttons[y], curr, self.letterCorrectPositionColor()))

        if all(colored):
            self.guess_count += 1
            QTimer.singleShot(1500, self.victory)
            return

        # Check for yellow
        for i, letter in enumerate(self.current_letter_guesses):
            letter = letter.lower()
            if letter in self.sol and count[letter] and not colored[i]:
                QTimer.singleShot(i*200, lambda g=self.guess_count, x=i: self.animateCell(self.display_buttons[g][x], "#444", self.letterInWordColor()))
                count[letter] -= 1
                colored[i] = True
                self.button_states[self.guess_count][i] = self.PARTIAL_CORRECT

                if self.key_button_states[letter.upper()] not in (self.CORRECT, self.PARTIAL_CORRECT):
                    curr = self.intToColor(self.key_button_states[letter.upper()])
                    self.key_button_states[letter.upper()] = self.PARTIAL_CORRECT
                    QTimer.singleShot(i*200, lambda y=letter.upper(): self.animateKey(self.key_buttons[y], curr, self.letterInWordColor()))
                


        # Color the rest gray
        for i, letter in enumerate(self.current_letter_guesses):
            if not colored[i]:
                QTimer.singleShot(i*200, lambda g=self.guess_count, x=i: self.animateCell(self.display_buttons[g][x], "#444", self.letterNotInWordColor()))
                self.button_states[self.guess_count][i] = self.INCORRECT
                if self.key_button_states[letter.upper()] == 0:
                    curr = self.intToColor(self.key_button_states[letter.upper()])
                    self.key_button_states[letter.upper()] = self.INCORRECT
                    QTimer.singleShot(i*200, lambda y=letter.upper(): self.animateKey(self.key_buttons[y], curr, self.letterNotInWordColor()))

        self.guess_count += 1
        self.current_letter_guesses = []
        self.letter_pointer = 0

        if self.guess_count == 6:
            QTimer.singleShot(1500, self.defeat)
        else:
            self.info_label.setText(f"Guessed {self.guess_count} of 6")
            QTimer.singleShot(1500, self.setAcceptInput)

    def setAcceptInput(self):
        self.acceptInput = True

    def victory(self):
        self.info_label.setText(f"Victory in {self.guess_count} guesses")
        self.setAcceptInput()
        self.gameState = self.WIN

    def defeat(self):
        self.info_label.setText(f"Defeat! Word was {self.sol.upper()}")
        self.setAcceptInput()
        self.gameState = self.LOSE

    def pressedKey(self, key):
        if not self.acceptInput or self.gameState != self.IN_PROGRESS:
            return
        
        if key == "DEL":
            if self.letter_pointer > 0:
                self.letter_pointer -= 1
                self.display_buttons[self.guess_count][self.letter_pointer].setText(None)
                self.current_letter_guesses.pop()
        elif key == "ENTER":
            if self.letter_pointer == 5:
                self.checkWord()
        else:
            if self.letter_pointer < 5:
                self.display_buttons[self.guess_count][self.letter_pointer].setText(key)
                self.current_letter_guesses.append(key)
                self.letter_pointer += 1

    def resizeEvent(self, a0):
        a = self.grid_layout.geometry().height()
        b = self.grid_layout.geometry().width()
        size = min(max(int(min(a,b)/7), 70),120)

        for row in self.display_buttons:
            for cell in row:
                cell.setFixedSize(size, size)

        for key,cell in self.key_buttons.items():
            if key in ("ENTER", "DEL"):
                cell.setFixedSize(size, size-20)
            else:
                cell.setFixedSize(size-20, size-20)

        return super().resizeEvent(a0)

    def keyPressEvent(self, a0):
        key = a0.key()
        if key == Qt.Key_Return or key == Qt.Key_Enter:
            a = "ENTER"
        elif key == Qt.Key_Backspace:
            a = "DEL"
        elif Qt.Key_A <= key <= Qt.Key_Z:
            a = chr(key)
        else:
            return
        self.pressedKey(a)
        return super().keyPressEvent(a0)
    
    def letterCorrectPositionColor(self):
        return ORANGE if self.contrast_mode else GREEN

    def letterInWordColor(self):
        return BLUE if self.contrast_mode else YELLOW

    def letterNotInWordColor(self):
        return GRAY

    # Helper to animate color
    def animateCell(self, cell, start_color, end_color, duration=350):
        anim = QVariantAnimation(cell, duration=duration, startValue=QColor(start_color), endValue=QColor(end_color))
        anim.valueChanged.connect(
            lambda color: cell.setStyleSheet(
                f"background-color: {color.name()}; color: {'black' if end_color in (GREEN, YELLOW, ORANGE, BLUE) else 'white'}; font-size: 24px; border: 2px solid #666;"
            )
        )
        anim.start()
    
    def animateKey(self, key, start_color, end_color, duration=350):
        anim = QVariantAnimation(key, duration=duration, startValue=QColor(start_color), endValue=QColor(end_color))
        anim.valueChanged.connect(
            lambda color: key.setStyleSheet(
                    "QPushButton {background-color: " + color.name() + "; color: " + ('black' if end_color in (GREEN, YELLOW, ORANGE, BLUE) else 'white') + "; font-size: 22px; border-radius: 6px; }" +
                    "QPushButton:pressed { background-color: #888; border: 2px inset #aaa; }"
            )
        )
        anim.start()
    
    def intToColor(self, n: int):
        match n:
            case self.UNKNOWN:
                return "#555"
            case self.CORRECT:
                return self.letterCorrectPositionColor()
            case self.PARTIAL_CORRECT:
                return self.letterInWordColor()
            case self.INCORRECT:
                return self.letterNotInWordColor()
    
    def openHelp(self):
        if self.help_window is not None and self.help_window.isVisible():
            self.help_window.activateWindow()
            return
        self.help_window = HelpWindow(self.contrast_mode, self)
        self.help_window.show()


class HelpWindow(QMainWindow):
    def __init__(self, contrast_mode: bool, parent=None):
        super().__init__(parent)
        self.contrast_mode = contrast_mode

        self.setWindowTitle("How to Play Parkour Wordle")
        self.setStyleSheet("background-color: #2e2e2e; color: white; font-size: 12px;")
        self.setWindowTitle("How to Play")
        self.setMinimumSize(800,900)
        self.setMaximumSize(1200,1000)

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        c = QVBoxLayout(self.central_widget)
        
        title = QLabel()
        title.setText("""<html><body style="background-color:#2e2e2e; color:#ffffff; font-size:24pt; white-space: pre-wrap;">How to Play</body><html>""")
        title.setAlignment(Qt.AlignCenter)
        title.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Minimum)
        c.addWidget(title)
        c.setSpacing(8)
        c.setContentsMargins(10, 10, 10, 10)

        self.label = QLabel()
        self.label.setWordWrap(True)
        self.label.setText(self.text1())
        c.addWidget(self.label)
        
        self.word = "GREAT"
        colors = self.getColors()

        example = QHBoxLayout()
        example.setAlignment(Qt.AlignCenter)
        self.buttons = []
        for i, letter, color in zip(range(5), self.word, colors):
            p = QPushButton(letter)
            p.setStyleSheet(
                "background-color:" + color + "; color: black; font-size: 24pt; border: 2px solid #666;"
            )
            p.setFixedSize(100,100)
            self.buttons.append(p)
            example.addWidget(p)

        c.addLayout(example)

        self.label2 = QLabel()
        self.label2.setText(self.text2())
        self.label2.setWordWrap(True)
        self.label2.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Minimum)
        c.addWidget(self.label2)

        title2 = QLabel()
        title2.setText("""<html><body style="background-color:#2e2e2e; color:#ffffff; font-size:24pt; white-space: pre-wrap;">Extra Notes</body><html>""")
        title2.setAlignment(Qt.AlignCenter)
        c.addWidget(title2)

        self.label3 = QLabel()
        self.label3.setText(self.text3())
        self.label3.setWordWrap(True)
        self.label3.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Minimum)
        c.addWidget(self.label3)

    def colorHtml(self, text, style: int):
        if style == 0:
            return f"<span style='color:#5f5f5f'>{text}</span>"
        elif style == 1:
            return f"<span style='color:{BLUE if self.contrast_mode else YELLOW}'>{text}</span>"
        elif style == 2:
            return f"<span style='color:{ORANGE if self.contrast_mode else GREEN}'>{text}</span>"

    def text1(self):
        return f"""<html><body style="background-color:#2e2e2e; color:#ffffff; font-size:16pt; white-space: pre-wrap;">
<div>Guess the minecraft parkour word in 6 or fewer tries. <span style='color:{ORANGE if self.contrast_mode else GREEN}'>{'Orange' if self.contrast_mode else 'Green'}</span> letters indicate the letter is in the right place. <span style='color:{BLUE if self.contrast_mode else YELLOW}'>{'Blue' if self.contrast_mode else 'Yellow'}</span> letters indicate the letter is in the word but in the wrong place. <span style='color:{"#5f5f5f"}'>Gray</span> letters indicate the letter is not in the word.<div>
</body></html>"""

    def text2(self):
        return f"""<html><body style="background-color:#2e2e2e; color:#ffffff; font-size:16pt; white-space: pre-wrap;">
<div>In this example, the letters {self.colorHtml('R', 2)} and {self.colorHtml('E',2)} are in the correct spot. The letters {self.colorHtml('G', 1)} and {self.colorHtml('T',1)} are in the word but not in the right spot. The letter {self.colorHtml('A',0)} is not in the word.</div>
</body></html>"""
    
    def text3(self):
        return f"""<html><body style="background-color:#2e2e2e; color:#ffffff; font-size:16pt; white-space: pre-wrap;">
<div>The parkour word can be plural. It can also be a player name, but only if the player name corresponds to a commonly used name for a jump or strategy.</div>
</body></html>"""
    
    def getColors(self):
        return (BLUE, ORANGE, ORANGE, "#5f5f5f", BLUE) if self.contrast_mode else (YELLOW, GREEN, GREEN, "#5f5f5f", YELLOW)
    
    def changedContrastMode(self):
        self.contrast_mode = not self.contrast_mode
        self.label.setText(self.text1())
        self.label2.setText(self.text2())
        self.label3.setText(self.text3())

        for btn, color in zip(self.buttons, self.getColors()):
            btn.setStyleSheet(
                "background-color:" + color + "; color: black; font-size: 24pt; border: 2px solid #666;"
            )
