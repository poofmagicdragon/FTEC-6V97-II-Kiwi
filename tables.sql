-- CREATE DATABASE kiwilocal2;
-- use kiwilocal2;

-- Drop tables in reverse dependency order
-- DROP TABLE IF EXISTS `transaction`;
-- DROP TABLE IF EXISTS `investment`;
-- DROP TABLE IF EXISTS `portfolio`;
-- DROP TABLE IF EXISTS `security`;
-- DROP TABLE IF EXISTS `user`;

-- -- Create USER table
-- CREATE TABLE `user` (
--     username VARCHAR(30) PRIMARY KEY,
--     password VARCHAR(30) NOT NULL,
--     firstname VARCHAR(30) NOT NULL,
--     lastname VARCHAR(30) NOT NULL,
--     balance FLOAT NOT NULL
-- );

-- -- Create SECURITY table
-- CREATE TABLE `security` (
--     ticker VARCHAR(10) PRIMARY KEY,
--     issuer VARCHAR(100) NOT NULL,
--     price FLOAT NOT NULL
-- );

-- -- Create PORTFOLIO table
-- CREATE TABLE `portfolio` (
--     id INT AUTO_INCREMENT PRIMARY KEY,
--     name VARCHAR(30) NOT NULL,
--     description VARCHAR(500),
--     owner VARCHAR(30) NOT NULL,

--     CONSTRAINT fk_portfolio_user
--         FOREIGN KEY (owner) REFERENCES user(username)
--         ON DELETE CASCADE
-- );

-- -- Create INVESTMENT table
-- CREATE TABLE `investment` (
--     id INT AUTO_INCREMENT PRIMARY KEY,
--     quantity INT NOT NULL,
--     ticker VARCHAR(10) NOT NULL,
--     portfolio_id INT NOT NULL,

--     CONSTRAINT fk_investment_security
--         FOREIGN KEY (ticker) REFERENCES security(ticker)
--         ON DELETE CASCADE,

--     CONSTRAINT fk_investment_portfolio
--         FOREIGN KEY (portfolio_id) REFERENCES portfolio(id)
--         ON DELETE CASCADE
-- );

-- -- Create TRANSACTION table
-- CREATE TABLE `transaction` (
--     transaction_id INT AUTO_INCREMENT PRIMARY KEY,
--     username VARCHAR(30) NOT NULL,
--     portfolio_id INT NOT NULL,
--     ticker VARCHAR(30) NOT NULL,
--     transaction_type VARCHAR(10) NOT NULL,
--     quantity INT NOT NULL,
--     price FLOAT NOT NULL,
--     date_time DATETIME NOT NULL,

--     CONSTRAINT fk_transaction_user
--         FOREIGN KEY (username) REFERENCES user(username)
--         ON DELETE CASCADE,

--     CONSTRAINT fk_transaction_portfolio
--         FOREIGN KEY (portfolio_id) REFERENCES portfolio(id)
--         ON DELETE CASCADE,

--     CONSTRAINT fk_transaction_security
--         FOREIGN KEY (ticker) REFERENCES security(ticker)
--         ON DELETE CASCADE
-- );
-- use kiwilocal2;
-- INSERT INTO security VALUES ('AAPL', 'Apple inc', 100);
-- INSERT INTO transaction (username, portfolio_id, ticker, transaction_type, quantity, price, date_time) VALUE ('mt', '1', 'AAPL', 'BUY', '1',100, '2022-01-01');

-- ALTER TABLE transaction DROP FOREIGN KEY fk_transaction_security;
use kiwilocal2;

CREATE TABLE portfoliosecurity (
    id INT AUTO_INCREMENT PRIMARY KEY,
    portfolio_id INT NOT NULL,
    username VARCHAR(30) NOT NULL,
    role VARCHAR(30) NOT NULL,

    CONSTRAINT fk_portfoliosecurity_portfolio
        FOREIGN KEY (portfolio_id) REFERENCES portfolio(id)
        ON DELETE CASCADE,

    CONSTRAINT fk_portfoliosecurity_user
        FOREIGN KEY (username) REFERENCES user(username)
        ON DELETE CASCADE
);
