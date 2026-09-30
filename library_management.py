import sqlite3
from datetime import datetime

DB_NAME = "library.db"


# ---------------- DATABASE ----------------

def connect_db():
    return sqlite3.connect(DB_NAME)


def create_tables():
    conn = connect_db()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS books (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            author TEXT NOT NULL,
            isbn TEXT UNIQUE NOT NULL,
            available INTEGER DEFAULT 1
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS members (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS issued_books (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            book_id INTEGER NOT NULL,
            member_id INTEGER NOT NULL,
            issue_date TEXT NOT NULL,
            return_date TEXT,
            FOREIGN KEY (book_id) REFERENCES books(id),
            FOREIGN KEY (member_id) REFERENCES members(id)
        )
    """)

    conn.commit()
    conn.close()


# ---------------- BOOK FUNCTIONS ----------------

def add_book():
    title = input("Enter book title: ").strip()
    author = input("Enter author: ").strip()
    isbn = input("Enter ISBN: ").strip()

    if not title or not author or not isbn:
        print("All fields are required.")
        return

    try:
        conn = connect_db()
        cursor = conn.cursor()

        cursor.execute(
            "INSERT INTO books (title, author, isbn) VALUES (?, ?, ?)",
            (title, author, isbn)
        )

        conn.commit()
        conn.close()

        print("Book added successfully.")

    except sqlite3.IntegrityError:
        print("ISBN already exists.")


def view_books():
    conn = connect_db()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM books")
    books = cursor.fetchall()

    conn.close()

    if not books:
        print("No books found.")
        return

    print("\n--- BOOK LIST ---")

    for book in books:
        status = "Available" if book[4] else "Issued"

        print(
            f"ID: {book[0]} | "
            f"Title: {book[1]} | "
            f"Author: {book[2]} | "
            f"ISBN: {book[3]} | "
            f"Status: {status}"
        )


def search_book():
    keyword = input("Enter title, author, or ISBN: ").strip()

    conn = connect_db()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT * FROM books
        WHERE title LIKE ?
           OR author LIKE ?
           OR isbn LIKE ?
    """, (
        f"%{keyword}%",
        f"%{keyword}%",
        f"%{keyword}%"
    ))

    books = cursor.fetchall()
    conn.close()

    if not books:
        print("No books found.")
        return

    print("\n--- SEARCH RESULTS ---")

    for book in books:
        status = "Available" if book[4] else "Issued"

        print(
            f"ID: {book[0]} | "
            f"Title: {book[1]} | "
            f"Author: {book[2]} | "
            f"ISBN: {book[3]} | "
            f"Status: {status}"
        )


def delete_book():
    try:
        book_id = int(input("Enter book ID to delete: "))

        conn = connect_db()
        cursor = conn.cursor()

        cursor.execute(
            "SELECT available FROM books WHERE id = ?",
            (book_id,)
        )

        book = cursor.fetchone()

        if not book:
            print("Book not found.")
        elif book[0] == 0:
            print("Cannot delete an issued book.")
        else:
            cursor.execute(
                "DELETE FROM books WHERE id = ?",
                (book_id,)
            )
            conn.commit()
            print("Book deleted successfully.")

        conn.close()

    except ValueError:
        print("Please enter a valid ID.")


# ---------------- MEMBER FUNCTIONS ----------------

def add_member():
    name = input("Enter member name: ").strip()
    email = input("Enter member email: ").strip()

    if not name or not email:
        print("All fields are required.")
        return

    try:
        conn = connect_db()
        cursor = conn.cursor()

        cursor.execute(
            "INSERT INTO members (name, email) VALUES (?, ?)",
            (name, email)
        )

        conn.commit()
        conn.close()

        print("Member registered successfully.")

    except sqlite3.IntegrityError:
        print("Email already registered.")


def view_members():
    conn = connect_db()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM members")
    members = cursor.fetchall()

    conn.close()

    if not members:
        print("No members found.")
        return

    print("\n--- MEMBER LIST ---")

    for member in members:
        print(
            f"ID: {member[0]} | "
            f"Name: {member[1]} | "
            f"Email: {member[2]}"
        )


# ---------------- ISSUE / RETURN ----------------

def issue_book():
    try:
        book_id = int(input("Enter book ID: "))
        member_id = int(input("Enter member ID: "))

        conn = connect_db()
        cursor = conn.cursor()

        cursor.execute(
            "SELECT available FROM books WHERE id = ?",
            (book_id,)
        )
        book = cursor.fetchone()

        if not book:
            print("Book not found.")
            conn.close()
            return

        if book[0] == 0:
            print("Book is already issued.")
            conn.close()
            return

        cursor.execute(
            "SELECT id FROM members WHERE id = ?",
            (member_id,)
        )
        member = cursor.fetchone()

        if not member:
            print("Member not found.")
            conn.close()
            return

        issue_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        cursor.execute("""
            INSERT INTO issued_books
            (book_id, member_id, issue_date)
            VALUES (?, ?, ?)
        """, (book_id, member_id, issue_date))

        cursor.execute(
            "UPDATE books SET available = 0 WHERE id = ?",
            (book_id,)
        )

        conn.commit()
        conn.close()

        print("Book issued successfully.")

    except ValueError:
        print("Please enter valid IDs.")


def return_book():
    try:
        book_id = int(input("Enter book ID to return: "))

        conn = connect_db()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT id
            FROM issued_books
            WHERE book_id = ? AND return_date IS NULL
        """, (book_id,))

        issued = cursor.fetchone()

        if not issued:
            print("This book is not currently issued.")
            conn.close()
            return

        return_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        cursor.execute("""
            UPDATE issued_books
            SET return_date = ?
            WHERE id = ?
        """, (return_date, issued[0]))

        cursor.execute(
            "UPDATE books SET available = 1 WHERE id = ?",
            (book_id,)
        )

        conn.commit()
        conn.close()

        print("Book returned successfully.")

    except ValueError:
        print("Please enter a valid book ID.")


def view_issued_books():
    conn = connect_db()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            issued_books.id,
            books.title,
            members.name,
            issued_books.issue_date,
            issued_books.return_date
        FROM issued_books
        JOIN books ON issued_books.book_id = books.id
        JOIN members ON issued_books.member_id = members.id
        WHERE issued_books.return_date IS NULL
    """)

    records = cursor.fetchall()
    conn.close()

    if not records:
        print("No books are currently issued.")
        return

    print("\n--- ISSUED BOOKS ---")

    for record in records:
        print(
            f"Record ID: {record[0]} | "
            f"Book: {record[1]} | "
            f"Member: {record[2]} | "
            f"Issue Date: {record[3]}"
        )


# ---------------- MAIN MENU ----------------

def main():
    create_tables()

    while True:
        print("\n================================")
        print("     LIBRARY MANAGEMENT SYSTEM")
        print("================================")
        print("1. Add Book")
        print("2. View Books")
        print("3. Search Book")
        print("4. Delete Book")
        print("5. Add Member")
        print("6. View Members")
        print("7. Issue Book")
        print("8. Return Book")
        print("9. View Issued Books")
        print("0. Exit")
        print("================================")

        choice = input("Enter your choice: ").strip()

        if choice == "1":
            add_book()
        elif choice == "2":
            view_books()
        elif choice == "3":
            search_book()
        elif choice == "4":
            delete_book()
        elif choice == "5":
            add_member()
        elif choice == "6":
            view_members()
        elif choice == "7":
            issue_book()
        elif choice == "8":
            return_book()
        elif choice == "9":
            view_issued_books()
        elif choice == "0":
            print("Thank you for using the Library Management System.")
            break
        else:
            print("Invalid choice. Please try again.")


if __name__ == "__main__":
    main()