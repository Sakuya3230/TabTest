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
    """
    折りたたみ可能なフレームウィジェット。
    
    ・タイトルバー付きのフレームで、クリックで展開/折りたたみが可能
    ・アニメーションやアイコン、タイトル・フレームのカスタマイズに対応
    ・内部に任意のウィジェットを追加できる
    ・展開/折りたたみ時にtoggledシグナルを発行
    """
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
        """
        CollapsibleFrameの初期化。
        Args:
            title (str): タイトルバーのテキスト
            color (QColor): タイトルの色
            parent (QWidget): 親ウィジェット
        """
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
        """
        タイトルバークリックで展開・折りたたみを切り替える。
        Args:
            event (QMouseEvent): マウスイベント
        """
        """タイトルバーのクリックで展開・折りたたみ"""
        if event.pos().y() < self._title_bar_height and self._is_collapsable:
            self._toggle()

    def paintEvent(self, event):
        """
        タイトルバーとアイコンのカスタム描画。
        Args:
            event (QPaintEvent): ペイントイベント
        """
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
            text_width = self._text_width(font_metrics, self._title)
            
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
        """
        ウィンドウのリサイズ時にフレームのジオメトリを更新。
        Args:
            event (QResizeEvent): リサイズイベント
        """
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
        """
        コンテンツ領域にウィジェットを追加。
        Args:
            widget (QWidget): 追加するウィジェット
        """
        self.content_layout.addWidget(widget)
        self._updateFrameMaxHeight()

    def insertWidget(self, index, widget):
        """
        コンテンツ領域にウィジェットを挿入。
        Args:
            index (int): 挿入位置
            widget (QWidget): 挿入するウィジェット
        """
        self.content_layout.insertWidget(index, widget)
        self._updateFrameMaxHeight()
        
    def removeWidget(self, widget):
        """
        コンテンツ領域からウィジェットを削除。
        Args:
            widget (QWidget): 削除するウィジェット
        """
        self.content_layout.removeWidget(widget)
        widget.setParent(None)
        self._updateFrameMaxHeight()
        
    def count(self):
        """
        コンテンツ領域内のウィジェット数を返す。
        Returns:
            int: ウィジェット数
        """
        return self.content_layout.count()

    def title(self):
        """
        タイトル名を返す。
        Returns:
            str: タイトル名
        """ 
        return self._title
    
    def titleColor(self):
        """
        タイトルのカラーを返す。
        Returns:
            QColor: 文字の色
        """
        return self._title_color
    
    def titleAlignment(self):
        """
        タイトルの配置を返す。
        Returns:
            int: 配置定数 kAlignLeft = 0 kAlignRight = 1 kAlignCenter = 2
        """ 
        return self._title_alignment
    
    def titleVisible(self):
        """
        タイトルの表示状態を返す。
        Returns:
            bool: 表示状態
        """
        return self._is_title_visible
    
    def titleBarColor(self):
        """
        タイトルバーの背景色を返す。
        Returns:
            QColor: 背景色
        """ 
        return self._title_bar_color
    
    def titleBarHeight(self):
        """
        タイトルバーの高さを返す。
        Returns:
            int: タイトルバーの高さ
        """   
        return self._title_bar_height
    
    def iconColor(self):
        """
        アイコンのカラーを返す。
        Returns:
            QColor: アイコンの色
        """ 
        return self._icon_color    
    
    def iconAlignment(self):
        """
        アイコンの配置を返す。
        Returns:
            int: 配置定数 kAlignLeft = 0 kAlignRight = 1 kAlignCenter = 2
        """  
        return self._icon_alignment
    
    def iconStyle(self):
        """
        アイコンのスタイルを返す。
        Returns:
            int: スタイル定数 kTriangle = 0 kPlusMinus = 1
        """   
        return self._icon_style
    
    def iconVisible(self):
        """
        アイコンの表示状態を返す。
        Returns:
            bool: 表示状態
        """
        return self._is_icon_visible
    
    def frameStyle(self):
        """
        フレームのスタイルを返す。
        Returns:
            int: スタイル定数 kDefault = 0 kSolid = 1 kRounded = 2 kDashed = 3
        """     
        return self._frame_style
        
    def isCollapsed(self):
        """
        フレームが折りたたまれているかどうか。
        Returns:
            bool: 折りたたみ状態
        """   
        return self._is_collapsed
    
    def isCollapsable(self):
        """
        折りたたみが有効かどうか。
        Returns:
            bool: 有効状態
        """   
        return self._is_collapsable
    
    def isAnimationEnabled(self):
        """
        アニメーションが有効かどうか。
        Returns:
            bool: 有効状態
        """     
        return self._is_animation_enabled
    
    def setTitle(self, title):
        """
        タイトルを変更する。
        Args:
            title (str): 新しいタイトル
        """
        self._title = title
        self.update()

    def setTitleColor(self, color):
        """
        タイトルの文字色を変更する。
        Args:
            color (QColor): 新しい色
        """
        self._title_color = color
        self.update()

    def setTitleAlignment(self, alignment):
        """
        タイトルの配置を変更する。
        Args:
            alignment (int): 配置定数 0: kAlignLeft, 1: kAlignRight, 2: kAlignCenter
        """
        if alignment in [self.kAlignLeft, self.kAlignRight, self.kAlignCenter]:
            self._title_alignment = alignment
            self.update()
        
    def setTitleVisible(self, visible):
        """
        タイトルの表示・非表示を切り替える。
        Args:
            visible (bool): 表示状態
        """
        self._is_title_visible = visible
        self.update()
        
    def setTitleBarColor(self, color):
        """
        タイトルバーの背景色を変更する。
        Args:
            color (QColor): 新しい色
        """
        self._title_bar_color = color
        self.update()

    def setTitleBarHeight(self, height):
        """
        タイトルバーの高さを変更する。
        Args:
            height (int): 新しい高さ (最小15px)
        """
        self._title_bar_height = max(15, height)
        self._updateTitleBarHeight()
        self._updateFrameMaxHeight()
        self.update()

    def setIconColor(self, color):
        """
        アイコンの色を変更する。
        Args:
            color (QColor): 新しい色
        """
        self._icon_color = color
        self.update()

    def setIconAlignment(self, alignment):
        """
        アイコンの配置を変更する。
        Args:
            alignment (int): 配置定数 0: kAlignLeft, 1: kAlignRight, 2: kAlignCenter
        """
        if alignment in [self.kAlignLeft, self.kAlignRight, self.kAlignCenter]:
            self._icon_alignment = alignment
            self.update()
            
    def setIconStyle(self, style):
        """
        アイコンのスタイルを変更する。
        Args:
            style (int): スタイル定数 0: kTriangle, 1: kArrow, 2: kPlusMinus, 3: kCircle
        """
        if style in [self.kTriangle, self.kArrow, self.kPlusMinus, self.kCircle]:
            self._icon_style = style
            self.update()

    def setIconVisible(self, visible):
        """
        アイコンの表示・非表示を切り替える。
        Args:
            visible (bool): 表示状態
        """
        self._is_icon_visible = visible
        self.update()

    def setFrameStyle(self, style):
        """
        フレームのスタイルを変更する。
        Args:
            style (int): スタイル定数
        """
        if style in [self.kDefault, self.kSolid, self.kRounded, self.kDashed]:
            self._frame_style = style
            self._updateFrameStyle()

    def setCollapsedEnabled(self, enabled):
        """
        折りたたみの有効化を変更する。
        Args:
            enabled (bool): 有効状態
        """
        self._is_collapsable = enabled

    def setAnimationEnabled(self, enabled):
        """
        アニメーションの有効化を変更する。
        Args:
            enabled (bool): 有効状態
        """
        self._is_animation_enabled = enabled

    def setContentsMargins(self, x, y, width, height):
        """
        コンテンツ領域のマージンを設定する。
        Args:
            x, y, width, height (int): マージン値
        """
        self.content_layout.setContentsMargins(x, y, width, height)

    def setSpacing(self, spacing):
        """
        コンテンツ領域のウィジェット間スペースを設定する。
        Args:
            spacing (int): スペース幅
        """
        self.content_layout.setSpacing(spacing)

    # ------------------------------
    # private method
    # ------------------------------
    def _updateTitleBarHeight(self):
        """タイトルバー高さに応じてメインレイアウトのマージンを更新"""
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

    def _text_width(self, metrics, text):
        """
        PySide2/PySide6両対応でテキスト幅を取得
        """
        if hasattr(metrics, "horizontalAdvance"):
            return metrics.horizontalAdvance(text)
        else:
            return metrics.width(text)

class ContentsWidget(QtWidgets.QWidget):
    """
    CollapsibleFrameを複数管理するためのコンテナウィジェット。
    
    ・スクロールエリア内に複数のCollapsibleFrameを追加・削除可能
    ・フレームの挿入・削除・タイトル変更などの管理機能を提供
    """
    def __init__(self, parent=None):
        """
        ContentsWidgetの初期化。
        Args:
            parent (QWidget): 親ウィジェット
        """
        super(ContentsWidget, self).__init__(parent)
        self._frames = [] 
        
        self.setup_ui()
        
    def setup_ui(self):
        """
        メインレイアウトとスクロールエリアの初期化。
        """
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
        """
        新しいCollapsibleFrameを追加。
        Args:
            title (str): フレームタイトル
        Returns:
            CollapsibleFrame: 追加されたフレーム
        """
        frame = CollapsibleFrame(title, parent=self)
        self.content_layout.insertWidget(self.content_layout.count() - 1, frame)
        self._frames.append(frame)
        return frame

    def insertFrame(self, index, title):
        """
        指定位置にCollapsibleFrameを挿入。
        Args:
            index (int): 挿入位置
            title (str): フレームタイトル
        Returns:
            CollapsibleFrame: 挿入されたフレーム
        """
        frame = CollapsibleFrame(title, parent=self)
        self.content_layout.insertWidget(index, frame)
        self._frames.insert(index, frame)
        return frame
    
    def removeFrame(self, index):
        """
        指定インデックスのフレームを削除。
        Args:
            index (int): 削除位置
        """
        if 0 <= index < len(self._frames):
            frame = self._frames[index]
            self.content_layout.removeWidget(frame)
            frame.setParent(None)
            del self._frames[index]
            
    def clear(self):
        """
        すべてのフレームを削除。
        """
        while self._frames:
            self.removeFrame(0)
            
    def frameCount(self):
        """
        フレーム数を返す。
        Returns:
            int: フレーム数
        """
        return len(self._frames)
    
    def frame(self, index):
        """
        指定インデックスのフレームを返す。
        Args:
            index (int): フレームインデックス
        Returns:
            CollapsibleFrame or None: フレーム
        """
        if 0 <= index < len(self._frames):
            return self._frames[index]
        return None 
    
    def indexOfTitle(self, title):
        """
        タイトル名からフレームのインデックスを返す。
        Args:
            title (str): フレームタイトル
        Returns:
            int: インデックス（見つからなければ-1）
        """
        for i, f in enumerate(self._frames):
            if f.title() == title:
                return i
        return -1
    
    def indexOf(self, frame):
        """
        フレームオブジェクトからインデックスを返す。
        Args:
            frame (CollapsibleFrame): 対象フレーム
        Returns:
            int: インデックス（見つからなければ-1）
        """
        for i, f in enumerate(self._frames):
            if f == frame:
                return i
        return -1
    
    def setContentsMargins(self, x, y, width, height):
        """
        コンテンツ領域のマージンを設定。
        Args:
            x, y, width, height (int): マージン値
        """
        self.content_layout.setContentsMargins(x, y, width, height)
        
    def setSpacing(self, spacing):
        """
        コンテンツ領域のウィジェット間スペースを設定。
        Args:
            spacing (int): スペース幅
        """
        self.content_layout.setSpacing(spacing)
        
    def setFrameTitle(self, index, title):
        """
        指定インデックスのフレームタイトルを変更。
        Args:
            index (int): フレームインデックス
            title (str): 新しいタイトル
        """
        if 0 <= index < len(self._frames):
            self.frame(index).setTitle(title)   

class TabInfo:
    """
    タブ情報を管理するクラス。
    
    Attributes:
        widget (QtWidgets.QWidget): タブに対応するウィジェット
        _title (str): タブタイトル
        _text_color (QtGui.QColor): タブの文字色
    """
    def __init__(self, widget, title, text_color=QtGui.QColor(200, 200, 200)):
        self._widget = widget
        self._title = title
        self._text_color = text_color

    def widget(self):
        return self._widget

    def title(self):
        return self._title
    
    def textColor(self):
        return self._text_color
    
    def setWidget(self, widget):
        self._widget = widget
    
    def setTitle(self, title):
        self._title = title
        
    def setTextColor(self, color):
        self._text_color = QtGui.QColor(color)

    def __repr__(self):
        return f"TabInfo(title={self._title!r}, widget={type(self._widget).__name__}, text_color={self._text_color.name()})"
    
    def __eq__(self, other):
        if not isinstance(other, TabInfo):
            return False
        return self.widget() == other.widget() and self.title() == other.title() and self.textColor() == other.textColor()

class CustomTabBar(QtWidgets.QWidget):
    """
    カスタムタブバーウィジェット。
    
    ・タブの追加・削除・選択・タイトル変更が可能
    ・タブのスクロール（ドラッグ/アニメーション）に対応
    ・選択タブのハイライトバーをアニメーションで表示
    ・タブのホバー/プレス状態の描画や色のカスタマイズが可能
    ・タブの幅や間隔、下線、背景色なども調整可能
    
    シグナル:
        currentChanged(int): 選択タブが変更されたとき
        tabSelected(int): タブが選択されたとき
        tabPressed(int): タブが押されたとき
        tabReleased(int): タブが離されたとき
    """
    currentChanged  = QtCore.Signal(int)
    tabSelected     = QtCore.Signal(int)
    tabPressed      = QtCore.Signal(int)
    tabReleased     = QtCore.Signal(int)

    # ------------------------------
    # override methods
    # ------------------------------
    def __init__(self, parent=None):
        super(CustomTabBar, self).__init__(parent)
        self._tabs                  = []
        self._current_index         = -1
        self._scroll_offset         = 0
        self._scroll_anim_offset    = 0
        self._dragging              = False
        self._last_mouse_x          = 0
        self._pressed_tab           = -1
        self._hovered_tab           = -1
        self._highlight_rect        = QtCore.QRectF()
        
        # カスタマイズ用プロパティ
        self._highlight_bar_color        = QtGui.QColor(0, 120, 215)
        self._tab_hovered_color         = QtGui.QColor(80, 80, 80)
        self._background_color          = QtGui.QColor(68, 68, 68)
        self._tab_padding               = 30
        self._tab_spacing               = 2
        self._highlight_bar_height          = 2
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
        """
        推奨されるウィジェットサイズを返す。
        Returns:
            QtCore.QSize: 推奨サイズ
        """
        return QtCore.QSize(200, 40)
        
    def paintEvent(self, event):
        """
        タブバー全体の描画処理。
        タブ、ハイライトバー、下線などをカスタム描画する。
        """
        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.Antialiasing)
        
        # 背景描画
        if self._background_color.isValid():
            painter.fillRect(self.rect(), self._background_color)
        else:
            painter.fillRect(self.rect(), self.palette().window())
        
        # ホバー/プレス状態のタブ背景描画
        for i, _ in enumerate(self._tabs):
            if i == self._hovered_tab:
                rect = self.tabRect(i)
                painter.setBrush(self._tab_hovered_color)
                painter.setPen(QtCore.Qt.NoPen)
                painter.drawRect(rect)
        
        # タブタイトル描画
        for i, tab in enumerate(self._tabs):
            rect = self.tabRect(i)
            painter.setPen(QtGui.QPen(self._tabTextColor(i)))
            font = painter.font()
            font.setBold(i == self._current_index)
            painter.setFont(font)
            painter.drawText(rect, QtCore.Qt.AlignCenter, tab.title())
            
        # ハイライトバー描画
        highlight_rect = None
        if not self._highlight_rect.isNull():
            highlight_rect = QtCore.QRectF(self._highlight_rect)
            highlight_rect.translate(-self._scroll_offset, 0)
            
        elif self._tabs and self._current_index >= 0:
            highlight_rect = self._getHighlightRect(self._current_index)
            
        if highlight_rect is not None:
            painter.setPen(QtCore.Qt.NoPen)
            painter.setBrush(self._highlight_bar_color)
            painter.drawRoundedRect(highlight_rect, 2, 2)
            
        # タブバー下部に細いグレーのライン
        painter.setBrush(QtCore.Qt.NoBrush)
        pen = QtGui.QPen(self._bottom_line_color)
        pen.setWidthF(self._bottom_line_width)
        painter.setPen(pen)
        painter.drawLine(0, self.height() - 1, self.width(), self.height() - 1)
        
    def leaveEvent(self, event):
        """
        マウスがタブバー領域から離れたときの処理。
        ホバー状態を解除する。
        """
        self._hovered_tab = -1
        self.update()
        super().leaveEvent(event)

    def mousePressEvent(self, event):
        """
        マウスボタンが押されたときの処理。
        タブのドラッグや押下状態の管理。
        """
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
        """
        マウス移動時の処理。
        タブのドラッグによるスクロールやホバー状態の更新。
        """
        if self._dragging:
            self._pressed_tab = -1
            dx = event.x() - self._last_mouse_x
            self._last_mouse_x = event.x()
            # 15ピクセル以上動いたらドラッグと判定
            if abs(event.x() - self._drag_start_pos.x()) > 15:
                self._drag_moved = True
            self._scroll_offset -= dx
            self._scroll_offset = max(0, self._scroll_offset)
            # 最大値制限
            total_width = 0
            font_metrics = self.fontMetrics()
            for tab in self._tabs:
                total_width += self._text_width(font_metrics, tab.title()) + self._tab_padding + self._tab_spacing
            max_offset = max(0, total_width - self.width())
            self._scroll_offset = min(self._scroll_offset, max_offset)
            self.update()
            
        for i in range(len(self._tabs)):
            rect = self.tabRect(i)
            if rect.contains(event.pos()):
                if self._hovered_tab != i:
                    self._hovered_tab = i
                    self.update()
                break
            
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        """
        マウスボタンが離されたときの処理。
        タブの選択やドラッグ終了の管理。
        """
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
        """
        マウスホイール操作時の処理。
        ホイールでタブの選択を移動する。
        """
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
                
        self._hovered_tab = -1
        self.update()
        
    def resizeEvent(self, event):
        """
        リサイズ時の処理。
        横幅が変化した場合、タブ全体幅やオフセットを調整・出力する。
        """
        old_width = event.oldSize().width()
        new_width = event.size().width()
        if old_width != new_width:
            # タブ全体の幅を計算
            font_metrics = self.fontMetrics()
            total_width = 0
            for tab in self._tabs:
                total_width += self._text_width(font_metrics, tab.title()) + self._tab_padding + self._tab_spacing

            # オフセット調整
            visible_width = total_width - self._scroll_offset
            if visible_width < new_width:
                diff = new_width - visible_width
                self._scroll_offset = max(0, self._scroll_offset - diff)
                
        super().resizeEvent(event)
                
    # ------------------------------
    # public methods
    # ------------------------------
    def addTab(self, widget, title, text_color=QtGui.QColor(200, 200, 200)):
        """
        タブを末尾に追加する。
        Args:
            widget (QWidget): タブに対応するウィジェット
            title (str): タブタイトル
            text_color (QColor, optional): タブのテキスト色
        """
        
        self._tabs.append(TabInfo(widget, title, text_color))
        self.update()
    
    def insertTab(self, index, widget, title, text_color=QtGui.QColor(200, 200, 200)):
        """
        指定位置にタブを挿入する。
        Args:
            index (int): 挿入位置
            widget (QWidget): タブに対応するウィジェット
            title (str): タブタイトル
            text_color (QColor, optional): タブのテキスト色
        """
        self._tabs.insert(index, TabInfo(widget, title, text_color))
        self.update()
    
    def removeTab(self, index):
        """
        指定したインデックスのタブを削除する。
        Args:
            index (int): 削除するタブのインデックス
        """
        if 0 <= index < len(self._tabs):
            del self._tabs[index]
            if self._current_index >= len(self._tabs):
                self._current_index = len(self._tabs) - 1
            self.update()
    
    def currentIndex(self):
        """
        現在選択されているタブのインデックスを返す。
        Returns:
            int: 選択中のタブインデックス
        """
        return self._current_index
    
    def tabCount(self):
        """
        タブの総数を返す。
        Returns:
            int: タブ数
        """
        return len(self._tabs)
    
    def tabText(self, index):
        """
        指定インデックスのタブタイトルを返す。
        Args:
            index (int): タブインデックス
        Returns:
            str: タブタイトル
        """
        if 0 <= index < len(self._tabs):
            return self.tab(index).title()
        return ""
    
    def setTabText(self, index, title): 
        """
        指定インデックスのタブタイトルを変更する。
        Args:
            index (int): タブインデックス
            title (str): 新しいタイトル
        """
        if 0 <= index < len(self._tabs):
            self.tab(index).setTitle(title)
            self.update()
    
    def widget(self, index):    
        """
        指定インデックスのタブに対応するウィジェットを返す。
        Args:
            index (int): タブインデックス
        Returns:
            QWidget: 対応ウィジェット
        """
        if 0 <= index < len(self._tabs):
            return self.tab(index).widget()
        return None
    
    def indexOf(self, widget):
        """
        指定ウィジェットに対応するタブのインデックスを返す。
        Args:
            widget (QWidget): 対象ウィジェット
        Returns:
            int: インデックス（見つからなければ-1）
        """
        for i, tab in enumerate(self._tabs):
            if tab.widget() == widget:
                return i
        return -1
    
    def clear(self): 
        """
        すべてのタブを削除する。
        """
        self._tabs = []
        self._current_index = -1
        self.update()
        
    def tab(self, index):
        """
        指定インデックスのタブ情報を返す。
        Args:
            index (int): タブインデックス
        Returns:
            TabInfo: タブ情報オブジェクト
        """
        if 0 <= index < len(self._tabs):
            return self._tabs[index]
        return None
        
    def tabTextColor(self, index):
        """
        タブごとの文字色を返す。個別設定があればそれを優先。
        Args:
            index (int): タブインデックス
        Returns:
            QtGui.QColor: テキスト色
        """
        if 0 <= index < len(self._tabs):
            return self.tab(index).textColor()
        
    def tabRect(self, index, offset=True):
        """
        指定したタブの矩形を返す。
        Args:
            index (int): タブインデックス
            offset (bool): オフセットを適用するか
        Returns:
            QtCore.QRect: タブの矩形
        """
        """
        指定したタブの矩形を返す。
        offset=True で現在のスクロール/アニメーションオフセットを適用。
        offset=False でオフセットなしの絶対位置を返す。
        """
        font_metrics = self.fontMetrics()
        height = self.height()
        x = 0
        if offset:
            x -= self._getCurrentOffset()
        for i, tab in enumerate(self._tabs):
            width = self._text_width(font_metrics, tab.title()) + self._tab_padding
            x += self._tab_spacing
            rect = QtCore.QRect(x, 0, width, height)
            if i == index:
                return rect
            x += width
        return QtCore.QRect()
            
    def setTabTextColor(self, index, color):
        """
        タブごとの文字色を設定する。
        Args:
            index (int): タブインデックス
            color (QColor or str): 色
        """
        if 0 <= index < len(self._tabs):
            self.tab(index).setTextColor(color)
            self.update()
        
    def setCurrentIndex(self, index):
        """
        指定インデックスのタブを選択状態にする。
        Args:
            index (int): 選択するタブインデックス
        """
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
        """
        タブのパディング幅を設定する。
        Args:
            padding (int): パディング幅
        """
        self._tab_padding = padding
        self.update()
        
    def setTabSpacing(self, spacing):
        """
        タブ間のスペースを設定する。
        Args:
            spacing (int): スペース幅
        """
        self._tab_spacing = spacing
        self.update()
        
    def setTabTextColor(self, index, color):
        """
        タブの通常テキスト色を設定する。
        Args:
            index (int): タブインデックス
            color (QColor or str): 色
        """
        if 0 <= index < len(self._tabs):
            self.tab(index).setTextColor(color)
        self.update()
        
    def setTabHoveredColor(self, color):
        """
        ホバー時のタブ背景色を設定する。
        Args:
            color (QColor or str): 色
        """
        self._tab_hovered_color = QtGui.QColor(color)
        self.update()
        
    def setBackgroundColor(self, color):
        """
        タブバー全体の背景色を設定する。
        Args:
            color (QColor or str): 色
        """
        self._background_color = QtGui.QColor(color)
        self.update()
        
    def setHighlightBarColor(self, color):
        """
        ハイライトバーの色を設定する。
        Args:
            color (QColor or str): 色
        """
        self._highlight_bar_color = QtGui.QColor(color)
        self.update()
        
    def setHighlightBarHeight(self, height):
        """
        ハイライトバーの高さを設定する。
        Args:
            height (int): 高さ
        """
        self._highlight_bar_height = height
        self.update()
        
    def setBottomLineColor(self, color):
        """
        タブバー下部のライン色を設定する。
        Args:
            color (QColor or str): 色
        """
        self._bottom_line_color = QtGui.QColor(color)
        self.update()
        
    def setBottomLineWidth(self, width):
        """
        タブバー下部のライン幅を設定する。
        Args:
            width (float): ライン幅
        """
        self._bottom_line_width = width
        self.update()
        
    # ------------------------------
    # private methods
    # ------------------------------
    def _tabTextColor(self, index):
        """
        タブの状態に応じたテキスト色を返す。
        Args:
            index (int): タブインデックス
        Returns:
            QtGui.QColor: テキスト色
        """
        if index == self._pressed_tab:
            return self.tab(index).textColor().darker(120)
        elif index == self._current_index:
            return self.tab(index).textColor().lighter(120)
        else:
            return self.tab(index).textColor()
        
    def _text_width(self, metrics, text):
        """
        PySide2/PySide6両対応でテキスト幅を取得
        """
        if hasattr(metrics, "horizontalAdvance"):
            return metrics.horizontalAdvance(text)
        else:
            return metrics.width(text)
    
    def _getCurrentOffset(self):
        """
        現在のスクロール/アニメーションオフセット値を返す。
        Returns:
            int or float: オフセット値
        """
        return self._scroll_anim_offset if self._scroll_anim.state() == QtCore.QAbstractAnimation.Running else self._scroll_offset
    
    def _getHighlightRect(self, index, offset=True):
        """
        指定インデックスのタブのタイトル幅に合わせたハイライトバーの矩形を返す。
        """
        if not (0 <= index < len(self._tabs)):
            return QtCore.QRectF()
        
        tab = self._tabs[index]
        tab_rect = self.tabRect(index, offset=offset)
        font = self.font()
        font.setBold(index == self._current_index)
        metrics = QtGui.QFontMetrics(font)
        text_width = self._text_width(metrics, tab.title())
        bar_width = text_width + 8  # 余白
        bar_height = self._highlight_bar_height
        bar_x = tab_rect.x() + (tab_rect.width() - bar_width) // 2
        bar_y = tab_rect.bottom() - bar_height + 1
        
        return QtCore.QRectF(bar_x, bar_y, bar_width, bar_height)
    
    def _on_highlight_anim(self, value):
        """
        ハイライトバーアニメーションの値が変化したときの処理。
        Args:
            value (QRectF): 新しいハイライト矩形
        """
        self._highlight_rect = value
        self.update()
    
    def _scroll_to_tab(self, index):
        """
        指定インデックスのタブが見切れている場合に自動でスクロールする。
        Args:
            index (int): 対象タブインデックス
        """
        # 選択タブが見切れている場合に自動でスクロール
        if not self._tabs:
            return
        font_metrics = self.fontMetrics()
        height = self.height()

        x = 0
        for i, tab in enumerate(self._tabs):
            width = self._text_width(font_metrics, tab.title()) + self._tab_padding
            x += self._tab_spacing
            rect = QtCore.QRect(x, 0, width, height)
            if i == index:
                tab_rect = rect
            x += width
            
        left_visible = self._scroll_offset
        right_visible = self._scroll_offset + self.width()
        left_margin = 100
        right_margin = 100
        target_offset = self._scroll_offset
        
        if tab_rect.left() < left_visible + left_margin: # 左側が見切れている
            target_offset = max(tab_rect.left() - left_margin, 0)
            
        elif tab_rect.right() > right_visible - right_margin: # 右側が見切れている
            target_offset = tab_rect.right() - self.width() + right_margin
            # 最大値制限
            total_width = 0
            for tab in self._tabs:
                total_width += self._text_width(font_metrics, tab.title()) + self._tab_padding + self._tab_spacing
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
        """
        スクロールアニメーションの値が変化したときの処理。
        Args:
            value (int or float): 新しいオフセット値
        """
        self._scroll_anim_offset = value
        self.update()

    def _start_highlight_animation(self, old_index, new_index):
        """
        ハイライトバーのアニメーションを開始する。
        Args:
            old_index (int): 以前の選択タブインデックス
            new_index (int): 新しい選択タブインデックス
        """
        if old_index == new_index or old_index < 0 or new_index < 0 or not self._tabs:
            self._highlight_rect = QtCore.QRectF()
            self.update()
            return
        # オフセットなしの絶対位置で矩形を取得
        old_highlight = self._getHighlightRect(old_index, offset=False)
        new_highlight = self._getHighlightRect(new_index, offset=False)
        
        self._highlight_anim.stop()
        self._highlight_anim.setStartValue(old_highlight)
        self._highlight_anim.setEndValue(new_highlight)
        self._highlight_anim.setDuration(200)
        self._highlight_anim.start()
    
class CustomTabWidget(QtWidgets.QWidget):
    """
    カスタムタブバー(CustomTabBar)とスタックウィジェットを組み合わせたタブウィジェット。
    
    ・タブの追加・削除・選択・タイトル変更が可能
    ・タブごとに異なるウィジェットを表示できる
    ・CustomTabBarのシグナルと連携
    """
    def __init__(self, parent=None):
        """
        CustomTabWidgetの初期化。
        Args:
            parent (QWidget): 親ウィジェット
        """
        super(CustomTabWidget, self).__init__(parent)
        self.setup_ui()
        self.connectSignals()
         
    def setup_ui(self):
        """
        レイアウトとタブバー・スタックウィジェットの初期化。
        """
        layout = QtWidgets.QVBoxLayout(self)
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)
        
        self._tab_bar = CustomTabBar(self)
        layout.addWidget(self._tab_bar)
        
        self._stack = QtWidgets.QStackedWidget(self)
        layout.addWidget(self._stack)
                
    def connectSignals(self):
        """
        タブバーのシグナルとスタックウィジェットを接続。
        """
        self._tab_bar.currentChanged.connect(self._stack.setCurrentIndex)
        
    def addTab(self, widget, title, text_color=QtGui.QColor(200, 200, 200)):
        """
        タブと対応ウィジェットを追加。
        Args:
            widget (QWidget): 追加するウィジェット
            title (str): タブタイトル
            text_color (QColor, optional): タブのテキスト色
        """
        self._tab_bar.addTab(widget, title, text_color)
        self._stack.addWidget(widget)
        if self._tab_bar.tabCount() == 1:
            self._tab_bar.setCurrentIndex(0)

    def insertTab(self, index, widget, title, text_color=QtGui.QColor(200, 200, 200)):
        """
        指定位置にタブとウィジェットを挿入。
        Args:
            index (int): 挿入位置
            widget (QWidget): 挿入するウィジェット
            title (str): タブタイトル
            text_color (QColor, optional): タブのテキスト色
        """
        self._tab_bar.insertTab(index, widget, title, text_color)
        self._stack.insertWidget(index, widget)
    
    def removeTab(self, index):
        """
        指定インデックスのタブとウィジェットを削除。
        Args:
            index (int): 削除位置
        """
        self._tab_bar.removeTab(index)
        widget = self._stack.widget(index)
        self._stack.removeWidget(widget)
    
    def setCurrentIndex(self, index):
        """
        指定インデックスのタブを選択状態にする。
        Args:
            index (int): 選択するタブインデックス
        """
        self._tab_bar.setCurrentIndex(index)
    
    def currentIndex(self):
        """
        現在選択されているタブのインデックスを返す。
        Returns:
            int: 選択中のタブインデックス
        """
        return self._tab_bar.currentIndex()
    
    def tabCount(self):
        """
        タブの総数を返す。
        Returns:
            int: タブ数
        """
        return self._tab_bar.tabCount()
    
    def tabText(self, index):
        """
        指定インデックスのタブタイトルを返す。
        Args:
            index (int): タブインデックス
        Returns:
            str: タブタイトル
        """
        return self._tab_bar.tabText(index)
    
    def setTabText(self, index, title): 
        """
        指定インデックスのタブタイトルを変更する。
        Args:
            index (int): タブインデックス
            title (str): 新しいタイトル
        """
        self._tab_bar.setTabText(index, title)
    
    def widget(self, index):    
        """
        指定インデックスのタブに対応するウィジェットを返す。
        Args:
            index (int): タブインデックス
        Returns:
            QWidget: 対応ウィジェット
        """
        return self._tab_bar.widget(index)
    
    def indexOf(self, widget):
        """
        指定ウィジェットに対応するタブのインデックスを返す。
        Args:
            widget (QWidget): 対象ウィジェット
        Returns:
            int: インデックス（見つからなければ-1）
        """
        return self._tab_bar.indexOf(widget)
    
    def clear(self): 
        """
        すべてのタブとウィジェットを削除する。
        """
        self._tab_bar.clear()
        while self._stack.count() > 0:
            widget = self._stack.widget(0)
            self._stack.removeWidget(widget)

class TestMainWindow(QtWidgets.QMainWindow):
    """
    サンプル用のメインウィンドウ。
    
    ・CustomTabWidgetを中心に、各種サンプルタブ・フレームを配置
    ・UIの初期化やレイアウト設定を行う
    """
    def __init__(self, parent=None):
        """
        TestMainWindowの初期化。
        Args:
            parent (QWidget): 親ウィジェット
        """
        super(TestMainWindow, self).__init__(parent)

        self.setWindowTitle(WINDOW_TITLE)
        self.setObjectName(OBJECT_NAME)
        self.resize(700, 420)
        
        self.setup_ui()
        
    def setup_ui(self):
        """
        メインウィンドウのUI初期化とレイアウト設定。
        """
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
        self.tab_widget.addTab(contents1, "Default", QtGui.QColor(200, 200, 200))

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
        self.tab_widget.addTab(contents2, "Solid & Blue Title", QtGui.QColor(0, 220, 215))

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
        self.tab_widget.addTab(contents3, "Rounded & Center Title", QtGui.QColor(150, 0, 150))

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
        self.tab_widget.addTab(contents4, "Dashed & Icon Style", QtGui.QColor(0, 150, 150))

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
        self.tab_widget.addTab(contents5, "No Animation", QtGui.QColor(150, 100, 0))

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
        self.tab_widget.addTab(contents6, "Icon Only", QtGui.QColor(100, 150, 0))

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

