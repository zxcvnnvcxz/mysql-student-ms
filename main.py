import sys

from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QAction, QIcon
from PyQt6.QtWidgets import QApplication, QLabel, QWidget, QGridLayout, QLineEdit, QPushButton, QMainWindow, \
    QTableWidget, QTableWidgetItem, QDialog, QVBoxLayout, QComboBox, QToolBar, QStatusBar, QMessageBox
import mysql.connector
import os
import logging

# Set up logging
logging.basicConfig(level=logging.DEBUG)


class DatabaseWorker(QThread):
    data_loaded = pyqtSignal(list)  # Signal to emit when data is loaded

    def __init__(self):
        super().__init__()
        self.connection = None
        self.cursor = None

    def run(self):
        # Perform database operations in the background thread
        try:
            connection = mysql.connector.connect(
                host="localhost",
                user="root",
                password=os.getenv("mysql_pw"),
                database="school"
            )
            cursor = connection.cursor()
            cursor.execute("SELECT * FROM students")
            result = cursor.fetchall()

            # Emit the data to the main thread
            self.data_loaded.emit(result)

        except mysql.connector.Error as err:
            print(f"Error connecting to MySQL: {err}")
        finally:
            # Close resources
            if cursor:
                cursor.close()
            if connection:
                connection.close()


class DatabaseConnection:
    password = os.getenv("mysql_pw")
    def __init__(self, host="localhost", user="root", password="science choosing surpass", database="school"):
        self.host = host
        self.user = user
        self.password = password
        self.database = database
        logging.debug(f"Initialising DatabaseConnection with host={host}, user={user}")

    def connect(self):
        try:
            logging.debug("Attempting to connect to database...")
            connection = mysql.connector.connect(host=self.host, user=self.user, password=self.password, database=self.database)
            logging.debug("Database connection successful!")
            return connection
        except mysql.connector.Error as err:
            if err.errno == 1045:
                logging.debug(f"Access denied: {err.msg}. Please check your username/password.")
            elif err.errno == 1049:
                logging.debug(f"Unknown database: {err.msg}. Please check your database name.")
            else:
                logging.debug(f"Database connection error: {err.msg}")
            return None


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Student Management System")
        self.setMinimumSize(800, 600)

        file_menu_item = self.menuBar().addMenu("&File")
        edit_menu_item = self.menuBar().addMenu("&Edit")
        help_menu_item = self.menuBar().addMenu("&Help")


        add_student_action = QAction(QIcon("icons/add.png"),"Add Student", self)
        add_student_action.triggered.connect(self.insert)
        file_menu_item.addAction(add_student_action)

        search_action = QAction(QIcon("icons/search.png"), "Search", self)
        search_action.triggered.connect(self.search)
        edit_menu_item.addAction(search_action)

        about_action = QAction("About", self)
        help_menu_item.addAction(about_action)
        about_action.triggered.connect(self.about)

        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(("Id", "Name", "Course", "Mobile"))
        self.table.verticalHeader().setVisible(False)
        self.setCentralWidget(self.table)

        # Create toolbar and add toolbar elements
        toolbar = QToolBar()
        toolbar.setMovable(True)
        self.addToolBar(toolbar)
        toolbar.addAction(add_student_action)

        self.addToolBar(toolbar)
        toolbar.addAction(search_action)

        # Create status bar and add status bar elements
        self.statusbar = QStatusBar()
        self.setStatusBar(self.statusbar)

        # Detect a cell click
        self.table.cellClicked.connect(self.cell_clicked)

        self.show()

    def load_data(self):
        # Start the database worker thread to fetch data
        self.worker = DatabaseWorker()
        self.worker.data_loaded.connect(self.populate_table)  # Connect the signal to the slot
        self.worker.start()

    def populate_table(self, data):
        # This method will be called once the data is loaded
        self.table.setRowCount(0)  # Clear existing data
        for row_number, row_data in enumerate(data):
            self.table.insertRow(row_number)
            for column_number, data_item in enumerate(row_data):
                self.table.setItem(row_number, column_number, QTableWidgetItem(str(data_item)))

    def cell_clicked(self):
        edit_button = QPushButton("Edit Record")
        edit_button.clicked.connect(self.edit)

        delete_button = QPushButton("Delete Record")
        delete_button.clicked.connect(self.delete)

        children = self.findChildren(QPushButton)
        if children:
            for child in children:
                self.statusbar.removeWidget(child)

        self.statusbar.addWidget(edit_button)
        self.statusbar.addWidget(delete_button)

    def insert(self):
        dialog = InsertDialog(self)
        dialog.exec()

    def search(self):
        dialog = SearchDialog(self)
        dialog.exec()

    def edit(self):
        dialog = EditDialog(self)
        dialog.exec()

    def delete(self):
        dialog = DeleteDialog(self)
        dialog.exec()

    def about(self):
        dialog = AboutDialog(self)
        dialog.exec()


class AboutDialog(QMessageBox):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.setWindowTitle("About")
        content = """
        This app was created during an online course by Ardit Sulce, "Python Mega Course". 
        Feel free to modify and reuse this app.
        """
        self.setText(content)


class EditDialog(QDialog):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.setWindowTitle("Update Student Data")
        self.setFixedWidth(300)
        self.setFixedHeight(300)

        layout = QVBoxLayout()

        # Get Student name from selected row
        index = main_window.table.currentRow()
        student_name = main_window.table.item(index, 1).text()

        # Get ID from selected row
        self.student_id = main_window.table.item(index, 0).text()

        self.student_name = QLineEdit(student_name)
        self.student_name.setPlaceholderText("Name")
        layout.addWidget(self.student_name)

        # Get student course from selected row
        course_name = main_window.table.item(index, 2).text()

        self.course_name = QComboBox()
        courses = ["Biology", "Math", "Astronomy", "Physics"]
        self.course_name.addItems(courses)
        self.course_name.setCurrentText(course_name)
        layout.addWidget(self.course_name)

        # Get student number from selected row
        student_mobile = main_window.table.item(index, 3).text()

        self.mobile = QLineEdit(student_mobile)
        self.mobile.setPlaceholderText("Mobile")
        layout.addWidget(self.mobile)

        button = QPushButton("Update")
        button.clicked.connect(self.update_student)
        layout.addWidget(button)

        self.setLayout(layout)

    def update_student(self):
        connection = DatabaseConnection().connect()
        cursor = connection.cursor()
        cursor.execute("UPDATE students SET name = %s, course = %s, mobile = %s WHERE id = %s",
             (self.student_name.text(), self.course_name.itemText(self.course_name.currentIndex()),
                        self.mobile.text(), self.student_id))
        connection.commit()
        cursor.close()
        connection.close()

        # Refresh the table
        main_window.load_data()


class DeleteDialog(QDialog):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.setWindowTitle("Delete Student Data")

        layout = QGridLayout()
        confirmation = QLabel("Are you sure you want to delete?")
        yes = QPushButton("Yes")
        no = QPushButton("No")

        layout.addWidget(confirmation, 0, 0, 1, 2) # Column 0, 0, expanding 1 row, 2 columns
        layout.addWidget(yes, 1, 0)
        layout.addWidget(no, 1, 1)
        self.setLayout(layout)

        yes.clicked.connect(self.delete_student)

    def delete_student(self):
        # Get selected row index and student id
        index = main_window.table.currentRow()
        student_id = main_window.table.item(index, 0).text()

        connection = DatabaseConnection().connect()
        cursor = connection.cursor()
        cursor.execute("DELETE from students WHERE id = %s", (student_id, )) # , is to make python think it's a tuple
        connection.commit()
        cursor.close()
        connection.close()
        main_window.load_data()

        self.close()

        confirmation_widget = QMessageBox()
        confirmation_widget.setWindowTitle("Success")
        confirmation_widget.setText("The record was deleted successfully!")
        confirmation_widget.exec()


class InsertDialog(QDialog):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.setWindowTitle("Insert Student Data")
        self.setFixedWidth(300)
        self.setFixedHeight(300)

        layout = QVBoxLayout()

        self.student_name = QLineEdit()
        self.student_name.setPlaceholderText("Name")
        layout.addWidget(self.student_name)

        self.course_name = QComboBox()
        courses = ["Biology", "Math", "Astronomy", "Physics"]
        self.course_name.addItems(courses)
        layout.addWidget(self.course_name)

        self.mobile = QLineEdit()
        self.mobile.setPlaceholderText("Mobile")
        layout.addWidget(self.mobile)

        button = QPushButton("Register")
        button.clicked.connect(self.add_student)
        layout.addWidget(button)

        self.setLayout(layout)

    def add_student(self):
        name = self.student_name.text()
        course = self.course_name.itemText(self.course_name.currentIndex())
        mobile = self.mobile.text()

        connection = DatabaseConnection().connect()
        cursor = connection.cursor()
        cursor.execute("INSERT INTO students (name, course, mobile) VALUES (%s, %s, %s)",
                       (name, course, mobile))
        connection.commit()
        cursor.close()
        connection.close()
        main_window.load_data()


class SearchDialog(QDialog):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.setWindowTitle("Search Student")
        self.setFixedWidth(300)
        self.setFixedHeight(300)

        layout = QVBoxLayout()

        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("Name")
        layout.addWidget(self.search_box)

        search_button = QPushButton("Search")
        search_button.clicked.connect(self.search)
        layout.addWidget(search_button)

        self.setLayout(layout)

    def search(self):
        name = self.search_box.text()
        connection = DatabaseConnection().connect()
        cursor = connection.cursor()
        cursor.execute("SELECT * FROM students where name = %s", (name,))
        result = cursor.fetchall()
        rows = list(result)
        items = main_window.table.findItems(name, Qt.MatchFlag.MatchFixedString)
        for item in items:
            main_window.table.item(item.row(), 1).setSelected(True)

        cursor.close()
        connection.close()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    main_window = MainWindow()
    main_window.show()
    main_window.load_data()
    sys.exit(app.exec())