from __future__ import annotations

import os
import sys
import sqlite3
import webbrowser
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from urllib.parse import urlparse

from PyQt6.QtCore import Qt, QDate, QUrl
from PyQt6.QtGui import QAction, QDesktopServices, QFont, QIcon
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QTabWidget,
    QTreeWidget, QTreeWidgetItem, QPushButton, QLineEdit, QLabel, QDialog,
    QFormLayout, QDialogButtonBox, QDateEdit, QSpinBox, QFileDialog,
    QMessageBox, QMenu, QSystemTrayIcon, QStyle, QAbstractItemView,
    QHeaderView, QCheckBox
)

APP_NAME = "Auto Todo Desktop"

def app_data_dir() -> Path:
    base = os.getenv("LOCALAPPDATA")
    if base:
        p = Path(base) / "AutoTodoDesktop"
    else:
        p = Path.home() / ".autotodo_desktop"
    p.mkdir(parents=True, exist_ok=True)
    return p

DB_PATH = app_data_dir() / "todo.db"


class TodoDB:
    def __init__(self, path: Path):
        self.conn = sqlite3.connect(path)
        self.conn.row_factory = sqlite3.Row
        self._init_db()

    def _init_db(self):
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                parent_id INTEGER,
                title TEXT NOT NULL,
                start_date TEXT NOT NULL,
                due_date TEXT NOT NULL,
                progress INTEGER NOT NULL DEFAULT 0,
                status TEXT NOT NULL DEFAULT 'active',
                project_ref TEXT DEFAULT '',
                move_on_complete INTEGER NOT NULL DEFAULT 0,
                completed_root TEXT DEFAULT '',
                created_at TEXT NOT NULL,
                completed_at TEXT,
                FOREIGN KEY(parent_id) REFERENCES tasks(id)
            )
        """)
        self.conn.commit()

    def add_task(self, title, start_date, due_date, progress=0, project_ref="",
                 parent_id=None, move_on_complete=False, completed_root=""):
        now = datetime.now().isoformat(timespec="seconds")
        cur = self.conn.execute("""
            INSERT INTO tasks
            (parent_id, title, start_date, due_date, progress, status, project_ref,
             move_on_complete, completed_root, created_at)
            VALUES (?, ?, ?, ?, ?, 'active', ?, ?, ?, ?)
        """, (
            parent_id, title, start_date, due_date, progress, project_ref,
            int(move_on_complete), completed_root, now
        ))
        self.conn.commit()
        return cur.lastrowid

    def update_task(self, task_id, **kwargs):
        allowed = {
            "title", "start_date", "due_date", "progress", "status", "project_ref",
            "completed_at", "move_on_complete", "completed_root", "parent_id"
        }
        parts, vals = [], []
        for k, v in kwargs.items():
            if k in allowed:
                parts.append(f"{k}=?")
                vals.append(v)
        if not parts:
            return
        vals.append(task_id)
        self.conn.execute(f"UPDATE tasks SET {', '.join(parts)} WHERE id=?", vals)
        self.conn.commit()

    def get(self, task_id):
        return self.conn.execute("SELECT * FROM tasks WHERE id=?", (task_id,)).fetchone()

    def children(self, parent_id):
        return self.conn.execute(
            "SELECT * FROM tasks WHERE parent_id=? ORDER BY id", (parent_id,)
        ).fetchall()

    def roots(self, status):
        return self.conn.execute(
            "SELECT * FROM tasks WHERE parent_id IS NULL AND status=? ORDER BY due_date, id",
            (status,)
        ).fetchall()

    def delete_recursive(self, task_id):
        for child in self.children(task_id):
            self.delete_recursive(child["id"])
        self.conn.execute("DELETE FROM tasks WHERE id=?", (task_id,))
        self.conn.commit()

    def set_status_recursive(self, task_id, status):
        completed_at = datetime.now().isoformat(timespec="seconds") if status == "completed" else None
        progress = 100 if status == "completed" else None
        if progress is None:
            self.update_task(task_id, status=status, completed_at=completed_at)
        else:
            self.update_task(task_id, status=status, completed_at=completed_at, progress=progress)
        for child in self.children(task_id):
            self.set_status_recursive(child["id"], status)


def dday_text(due_iso: str) -> str:
    try:
        due = date.fromisoformat(due_iso)
        delta = (due - date.today()).days
        if delta > 0:
            return f"D-{delta}"
        if delta == 0:
            return "D-Day"
        return f"D+{abs(delta)}"
    except Exception:
        return "-"


def is_url(value: str) -> bool:
    try:
        return urlparse(value).scheme in ("http", "https")
    except Exception:
        return False


@dataclass
class TaskFormData:
    title: str
    start_date: str
    due_date: str
    progress: int
    project_ref: str
    move_on_complete: bool
    completed_root: str


class TaskDialog(QDialog):
    def __init__(self, parent=None, row=None, is_subtask=False):
        super().__init__(parent)
        self.setWindowTitle("세부항목" if is_subtask else "할 일")
        self.resize(560, 300)

        self.title_edit = QLineEdit()
        self.start_edit = QDateEdit()
        self.start_edit.setCalendarPopup(True)
        self.start_edit.setDisplayFormat("yyyy-MM-dd")
        self.start_edit.setDate(QDate.currentDate())

        self.due_edit = QDateEdit()
        self.due_edit.setCalendarPopup(True)
        self.due_edit.setDisplayFormat("yyyy-MM-dd")
        self.due_edit.setDate(QDate.currentDate().addDays(7))

        self.progress = QSpinBox()
        self.progress.setRange(0, 100)
        self.progress.setSuffix("%")

        self.project_edit = QLineEdit()
        self.project_edit.setPlaceholderText("https://... 또는 로컬 파일/폴더 경로")

        btn_link = QPushButton("URL 입력")
        btn_link.clicked.connect(self._url_focus)
        btn_file = QPushButton("파일")
        btn_file.clicked.connect(self._choose_file)
        btn_folder = QPushButton("폴더")
        btn_folder.clicked.connect(self._choose_folder)

        project_row = QWidget()
        project_layout = QHBoxLayout(project_row)
        project_layout.setContentsMargins(0, 0, 0, 0)
        project_layout.addWidget(self.project_edit, 1)
        project_layout.addWidget(btn_link)
        project_layout.addWidget(btn_file)
        project_layout.addWidget(btn_folder)

        self.move_cb = QCheckBox("완료 시 연결된 로컬 파일/폴더를 완료 폴더로 이동")
        self.completed_root = QLineEdit()
        self.completed_root.setPlaceholderText("선택 사항: 실제 파일 이동 목적지")
        self.completed_root_btn = QPushButton("완료 폴더")
        self.completed_root_btn.clicked.connect(self._choose_completed_root)

        completed_row = QWidget()
        completed_layout = QHBoxLayout(completed_row)
        completed_layout.setContentsMargins(0, 0, 0, 0)
        completed_layout.addWidget(self.completed_root, 1)
        completed_layout.addWidget(self.completed_root_btn)

        form = QFormLayout()
        form.addRow("할 일", self.title_edit)
        form.addRow("시작 날짜", self.start_edit)
        form.addRow("언제까지", self.due_edit)
        form.addRow("진척도", self.progress)
        form.addRow("Project 링크 / 파일 / 폴더", project_row)
        form.addRow("", self.move_cb)
        form.addRow("완료 파일 이동 위치", completed_row)

        self.buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save |
            QDialogButtonBox.StandardButton.Cancel
        )
        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)

        layout = QVBoxLayout(self)
        layout.addLayout(form)
        layout.addWidget(self.buttons)

        self.move_cb.toggled.connect(self._toggle_move_fields)
        self._toggle_move_fields(False)

        if row is not None:
            self.title_edit.setText(row["title"])
            self.start_edit.setDate(QDate.fromString(row["start_date"], "yyyy-MM-dd"))
            self.due_edit.setDate(QDate.fromString(row["due_date"], "yyyy-MM-dd"))
            self.progress.setValue(int(row["progress"]))
            self.project_edit.setText(row["project_ref"] or "")
            self.move_cb.setChecked(bool(row["move_on_complete"]))
            self.completed_root.setText(row["completed_root"] or "")

    def _toggle_move_fields(self, checked):
        self.completed_root.setEnabled(checked)
        self.completed_root_btn.setEnabled(checked)

    def _url_focus(self):
        self.project_edit.setFocus()
        if not self.project_edit.text():
            self.project_edit.setText("https://")
            self.project_edit.setCursorPosition(len(self.project_edit.text()))

    def _choose_file(self):
        p, _ = QFileDialog.getOpenFileName(self, "연결할 파일 선택")
        if p:
            self.project_edit.setText(p)

    def _choose_folder(self):
        p = QFileDialog.getExistingDirectory(self, "연결할 폴더 선택")
        if p:
            self.project_edit.setText(p)

    def _choose_completed_root(self):
        p = QFileDialog.getExistingDirectory(self, "완료된 프로젝트를 이동할 폴더")
        if p:
            self.completed_root.setText(p)

    def accept(self):
        if not self.title_edit.text().strip():
            QMessageBox.warning(self, "확인", "할 일 이름을 입력하세요.")
            return
        if self.due_edit.date() < self.start_edit.date():
            QMessageBox.warning(self, "확인", "마감일은 시작일보다 빠를 수 없습니다.")
            return
        if self.move_cb.isChecked():
            ref = self.project_edit.text().strip()
            dst = self.completed_root.text().strip()
            if not ref or is_url(ref):
                QMessageBox.warning(self, "확인", "실제 파일 이동은 로컬 파일/폴더 연결일 때만 사용할 수 있습니다.")
                return
            if not dst:
                QMessageBox.warning(self, "확인", "완료 파일 이동 위치를 선택하세요.")
                return
        super().accept()

    def data(self) -> TaskFormData:
        return TaskFormData(
            title=self.title_edit.text().strip(),
            start_date=self.start_edit.date().toString("yyyy-MM-dd"),
            due_date=self.due_edit.date().toString("yyyy-MM-dd"),
            progress=self.progress.value(),
            project_ref=self.project_edit.text().strip(),
            move_on_complete=self.move_cb.isChecked(),
            completed_root=self.completed_root.text().strip()
        )


class TodoTree(QTreeWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setColumnCount(6)
        self.setHeaderLabels(["할 일 / 세부항목", "시작", "마감", "남은날", "진척도", "Project"])
        self.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.setAlternatingRowColors(True)
        self.setUniformRowHeights(True)
        self.setIndentation(24)
        self.header().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        for col in (1, 2, 3, 4):
            self.header().setSectionResizeMode(col, QHeaderView.ResizeMode.ResizeToContents)
        self.header().setSectionResizeMode(5, QHeaderView.ResizeMode.Stretch)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.db = TodoDB(DB_PATH)
        self.setWindowTitle(APP_NAME)
        self.resize(1180, 720)
        self._really_quit = False

        self.search = QLineEdit()
        self.search.setPlaceholderText("할 일 검색...")
        self.search.textChanged.connect(self.refresh)

        self.tabs = QTabWidget()
        self.active_tree = TodoTree()
        self.completed_tree = TodoTree()
        self.tabs.addTab(self.active_tree, "진행 중")
        self.tabs.addTab(self.completed_tree, "완료")
        self.tabs.currentChanged.connect(self._sync_buttons)

        self.add_btn = QPushButton("＋ 할 일 추가")
        self.sub_btn = QPushButton("＋ 세부항목")
        self.edit_btn = QPushButton("수정")
        self.progress_btn = QPushButton("진척도")
        self.complete_btn = QPushButton("✓ 완료")
        self.open_btn = QPushButton("Project 열기")
        self.delete_btn = QPushButton("삭제")

        self.add_btn.clicked.connect(self.add_task)
        self.sub_btn.clicked.connect(self.add_subtask)
        self.edit_btn.clicked.connect(self.edit_task)
        self.progress_btn.clicked.connect(self.update_progress)
        self.complete_btn.clicked.connect(self.toggle_complete)
        self.open_btn.clicked.connect(self.open_project)
        self.delete_btn.clicked.connect(self.delete_task)

        top = QHBoxLayout()
        top.addWidget(QLabel("TODO"))
        top.addWidget(self.search, 1)
        for b in (
            self.add_btn, self.sub_btn, self.edit_btn, self.progress_btn,
            self.complete_btn, self.open_btn, self.delete_btn
        ):
            top.addWidget(b)

        wrapper = QWidget()
        layout = QVBoxLayout(wrapper)
        layout.addLayout(top)
        layout.addWidget(self.tabs, 1)
        self.setCentralWidget(wrapper)

        for tree in (self.active_tree, self.completed_tree):
            tree.itemDoubleClicked.connect(lambda item, col: self.edit_task())
            tree.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
            tree.customContextMenuRequested.connect(self.show_context_menu)

        self.statusBar().showMessage(f"데이터 저장 위치: {DB_PATH}")
        self._setup_tray()
        self._apply_style()
        self.refresh()

    def _apply_style(self):
        self.setStyleSheet("""
            QMainWindow { background: #f5f7fb; }
            QLineEdit, QDateEdit, QSpinBox {
                padding: 7px; border: 1px solid #cfd6e4; border-radius: 6px; background: white;
            }
            QPushButton {
                padding: 7px 10px; border: 1px solid #cfd6e4; border-radius: 6px; background: white;
            }
            QPushButton:hover { background: #eef3ff; }
            QTreeWidget {
                background: white; border: 1px solid #d9deea; border-radius: 8px;
                font-size: 13px;
            }
            QHeaderView::section {
                background: #eef2f8; padding: 7px; border: 0; border-bottom: 1px solid #d9deea;
                font-weight: 600;
            }
            QTabWidget::pane { border: 0; }
            QTabBar::tab { padding: 9px 18px; }
        """)

    def _setup_tray(self):
        self.tray = None
        if QSystemTrayIcon.isSystemTrayAvailable():
            icon = self.style().standardIcon(QStyle.StandardPixmap.SP_FileDialogDetailedView)
            self.setWindowIcon(icon)
            self.tray = QSystemTrayIcon(icon, self)
            menu = QMenu()
            act_show = QAction("열기", self)
            act_show.triggered.connect(self.show_normal)
            act_quit = QAction("완전히 종료", self)
            act_quit.triggered.connect(self.quit_app)
            menu.addAction(act_show)
            menu.addSeparator()
            menu.addAction(act_quit)
            self.tray.setContextMenu(menu)
            self.tray.activated.connect(self._tray_activated)
            self.tray.show()

    def _tray_activated(self, reason):
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            self.show_normal()

    def show_normal(self):
        self.show()
        self.raise_()
        self.activateWindow()

    def quit_app(self):
        self._really_quit = True
        QApplication.instance().quit()

    def closeEvent(self, event):
        if self._really_quit or self.tray is None:
            event.accept()
        else:
            event.ignore()
            self.hide()
            self.tray.showMessage(
                APP_NAME,
                "프로그램은 트레이에서 계속 실행 중입니다.",
                QSystemTrayIcon.MessageIcon.Information,
                1500
            )

    def current_tree(self):
        return self.active_tree if self.tabs.currentIndex() == 0 else self.completed_tree

    def selected_id(self):
        item = self.current_tree().currentItem()
        if not item:
            return None
        return item.data(0, Qt.ItemDataRole.UserRole)

    def _sync_buttons(self):
        completed = self.tabs.currentIndex() == 1
        self.complete_btn.setText("↩ 진행 중으로" if completed else "✓ 완료")
        self.sub_btn.setEnabled(not completed)

    def refresh(self):
        query = self.search.text().strip().lower()
        self.active_tree.clear()
        self.completed_tree.clear()
        for row in self.db.roots("active"):
            item = self._build_item(row, query=query, parent_active=True)
            if item:
                self.active_tree.addTopLevelItem(item)
        for row in self.db.roots("completed"):
            item = self._build_item(row, query=query, parent_active=False)
            if item:
                self.completed_tree.addTopLevelItem(item)
        self.active_tree.expandAll()
        self.completed_tree.expandAll()
        self._sync_buttons()

    def _build_item(self, row, query="", parent_active=True):
        children = self.db.children(row["id"])
        child_items = []
        for child in children:
            ci = self._build_item(child, query=query, parent_active=parent_active)
            if ci:
                child_items.append(ci)

        this_matches = (
            not query
            or query in (row["title"] or "").lower()
            or query in (row["project_ref"] or "").lower()
        )
        if not this_matches and not child_items:
            return None

        project_label = row["project_ref"] or ""
        if project_label and len(project_label) > 45:
            project_label = "…" + project_label[-44:]

        item = QTreeWidgetItem([
            row["title"],
            row["start_date"],
            row["due_date"],
            dday_text(row["due_date"]),
            f'{int(row["progress"])}%',
            project_label
        ])
        item.setData(0, Qt.ItemDataRole.UserRole, row["id"])
        item.setToolTip(5, row["project_ref"] or "")
        if row["status"] == "completed":
            font = item.font(0)
            font.setStrikeOut(True)
            item.setFont(0, font)
        if row["parent_id"] is None:
            font = item.font(0)
            font.setBold(True)
            item.setFont(0, font)

        for ci in child_items:
            item.addChild(ci)
        return item

    def add_task(self):
        dlg = TaskDialog(self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            d = dlg.data()
            self.db.add_task(
                d.title, d.start_date, d.due_date, d.progress, d.project_ref,
                None, d.move_on_complete, d.completed_root
            )
            self.refresh()

    def add_subtask(self):
        task_id = self.selected_id()
        if not task_id:
            QMessageBox.information(self, "세부항목", "부모가 될 할 일 또는 세부항목을 먼저 선택하세요.")
            return
        parent = self.db.get(task_id)
        dlg = TaskDialog(self, is_subtask=True)
        dlg.start_edit.setDate(QDate.fromString(parent["start_date"], "yyyy-MM-dd"))
        dlg.due_edit.setDate(QDate.fromString(parent["due_date"], "yyyy-MM-dd"))
        if dlg.exec() == QDialog.DialogCode.Accepted:
            d = dlg.data()
            self.db.add_task(
                d.title, d.start_date, d.due_date, d.progress, d.project_ref,
                task_id, d.move_on_complete, d.completed_root
            )
            self.refresh()

    def edit_task(self):
        task_id = self.selected_id()
        if not task_id:
            QMessageBox.information(self, "수정", "수정할 항목을 선택하세요.")
            return
        row = self.db.get(task_id)
        dlg = TaskDialog(self, row=row, is_subtask=row["parent_id"] is not None)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            d = dlg.data()
            self.db.update_task(
                task_id, title=d.title, start_date=d.start_date, due_date=d.due_date,
                progress=d.progress, project_ref=d.project_ref,
                move_on_complete=int(d.move_on_complete), completed_root=d.completed_root
            )
            self.refresh()

    def update_progress(self):
        task_id = self.selected_id()
        if not task_id:
            QMessageBox.information(self, "진척도", "항목을 선택하세요.")
            return
        row = self.db.get(task_id)
        dlg = QDialog(self)
        dlg.setWindowTitle("진척도 업데이트")
        spin = QSpinBox()
        spin.setRange(0, 100)
        spin.setSuffix("%")
        spin.setValue(int(row["progress"]))
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save |
            QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(dlg.accept)
        buttons.rejected.connect(dlg.reject)
        layout = QVBoxLayout(dlg)
        layout.addWidget(QLabel(row["title"]))
        layout.addWidget(spin)
        layout.addWidget(buttons)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            self.db.update_task(task_id, progress=spin.value())
            self.refresh()

    def toggle_complete(self):
        task_id = self.selected_id()
        if not task_id:
            QMessageBox.information(self, "완료", "항목을 선택하세요.")
            return
        row = self.db.get(task_id)

        if self.tabs.currentIndex() == 1:
            self.db.set_status_recursive(task_id, "active")
            self.refresh()
            return

        if row["parent_id"] is None:
            answer = QMessageBox.question(
                self, "완료 처리",
                "이 할 일을 완료 처리할까요?\n하위 세부항목도 함께 완료 처리됩니다.",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if answer != QMessageBox.StandardButton.Yes:
                return

        if not self._move_project_if_requested(row):
            return

        if row["parent_id"] is None:
            self.db.set_status_recursive(task_id, "completed")
        else:
            self.db.update_task(
                task_id, status="completed", progress=100,
                completed_at=datetime.now().isoformat(timespec="seconds")
            )
        self.refresh()

    def _move_project_if_requested(self, row):
        if not row["move_on_complete"]:
            return True
        src = Path(row["project_ref"])
        dst_root = Path(row["completed_root"])
        if not src.exists():
            QMessageBox.warning(self, "Project 이동", f"연결된 경로를 찾을 수 없습니다:\n{src}")
            return False
        try:
            dst_root.mkdir(parents=True, exist_ok=True)
            dst = dst_root / src.name
            if dst.exists():
                stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                dst = dst_root / f"{src.stem}_{stamp}{src.suffix}"
            import shutil
            shutil.move(str(src), str(dst))
            self.db.update_task(row["id"], project_ref=str(dst))
            return True
        except Exception as e:
            QMessageBox.critical(self, "Project 이동 실패", str(e))
            return False

    def open_project(self):
        task_id = self.selected_id()
        if not task_id:
            QMessageBox.information(self, "Project", "항목을 선택하세요.")
            return
        row = self.db.get(task_id)
        ref = (row["project_ref"] or "").strip()
        if not ref:
            QMessageBox.information(self, "Project", "연결된 링크/파일/폴더가 없습니다.")
            return
        if is_url(ref):
            QDesktopServices.openUrl(QUrl(ref))
            return
        p = Path(ref)
        if not p.exists():
            QMessageBox.warning(self, "Project", f"경로를 찾을 수 없습니다:\n{ref}")
            return
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(p)))

    def delete_task(self):
        task_id = self.selected_id()
        if not task_id:
            QMessageBox.information(self, "삭제", "삭제할 항목을 선택하세요.")
            return
        row = self.db.get(task_id)
        ans = QMessageBox.question(
            self, "삭제",
            f"'{row['title']}' 을(를) 삭제할까요?\n하위 항목도 함께 삭제됩니다.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if ans == QMessageBox.StandardButton.Yes:
            self.db.delete_recursive(task_id)
            self.refresh()

    def show_context_menu(self, pos):
        tree = self.current_tree()
        item = tree.itemAt(pos)
        if not item:
            return
        tree.setCurrentItem(item)
        menu = QMenu(self)
        if self.tabs.currentIndex() == 0:
            menu.addAction("세부항목 추가", self.add_subtask)
            menu.addAction("진척도 업데이트", self.update_progress)
            menu.addAction("완료", self.toggle_complete)
        else:
            menu.addAction("진행 중으로 되돌리기", self.toggle_complete)
        menu.addSeparator()
        menu.addAction("수정", self.edit_task)
        menu.addAction("Project 열기", self.open_project)
        menu.addSeparator()
        menu.addAction("삭제", self.delete_task)
        menu.exec(tree.viewport().mapToGlobal(pos))


def main():
    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setQuitOnLastWindowClosed(False)
    font = QFont()
    font.setPointSize(10)
    app.setFont(font)

    w = MainWindow()
    w.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
