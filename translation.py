'''
Time    : 2020.06.11
Author  : walirt
File    : translation.py
License : GPL
'''
import os
import re # main fuction no use, import for script use
import sys
import time 
import ctypes # main fuction no use, import for script use
import random # main fuction no use, import for script use
import hashlib # main fuction no use, import for script use
from math import sqrt
from functools import partial
from shutil import copy as copy_file
from tempfile import NamedTemporaryFile
from importlib import import_module, reload
from concurrent.futures import ThreadPoolExecutor

import requests # main fuction no use, import for script use
from playsound import playsound

from pynput import mouse, keyboard
from pynput.mouse import Button
from pynput.keyboard import Key
from PySide6.QtWidgets import \
	QMenu, \
	QStyle, \
	QLabel, \
	QWidget, \
	QComboBox, \
	QSpacerItem, \
	QFileDialog, \
	QPushButton, \
	QSizePolicy, \
	QVBoxLayout, \
	QHBoxLayout, \
	QApplication, \
	QStyleOption, \
	QSystemTrayIcon, \
	QGraphicsDropShadowEffect  
from PySide6.QtGui import \
	Qt, \
	QIcon, \
	QFont, \
	QBrush, \
	QColor, \
	QCursor, \
	QAction, \
	QPainter, \
	QPalette, \
	QGuiApplication
from PySide6.QtCore import \
	Qt as CoreQt, \
	Slot, \
	QSize, \
	QPoint, \
	Signal, \
	QTimer, \
	QObject, \
	QMimeData, \
	QCoreApplication

SOURCE_SCRIPT_PACKAGE = "source_script"
SOURCE_SCRIPT_PACKAGE_PATH = os.path.abspath(SOURCE_SCRIPT_PACKAGE)
TMP_FILES = []

executor = ThreadPoolExecutor(max_workers=5, thread_name_prefix="translator")

def threadExec(func, callback=None, *args, **kwargs):
	future = executor.submit(func, *args, **kwargs)
	if callback is not None and callable(callback):
		future.add_done_callback(callback)
	return future

def chainThreadExec(funcs, *args, **kwargs):
	f = funcs[0]
	future = executor.submit(f, *args, **kwargs)
	if len(funcs[1:]) == 0:
		return future
	return chainThreadExec(funcs[1:], future.result())

class EventBus(QObject):
	show = Signal(list)
	hide = Signal(list)

	def __init__(self):
		super().__init__()

		self.SHIFT_PRESS = False

		self.LAST_MOUSE_RELEASED_X = None
		self.LAST_MOUSE_RELEASED_Y = None
		self.LAST_MOUSE_RELEASED = None

		self.k_listener = keyboard.Listener(
			on_press=self.onPress,
			on_release=self.onRelease
		)
		self.m_listener = mouse.Listener(on_click=self.onClick)

	def onPress(self, key):
		if key == Key.shift or key == Key.shift_r:
			self.SHIFT_PRESS = True

	def onRelease(self, key):
		if key == Key.shift or key == Key.shift_r:
			self.SHIFT_PRESS = False

	def onClick(self, x, y, button, pressed):
		if button == Button.left:
			if pressed:
				self.LAST_MOUSE_PRESSED = int(time.time() * 1000)
				self.LAST_MOUSE_PRESSED_X = x
				self.LAST_MOUSE_PRESSED_Y = y

				self.hide.emit([x, y])
			else:
				if self.SHIFT_PRESS:
					self.show.emit([x, y])
					return

				now = int(time.time() * 1000)
				if self.LAST_MOUSE_RELEASED is not None and (now - self.LAST_MOUSE_RELEASED < 200):
					self.show.emit([x, y])
					return
						
				dist = sqrt(abs(x - self.LAST_MOUSE_PRESSED_X) + abs(y - self.LAST_MOUSE_PRESSED_Y))
				if now - self.LAST_MOUSE_PRESSED > 200 and dist > 0:
					self.show.emit([x, y])
					return

				self.LAST_MOUSE_RELEASED = int(time.time() * 1000)

	def start(self):
		self.k_listener.start()
		self.m_listener.start()

	def stop(self):
		self.k_listener.stop()
		self.m_listener.stop()

		# recreate listener
		self.k_listener = keyboard.Listener(
			on_press=self.onPress,
			on_release=self.onRelease
		)
		self.m_listener = mouse.Listener(on_click=self.onClick)

class TranslationWidget(QWidget):
	showResult = Signal(dict)

	def __init__(self, event_bus):
		super().__init__()

		self.event_bus = event_bus
		self.is_open = False

		self.resize(300, 76)		
		self.setMinimumSize(QSize(300, 76))
		self.setMaximumSize(QSize(300, 76))
		self.setWindowFlags(CoreQt.WindowCloseButtonHint)
		self.setWindowIcon(QIcon("resource/translate-main.png"))
		self.setWindowTitle("划词翻译")

		self.tray = QSystemTrayIcon()
		self.tray.setIcon(QIcon("resource/translate-main.png"))
		self.tray.activated.connect(self.trayClickEvent)
		self.tray_menu = QMenu()
		self.restore_action = QAction("打开主面板", triggered=self.show)
		self.quit_action = QAction("退出", triggered=self.trayQuitAction)
		self.tray_menu.addAction(self.restore_action)
		self.tray_menu.addAction(self.quit_action)
		self.tray.setContextMenu(self.tray_menu)
		self.tray.setToolTip("划词翻译")
		self.tray.show()
		self.tray_show_msg = False

		self.verticalLayout = QVBoxLayout(self)
		self.verticalLayout_2 = QVBoxLayout()
		self.horizontalLayout = QHBoxLayout()
		self.horizontalLayout_2 = QHBoxLayout()

		self.label = QLabel(self)
		self.label.setText("翻译源：")
		sizePolicy = QSizePolicy(QSizePolicy.Fixed, QSizePolicy.Preferred)
		sizePolicy.setHorizontalStretch(0)
		sizePolicy.setVerticalStretch(0)
		sizePolicy.setHeightForWidth(self.label.sizePolicy().hasHeightForWidth())
		self.label.setSizePolicy(sizePolicy)
		self.label.setMinimumSize(QSize(60, 0))
		self.label.setAlignment(CoreQt.AlignRight | CoreQt.AlignTrailing | CoreQt.AlignVCenter)

		self.comboBox = QComboBox(self)	
		# self.comboBox.addItem("谷歌翻译")
		# self.comboBox.addItem("有道翻译")
		# self.comboBox.addItem("百度翻译")

		self.loadIcon = QIcon("resource/load.png")
		self.reloadIcon = QIcon("resource/reload.png")

		self.pushButton = QPushButton(self)
		self.pushButton.setIcon(self.reloadIcon)
		self.pushButton.setCursor(Qt.PointingHandCursor)
		self.pushButton.setToolTip("重载源")
		sizePolicy_2 = QSizePolicy(QSizePolicy.Fixed, QSizePolicy.Preferred)
		sizePolicy_2.setHorizontalStretch(0)
		sizePolicy_2.setVerticalStretch(0)
		sizePolicy_2.setHeightForWidth(self.pushButton.sizePolicy().hasHeightForWidth())
		self.pushButton.setSizePolicy(sizePolicy_2)
		self.pushButton.clicked.connect(self.reloadResourceScript)

		self.horizontalLayout.addWidget(self.label)
		self.horizontalLayout.addWidget(self.comboBox)
		self.horizontalLayout.addWidget(self.pushButton)

		self.pushButton_2 = QPushButton(self)
		self.pushButton_2.setIcon(QIcon("resource/script.png"))
		self.pushButton_2.setCursor(Qt.PointingHandCursor)
		self.pushButton_2.setText("加载源")
		self.pushButton_2.clicked.connect(self.loadResourceScriptAction)

		self.openIcon = QIcon("resource/start.png")
		self.closeIcon = QIcon("resource/stop.png")

		self.pushButton_3 = QPushButton(self)
		self.pushButton_3.setIcon(self.openIcon)
		self.pushButton_3.setCursor(Qt.PointingHandCursor)
		self.pushButton_3.setText("开启")
		self.pushButton_3.clicked.connect(self.toggleTranslate)		

		self.horizontalLayout_2.addWidget(self.pushButton_2)
		self.horizontalLayout_2.addWidget(self.pushButton_3)

		self.verticalLayout_2.addLayout(self.horizontalLayout)
		self.verticalLayout_2.addLayout(self.horizontalLayout_2)

		self.verticalLayout.addLayout(self.verticalLayout_2)

		self.modules = []
		self.loadResourceScript()

	def resourceScriptIndexOf(self, module_name):
		for i, m in enumerate(self.modules):
			if m["module_name"] == module_name:
				return i
		return -1

	def loadResourceScript(self, file_name=None):
		'''
		The top-level folder must be source_script
		'''
		module_names = []
		if file_name is None:
			for fn in os.listdir(SOURCE_SCRIPT_PACKAGE_PATH):
				if fn.startswith("__") or os.path.splitext(fn)[1] not in (".py", ".pyd"):
					continue
				module_name = f"{SOURCE_SCRIPT_PACKAGE}.{fn.split('.')[0]}"
				module_names.append(module_name)
		else:
			module_names = [f"{SOURCE_SCRIPT_PACKAGE}.{file_name.split('.')[0]}"]

		for module_name in module_names:
			index = self.resourceScriptIndexOf(module_name)
			if index != -1:
				m = self.modules[index]["module"]
				module = reload(m)
			else:
				module = import_module(module_name)
			
			for attr in dir(module):
				if attr.endswith("Translator"):
					cls = getattr(module, attr)
					ins = cls()
					threadExec(ins.preRequest)
					name = ins.name()
					icon = getattr(ins, "icon", lambda: None)()
					m = {
						"module_name": module_name,
						"module": module,
						"cls": cls,
						"ins": ins,
						"name": name,
						"icon": icon
					}
					if index != -1:
						self.modules[index] = m
					else:
						self.modules.append(m)
					break
		
		# clear
		self.comboBox.clear()
		# addItem
		for m in self.modules:
			name = m["name"]
			icon = m["icon"]
			ins = m["ins"]
			self.comboBox.addItem(QIcon(icon), name, ins)

	@Slot()
	def reloadResourceScript(self):
		self.pushButton.setIcon(self.loadIcon)
		self.loadResourceScript()
		QTimer.singleShot(500, lambda: self.pushButton.setIcon(self.reloadIcon))

	@Slot()
	def loadResourceScriptAction(self):
		path, _ = QFileDialog.getOpenFileName(self, "加载源", filter="Python files (*.py *.pyd)")
		if path is None or len(path) == 0:
			return 
		# if load outside script, copy to source_script 
		file_name = os.path.split(path)[1]
		current_path = os.path.join(SOURCE_SCRIPT_PACKAGE_PATH, file_name)
		copy_file(path, current_path)
		self.loadResourceScript(file_name)

	@Slot()
	def trayClickEvent(self, reason):
		if reason == QSystemTrayIcon.ActivationReason.Trigger or reason == QSystemTrayIcon.ActivationReason.DoubleClick:
			self.show()

	def trayQuitAction(self):
		self.tray.setVisible(False)
		if self.is_open:
			self.event_bus.stop()		
		executor.shutdown(wait=False)
		QCoreApplication.instance().quit()

	def closeEvent(self, event):
		event.ignore()
		self.hide()
		if self.tray.supportsMessages() and not self.tray_show_msg:
			self.tray_show_msg = True
			self.tray.showMessage("窗口已隐藏", "退出请右键托盘图标并点击退出")

	@Slot()
	def toggleTranslate(self):
		if self.is_open:
			self.event_bus.stop()
			self.comboBox.setEnabled(True)
			self.pushButton.setEnabled(True)
			self.pushButton_2.setEnabled(True)
			self.pushButton_3.setText("开启")
			self.pushButton_3.setIcon(self.openIcon)
		else:
			self.event_bus.start()
			self.comboBox.setEnabled(False)
			self.pushButton.setEnabled(False)
			self.pushButton_2.setEnabled(False)
			self.pushButton_3.setText("关闭")
			self.pushButton_3.setIcon(self.closeIcon)
		self.is_open = not self.is_open

	@Slot(str)
	def translate(self, data):
		def wrap_callback(pos, future):
			result = future.result()
			result.update({
				"pos": pos
			})
			self.showResult.emit(result)
		pos = data["pos"]
		src = data["text"]
		translator = self.comboBox.currentData()
		callback = partial(wrap_callback, pos)
		threadExec(translator.translate, callback, src)

class TranslationFloatWidget(QWidget):
	backHaul = Signal(dict)
	def __init__(self):
		super().__init__()

		self.k_controller = keyboard.Controller()
		self.clipboard = QGuiApplication.clipboard()

		self.button = QPushButton()
		self.button.setMinimumSize(QSize(30, 30))
		self.button.setMaximumSize(QSize(30, 30))
		self.button.setCursor(QCursor(Qt.PointingHandCursor))
		self.button.setStyleSheet("border-radius: 5px;")
		icon = QIcon("resource/translate-float.png")
		self.button.setIcon(icon)
		self.button.setIconSize(QSize(25, 25))

		self.layout = QVBoxLayout(self)
		self.layout.setSpacing(0)
		self.layout.setContentsMargins(0, 0, 0, 0)
		self.layout.addWidget(self.button)

		self.setWindowFlags(CoreQt.FramelessWindowHint | CoreQt.WindowStaysOnTopHint | CoreQt.Tool)
		self.setAttribute(CoreQt.WA_TranslucentBackground)
		self.setStyleSheet("background-color: white; border-radius: 5px;")

		self.button.clicked.connect(self.translate)
		self.installEventFilter(self)

		self.cache = None

	def show(self, coord):
		if not self.isVisible():
			x, y = coord
			self.move(x + 15, y + 15)
			super().show()
			# self.activateWindow()

	def hide(self, coord):
		if self.isVisible():
			x, y = coord
			wx, wy = self.pos().toTuple()
			if x >= wx and x <= (wx + 30) and y > wy and y <= (wy + 30):
				return
			super().hide()

	@Slot()
	def close(self):
		super().close()

	@Slot()
	def translate(self):
		super().hide()
		self.backup()
		# Add a timer to prevent the clipboard from being repeatedly occupied
		QTimer.singleShot(50, self.copy)
		QTimer.singleShot(100, self.getCliboardData)
		QTimer.singleShot(150, self.restore)

	def backup(self):
		'''
		backup clipboard data
		'''
		self.cache = self.copyMimeData()
		self.clipboard.clear()

	def copyMimeData(self):
		mime_data = self.clipboard.mimeData()
		mime_copy = QMimeData()
		for format_ in mime_data.formats():
			byte_array_data = mime_data.data(format_)
			if len(byte_array_data) == 0:
				continue
			real_format = format_
			if format_.startswith("application/x-qt"):
				if "\"" in format_:
					index_begin = format_.index("\"") + 1
					index_end = format_.index("\"", index_begin)
					real_format = format_[index_begin:index_end]
			mime_copy.setData(real_format, byte_array_data)
		if len(mime_data.formats()) != 0 and len(mime_copy.formats()) == 0:
			if mime_data.hasText():
				mime_copy.setText(mime_data.text())
			if mime_data.hasHtml():
				mime_copy.setHtml(mime_data.html())
			if mime_data.hasUrls():
				mime_copy.setUrls(mime_data.urls())
			if mime_data.hasImage():
				mime_copy.setImageData(mime_data.imageData())
			if mime_data.hasColor():
				mime_copy.setColorData(mime_data.colorData())
		return mime_copy

	def getCliboardData(self):
		mimeData = self.clipboard.mimeData()
		text = mimeData.text()
		if len(text) > 0:
			data = {
				"pos": self.pos().toTuple(),
				"text": text
			}
			self.backHaul.emit(data)

	def copy(self):
		with self.k_controller.pressed(Key.ctrl):
			self.k_controller.tap('c')

	def restore(self):
		'''
		restore clipboard data
		'''
		self.clipboard.clear()
		self.clipboard.setMimeData(self.cache)

	def paintEvent(self, event):
		opt = QStyleOption()
		opt.initFrom(self)
		painter = QPainter(self)
		self.style().drawPrimitive(QStyle.PE_Widget, opt, painter, self)

class TranslationResultWidget(QWidget):
	def __init__(self):
		super().__init__()

		palette = QPalette()
		brush = QBrush(QColor(255, 255, 255, 255))
		brush.setStyle(CoreQt.SolidPattern)
		brush_2 = QBrush(QColor(255, 255, 255, 255))
		brush_2.setStyle(Qt.SolidPattern)
		palette.setBrush(QPalette.Active, QPalette.Window, brush)
		palette.setBrush(QPalette.Inactive, QPalette.Window, brush_2)

		# inner container widget for shadow and border
		self.container_widget = QWidget()
		self.container_widget.setPalette(palette)
		self.container_widget.setAutoFillBackground(True)
		self.container_widget.setMinimumSize(QSize(200, 150))
		# self.container_widget.setMaximumSize(QSize(430, 600))
		self.container_widget.setMaximumWidth(430)

		# container layout
		self.container_layout = QHBoxLayout(self)
		# self.container_layout.setSpacing(6)
		self.container_layout.addWidget(self.container_widget)

		# layout inside the container
		# main layout
		self.horizontalLayout = QHBoxLayout(self.container_widget)
		# left sub first layout
		self.horizontalLayout_2 = QHBoxLayout()
		# left sub second layout
		self.horizontalLayout_3 = QHBoxLayout()
		self.horizontalLayout_3.setSpacing(0)
		# left sub third layout	
		self.horizontalLayout_4 = QHBoxLayout()
		self.horizontalLayout_4.setSpacing(0)

		# left main layout
		self.verticalLayout = QVBoxLayout()
		# right layout
		self.verticalLayout_2 = QVBoxLayout()

		# left first spacer
		self.horizontalSpacer = QSpacerItem(0, 0, QSizePolicy.Expanding, QSizePolicy.Minimum)
		# left second spacer
		self.horizontalSpacer_2 = QSpacerItem(0, 0, QSizePolicy.Expanding, QSizePolicy.Minimum)
		# right spacer
		self.verticalSpacer = QSpacerItem(0, 0, QSizePolicy.Minimum, QSizePolicy.Expanding)

		# font
		font_1 = QFont("微软雅黑", 11, QFont.Normal)
		font_2 = QFont("微软雅黑", 10, QFont.Normal)
		font_3 = QFont("微软雅黑", 10, QFont.Normal)

		# left first label
		self.label = QLabel(self)
		self.label.setWordWrap(True)
		self.label.setFont(font_1)
		# self.label.setAlignment(Qt.AlignBaseline)
		# left second label
		self.label_2 = QLabel(self)
		self.label_2.setFont(font_2)
		# left third label
		self.label_3 = QLabel(self)
		self.label_3.setWordWrap(True)
		self.label_3.setFont(font_1)
		# self.label_3.setAlignment(Qt.AlignBaseline)
		# left fourth label
		self.label_4 = QLabel(self)
		self.label_4.setWordWrap(True)
		self.label_4.setFont(font_3)

		# close pushButton
		self.pushButton = QPushButton(self)
		self.pushButton.setCursor(QCursor(Qt.PointingHandCursor))
		self.pushButton.setStyleSheet("QPushButton{border:none;}")
		self.pushButton.setFlat(True)
		self.pushButton.setToolTip("关闭")
		self.pushButton.setIcon(QIcon("resource/close.png"))
		self.pushButton.setIconSize(QSize(16, 16))

		# fixed pushButton
		self.fixedIcon = QIcon("resource/fixed.png")
		self.unfixedIcon = QIcon("resource/unfixed.png")
		self.pushButton_4 = QPushButton(self)
		self.pushButton_4.setCursor(QCursor(Qt.PointingHandCursor))
		self.pushButton_4.setStyleSheet("QPushButton{border:none;}")
		self.pushButton_4.setFlat(True)
		self.pushButton_4.setToolTip("固定")
		self.pushButton_4.setIcon(self.unfixedIcon)
		self.pushButton_4.setIconSize(QSize(16, 16))

		speakerIcon = QIcon("resource/speaker.png")
		# speaker first pushButton
		self.pushButton_2 = QPushButton(self)
		self.pushButton_2.setCursor(QCursor(Qt.PointingHandCursor))
		self.pushButton_2.setStyleSheet("QPushButton{border:none;}")
		self.pushButton_2.setFlat(True)
		self.pushButton_2.setToolTip("播放")
		self.pushButton_2.setIcon(speakerIcon)
		# speaker second pushButton
		self.pushButton_3 = QPushButton(self)
		self.pushButton_3.setCursor(QCursor(Qt.PointingHandCursor))
		self.pushButton_3.setStyleSheet("QPushButton{border:none;}")
		self.pushButton_3.setFlat(True)
		self.pushButton_3.setToolTip("播放")
		self.pushButton_3.setIcon(speakerIcon)

		self.comboBox = QComboBox(self)

		# left layout add widget
		# sub layout 
		self.horizontalLayout_2.addWidget(self.comboBox)
		self.horizontalLayout_2.addItem(self.horizontalSpacer_2)
		self.horizontalLayout_3.addWidget(self.pushButton_2)
		self.horizontalLayout_3.addWidget(self.label)
		self.horizontalLayout_4.addWidget(self.pushButton_3)
		self.horizontalLayout_4.addWidget(self.label_3)

		self.verticalLayout.addItem(self.horizontalSpacer)
		self.verticalLayout.addLayout(self.horizontalLayout_2)
		self.verticalLayout.addLayout(self.horizontalLayout_3)
		self.verticalLayout.addWidget(self.label_2)
		self.verticalLayout.addLayout(self.horizontalLayout_4)
		self.verticalLayout.addWidget(self.label_4)

		# right layout add widget
		self.verticalLayout_2.addWidget(self.pushButton)
		self.verticalLayout_2.addItem(self.verticalSpacer)
		self.verticalLayout_2.addWidget(self.pushButton_4)

		# main layouy add layout
		self.horizontalLayout.addLayout(self.verticalLayout)
		self.horizontalLayout.addLayout(self.verticalLayout_2)

		self.horizontalLayout.setStretch(0, 9)
		self.horizontalLayout.setStretch(1, 1)
		self.horizontalLayout_2.setStretch(0, 2)	
		self.horizontalLayout_2.setStretch(1, 1)
		self.horizontalLayout_3.setStretch(0, 1)	
		self.horizontalLayout_3.setStretch(1, 9)	
		self.horizontalLayout_4.setStretch(0, 1)
		self.horizontalLayout_4.setStretch(1, 9)
		self.verticalLayout.setStretch(0, 1)
		self.verticalLayout.setStretch(1, 1)
		self.verticalLayout.setStretch(2, 3)
		self.verticalLayout.setStretch(3, 1)
		self.verticalLayout.setStretch(4, 3)

		# button click event bind
		self.pushButton.clicked.connect(self.hide)
		self.pushButton_2.clicked.connect(self.speaker)
		self.pushButton_3.clicked.connect(self.speaker)
		self.pushButton_4.clicked.connect(self.toggleFixed)

		self.setWindowFlags(CoreQt.FramelessWindowHint | CoreQt.WindowStaysOnTopHint | CoreQt.Tool)
		self.setAttribute(CoreQt.WA_TranslucentBackground)

		# add shadow
		shadow = QGraphicsDropShadowEffect(self)
		shadow.setOffset(0)
		shadow.setColor(Qt.gray)
		shadow.setBlurRadius(15)
		self.container_widget.setGraphicsEffect(shadow)

		# Make widgets dragable
		self.drag = False
		self.drag_position = None

		# translator
		self.current_translator = None
		self.current_src_lan = None
		self.current_dest_lan = None

		# comboBox 
		self.comboBox_changed_bind = False

		# fixed
		self.fixed = False		
		self.fixed_pos = None	

	def mousePressEvent(self, event):
		if event.button() == CoreQt.MouseButton.LeftButton:
			self.drag = True
			self.drag_position = event.globalPos() - self.pos()
			event.accept()
		super().mousePressEvent(event)

	def mouseMoveEvent(self, event):
		if self.drag:
			self.move(event.globalPos() - self.drag_position)
			event.accept()
		super().mouseMoveEvent(event)

	def mouseReleaseEvent(self, event):
		self.drag = False
		self.drag_position = None
		super().mouseReleaseEvent(event)

	# def paintEvent(self, event):
	# 	'''
	# 	draw a small triangle
	# 	'''
	# 	painter = QPainter(self)
	# 	painter.setRenderHint(QPainter.Antialiasing, True)
	# 	painter.setPen(Qt.gray)
	# 	painter.setBrush(QColor(255, 255, 255))

	# 	width = self.size().width()
	# 	height = self.size().height()

	# 	top_mid_triangle = QPolygon([
	# 		QPoint(width / 2 - 10, 12),
	# 		QPoint(width / 2, 0),
	# 		QPoint(width / 2 + 10, 12)
	# 	])

	# 	bottom_mid_triangle = QPolygon([
	# 		QPoint(width / 2 - 10, height - 12),
	# 		QPoint(width / 2, height),
	# 		QPoint(width / 2 + 10, height - 12),
	# 	])

	# 	left_triangle = QPolygon([
	# 		QPoint(12, height / 2 - 10),
	# 		QPoint(0, height / 2),
	# 		QPoint(12, height / 2 + 10),
	# 	])

	# 	right_triangle = QPolygon([
	# 		QPoint(width - 12, height / 2 - 10),
	# 		QPoint(width, height / 2),
	# 		QPoint(width - 12, height / 2 + 10),
	# 	])

	# 	top_left_triangle = QPolygon([
	# 		QPoint(12 + 5, 12),
	# 		QPoint(24 + 5, 0),
	# 		QPoint(36 + 5, 12),
	# 	])

	# 	top_right_triangle = QPolygon([
	# 		QPoint(width - 12 - 5, 12),
	# 		QPoint(width - 24 - 5, 0),
	# 		QPoint(width - 36 - 5, 12),
	# 	])

	# 	bottom_left_triangle = QPolygon([
	# 		QPoint(12 + 5, height - 12),
	# 		QPoint(24 + 5, height),
	# 		QPoint(36 + 5, height - 12),
	# 	])

	# 	bottom_right_triangle = QPolygon([
	# 		QPoint(width - 12 - 5, height - 12),
	# 		QPoint(width - 24 - 5, height),
	# 		QPoint(width - 36 - 5, height- 12),
	# 	])

	# 	painter.drawPolygon(bottom_right_triangle)

	def toggleFixed(self):
		self.fixed = not self.fixed
		if self.fixed:
			self.pushButton_4.setIcon(self.fixedIcon)
			self.pushButton_4.setToolTip("解除固定")
			self.fixed_pos = self.pos()
		else:
			self.pushButton_4.setIcon(self.unfixedIcon)
			self.pushButton_4.setToolTip("固定")

	def switchSrcLanguage(self):
		src = self.label.text()
		src_lan = self.comboBox.currentData()
		future = threadExec(self.current_translator.translate, None, src, src_lan)
		object_ = future.result()
		object_.update({
			"pos": self.pos().toTuple()
		})	
		self.show(object_)

	def speaker(self):
		sender = self.sender()
		text = None
		lan = None
		raw = None
		if sender is self.pushButton_2:
			text = self.label.text()
			lan = self.current_src_lan
		elif sender is self.pushButton_3:
			text = self.label_3.text()
			lan = self.current_dest_lan

		if hasattr(self.current_translator, "speak"):
			def saveAsTmp(audio_bytes):
				if audio_bytes is None:
					return None
				audio = NamedTemporaryFile(delete=False, suffix=".mp3")
				audio.write(audio_bytes)
				audio.close()
				return audio.name
			future = chainThreadExec([self.current_translator.speak, saveAsTmp], text, lan)
			tmp_file = future.result()
			if tmp_file is not None:
				threadExec(
					lambda fn: playsound(fn),
					tmp_file
				)
				TMP_FILES.append(tmp_file)

	def myquit(self):
		QCoreApplication.instance().quit()

	def show(self, object_):
		translator = object_["translator"]
		src_lan = object_["src_lan"]
		dest_lan = object_["dest_lan"]
		self.current_src_lan = src_lan
		self.current_dest_lan = dest_lan
		src = object_["src"]
		dest = object_["dest"]
		extend = object_["extend"]
		lans = translator.languages()
		# comboBox fill 
		if self.current_translator != translator:
			# comboBox change event bind
			if self.comboBox_changed_bind:
				self.comboBox.currentTextChanged.disconnect(self.switchSrcLanguage)
			self.current_translator = translator
			self.comboBox.clear()
			for k, v in lans.items():
				self.comboBox.addItem(v, k)
			self.comboBox.currentTextChanged.connect(self.switchSrcLanguage)
			self.comboBox_changed_bind = True

		self.comboBox.blockSignals(True)
		self.comboBox.setCurrentText(lans[src_lan])	
		self.comboBox.blockSignals(False)
		self.label.clear()
		self.label.setText(src)
		# self.label.adjustSize()
		self.label_2.setText(lans[dest_lan])
		self.label_3.clear()
		self.label_3.setText(dest)
		# self.label_3.adjustSize()
		if len(extend) != 0:
			self.label_4.show()
			self.label_4.clear()
			self.label_4.setText(extend)
			# self.label_4.adjustSize()
		else:
			self.label_4.hide()
		
		global_pos_tuple = object_["pos"]
		global_pos = QPoint(*global_pos_tuple)

		self.container_widget.adjustSize()
		self.adjustSize()
		if self.fixed:
			if self.pos() != self.fixed_pos:
				self.move(self.fixed_pos)
		else:
			self.move(global_pos)
		if not self.isVisible():
			super().show()

@Slot(list)
def relayShow(widget, coord):
	widget.show(coord)

@Slot(list)
def relayHide(widget, coord):
	widget.hide(coord)

def clean():
	for tmp_file in TMP_FILES:
		os.remove(tmp_file)

def main():
	app = QApplication([])

	float_widget = TranslationFloatWidget()
	event_bus = EventBus()

	# event_bus signal bind
	bindRelayShow = partial(relayShow, float_widget)
	bindRelayHide = partial(relayHide, float_widget)
	event_bus.show.connect(bindRelayShow)
	event_bus.hide.connect(bindRelayHide)

	main_widget = TranslationWidget(event_bus)
	result_widget = TranslationResultWidget()

	# float_widget signal bind 
	float_widget.backHaul.connect(main_widget.translate)

	# main_widget signal bind
	main_widget.showResult.connect(result_widget.show)

	main_widget.show()

	app.exec()

	print("clean...")
	clean()
	print("bye~")

if __name__ == '__main__':
	main()

