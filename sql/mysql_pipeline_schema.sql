CREATE TABLE IF NOT EXISTS `entities` (
  `id` varchar(32) CHARACTER SET utf8 COLLATE utf8_bin NOT NULL,
  `symbol` varchar(20) CHARACTER SET utf8 COLLATE utf8_bin NOT NULL,
  `type` varchar(15) CHARACTER SET utf8 COLLATE utf8_bin NOT NULL,
  `updated` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `hash` varchar(32) CHARACTER SET utf8 COLLATE utf8_bin NOT NULL,
  `body` longtext CHARACTER SET utf8 COLLATE utf8_unicode_ci NOT NULL,
  PRIMARY KEY (`id`),
  KEY `updated` (`updated`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8_unicode_ci;

DELIMITER $$
CREATE TRIGGER dataToQueueWhenInsert AFTER INSERT ON entities
  FOR EACH ROW BEGIN
    SET @ret=gman_do_background('spiderMysqlQueue', NEW.id); 
  END$$
DELIMITER ;


DELIMITER $$
CREATE TRIGGER dataToQueueWhenUpdate AFTER UPDATE ON entities
  FOR EACH ROW BEGIN
    SET @ret=gman_do_background('spiderMysqlQueue', NEW.id); 
  END$$
DELIMITER ;