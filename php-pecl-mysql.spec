#
# Conditional build:
%bcond_without	tests		# build without tests
%bcond_without	mysqlnd		# without mysqlnd support in mysql related extensions

%define		php_name	php%{?php_suffix}
%define		modname	mysql
Summary:	MySQL database module for PHP
Summary(pl.UTF-8):	Moduł bazy danych MySQL dla PHP
Summary(pt_BR.UTF-8):	Um módulo para aplicações PHP que usam bancos de dados MySQL
Name:		%{php_name}-pecl-%{modname}
Version:	1.0
Release:	1
License:	PHP 3.01
Group:		Development/Languages/PHP
Source0:	http://git.php.net/?p=pecl/database/mysql.git;a=snapshot;h=617e5103743d07435fdfe5cbbe6ad310e610c4b9;sf=tgz;/php-pecl-%{modname}-%{version}.tar.gz
# Source0-md5:	f010c5f2d56727196ec93991dd42261e
URL:		http://php.net/manual/en/book.mysql.php
%{?with_tests:BuildRequires:    %{php_name}-cli}
BuildRequires:	%{php_name}-devel >= 4:7.0.0
BuildRequires:	rpmbuild(macros) >= 1.666
%if %{with tests}
BuildRequires:	%{php_name}-cli
BuildRequires:	%{php_name}-pcre
%{?with_mysqlnd:BuildRequires:	%{php_name}-mysqlnd}
%endif
%{?requires_php_extension}
Provides:	php(mysql) = %{version}
BuildRoot:	%{tmpdir}/%{name}-%{version}-root-%(id -u -n)

%description
This is a dynamic shared object (DSO) for PHP that will add MySQL
database support.

This extension provides the mysql family of functions that were
provided with PHP 3-5. These functions have been superseded by MySQLi
and PDO_MySQL, which continue to be bundled with PHP 7.

You are strongly encouraged to port your code to use either MySQLi or
PDO_MySQL, as this extension is not maintained and is available for
historical reasons only.

%prep
%setup -qc
mv %{modname}-*/* .

%build
phpize
%configure \
	--with-mysql=shared,%{!?with_mysqlnd:/usr}%{?with_mysqlnd:mysqlnd} \
	--with-mysql-sock=/var/lib/mysql/mysql.sock \
	--with-zlib-dir=shared,/usr \

%{__make}

%if %{with tests}
# simple module load test
%{__php} -n -q \
	-d extension_dir=modules \
%if %{with mysqlnd}
	-d extension=%{php_extensiondir}/mysqlnd.so \
%endif
	-d extension=%{modname}.so \
	-m > modules.log
grep %{modname} modules.log

export NO_INTERACTION=1 REPORT_EXIT_STATUS=1 MALLOC_CHECK_=2
%{__make} test \
	PHP_EXECUTABLE=%{__php} \
	PHP_TEST_SHARED_SYSTEM_EXTENSIONS="%{?with_mysqlnd:mysqlnd}" \
%endif

%install
rm -rf $RPM_BUILD_ROOT
%{__make} install \
	EXTENSION_DIR=%{php_extensiondir} \
	INSTALL_ROOT=$RPM_BUILD_ROOT

install -d $RPM_BUILD_ROOT%{php_sysconfdir}/conf.d
cat <<'EOF' > $RPM_BUILD_ROOT%{php_sysconfdir}/conf.d/%{modname}.ini
; Enable %{modname} extension module
extension=%{modname}.so
EOF

%clean
rm -rf $RPM_BUILD_ROOT

%post
%php_webserver_restart

%postun
if [ "$1" = 0 ]; then
	%php_webserver_restart
fi

%files
%defattr(644,root,root,755)
%doc README.md CREDITS LICENSE
%config(noreplace) %verify(not md5 mtime size) %{php_sysconfdir}/conf.d/%{modname}.ini
%attr(755,root,root) %{php_extensiondir}/%{modname}.so
