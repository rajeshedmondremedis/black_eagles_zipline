import pymysql

pymysql.install_as_MySQLdb()

# Backward compatibility for local development environments with MariaDB < 10.11 / < 10.5
try:
    from django.db.backends.mysql.base import DatabaseWrapper as MySQLDatabaseWrapper
    from django.db.backends.mysql.features import DatabaseFeatures as MySQLDatabaseFeatures

    # 1. Allow version check to pass on legacy local MariaDB
    _original_check_version = MySQLDatabaseWrapper.check_database_version_supported

    def _safe_check_database_version_supported(self):
        try:
            return _original_check_version(self)
        except Exception:
            pass

    MySQLDatabaseWrapper.check_database_version_supported = _safe_check_database_version_supported

    # 2. MariaDB < 10.5 does not support INSERT ... RETURNING syntax
    MySQLDatabaseFeatures.can_return_columns_from_insert = property(
        lambda self: self.connection.mysql_is_mariadb and self.connection.mysql_version >= (10, 5, 0)
    )
except Exception:
    pass
