mysql -u root -p$MYSQL_ROOT_PASSWORD <<EOF

DROP DATABASE IF EXISTS $MYSQL_DATABASE;
CREATE DATABASE $MYSQL_DATABASE;

exit
EOF