class expensereport {

  appdeploy::django { 'expensereport':
    user      => 'expensereport',
    directory => '/home/expensereport/expensereport/src',
    proxy_hosts => [
      'expensereport.placeholder',
    ],

  }
}
