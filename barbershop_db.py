import psycopg2
from config import DB_USER, DB_HOST, DB_NAME, DB_PASSWORD, DB_PORT


class DataBase:
    def __init__(self):
        self.conn = psycopg2.connect(
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            host=DB_HOST,
            port=DB_PORT
        )
        self.cursor = self.conn.cursor()

        self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS regions (
                region_id SERIAL PRIMARY KEY,
                region_name VARCHAR(100) NOT NULL
                );
        """)

        self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS barbers (
                barber_id SERIAL PRIMARY KEY,
                name VARCHAR(100) NOT NULL,
                telegram_link TEXT,
                phone VARCHAR(20),
                gender CHAR(1),
                bio TEXT,
                region_id INT,
                latitude DECIMAL(10, 8),
                longitude DECIMAL(11, 8),
                CONSTRAINT fk_region FOREIGN KEY (region_id) REFERENCES regions(region_id) ON DELETE CASCADE);
        """)

        self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS photos (
                photo_id SERIAL PRIMARY KEY,
                barber_id INT NOT NULL,
                photo_url TEXT NOT NULL,
                FOREIGN KEY (barber_id) REFERENCES barbers(barber_id) ON DELETE CASCADE);
        """)

        self.conn.commit()

    def create_barber(self, name, telegram_link, phone, gender, bio, region_id, latitude, longitude):
        self.cursor.execute("""
        INSERT INTO barbers (name, links, phone, gender, bio, region_id, latitude, longitude)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)""", (name, telegram_link, phone, gender, bio, region_id, latitude, longitude))
        self.conn.commit()

    def create_region(self, region_name):
        self.cursor.execute("""
        INSERT INTO regions (region_name)
        VALUES (%s)""", (region_name,))
        self.conn.commit()

    def insert_photo(self, barber_id, photo_url):
        self.cursor.execute("""
        INSERT INTO photos (barber_id, photo_url)
        VALUES (%s, %s)""", (barber_id, photo_url))
        self.conn.commit()

    def get_all_regions(self):
        self.cursor.execute(""" SELECT * from regions """)
        all_regions = dict_fetchall(self.cursor)
        return all_regions

    def get_barbers(self, region_id, gender):
        self.cursor.execute("""
        SELECT barbers.*
        FROM barbers
        JOIN regions ON barbers.region_id = regions.region_id
        WHERE regions.region_id = %s AND barbers.gender = %s;
        """, (region_id, gender))
        barbers = dict_fetchall(self.cursor)
        return barbers

    def get_barber_details(self, barber_id, gender):
        self.cursor.execute("""
        SELECT * from barbers WHERE barber_id = %s AND gender = %s;
        """, (barber_id, gender))
        detail = dict_fetchone(self.cursor)
        return detail

    def get_barber_photos(self, barber_id):
        self.cursor.execute("""
        SELECT * 
        FROM photos
        WHERE barber_id = %s;
        """, (barber_id,))
        barber_photos = dict_fetchall(self.cursor)
        return barber_photos

    def get_regions(self, gender):
        self.cursor.execute("""
        SELECT DISTINCT regions.*
        FROM regions
        JOIN barbers ON regions.region_id = barbers.region_id
        WHERE barbers.gender = %s
        """, (gender,))
        regions = dict_fetchall(self.cursor)
        return regions


def dict_fetchall(cursor):
    columns = [col[0] for col in cursor.description]
    return [
        dict(zip(columns, row))
        for row in cursor.fetchall()
    ]


def dict_fetchone(cursor):
    row = cursor.fetchone()
    if row is None:
        return False
    columns = [col[0] for col in cursor.description]
    return dict(zip(columns, row))
