CREATE SCHEMA IF NOT EXISTS `Library` DEFAULT CHARACTER SET latin1;

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
SET AUTOCOMMIT = 0;
START TRANSACTION;
SET time_zone = "+00:00";

USE `Library`;

DROP TABLE IF EXISTS `Reserve`; -- relationship
DROP TABLE IF EXISTS `Borrow`; -- relationship
DROP TABLE IF EXISTS `Payment`; -- entity
DROP TABLE IF EXISTS `Fine`; -- entity
DROP TABLE IF EXISTS `Admin`; -- entity
DROP TABLE IF EXISTS `Book`; -- entity
DROP TABLE IF EXISTS `User`; -- entity

-- make username primary key because need username to be unique
-- userid is already unique by default
CREATE TABLE `User` (
  `userID` bigint(20) UNSIGNED NOT NULL AUTO_INCREMENT,
  `userName` varchar(50) UNIQUE NOT NULL,
  `userPassword` varchar(256) NOT NULL,
  PRIMARY KEY (`userID`)
);

-- bookID depends on book database--
CREATE TABLE `Book` (
	`bookID` bigint(20) NOT NULL,
    `title` varchar(256) NOT NULL DEFAULT "",
    `ISBN` varchar(50) UNIQUE NOT NULL DEFAULT "",
    `status` tinyint(3) NOT NULL DEFAULT 0,
    PRIMARY KEY (`bookID`)
);

CREATE TABLE `Admin`(
	`adminID` bigint(20) NOT NULL AUTO_INCREMENT,
    `adminUsername` varchar(50) NOT NULL,
    `adminPassword` varchar(256) NOT NULL,
    PRIMARY KEY (`adminID`)
);

CREATE TABLE `Fine`(
    `amount` int(20) NOT NULL DEFAULT 0,
    `userID` bigint(20) UNSIGNED NOT NULL,
    PRIMARY KEY (`userID`),
    FOREIGN KEY (`userID`) REFERENCES User(`userID`),
	CHECK (amount >= 0)
);

CREATE TABLE `Payment`(
	`paymentID` bigint(20) NOT NULL AUTO_INCREMENT,
    `amount` bigint(20) NOT NULL DEFAULT 0,
    `datetime` DATETIME,
    `userID` bigint(20) UNSIGNED NOT NULL,
    PRIMARY KEY (`paymentID`),
    FOREIGN KEY (`userID`) REFERENCES User(`userID`),
    CHECK (amount > 0)
);

CREATE TABLE `Borrow`(
	`borrowUserID` bigint(20) UNSIGNED NOT NULL,
    `bookID` bigint(20) NOT NULL,
    `borrowDate` DATETIME NOT NULL,
    `dueDate` DATETIME NOT NULL, --  for extension
    PRIMARY KEY (`borrowUserID`,`bookID`), -- added bookID to ensure user can borrow more than 1 book
    FOREIGN KEY (`borrowUserID`) REFERENCES User(`userID`),
    FOREIGN KEY (`bookID`) REFERENCES Book(`bookID`)
);

CREATE TABLE `Reserve`(
	`reserveUserID` bigint(20) UNSIGNED NOT NULL,
    `bookID` bigint(20) NOT NULL,
    `reserveDate` DATETIME NOT NULL,
    PRIMARY KEY (`bookID`), -- because each book can only be reserved once.
    FOREIGN KEY (`reserveUserID`) REFERENCES User(`userID`),
    FOREIGN KEY (`bookID`) REFERENCES Book(`bookID`)
);

-- --  -- CONSTRAINTS -- -- --
-- Borrow up to 4 books constraint. no more constraint on reserving
-- returnDate = NULL is to filter out the past borrows, only want current borrows
DELIMITER $$
DROP TRIGGER IF EXISTS check_borrow_count $$
CREATE TRIGGER check_borrow_count BEFORE INSERT ON `Borrow`
  FOR EACH ROW BEGIN
    DECLARE numbooks int DEFAULT 0;
    SELECT COUNT(*) INTO numbooks FROM `Borrow` WHERE borrowUserID=NEW.borrowUserID;
    if numbooks=4 THEN
      SET NEW.bookID = NULL;
    END IF;
  END;
$$
DELIMITER ;
