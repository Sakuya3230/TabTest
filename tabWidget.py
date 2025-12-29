# -*- coding: utf-8 -*-try:

import maya.cmds as cmds
import maya.OpenMayaUI as omui

try:
    from PySide6 import QtWidgets, QtGui, QtCore
    from shiboken6 import wrapInstance
except ImportError:
    from PySide2 import QtWidgets, QtGui, QtCore
    from shiboken2 import wrapInstance
    
    
WINDOW_TITLE = "Test Main Window"
OBJECT_NAME = "testMainWindow"

class CollapsibleFrame(QtWidgets.QWidget):
    toggled = QtCore.Signal(bool)  # 展開/折りたたみ時に発信されるシグナル

    kAlignLeft      = 0
    kAlignRight     = 1
    kAlignCenter    = 2
    
    kDefault        = 0
    kSolid          = 1
    kRounded        = 2
    kDashed         = 3
    
    kTriangle       = 0
    kArrow          = 1
    kPlusMinus      = 2
    kCircle         = 3

    # ------------------------------
    # override method
    # ------------------------------
    def __init__(self, title="Title", color=QtGui.QColor(187, 187, 187), parent=None):
        super(CollapsibleFrame, self).__init__(parent)
        self._title                 = title
        self._title_color           = color
        self._title_alignment       = self.kAlignLeft
        self._title_bar_color       = QtGui.QColor(93, 93, 93)
        self._title_bar_height      = 20
        self._icon_color            = QtGui.QColor(238, 238, 238)
        self._icon_alignment        = self.kAlignLeft
        self._icon_style            = self.kTriangle
        self._frame_style           = self.kDefault
        self._rotation_angle        = 0
        
        self._is_collapsed          = False
        self._is_collapsable        = True
        self._is_title_visible      = True
        self._is_icon_visible       = True
        self._is_animation_enabled  = True
        
        self._frame_styles = {
            self.kDefault:      "#ContentFrame{border: none;}",
            self.kSolid:        "#ContentFrame{border: 2px solid gray;}",
            self.kRounded:      "#ContentFrame{border: 2px solid gray; border-radius: 6px;}",
            self.kDashed:       "#ContentFrame{border: 2px dashed gray;}",
        }
        
        self.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)

        # メインレイアウト
        self.main_layout = QtWidgets.QVBoxLayout(self)
        self._updateTitleBarHeight()

        # コンテンツフレーム
        self.frame = QtWidgets.QFrame(self)
        self.frame.setObjectName("ContentFrame")
        self._updateFrameStyle()
        self._frame_geometry = self.frame.geometry()

        # 内部レイアウト
        self.content_layout = QtWidgets.QVBoxLayout(self.frame)
        self.content_layout.setContentsMargins(5, 5, 5, 5)
        self.content_layout.setSpacing(5)
        self.main_layout.addWidget(self.frame)

        # アニメーション
        self._content_anim = QtCore.QPropertyAnimation(self, b"maximumHeight")
        self._content_anim.setDuration(200)
        
        self.icon_animation = QtCore.QVariantAnimation()
        self.icon_animation.setDuration(200)
        self.icon_animation.valueChanged.connect(self._updateIconRotation)

    def mousePressEvent(self, event):
        """タイトルバーのクリックで展開・折りたたみ"""
        if event.pos().y() < self._title_bar_height and self._is_collapsable:
            self._toggle()

    def paintEvent(self, event):
        """カスタム描画（タイトルバー + 三角形アイコン）"""
        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.Antialiasing)

        # タイトルバー描画
        painter.setBrush(self._title_bar_color)
        painter.setPen(QtCore.Qt.NoPen)
        painter.drawRect(0, 0, self.width(), self._title_bar_height)

        # タイトル描画
        if self._is_title_visible:
            font = painter.font()
            font.setBold(True)
            painter.setFont(font)
            font_metrics = QtGui.QFontMetrics(font)
            text_width = font_metrics.horizontalAdvance(self._title)
            
            # タイトル位置
            rect = self.rect()
            if self._title_alignment == self.kAlignLeft:
                if self._is_icon_visible and self._icon_alignment == self.kAlignLeft:
                    text_x = rect.left() + 25
                else:
                    text_x = rect.left() + 10
                
            elif self._title_alignment == self.kAlignRight:
                if self._is_icon_visible and self._icon_alignment == self.kAlignRight:
                    text_x = rect.right() - text_width - 25
                else:
                    text_x = rect.right() - text_width - 10
            else:
                text_x = rect.right() / 2 - text_width / 2 

            painter.setPen(self._title_color)
            text_rect = QtCore.QRect(text_x, 0, text_width, self._title_bar_height)
            painter.drawText(text_rect, QtCore.Qt.AlignVCenter, self._title)
        
        # アイコン描画
        if self._is_icon_visible:
            # アイコン位置
            if self._icon_alignment == self.kAlignLeft:
                icon_pos = QtCore.QPoint(10, self._title_bar_height / 2)
                
            elif self._icon_alignment == self.kAlignRight:
                icon_pos = QtCore.QPoint(self.width() - 10, self._title_bar_height / 2)

            else:
                if self._is_title_visible and self._title_alignment == self.kAlignCenter:
                    icon_pos = QtCore.QPoint(self.width() / 2 - text_width / 2 - 15, self._title_bar_height / 2)
                else:
                    icon_pos = QtCore.QPoint(self.width() / 2, self._title_bar_height / 2)

            if self._icon_style == self.kTriangle:
                self._drawTriangle(painter, icon_pos)
            elif self._icon_style == self.kArrow:
                self._drawArrow(painter, icon_pos)
            elif self._icon_style == self.kPlusMinus:
                self._drawPlusMinus(painter, icon_pos)
            elif self._icon_style == self.kCircle:
                self._drawCircle(painter, icon_pos)

    def resizeEvent(self, event):
        """ウィンドウのリサイズ時にフレームのジオメトリを更新"""
        super(CollapsibleFrame, self).resizeEvent(event)
        # レイアウト内のフレームのサイズを更新
        margin = 0
        width  = self.width() - 2 * margin
        height = self.height() - 2 * margin
        self.frame_geometry = QtCore.QRect(margin, margin + self._title_bar_height, width, height - self._title_bar_height)

    # ------------------------------
    # public method
    # ------------------------------
    def addWidget(self, widget):
        """コンテンツ領域にウィジェットを追加"""
        self.content_layout.addWidget(widget)
        self._updateFrameMaxHeight()

    def insertWidget(self, index, widget):
        """コンテンツ領域にウィジェットを挿入"""
        self.content_layout.insertWidget(index, widget)
        self._updateFrameMaxHeight()
        
    def removeWidget(self, widget):
        """コンテンツ領域からウィジェットを削除"""
        self.content_layout.removeWidget(widget)
        widget.setParent(None)
        self._updateFrameMaxHeight()
        
    def count(self):
        """コンテンツ領域内のウィジェット数を返す"""
        return self.content_layout.count()

    def title(self):
        """タイトル名を返す
        Returns:
            string: タイトル名
        """        
        return self._title
    
    def titleColor(self):
        """タイトルのカラーを返す
        Returns:
            QtGui.QColor: 文字の色
        """        
        return self._title_color
    
    def titleAlignment(self):
        """タイトルの配置を返す

        Returns:
            int: kAlignLeft = 0 kAlignRight = 1 kAlignCenter = 2
        """        
        return self._title_alignment
    
    def titleVisible(self):
        """タイトルの表示状態を返す

        Returns:
            bool: 表示状態
        """   
        return self._is_title_visible
    
    def titleBarColor(self):
        """タイトルバーの背景色を返す

        Returns:
            QtGui.QColor: 背景色
        """        
        return self._title_bar_color
    
    def titleBarHeight(self):
        """タイトルバーの高さを返す

        Returns:
            int: タイトルバーの高さ
        """        
        return self._title_bar_height
    
    def iconColor(self):
        """アイコンのカラーを返す
        Returns:
            QtGui.QColor: アイコンの色
        """        
        return self._icon_color    
    
    def iconAlignment(self):
        """アイコンの配置を返す

        Returns:
            int: kAlignLeft = 0 kAlignRight = 1 kAlignCenter = 2
        """        
        return self._icon_alignment
    
    def iconStyle(self):
        """アイコンのスタイルを返す

        Returns:
            int: kTriangle = 0 kPlusMinus = 1
        """        
        return self._icon_style
    
    def iconVisible(self):
        """アイコンの表示状態を返す

        Returns:
            bool: 表示状態
        """   
        return self._is_icon_visible
    
    def frameStyle(self):
        """フレームのスタイルを返す

        Returns:
            int: kDefault = 0 kSolid = 1 kRounded = 2 kDashed = 3
        """        
        return self._frame_style
        
    def isCollapsed(self):
        """フレームが折りたたまれているかどうか

        Returns:
            bool: 折りたたみ状態
        """        
        return self._is_collapsed
    
    def isCollapsable(self):
        """折りたたみが有効化どうか

        Returns:
            bool: 有効化状態
        """        
        return self._is_collapsable
    
    def isAnimationEnabled(self):
        """アニメーションが有効化どうか

        Returns:
            bool: 有効化状態
        """        
        return self._is_animation_enabled
    
    def setTitle(self, title):
        """タイトルを変更する"""
        self._title = title
        self.update()

    def setTitleColor(self, color):
        """タイトルの文字の色を変更する"""
        self._title_color = color
        self.update()

    def setTitleAlignment(self, alignment):
        """タイトルの配置を変更 (0: kAlignLeft, 1: kAlignRight, 2: kAlignCenter)"""
        if alignment in [self.kAlignLeft, self.kAlignRight, self.kAlignCenter]:
            self._title_alignment = alignment
            self.update()
        
    def setTitleVisible(self, visible):
        """タイトルの表示・非表示を切り替える"""
        self._is_title_visible = visible
        self.update()
        
    def setTitleBarColor(self, color):
        """タイトルバーの背景色を変更"""
        self._title_bar_color = color
        self.update()

    def setTitleBarHeight(self, height):
        """タイトルバーの高さを変更 最小15px"""
        self._title_bar_height = max(15, height)
        self._updateTitleBarHeight()
        self._updateFrameMaxHeight()
        self.update()

    def setIconColor(self, color):
        """アイコンの色を変更する"""
        self._icon_color = color
        self.update()

    def setIconAlignment(self, alignment):
        """アイコンの配置を変更 (0: kAlignLeft, 1: kAlignRight, 2: kAlignCenter)"""
        if alignment in [self.kAlignLeft, self.kAlignRight, self.kAlignCenter]:
            self._icon_alignment = alignment
            self.update()
            
    def setIconStyle(self, style):
        """アイコンの配置を変更 (0: left, 1: kArrow, 2: kPlusMinus, 3: kCircle)"""
        if style in [self.kTriangle, self.kArrow, self.kPlusMinus, self.kCircle]:
            self._icon_style = style
            self.update()

    def setIconVisible(self, visible):
        """タイトルの表示・非表示を切り替える"""
        self._is_icon_visible = visible
        self.update()

    def setFrameStyle(self, style):
        """フレームのスタイルを変更"""
        if style in [self.kDefault, self.kSolid, self.kRounded, self.kDashed]:
            self._frame_style = style
            self._updateFrameStyle()

    def setCollapsedEnabled(self, enabled):
        """折りたたみの効化を変更"""
        self._is_collapsable = enabled

    def setAnimationEnabled(self, enabled):
        """アニメーション有効化を変更"""
        self._is_animation_enabled = enabled

    def setContentsMargins(self, x, y, width, height):
        self.content_layout.setContentsMargins(x, y, width, height)

    def setSpacing(self, spacing):
        self.content_layout.setSpacing(spacing)

    # ------------------------------
    # private method
    # ------------------------------
    def _updateTitleBarHeight(self):
        self.main_layout.setContentsMargins(0, self._title_bar_height, 0, 0)
    
    def _updateFrameStyle(self):
        """フレームデザインを適用"""
        self.frame.setStyleSheet(self._frame_styles.get(self._frame_style, "border: 2px solid gray;"))

    def _updateIconRotation(self, value):
        """アイコンの回転角度を更新"""
        self._rotation_angle = value
        self.update()

    def _updateFrameMaxHeight(self):
        """フレームの最大高さを更新"""
        if not self._is_collapsed:
            self.setMaximumHeight(self._getContentHeight() + self._title_bar_height + self.layout().contentsMargins().top() + self.layout().contentsMargins().bottom())

    def _getContentHeight(self):
        """レイアウト内のすべてのウィジェットの合計最小高さを取得"""
        margin = 5
        total_height = margin
        for i in range(self.content_layout.count()):
            item = self.content_layout.itemAt(i)
            if item.widget():
                total_height += item.widget().sizeHint().height() + margin
        return total_height

    def _toggle(self):
        """折りたたみ/展開を切り替え"""
        self._is_collapsed = not self._is_collapsed

        if self._is_animation_enabled:
            self._content_anim.stop()
            min_height = self._title_bar_height
            
            content_height = self._getContentHeight() + self._title_bar_height + self.layout().contentsMargins().top() + self.layout().contentsMargins().bottom()
            if self._is_collapsed:
                self._content_anim.setStartValue(self.size().height())
                self._content_anim.setEndValue(min_height)
            else:
                self._content_anim.setStartValue(self.maximumHeight())
                self._content_anim.setEndValue(content_height)
            self._content_anim.start()

            # アイコン回転のアニメーション
            if self._icon_alignment == self.kAlignRight:
                start_angle = 0 if self._is_collapsed else 90
                end_angle = 90 if self._is_collapsed else 0
            else:
                start_angle = 0 if self._is_collapsed else -90
                end_angle = -90 if self._is_collapsed else 0

            self.icon_animation.setStartValue(start_angle)
            self.icon_animation.setEndValue(end_angle)
            self.icon_animation.start()
        else:
            min_height = self._title_bar_height + self.layout().contentsMargins().top() + self.layout().contentsMargins().bottom()
            if self._is_collapsed:
                self.setMaximumHeight(min_height)
                self.frame.setVisible(False)
            else:
                self.setMaximumHeight(self._getContentHeight() + self._title_bar_height + self.layout().contentsMargins().top() + self.layout().contentsMargins().bottom())
                self.frame.setVisible(True)

        self.toggled.emit(self._is_collapsed)
        self.update()

    def _drawTriangle(self, painter, center):
        """展開アイコン（三角形）の描画"""
        path = QtGui.QPainterPath()
        
        if self._is_animation_enabled:
            path.moveTo(center.x() - 5, center.y() - 4)
            path.lineTo(center.x() + 5, center.y() - 4)
            path.lineTo(center.x(), center.y() + 4)
            path.closeSubpath()
            
            transform = QtGui.QTransform()
            transform.translate(center.x(), center.y())
            transform.rotate(self._rotation_angle)
            transform.translate(-center.x(), -center.y())
            path = transform.map(path)
        else:
            if self._is_collapsed:
                path.moveTo(center.x() - 4, center.y() - 5)
                path.lineTo(center.x() - 4, center.y() + 5)
                path.lineTo(center.x() + 4, center.y())
            else:
                path.moveTo(center.x() - 5, center.y() - 4)
                path.lineTo(center.x() + 5, center.y() - 4)
                path.lineTo(center.x(), center.y() + 4)
        
        painter.setBrush(self._icon_color)
        painter.setPen(QtCore.Qt.NoPen)
        painter.drawPath(path)
        
    def _drawArrow(self, painter, center):
        """展開アイコン（矢印）の描画"""
        path = QtGui.QPainterPath()
        
        if self._is_animation_enabled:
            path.moveTo(center.x() - 5, center.y() - 2)
            path.lineTo(center.x(), center.y() + 3)
            path.lineTo(center.x() + 5, center.y() - 2)
            
            transform = QtGui.QTransform()
            transform.translate(center.x(), center.y())
            transform.rotate(self._rotation_angle)
            transform.translate(-center.x(), -center.y())
            path = transform.map(path)
        else:
            if self._is_collapsed:
                path.moveTo(center.x() - 2, center.y() - 5)
                path.lineTo(center.x() + 3, center.y())
                path.lineTo(center.x() - 2, center.y() + 5)
            else:
                path.moveTo(center.x() - 5, center.y() - 2)
                path.lineTo(center.x(), center.y() + 3)
                path.lineTo(center.x() + 5, center.y() - 2)

        pen = QtGui.QPen(self._icon_color)
        pen.setWidth(2)
        painter.setPen(pen)
        painter.setBrush(QtCore.Qt.NoBrush)
        painter.drawPath(path)
        
    def _drawPlusMinus(self, painter, center):
        """展開アイコン（プラス、マイナス）の描画"""
        path = QtGui.QPainterPath()

        if self._is_collapsed:
            path.moveTo(center.x() - 4, center.y())
            path.lineTo(center.x() + 4, center.y())
            path.moveTo(center.x(), center.y() - 5)
            path.lineTo(center.x(), center.y() + 5)
        else:
            path.moveTo(center.x() - 5, center.y())
            path.lineTo(center.x() + 5, center.y())

        path.closeSubpath()

        pen = QtGui.QPen(self._icon_color)
        pen.setWidth(2)
        painter.setPen(pen)
        painter.setBrush(QtGui.QColor(0, 0, 0))
        painter.drawPath(path)

    def _drawCircle(self, painter, center):
        """展開アイコン（プラス、マイナス）の描画"""
        pen = QtGui.QPen(self._icon_color)
        pen.setWidth(2)
        painter.setPen(pen)

        if self._is_collapsed:
            painter.setBrush(self._icon_color)
        else:
            painter.setBrush(QtCore.Qt.NoBrush)

        painter.drawEllipse(center, 5, 5)

class ContentsWidget(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super(ContentsWidget, self).__init__(parent)
        self._frames = [] 
        
        self.setup_ui()
        
    def setup_ui(self):
        self.main_layout = QtWidgets.QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(5)
        
        self.content_widget = QtWidgets.QWidget()
        self.scroll_area = QtWidgets.QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setWidget(self.content_widget)
        self.main_layout.addWidget(self.scroll_area)
        
        self.content_layout = QtWidgets.QVBoxLayout(self.content_widget)
        self.content_layout.setContentsMargins(0, 0, 0, 0)
        self.content_layout.setSpacing(5)
        self.content_layout.addStretch()
        
    def addFrame(self, title):
        frame = CollapsibleFrame(title, parent=self)
        self.content_layout.insertWidget(self.content_layout.count() - 1, frame)
        self._frames.append(frame)
        return frame

    def insertFrame(self, index, title):
        frame = CollapsibleFrame(title, parent=self)
        self.content_layout.insertWidget(index, frame)
        self._frames.insert(index, frame)
        return frame
    
    def removeFrame(self, index):
        if 0 <= index < len(self._frames):
            frame = self._frames[index]
            self.content_layout.removeWidget(frame)
            frame.setParent(None)
            del self._frames[index]
            
    def clear(self):
        while self._frames:
            self.removeFrame(0)
            
    def frameCount(self):
        return len(self._frames)
    
    def frame(self, index):
        if 0 <= index < len(self._frames):
            return self._frames[index]
        return None 
    
    def indexOfTitle(self, title):
        for i, f in enumerate(self._frames):
            if f.title() == title:
                return i
        return -1
    
    def indexOf(self, frame):
        for i, f in enumerate(self._frames):
            if f == frame:
                return i
        return -1
    
    def setContentsMargins(self, x, y, width, height):
        self.content_layout.setContentsMargins(x, y, width, height)
        
    def setSpacing(self, spacing):
        self.content_layout.setSpacing(spacing)
        
    def setFrameTitle(self, index, title):
        if 0 <= index < len(self._frames):
            self.frame(index).setTitle(title)   

class CustomTabBar(QtWidgets.QWidget):
    currentChanged  = QtCore.Signal(int)
    tabSelected     = QtCore.Signal(int)
    tabPressed      = QtCore.Signal(int)
    tabReleased     = QtCore.Signal(int)

    # ------------------------------
    # override methods
    # ------------------------------
    def __init__(self, parent=None):
        super(CustomTabBar, self).__init__(parent)
        self._tabs                  = []  # list of dicts {'widget': widget, 'title': title}
        self._current_index         = -1
        self._scroll_offset         = 0
        self._scroll_anim_offset    = 0
        self._dragging              = False
        self._last_mouse_x          = 0
        self._pressed_tab           = -1
        self._highlight_rect        = QtCore.QRectF()
        
        # カスタマイズ用プロパティ
        self._selected_bar_color        = QtGui.QColor(0, 120, 215)
        self._tab_text_color            = QtGui.QColor(200, 200, 200)
        self._tab_text_selected_color   = QtGui.QColor(255, 255, 255)
        self._tab_text_pressed_color    = QtGui.QColor(120, 120, 120)
        self._tab_padding               = 30
        self._tab_spacing               = 2
        self._highlight_height          = 2
        self._bottom_line_color         = QtGui.QColor(180, 180, 180)
        self._bottom_line_width         = 0.2
                
        # アニメーション用
        self._highlight_anim = QtCore.QVariantAnimation(self)
        self._highlight_anim.valueChanged.connect(self._on_highlight_anim)
        
        self._scroll_anim = QtCore.QVariantAnimation(self)
        self._scroll_anim.valueChanged.connect(self._on_scroll_anim)
        
        # マウストラッキング有効化
        self.setMouseTracking(True)
        self.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        
    def sizeHint(self):
        return QtCore.QSize(200, 40)
    
    def paintEvent(self, event):
        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.Antialiasing)

        for i, tab in enumerate(self._tabs):
            rect = self.tabRect(i)
            painter.setPen(QtGui.QPen(self.tabTextColor(i)))
            painter.drawText(rect, QtCore.Qt.AlignCenter, tab['title'])
            
        # アニメーション用ハイライト
        if not self._highlight_rect.isNull():
            highlight_rect = QtCore.QRectF(self._highlight_rect)
            highlight_rect.moveLeft(self._highlight_rect.left() - self._scroll_offset)
            highlight_rect.moveRight(self._highlight_rect.right() - self._scroll_offset)
            painter.setPen(QtCore.Qt.NoPen)
            painter.setBrush(self._selected_bar_color)
            painter.drawRoundedRect(highlight_rect, 2, 2)
            
        elif self._tabs and self._current_index >= 0:
            rect = self.tabRect(self._current_index)
            highlight_rect = QtCore.QRectF(rect.left(), rect.bottom() - self._highlight_height - 1, rect.width(), self._highlight_height)
            painter.setPen(QtCore.Qt.NoPen)
            painter.setBrush(self._selected_bar_color)
            painter.drawRoundedRect(highlight_rect, 2, 2)
            
        # タブバー下部に細いグレーのライン
        painter.setBrush(QtCore.Qt.NoBrush)
        pen = QtGui.QPen(self._bottom_line_color)
        pen.setWidthF(self._bottom_line_width)
        painter.setPen(pen)
        painter.drawLine(0, self.height() - 1, self.width(), self.height() - 1)

    def mousePressEvent(self, event):
        if event.button() == QtCore.Qt.LeftButton:
            self._dragging = True
            self._last_mouse_x = event.x()
            self._drag_start_pos = event.pos()
            self._drag_moved = False
            self._pressed_tab = -1
            for i in range(len(self._tabs)):
                rect = self.tabRect(i)
                if rect.contains(event.pos()):
                    self._pressed_tab = i
                    self.tabPressed.emit(i)
                    self.update()
                    break
                
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self._dragging:
            dx = event.x() - self._last_mouse_x
            self._last_mouse_x = event.x()
            # 5ピクセル以上動いたらドラッグと判定
            if abs(event.x() - self._drag_start_pos.x()) > 15:
                self._drag_moved = True
            self._scroll_offset -= dx
            self._scroll_offset = max(0, self._scroll_offset)
            # 最大値制限
            total_width = 0
            font_metrics = self.fontMetrics()
            padding = 30
            for tab in self._tabs:
                total_width += font_metrics.horizontalAdvance(tab['title']) + padding + 2
            max_offset = max(0, total_width - self.width())
            self._scroll_offset = min(self._scroll_offset, max_offset)
            self.update()
            
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        released_index = -1
        if self._dragging and not self._drag_moved:
            # ドラッグしていなければクリック判定
            for i in range(len(self._tabs)):
                rect = self.tabRect(i)
                if rect.contains(event.pos()):
                    self.setCurrentIndex(i)
                    released_index = i
                    break
                
        self._dragging = False
        self._drag_moved = False
        self._pressed_tab = -1
        self.update()
        if released_index != -1:
            self.tabReleased.emit(released_index)
            
        super().mouseReleaseEvent(event)
        
    def wheelEvent(self, event):
        # ホイールで選択タブも移動
        delta = event.angleDelta().y() if event.angleDelta().y() != 0 else event.angleDelta().x()
        if delta > 0:
            # 前のタブ
            if self._current_index > 0:
                self.setCurrentIndex(self._current_index - 1)
        elif delta < 0:
            # 次のタブ
            if self._current_index < len(self._tabs) - 1:
                self.setCurrentIndex(self._current_index + 1)
        
    # ------------------------------
    # public methods
    # ------------------------------
    def addTab(self, widget, title):
        self._tabs.append({'widget': widget, 'title': title})
        self.update()
    
    def insertTab(self, index, widget, title):
        self._tabs.insert(index, {'widget': widget, 'title': title})
        self.update()
    
    def removeTab(self, index):
        if 0 <= index < len(self._tabs):
            del self._tabs[index]
            if self._current_index >= len(self._tabs):
                self._current_index = len(self._tabs) - 1
            self.update()
    
    def currentIndex(self):
        return self._current_index
    
    def tabCount(self):
        return len(self._tabs)
    
    def tabText(self, index):
        if 0 <= index < len(self._tabs):
            return self._tabs[index]['title']
        return ""
    
    def setTabText(self, index, title): 
        if 0 <= index < len(self._tabs):
            self._tabs[index]['title'] = title
            self.update()
    
    def widget(self, index):    
        if 0 <= index < len(self._tabs):
            return self._tabs[index]['widget']
        return None
    
    def indexOf(self, widget):
        for i, tab in enumerate(self._tabs):
            if tab['widget'] == widget:
                return i
        return -1
    
    def clear(self): 
        self._tabs = []
        self._current_index = -1
        self.update()
        
    def tabRect(self, index):
        font_metrics = self.fontMetrics()
        height = self.height()
        x = -self._getCurrentOffset()
        for i, tab in enumerate(self._tabs):
            title = tab['title']
            width = font_metrics.horizontalAdvance(title) + self._tab_padding
            x += self._tab_spacing
            rect = QtCore.QRect(x, 0, width, height)
            if i == index:
                return rect
            x += width
            
        return QtCore.QRect()
    
    def tabTextColor(self, index):
        if index == self._pressed_tab:
            return self._tab_text_pressed_color
        elif index == self._current_index:
            return self._tab_text_selected_color
        else:
            return self._tab_text_color
        
    def setCurrentIndex(self, index):
        if 0 <= index < len(self._tabs):
            old_index = self._current_index
            self._current_index = index
            self._scroll_to_tab(index)
            # アニメーション開始
            self._start_highlight_animation(old_index, index)
            # シグナル発行
            self.tabSelected.emit(index)
            self.currentChanged.emit(index)
    
    def setTabPadding(self, padding):
        self._tab_padding = padding
        self.update()
        
    def setTabSpacing(self, spacing):
        self._tab_spacing = spacing
        self.update()
        
    def setTabTextColor(self, color):
        self._tab_text_color = QtGui.QColor(color)
        self.update()
        
    def setTabTextSelectedColor(self, color):
        self._tab_text_selected_color = QtGui.QColor(color)
        self.update()
        
    def setTabTextPressedColor(self, color):
        self._tab_text_pressed_color = QtGui.QColor(color)
        self.update()
        
    def setHighlightColor(self, color):
        self._selected_bar_color = QtGui.QColor(color)
        self.update()
        
    def setHighlightHeight(self, height):
        self._highlight_height = height
        self.update()
        
    def setBottomLineColor(self, color):
        self._bottom_line_color = QtGui.QColor(color)
        self.update()
        
    def setBottomLineWidth(self, width):
        self._bottom_line_width = width
        self.update()

    # ------------------------------
    # private methods
    # ------------------------------
    def _getCurrentOffset(self):
        return self._scroll_anim_offset if self._scroll_anim.state() == QtCore.QAbstractAnimation.Running else self._scroll_offset
    
    def _on_highlight_anim(self, value):
        self._highlight_rect = value
        self.update()
    
    def _scroll_to_tab(self, index):
        # 選択タブが見切れている場合に自動でスクロール
        if not self._tabs:
            return
        font_metrics = self.fontMetrics()
        height = self.height()
        padding = 30
        x = 0
        for i, tab in enumerate(self._tabs):
            title = tab['title']
            width = font_metrics.horizontalAdvance(title) + padding
            x += 2
            rect = QtCore.QRect(x, 0, width, height)
            if i == index:
                tab_rect = rect
            x += width
        left_visible = self._scroll_offset
        right_visible = self._scroll_offset + self.width()
        left_margin = 100
        right_margin = 100
        target_offset = self._scroll_offset
        # 左側が見切れている
        if tab_rect.left() < left_visible + left_margin:
            target_offset = max(tab_rect.left() - left_margin, 0)
        # 右側が見切れている
        elif tab_rect.right() > right_visible - right_margin:
            target_offset = tab_rect.right() - self.width() + right_margin
            # 最大値制限
            total_width = 0
            for tab in self._tabs:
                total_width += font_metrics.horizontalAdvance(tab['title']) + padding + 2
            max_offset = max(0, total_width - self.width())
            target_offset = min(target_offset, max_offset)
        # アニメーション
        if target_offset != self._scroll_offset:
            self._scroll_anim.stop()
            self._scroll_anim.setStartValue(self._scroll_offset)
            self._scroll_anim.setEndValue(target_offset)
            self._scroll_anim.setDuration(200)
            self._scroll_anim.start()
            self._scroll_offset = target_offset
        else:
            self.update()

    def _on_scroll_anim(self, value):
        self._scroll_anim_offset = value
        self.update()

    def _start_highlight_animation(self, old_index, new_index):
        if old_index == new_index or old_index < 0 or new_index < 0 or not self._tabs:
            self._highlight_rect = QtCore.QRectF()
            self.update()
            return
        font_metrics = self.fontMetrics()
        height = self.height()
        padding = 30
        
        # 古いタブと新しいタブの矩形を取得
        old_rect = QtCore.QRect()
        new_rect = QtCore.QRect()
        
        x = 0
        for i, tab in enumerate(self._tabs):
            title = tab['title']
            width = font_metrics.horizontalAdvance(title) + padding
            x += 2
            rect = QtCore.QRect(x, 0, width, height)
            if i == old_index:
                old_rect = rect
            if i == new_index:
                new_rect = rect
            x += width
            
        highlight_height = self._highlight_height
        old_highlight = QtCore.QRectF(old_rect.left(), old_rect.bottom() - highlight_height - 1, old_rect.width(), highlight_height)
        new_highlight = QtCore.QRectF(new_rect.left(), new_rect.bottom() - highlight_height - 1, new_rect.width(), highlight_height)
        self._highlight_anim.stop()
        self._highlight_anim.setStartValue(old_highlight)
        self._highlight_anim.setEndValue(new_highlight)
        self._highlight_anim.setDuration(200)
        self._highlight_anim.start()
    
class CustomTabWidget(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super(CustomTabWidget, self).__init__(parent)
        self.setup_ui()
        self.connectSignals()
         
    def setup_ui(self):
        layout = QtWidgets.QVBoxLayout(self)
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)
        
        self._header = CustomTabBar(self)
        layout.addWidget(self._header)
        
        self._stack = QtWidgets.QStackedWidget(self)
        layout.addWidget(self._stack)
                
    def connectSignals(self):
        self._header.currentChanged.connect(self._stack.setCurrentIndex)
        
    def addTab(self, widget, title):
        self._header.addTab(widget, title)
        self._stack.addWidget(widget)
        if self._header.tabCount() == 1:
            self._header.setCurrentIndex(0)
    
    def insertTab(self, index, widget, title):
        self._header.insertTab(index, widget, title)
        self._stack.insertWidget(index, widget)
    
    def removeTab(self, index):
        self._header.removeTab(index)
        widget = self._stack.widget(index)
        self._stack.removeWidget(widget)
    
    def setCurrentIndex(self, index):
        self._header.setCurrentIndex(index)
    
    def currentIndex(self):
        return self._header.currentIndex()
    
    def tabCount(self):
        return self._header.tabCount()
    
    def tabText(self, index):
        return self._header.tabText(index)
    
    def setTabText(self, index, title): 
        self._header.setTabText(index, title)
    
    def widget(self, index):    
        return self._header.widget(index)
    
    def indexOf(self, widget):
        return self._header.indexOf(widget)
    
    def clear(self): 
        self._header.clear()
        while self._stack.count() > 0:
            widget = self._stack.widget(0)
            self._stack.removeWidget(widget)

class TestMainWindow(QtWidgets.QMainWindow):
    def __init__(self, parent=None):
        super(TestMainWindow, self).__init__(parent)

        self.setWindowTitle(WINDOW_TITLE)
        self.setObjectName(OBJECT_NAME)
        self.resize(700, 420)
        
        self.setup_ui()
        
    def setup_ui(self):
        self.central_widget = QtWidgets.QWidget(self)
        self._layout = QtWidgets.QVBoxLayout(self.central_widget)
        self._layout.setSpacing(5)
        self._layout.setContentsMargins(0, 0, 0, 0)

        self.setCentralWidget(self.central_widget)

        self.tab_widget = CustomTabWidget(self)
        self._layout.addWidget(self.tab_widget)

        # タブごとに異なる設定のサンプル
        # 1. デフォルト
        contents1 = ContentsWidget()
        for l in range(2):
            frame = contents1.addFrame(f"Default Frame {l}")
            frame.setFrameStyle(CollapsibleFrame.kDefault)
            label = QtWidgets.QLabel(f"Default Content {l}")
            frame.addWidget(label)
            if l == 0:
                add_btn = QtWidgets.QPushButton("ウィジェット追加")
                def add_widget(f=frame):
                    count = f.count()
                    new_label = QtWidgets.QLabel(f"追加ラベル {count}")
                    f.addWidget(new_label)
                add_btn.clicked.connect(lambda *args, f=frame: add_widget(f))
                frame.addWidget(add_btn)
        self.tab_widget.addTab(contents1, "Default")

        # 2. Solid枠・タイトル色変更
        contents2 = ContentsWidget()
        for l in range(2):
            frame = CollapsibleFrame(f"Solid Frame {l}", parent=contents2)
            frame.setFrameStyle(CollapsibleFrame.kSolid)
            frame.setTitleColor(QtGui.QColor(0, 120, 215))
            label = QtWidgets.QLabel(f"Solid Content {l}")
            frame.addWidget(label)
            if l == 0:
                add_btn = QtWidgets.QPushButton("ウィジェット追加")
                def add_widget(f=frame):
                    count = f.count()
                    new_label = QtWidgets.QLabel(f"追加ラベル {count}")
                    f.addWidget(new_label)
                    f.setMaximumHeight(f._getContentHeight() + f._title_bar_height + f.layout().contentsMargins().top() + f.layout().contentsMargins().bottom())
                add_btn.clicked.connect(lambda *args, f=frame: add_widget(f))
                frame.addWidget(add_btn)
            contents2.main_layout.insertWidget(contents2.main_layout.count() - 1, frame)
        self.tab_widget.addTab(contents2, "Solid & Blue Title")

        # 3. Rounded枠・アイコン右・タイトル中央
        contents3 = ContentsWidget()
        for l in range(2):
            frame = CollapsibleFrame(f"Rounded Frame {l}", parent=contents3)
            frame.setFrameStyle(CollapsibleFrame.kRounded)
            frame.setIconAlignment(CollapsibleFrame.kAlignRight)
            frame.setTitleAlignment(CollapsibleFrame.kAlignCenter)
            label = QtWidgets.QLabel(f"Rounded Content {l}")
            frame.addWidget(label)
            if l == 0:
                add_btn = QtWidgets.QPushButton("ウィジェット追加")
                def add_widget(f=frame):
                    count = f.count()
                    new_label = QtWidgets.QLabel(f"追加ラベル {count}")
                    f.addWidget(new_label)
                    f.setMaximumHeight(f._getContentHeight() + f._title_bar_height + f.layout().contentsMargins().top() + f.layout().contentsMargins().bottom())
                add_btn.clicked.connect(lambda *args, f=frame: add_widget(f))
                frame.addWidget(add_btn)
            contents3.main_layout.insertWidget(contents3.main_layout.count() - 1, frame)
        self.tab_widget.addTab(contents3, "Rounded & Center Title")

        # 4. Dashed枠・アイコンスタイル変更
        contents4 = ContentsWidget()
        for l, icon_style in enumerate([CollapsibleFrame.kArrow, CollapsibleFrame.kPlusMinus]):
            frame = CollapsibleFrame(f"Dashed Frame {l}", parent=contents4)
            frame.setFrameStyle(CollapsibleFrame.kDashed)
            frame.setIconStyle(icon_style)
            label = QtWidgets.QLabel(f"Dashed Content {l}")
            frame.addWidget(label)
            if l == 0:
                add_btn = QtWidgets.QPushButton("ウィジェット追加")
                def add_widget(f=frame):
                    count = f.count()
                    new_label = QtWidgets.QLabel(f"追加ラベル {count}")
                    f.addWidget(new_label)
                    f.setMaximumHeight(f._getContentHeight() + f._title_bar_height + f.layout().contentsMargins().top() + f.layout().contentsMargins().bottom())
                add_btn.clicked.connect(lambda *args, f=frame: add_widget(f))
                frame.addWidget(add_btn)
            contents4.main_layout.insertWidget(contents4.main_layout.count() - 1, frame)
        self.tab_widget.addTab(contents4, "Dashed & Icon Style")

        # 5. タイトルバー色・アニメーション無効
        contents5 = ContentsWidget()
        for l in range(2):
            frame = CollapsibleFrame(f"NoAnim Frame {l}", parent=contents5)
            frame.setTitleBarColor(QtGui.QColor(200, 200, 100))
            frame.setAnimationEnabled(False)
            label = QtWidgets.QLabel(f"NoAnim Content {l}")
            frame.addWidget(label)
            if l == 0:
                add_btn = QtWidgets.QPushButton("ウィジェット追加")
                def add_widget(f=frame):
                    count = f.count()
                    new_label = QtWidgets.QLabel(f"追加ラベル {count}")
                    f.addWidget(new_label)
                    f.setMaximumHeight(f._getContentHeight() + f._title_bar_height + f.layout().contentsMargins().top() + f.layout().contentsMargins().bottom())
                add_btn.clicked.connect(lambda *args, f=frame: add_widget(f))
                frame.addWidget(add_btn)
            contents5.main_layout.insertWidget(contents5.main_layout.count() - 1, frame)
        self.tab_widget.addTab(contents5, "No Animation")

        # 6. タイトル非表示・アイコンのみ
        contents6 = ContentsWidget()
        for l in range(2):
            frame = CollapsibleFrame(f"IconOnly Frame {l}", parent=contents6)
            frame.setTitleVisible(False)
            frame.setIconVisible(True)
            label = QtWidgets.QLabel(f"IconOnly Content {l}")
            frame.addWidget(label)
            if l == 0:
                add_btn = QtWidgets.QPushButton("ウィジェット追加")
                def add_widget(f=frame):
                    count = f.count()
                    new_label = QtWidgets.QLabel(f"追加ラベル {count}")
                    f.addWidget(new_label)
                    f.setMaximumHeight(f._getContentHeight() + f._title_bar_height + f.layout().contentsMargins().top() + f.layout().contentsMargins().bottom())
                add_btn.clicked.connect(lambda *args, f=frame: add_widget(f))
                frame.addWidget(add_btn)
            contents6.main_layout.insertWidget(contents6.main_layout.count() - 1, frame)
        self.tab_widget.addTab(contents6, "Icon Only")

        # 7. タブバーの色・高さ・文字色変更
        self.tab_widget._header.setHighlightColor(QtGui.QColor(255, 100, 100))
        self.tab_widget._header.setHighlightHeight(4)
        self.tab_widget._header.setTabTextColor(QtGui.QColor(50, 200, 50))
        self.tab_widget._header.setTabTextSelectedColor(QtGui.QColor(255, 255, 255))
        self.tab_widget._header.setTabTextPressedColor(QtGui.QColor(100, 100, 100))
                  
def main():
    maya_main_window = wrapInstance(int(omui.MQtUtil.mainWindow()), QtWidgets.QWidget)
    this_win = maya_main_window.findChild(QtWidgets.QWidget, OBJECT_NAME)
    if this_win:
        this_win.close()
        this_win.deleteLater()
    
    app = QtWidgets.QApplication.instance()
    win = TestMainWindow(maya_main_window)
    
    win.show()
    app.exec_()

