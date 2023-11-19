DROP TABLE IF EXISTS questions;
DROP TABLE IF EXISTS reviews;
DROP TABLE IF EXISTS sizes;
DROP TABLE IF EXISTS material_filler;
DROP TABLE IF EXISTS lining_material;
DROP TABLE IF EXISTS material_filling;
DROP TABLE IF EXISTS materials;
DROP TABLE IF EXISTS products;
DROP TABLE IF EXISTS brands;

CREATE TABLE IF NOT EXISTS brands (
    brand_id SMALLINT PRIMARY KEY,
    brand_name VARCHAR(32) UNIQUE
);

CREATE TABLE IF NOT EXISTS products (
    product_id VARCHAR(16) PRIMARY KEY,
    sex VARCHAR(8),
    brand_id SMALLINT,
    model VARCHAR(64),
    color VARCHAR(16),
    price NUMERIC(8, 2),
    old_price NUMERIC(8, 2),
    season_wear VARCHAR(16),
    print VARCHAR(64),
    guarantee_period VARCHAR(16),
    production_country VARCHAR(32),
    clothes_clasp VARCHAR(32),
    average_rating NUMERIC(2, 1),
    FOREIGN KEY (brand_id) REFERENCES brands (brand_id),
    CONSTRAINT sex_check CHECK(sex IN ('men', 'women', 'girls', 'boys', 'unisex'))
    );

CREATE TABLE IF NOT EXISTS materials (
    material_id SMALLINT PRIMARY KEY,
    material_name VARCHAR(32) UNIQUE
);

CREATE TABLE IF NOT EXISTS material_filling (
    product_id VARCHAR(16),
    material_id SMALLINT,
    percentage_in SMALLINT,
    FOREIGN KEY (product_id) REFERENCES products (product_id),
    FOREIGN KEY (material_id) REFERENCES materials (material_id)
    );

CREATE TABLE IF NOT EXISTS lining_material (
    product_id VARCHAR(16),
    material_id SMALLINT,
    percentage_in SMALLINT,
    FOREIGN KEY (product_id) REFERENCES products (product_id),
    FOREIGN KEY (material_id) REFERENCES materials (material_id)
    );

CREATE TABLE IF NOT EXISTS material_filler (
    product_id VARCHAR(16),
    material_id SMALLINT,
    percentage_in SMALLINT,
    FOREIGN KEY (product_id) REFERENCES products (product_id),
    FOREIGN KEY (material_id) REFERENCES materials (material_id)
    );

CREATE TABLE IF NOT EXISTS sizes (
    product_id VARCHAR(16),
    rus_size VARCHAR(8),
    brand_size VARCHAR(8),
    stock_quantity SMALLINT,
    FOREIGN KEY (product_id) REFERENCES products (product_id)
);

CREATE TABLE IF NOT EXISTS reviews (
    review_id SERIAL PRIMARY KEY,
    product_id VARCHAR(16),
    uuid VARCHAR(64),
    text_review VARCHAR(512),
    fittings VARCHAR(128),
    created_time TIMESTAMP WITH TIME ZONE,
    rating SMALLINT,
    FOREIGN KEY (product_id) REFERENCES products (product_id)
);

CREATE TABLE IF NOT EXISTS questions (
    question_id SERIAL PRIMARY KEY,
    product_id VARCHAR(16),
    username VARCHAR(16),
    text_question VARCHAR(512),
    answer VARCHAR(512),
    created_time TIMESTAMP WITH TIME ZONE,
    FOREIGN KEY (product_id) REFERENCES products (product_id)
);
