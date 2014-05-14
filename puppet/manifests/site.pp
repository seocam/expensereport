# Use this file to add stuff required only on the development
#   environement. 
# Example: database creation and configuration (usually)
#
# Anything required on both (development and production)
#   environments should be placed on the expensereport
#   module instead of here.

include expensereport


### MySQL example:
#
# class { 'mysql::server':
#   override_options => {
#     mysqld => {
#       "default-storage-engine" => 'InnoDB',
#     },
#   },
# }
#
# mysql::db { 'expensereport':
#   user     => 'expensereport',
#   password => 'expensereport',
#   host     => 'localhost',
#   grant    => ['ALL'],
#   charset  => 'utf8',
# }


### PostgreSQL example:
#
# include postgresql::server
#
# postgresql::server::db { 'expensereport':
#   user     => 'expensereport',
#   password => 'expensereport',
# }
