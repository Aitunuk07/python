import tkinter as tk #Импорт библиотеки tkinter для создания графического интерфейса
from tkinter import ttk
import os
import psycopg2 #Импорт библиотеки psycopg2 для работы с PostgreSQL


def get_db_connection():
    try:
        database_url = os.getenv('DATABASE_URL',
                                 'postgresql://library_owner:npg_ceuv1IqpZt2U@ep-old-rice-a8e8xbki-pooler.eastus2.azure.neon.tech/library?sslmode=require')
        connection = psycopg2.connect(database_url) #Подключение к базе данных
        return connection
    except Exception as e:
        print(f"Ошибка подключения к базе данных: {e}")
        return None


class Book:
    def __init__(self, book_id, title, author, year, isbn): #Инициализация объекта книги с атрибутами
        self.book_id = book_id
        self.title = title
        self.author = author
        self.year = year
        self.isbn = isbn


class Library:
    def __init__(self):
        self.connection = get_db_connection() #Получение соединение с БД
        self.cursor = self.connection.cursor() if self.connection else None
        self.create_table()
        self.book_id_counter = self.get_max_id() + 1 if self.cursor else 1 #установка счетчика ID для новых книг

    def create_table(self):
        if not self.cursor:
            return
        try:
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS books (
                    book_id INTEGER PRIMARY KEY,
                    title VARCHAR(255) NOT NULL,
                    author VARCHAR(255) NOT NULL,
                    year INTEGER,
                    isbn VARCHAR(13)
                );
            """)
            self.connection.commit() #Фиксация изменений в БД
        except Exception as e:
            print(f"Ошибка создания таблицы: {e}")

    def get_max_id(self):
        try:
            self.cursor.execute("SELECT MAX(book_id) FROM books;")
            result = self.cursor.fetchone()[0] #Получение результата запроса
            return result if result is not None else 0
        except Exception:
            return 0

    def add_book(self, title, author, year, isbn):
        if not self.cursor:
            return "Ошибка подключения базе данных"
        try:
            query = """
            INSERT INTO books (book_id, title, author, year, isbn)
            VALUES (%s, %s, %s, %s, %s);
            """
            self.cursor.execute(query, (self.book_id_counter, title, author, year, isbn))
            self.connection.commit() #Фиксация изменений
            self.book_id_counter += 1 #Увеличение счетчика ID
            return f"Книга добавлена: {title}" 
        except Exception as e:
            self.connection.rollback()
            return f"Ошибка добавления книги: {e}"

    def remove_book(self, book_id):
        if not self.cursor:
            return "Ошибка подключения базе данных"
        try:
            #Удаление книги по ID
            query = "DELETE FROM books WHERE book_id = %s;"
            self.cursor.execute(query, (book_id,))
            if self.cursor.rowcount > 0:
                self.connection.commit()
                return f"Книга удалена (ID: {book_id})"
            return "Книга не найдена."
        except Exception as e:
            self.connection.rollback()
            return f"Ошибка удаления книги: {e}"

    def find_book(self, title):
        if not self.cursor:
            return "Ошибка подключения базе данных"
        try:
            #Поиск книги по названию
            query = "SELECT * FROM books WHERE LOWER(title) LIKE LOWER(%s);"
            self.cursor.execute(query, (f"%{title}%",))
            books = self.cursor.fetchall()
            return [Book(*book) for book in books] if books else "Книги не найдены."
        except Exception as e:
            return f"Ошибка поиска книги: {e}"

    def find_by_author(self, author):
        if not self.cursor:
            return "Ошибка подключения базе данных"
        try:
            #Поиск книги по автору
            query = "SELECT * FROM books WHERE LOWER(author) LIKE LOWER(%s);"
            self.cursor.execute(query, (f"%{author}%",))
            books = self.cursor.fetchall()
            return [Book(*book) for book in books] if books else "Книги не найдены."
        except Exception as e:
            return f"Ошибка поиска автору: {e}"

    def find_by_isbn(self, isbn):
        if not self.cursor:
            return "Ошибка подключения базе данных"
        try:
            # Поиск книги по ISBN
            query = "SELECT * FROM books WHERE isbn LIKE %s;"
            self.cursor.execute(query, (f"%{isbn}%",))
            books = self.cursor.fetchall()
            return [Book(*book) for book in books] if books else "Книги не найдены."
        except Exception as e:
            return f"Ошибка поиска по шифру: {e}"

    def find_by_year(self, year):
        if not self.cursor:
            return "Ошибка подключения к базе данных"
        try:
             # Поиск книг по году
            query = "SELECT * FROM books WHERE year::text LIKE %s;"
            self.cursor.execute(query, (f"%{year}%",))
            books = self.cursor.fetchall()
            return [Book(*book) for book in books] if books else "Книги не найдены."
        except Exception as e:
            return f"Ошибка поиска по году: {e}"

    def list_books(self):
        if not self.cursor:
            return "Ошибка подключения к базе данных"
        try:
             # Получение списка всех книг
            query = "SELECT * FROM books;"
            self.cursor.execute(query)
            books = self.cursor.fetchall()
            return [Book(*book) for book in books] if books else "Нет доступных книг."
        except Exception as e:
            return f"Ошибка получения списка книг: {e}"

    def update_book(self, book_id, new_title, new_author, new_year, new_isbn):
        if not self.cursor:
            return "Ошибка подключения к базе данных"
        try:
                # Обновление информации о книге
            query = """
            UPDATE books 
            SET title = %s, author = %s, year = %s, isbn = %s
            WHERE book_id = %s;
            """
            self.cursor.execute(query, (new_title, new_author, new_year, new_isbn, book_id))
            if self.cursor.rowcount > 0:
                self.connection.commit()
                return f"Книга обновлена: {new_title}"
            return "Книга не найдена."
        except Exception as e:
            self.connection.rollback()
            return f"Ошибка обновления книги: {e}"

    def get_statistics(self):
        if not self.cursor:
            return "Ошибка подключения к базе данных"
        try:
             # Получение количества книг в библиотеке
            query = "SELECT COUNT(*) FROM books;"
            self.cursor.execute(query)
            count = self.cursor.fetchone()[0]
            return f"Всего книг в библиотеке: {count}"
        except Exception as e:
            return f"Ошибка получения статистики: {e}"

    def __del__(self):
        if self.cursor:
            self.cursor.close()
        if self.connection:
            self.connection.close() # Закрытие соединения с базой данных


class LibraryApp:
    def __init__(self, root):
        self.library = Library() #Создание объекта библиотеки
        self.root = root  #Основное окно приложения
        self.root.title("Управление библиотекой") #заголовок окна
        self.root.geometry("900x600") #размеры окна
        self.root.configure(bg="#f0f2f5") #фоновый цвет окна

        #Боковая панель
        self.sidebar = tk.Frame(root, bg="#4a90e2", width=200) #Создание боковой панели
        self.sidebar.pack(side=tk.LEFT, fill=tk.Y)
         #Заголовок боковой панели
        tk.Label(self.sidebar, text="Библиотека", font=("Helvetica", 18, "bold"),
                 bg="#4a90e2", fg="white").pack(pady=20)

        #Элементы меню боковой панели
        menu_items = [
            ("Книги", self.show_books),  #Кнопка для отображения списка книг
            ("Добавить книгу", self.show_add_book),  #Кнопка для добавления книги
            ("Поиск", self.show_search), #Кнопка для поиска книг
            ("Статистика", self.show_stats)  #Кнопка для отображения статистики
        ]
        # Создание кнопок меню
        for text, command in menu_items:
            btn = tk.Button(self.sidebar, text=text, font=("Helvetica", 12),
                            bg="#1e3a8a", fg="white", bd=0, pady=10,
                            command=command)
            btn.pack(fill=tk.X, padx=10, pady=5) #Размещение кнопок на боковой панели
        # Основная область приложения
        self.main_frame = tk.Frame(root, bg="#f0f2f5")
        self.main_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=20, pady=20)

        self.show_books() #Отображение списка книг при запуске

    def clear_main_frame(self):
        # Очистка основной области приложения
        for widget in self.main_frame.winfo_children():
            widget.destroy()

    def show_notification(self, message, success=True): #Отображение уведомления
        noti_frame = tk.Frame(self.root, bg="#2ecc71" if success else "#e74c3c")
        noti_frame.place(relx=0.5, rely=0.9, anchor="center")
        tk.Label(noti_frame, text=message, font=("Helvetica", 12),
                 bg="#2ecc71" if success else "#e74c3c", fg="white", padx=20, pady=10).pack()
        self.root.after(3000, noti_frame.destroy)   #Автоматическое закрытие уведомления через 3 секунды

    def show_books(self):
        self.clear_main_frame() #Очистка основной области
          #Заголовок раздела "Все книги"
        tk.Label(self.main_frame, text="Все книги", font=("Helvetica", 20, "bold"),
                 bg="#f0f2f5").pack(pady=10)
         #Фрейм для таблицы с книгами
        tree_frame = tk.Frame(self.main_frame, bg="white", bd=1, relief="solid")
        tree_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        # Создание стиля для заголовков
        style = ttk.Style()
        style.configure("Treeview.Heading", font=("Helvetica", 12, "bold"))
         #Создание таблицы для отображения книг
        self.tree = ttk.Treeview(tree_frame, columns=("ID", "Название", "Автор", "Год", "Шифр"),
                                 show="headings", height=15)
        self.tree.heading("ID", text="ID") 
        self.tree.heading("Название", text="Название") 
        self.tree.heading("Автор", text="Автор")  
        self.tree.heading("Год", text="Год") 
        self.tree.heading("Шифр", text="Шифр") 
        #Настройка стиля для данных в таблице
        style = ttk.Style()
        style.configure("Treeview", font=("Helvetica", 12))  #Установка шрифт для всех данных


        self.tree.column("ID", width=50)
        self.tree.column("Название", width=200)
        self.tree.column("Автор", width=150)
        self.tree.column("Год", width=70)
        self.tree.column("Шифр", width=120)

        self.tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        #Кнопка для удаления выбранной книги
        tk.Button(self.main_frame, text="Удалить выбранное", command=self.remove_book,
                  bg="#e74c3c", fg="white", font=("Helvetica", 12), bd=0, padx=20, pady=5).pack(pady=10)

        self.list_books()

    def show_add_book(self):
        self.clear_main_frame()  #Очистка основной области

        #Заголовок раздела "Добавить новую книгу"
        tk.Label(self.main_frame, text="Добавить новую книгу", font=("Helvetica", 20, "bold"),
                 bg="#f0f2f5").pack(pady=10)

        form_frame = tk.Frame(self.main_frame, bg="white", bd=1, relief="solid")
        form_frame.pack(pady=10, padx=20, fill=tk.X)
         #Поля для ввода данных о книге
        fields = ["Название", "Автор", "Год", "Шифр"]
        self.entries = {}

        for field in fields:
            frame = tk.Frame(form_frame, bg="white")
            frame.pack(fill=tk.X, padx=20, pady=10)
            tk.Label(frame, text=f"{field}:", font=("Helvetica", 12), bg="white",
                     width=10, anchor="w").pack(side=tk.LEFT)
            entry = tk.Entry(frame, font=("Helvetica", 12), width=30)
            entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
            self.entries[field.lower()] = entry
        #Кнопка для добавления книги
        tk.Button(form_frame, text="Добавить книгу", command=self.add_book,
                  bg="#2ecc71", fg="white", font=("Helvetica", 12), bd=0, padx=20, pady=5).pack(pady=20)

    def show_search(self):
        self.clear_main_frame()
        #Заголовок раздела "Поиск книг"
        tk.Label(self.main_frame, text="Поиск книг", font=("Helvetica", 20, "bold"),
                 bg="#f0f2f5").pack(pady=10)

        # Панель поиска
        search_bar_frame = tk.Frame(self.main_frame, bg="white", bd=1, relief="solid")
        search_bar_frame.pack(pady=10, padx=20, fill=tk.X)

        # Выбор типа поиска
        self.search_type = tk.StringVar(value="выбрать")
        search_types = [("Название", "название"), ("Автор", "автор"), ("Шифр", "шифр"), ("Год", "год")]
        type_menu = ttk.Combobox(search_bar_frame, textvariable=self.search_type,
                                 values=[t[1] for t in search_types], state="readonly",
                                 font=("Helvetica", 12), width=10) 
        
        type_menu.pack(side=tk.LEFT, padx=10, pady=10)

        #Поле ввода для поиска
        self.search_entry = tk.Entry(search_bar_frame, font=("Helvetica", 12), width=40,
                                     bd=0, bg="#ecf0f1")
        self.search_entry.insert(0, "Введите для поиска...")
        self.search_entry.config(fg="grey")
        self.search_entry.bind("<FocusIn>", lambda e: self.clear_placeholder())
        self.search_entry.bind("<FocusOut>", lambda e: self.add_placeholder())
        self.search_entry.bind("<KeyRelease>", self.search_books)
        self.search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=10, pady=10)
        #Результаты поиска
        self.search_tree = ttk.Treeview(self.main_frame, columns=("ID", "Название", "Автор", "Год", "Шифр"),
                                        show="headings", height=15)
        self.search_tree.heading("ID", text="ID")
        self.search_tree.heading("Название", text="Название")
        self.search_tree.heading("Автор", text="Автор")
        self.search_tree.heading("Год", text="Год")
        self.search_tree.heading("Шифр", text="Шифр")

        self.search_tree.column("ID", width=50)
        self.search_tree.column("Название", width=200)
        self.search_tree.column("Автор", width=150)
        self.search_tree.column("Год", width=70)
        self.search_tree.column("Шифр", width=120)

        self.search_tree.pack(fill=tk.BOTH, expand=True, pady=10)

    def clear_placeholder(self):
        if self.search_entry.get() == "Введите для поиска...":
            self.search_entry.delete(0, tk.END)
            self.search_entry.config(fg="black")

    def add_placeholder(self):
        if not self.search_entry.get():
            self.search_entry.insert(0, "Введите для поиска...")
            self.search_entry.config(fg="grey")

    def show_stats(self):
        self.clear_main_frame()
        #Заголовок раздела "Статистика библиотеки"
        tk.Label(self.main_frame, text="Статистика библиотеки", font=("Helvetica", 20, "bold"),
                 bg="#f0f2f5").pack(pady=10)

        stats = self.library.get_statistics()
        tk.Label(self.main_frame, text=stats, font=("Helvetica", 14), bg="#f0f2f5").pack(pady=20)

    def add_book(self):  #Получение данных из полей ввода
        title = self.entries["название"].get()
        author = self.entries["автор"].get()
        year = self.entries["год"].get()
        isbn = self.entries["шифр"].get()
        result = self.library.add_book(title, author, year, isbn)

        if "Книга добавлена" in result:
            self.show_notification("Книга успешно добавлена!", success=True)
        else:
            self.show_notification(result, success=False)  #Очистка полей ввода

        for entry in self.entries.values():
            entry.delete(0, tk.END)
        self.show_books() #Обновление списка книг

    def remove_book(self):
        selected = self.tree.selection() #Получение выбранной книги
        if not selected:
            tk.messagebox.showwarning("Предупреждение", "Пожалуйста, выберите книгу")
            return
        book_id = int(self.tree.item(selected)["values"][0])
        result = self.library.remove_book(book_id) #Удаление книги
        tk.messagebox.showinfo("Результат", result)
        self.list_books() #Обновление списка книг

    def search_books(self, event=None):
        search_type = self.search_type.get()
        query = self.search_entry.get().strip()

        if query == "Введите для поиска..." or not query:
            self.search_tree.delete(*self.search_tree.get_children())
            return

        if search_type == "название":
            books = self.library.find_book(query)
        elif search_type == "автор":
            books = self.library.find_by_author(query)
        elif search_type == "шифр":
            books = self.library.find_by_isbn(query)
        elif search_type == "год":
            books = self.library.find_by_year(query)

        self.search_tree.delete(*self.search_tree.get_children())
        if isinstance(books, list):
            for book in books:
                self.search_tree.insert("", "end",
                                        values=(book.book_id, book.title, book.author, book.year, book.isbn))

    def list_books(self):
        self.tree.delete(*self.tree.get_children()) #Очистка таблицы
        books = self.library.list_books()  #Получение списка книг
        if isinstance(books, list):
            for book in books:
                self.tree.insert("", "end",
                                 values=(book.book_id, book.title, book.author, book.year, book.isbn))


if __name__ == "__main__":
    root = tk.Tk()
    app = LibraryApp(root)
    root.mainloop() #Запуск основного цикла приложения
