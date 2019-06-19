#
# Conditional build:
%bcond_without	tests		# build without tests
%bcond_without	mysqlnd		# without mysqlnd support in mysql related extensions

%define		rel		1
%define		commit	d7643af
%define		php_name	php%{?php_suffix}
%define		modname	mysql
Summary:	Legacy MySQL extension
Summary(pl.UTF-8):	Moduł bazy danych MySQL dla PHP
Summary(pt_BR.UTF-8):	Um módulo para aplicações PHP que usam bancos de dados MySQL
Name:		%{php_name}-pecl-%{modname}
Version:	1.0.0
Release:	4.%{rel}.%{commit}
License:	PHP 3.01
Group:		Development/Languages/PHP
Source0:	https://git.php.net/?p=pecl/database/mysql.git;a=snapshot;h=%{commit};sf=tgz;/php-pecl-%{modname}-%{version}-%{commit}.tar.gz
# Source0-md5:	cd885ae5b99f265eb08d6a087ed2b549
URL:		https://secure.php.net/manual/en/book.mysql.php
%{?with_tests:BuildRequires:    %{php_name}-cli}
BuildRequires:	%{php_name}-devel >= 4:7.0.0
BuildRequires:	rpmbuild(macros) >= 1.666
%if %{with tests}
BuildRequires:	%{php_name}-cli
%{?with_mysqlnd:BuildRequires:	%{php_name}-mysqlnd}
BuildRequires:	%{php_name}-pcre
%endif
%{?with_mysqlnd:Requires:	%{php_name}-mysqlnd}
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
