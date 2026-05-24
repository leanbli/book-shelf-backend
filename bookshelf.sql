-- Пользователи (расширенная версия)
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL,
    first_name VARCHAR(50),
    last_name VARCHAR(50),
    avatar TEXT,
    role VARCHAR(20) DEFAULT 'user',
    is_active BOOLEAN DEFAULT TRUE,
    last_login TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Жанры книг
CREATE TABLE IF NOT EXISTS genres (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) UNIQUE NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
-- Издательства (с уникальным ограничением)
CREATE TABLE IF NOT EXISTS publishers (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) UNIQUE NOT NULL,  -- ДОБАВЛЕНО UNIQUE
    city VARCHAR(100),
    country VARCHAR(100),
    founded_year INTEGER CHECK (founded_year > 1400 AND founded_year <= EXTRACT(YEAR FROM CURRENT_DATE)),
    website VARCHAR(200),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Книги (расширенная версия)
CREATE TABLE IF NOT EXISTS books (
    id SERIAL PRIMARY KEY,
    title VARCHAR(200) NOT NULL,
    author VARCHAR(100),
    isbn VARCHAR(13) UNIQUE,
    pages INTEGER CHECK (pages > 0),
    year INTEGER CHECK (year > 1400 AND year <= EXTRACT(YEAR FROM CURRENT_DATE)),
    language VARCHAR(50) DEFAULT 'Русский',
    price DECIMAL(10, 2) CHECK (price >= 0),
    quantity INTEGER DEFAULT 1 CHECK (quantity >= 0),
    description TEXT,
    cover_image TEXT,
    publisher_id INTEGER REFERENCES publishers(id) ON DELETE SET NULL,
    user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    rating_avg DECIMAL(3,2) DEFAULT 0 CHECK (rating_avg >= 0 AND rating_avg <= 5),
    views_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Связь книг с жанрами (многие ко многим)
CREATE TABLE IF NOT EXISTS book_genres (
    book_id INTEGER REFERENCES books(id) ON DELETE CASCADE,
    genre_id INTEGER REFERENCES genres(id) ON DELETE CASCADE,
    PRIMARY KEY (book_id, genre_id)
);

-- Отзывы на книги
CREATE TABLE IF NOT EXISTS reviews (
    id SERIAL PRIMARY KEY,
    book_id INTEGER REFERENCES books(id) ON DELETE CASCADE,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    rating INTEGER NOT NULL CHECK (rating >= 1 AND rating <= 5),
    comment TEXT,
    is_edited BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(book_id, user_id) -- Один пользователь - один отзыв на книгу
);

-- Читательские списки
CREATE TABLE IF NOT EXISTS reading_lists (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    is_private BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Книги в читательских списках
CREATE TABLE IF NOT EXISTS reading_list_books (
    list_id INTEGER REFERENCES reading_lists(id) ON DELETE CASCADE,
    book_id INTEGER REFERENCES books(id) ON DELETE CASCADE,
    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    notes TEXT,
    PRIMARY KEY (list_id, book_id)
);

-- История операций с книгами (аудит)
CREATE TABLE IF NOT EXISTS book_history (
    id SERIAL PRIMARY KEY,
    book_id INTEGER REFERENCES books(id) ON DELETE SET NULL,
    user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    action VARCHAR(30) NOT NULL, -- CREATE, UPDATE, DELETE, VIEW, BORROW, RETURN
    old_data JSONB,
    new_data JSONB,
    ip_address INET,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Закладки пользователей
CREATE TABLE IF NOT EXISTS bookmarks (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    book_id INTEGER REFERENCES books(id) ON DELETE CASCADE,
    page_number INTEGER DEFAULT 1,
    note TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, book_id)
);

-- Индексы для книг
CREATE INDEX IF NOT EXISTS idx_books_title ON books(title);
CREATE INDEX IF NOT EXISTS idx_books_author ON books(author);
CREATE INDEX IF NOT EXISTS idx_books_year ON books(year);
CREATE INDEX IF NOT EXISTS idx_books_price ON books(price);
CREATE INDEX IF NOT EXISTS idx_books_rating ON books(rating_avg DESC);
CREATE INDEX IF NOT EXISTS idx_books_language ON books(language);
CREATE INDEX IF NOT EXISTS idx_books_publisher ON books(publisher_id);
CREATE INDEX IF NOT EXISTS idx_books_user ON books(user_id);
CREATE INDEX IF NOT EXISTS idx_books_created ON books(created_at DESC);

-- Индексы для поиска по тексту (полнотекстовый поиск)
CREATE INDEX IF NOT EXISTS idx_books_search ON books USING GIN(to_tsvector('russian', title || ' ' || COALESCE(author, '') || ' ' || COALESCE(description, '')));

-- Индексы для отзывов
CREATE INDEX IF NOT EXISTS idx_reviews_book_id ON reviews(book_id);
CREATE INDEX IF NOT EXISTS idx_reviews_user_id ON reviews(user_id);
CREATE INDEX IF NOT EXISTS idx_reviews_rating ON reviews(rating);
CREATE INDEX IF NOT EXISTS idx_reviews_created ON reviews(created_at DESC);

-- Индексы для пользователей
CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_role ON users(role);
CREATE INDEX IF NOT EXISTS idx_users_active ON users(is_active);

-- Индексы для списков чтения
CREATE INDEX IF NOT EXISTS idx_lists_user ON reading_lists(user_id);
CREATE INDEX IF NOT EXISTS idx_list_books_list ON reading_list_books(list_id);
CREATE INDEX IF NOT EXISTS idx_list_books_book ON reading_list_books(book_id);

-- Индексы для истории
CREATE INDEX IF NOT EXISTS idx_history_book ON book_history(book_id);
CREATE INDEX IF NOT EXISTS idx_history_user ON book_history(user_id);
CREATE INDEX IF NOT EXISTS idx_history_action ON book_history(action);
CREATE INDEX IF NOT EXISTS idx_history_created ON book_history(created_at DESC);

-- Функция обновления updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Триггеры для автоматического обновления updated_at
CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_books_updated_at BEFORE UPDATE ON books
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_reviews_updated_at BEFORE UPDATE ON reviews
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_lists_updated_at BEFORE UPDATE ON reading_lists
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Функция автоматического обновления среднего рейтинга книги
CREATE OR REPLACE FUNCTION update_book_rating()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE books 
    SET rating_avg = (
        SELECT COALESCE(AVG(rating), 0)
        FROM reviews 
        WHERE book_id = NEW.book_id
    )
    WHERE id = NEW.book_id;
    RETURN NEW;
END;
$$ language 'plpgsql';


-- Добавляем пользователей
INSERT INTO users (username, email, password, first_name, last_name, role) VALUES
('admin', 'admin@bookshelf.com', 'admin123', 'Admin', 'User', 'admin'),
('john_doe', 'john@example.com', 'pass123', 'John', 'Doe', 'user'),
('jane_smith', 'jane@example.com', 'pass456', 'Jane', 'Smith', 'user')
ON CONFLICT (username) DO NOTHING;

-- Добавляем жанры
INSERT INTO genres (name, description) VALUES
('Роман', 'Художественное повествование, обычно с сложным сюжетом'),
('Фантастика', 'Научная фантастика и фэнтези, нереальные миры'),
('Детектив', 'Захватывающие расследования и тайны'),
('Классика', 'Мировая классическая литература'),
('Поэзия', 'Стихотворные произведения'),
('Наука', 'Научно-популярная литература'),
('Приключения', 'Увлекательные путешествия и приключения'),
('История', 'Исторические произведения и исследования')
ON CONFLICT (name) DO NOTHING;

-- Добавляем издательства (без ON CONFLICT, используем INSERT ... WHERE NOT EXISTS)
INSERT INTO publishers (name, city, country, founded_year, website)
SELECT * FROM (VALUES
    ('Эксмо', 'Москва', 'Россия', 1991, 'https://eksmo.ru'),
    ('АСТ', 'Москва', 'Россия', 1990, 'https://ast.ru'),
    ('Питер', 'Санкт-Петербург', 'Россия', 1991, 'https://piter.com'),
    ('Азбука-Аттикус', 'Санкт-Петербург', 'Россия', 2008, 'https://azbooka.ru'),
    ('Манн, Иванов и Фербер', 'Москва', 'Россия', 2005, 'https://mif.ru')
) AS v(name, city, country, founded_year, website)
WHERE NOT EXISTS (SELECT 1 FROM publishers WHERE publishers.name = v.name);

-- Добавляем книги (с проверкой существования издательств)
INSERT INTO books (title, author, isbn, pages, year, language, price, quantity, description, publisher_id, user_id)
SELECT * FROM (VALUES
    ('Война и мир', 'Лев Толстой', '9785170901313', 1300, 1869, 'Русский', 500.00, 5, 'Роман-эпопея о судьбах русских семей на фоне наполеоновских войн', (SELECT id FROM publishers WHERE name = 'АСТ'), 1),
    ('1984', 'Джордж Оруэлл', '9785170891324', 320, 1949, 'Русский', 350.50, 3, 'Антиутопия о тоталитарном режиме и потере свободы', (SELECT id FROM publishers WHERE name = 'Эксмо'), 1),
    ('Мастер и Маргарита', 'Михаил Булгаков', '9785170902389', 416, 1967, 'Русский', 450.00, 4, 'Философский роман о добре и зле, любви и предательстве', (SELECT id FROM publishers WHERE name = 'АСТ'), 1),
    ('Преступление и наказание', 'Фёдор Достоевский', '9785170912340', 672, 1866, 'Русский', 480.00, 2, 'Роман о моральных дилеммах и поиске истины', (SELECT id FROM publishers WHERE name = 'АСТ'), 1),
    ('Гарри Поттер и философский камень', 'Джоан Роулинг', '9785389048531', 432, 1997, 'Русский', 650.00, 7, 'Первая книга о юном волшебнике', (SELECT id FROM publishers WHERE name = 'Питер'), 2),
    ('Маленький принц', 'Антуан де Сент-Экзюпери', '9785170905311', 96, 1943, 'Русский', 350.00, 6, 'Философская сказка о дружбе и любви', (SELECT id FROM publishers WHERE name = 'Эксмо'), 2),
    ('Три товарища', 'Эрих Мария Ремарк', '9785170906332', 448, 1936, 'Русский', 420.00, 3, 'Роман о дружбе и любви в послевоенной Германии', (SELECT id FROM publishers WHERE name = 'Эксмо'), 3),
    ('Убить пересмешника', 'Харпер Ли', '9785170892345', 384, 1960, 'Русский', 380.00, 4, 'Роман о расовой несправедливости и морали', (SELECT id FROM publishers WHERE name = 'Азбука-Аттикус'), 1),
    ('Сто лет одиночества', 'Габриэль Гарсиа Маркес', '9785170907322', 448, 1967, 'Русский', 550.00, 3, 'Магический реализм о семье Буэндиа', (SELECT id FROM publishers WHERE name = 'Азбука-Аттикус'), 2),
    ('Анна Каренина', 'Лев Толстой', '9785170913357', 864, 1877, 'Русский', 600.00, 2, 'Трагическая история любви', (SELECT id FROM publishers WHERE name = 'АСТ'), 1)
) AS v(title, author, isbn, pages, year, language, price, quantity, description, publisher_id, user_id)
WHERE NOT EXISTS (SELECT 1 FROM books WHERE books.isbn = v.isbn);

-- Связываем книги с жанрами
INSERT INTO book_genres (book_id, genre_id) VALUES
(71, 1), (71, 4),  -- Война и мир: Роман, Классика
(72, 2), (72, 4),  -- 1984: Фантастика, Классика
(73, 1), (73, 4),  -- Мастер и Маргарита: Роман, Классика
(74, 1), (74, 4),  -- Преступление и наказание: Роман, Классика
(75, 2), (75, 7),  -- Гарри Поттер: Фантастика, Приключения
(76, 4), (76, 6),  -- Маленький принц: Классика, Поэзия
(77, 1), (77, 4),  -- Три товарища: Роман, Классика
(78, 1), (78, 4),  -- Убить пересмешника: Роман, Классика
(79, 1), (79, 4),  -- Сто лет одиночества: Роман, Классика
(80, 1), (80, 4);  -- Анна Каренина: Роман, Классика

-- Добавляем отзывы
INSERT INTO reviews (book_id, user_id, rating, comment) VALUES
(71, 2, 5, 'Величайшее произведение! Обязательно к прочтению.'),
(71, 3, 4, 'Очень объемно, но интересно.'),
(72, 2, 5, 'Актуально и в наше время. Пугающе реалистично.'),
(73, 1, 5, 'Шедевр Булгакова. Читается на одном дыхании.'),
(75, 1, 4, 'Отличная книга для детей и взрослых.')
ON CONFLICT (book_id, user_id) DO NOTHING;

--Добавляем читательские списки
INSERT INTO reading_lists (user_id, name, description, is_private) VALUES
(2, 'Мои любимые книги', 'Книги, которые произвели на меня впечатление', FALSE),
(2, 'Хочу прочитать', 'Список книг, которые планирую прочитать', FALSE),
(3, 'Классика', 'Лучшие классические произведения', FALSE);
SELECT id, title FROM books;

--Добавляем книги в списки
INSERT INTO reading_list_books (list_id, book_id, notes) VALUES
(1, 71, 'Прочитал за месяц, очень понравилось'),
(1, 72, 'Страшно актуально'),
(1, 73, 'Гениально!'),
(2, 75, 'Друг посоветовал'),
(2, 79, 'Хочу познакомиться с магическим реализмом'),
(3, 71, 'Русская классика'),
(3, 74, 'Достоевский - гений');