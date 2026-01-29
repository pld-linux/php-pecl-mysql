#
# Conditional build:
%bcond_without	tests		# build without tests
%bcond_without	mysqlnd		# without mysqlnd support in mysql related extensions

%define		rel		9
%define		commit	ca514c4
%define		php_name	php%{?php_suffix}
%define		modname	mysql
Summary:	Legacy MySQL extension
Summary(pl.UTF-8):	Moduł bazy danych MySQL dla PHP
Summary(pt_BR.UTF-8):	Um módulo para aplicações PHP que usam bancos de dados MySQL
Name:		%{php_name}-pecl-%{modname}
Version:	1.0.0
Release:	%{rel}.%{commit}
License:	PHP 3.01
Group:		Development/Languages/PHP
# https://github.com/php/pecl-database-mysql
Source0:	https://github.com/php/pecl-database-mysql/archive/%{commit}/php-pecl-%{modname}-%{version}-%{commit}.tar.gz
# Source0-md5:	352114d54e0889d999577f9db8c06a74
Patch0:		revert-deprecate-ext-mysql.patch
Patch1:		build.patch
URL:		https://secure.php.net/manual/en/book.mysql.php
%{?with_tests:BuildRequires:    %{php_name}-cli}
BuildRequires:	%{php_name}-devel >= 4:7.0.0
%{?with_mysqlnd:BuildRequires:	%{php_name}-mysqlnd}
BuildRequires:	rpmbuild(macros) >= 1.666
%if %{with tests}
BuildRequires:	%{php_name}-cli
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
%setup -qc -n %{name}-%{version}-%{commit}
mv pecl-database-%{modname}-*/* .
%patch -P0 -p1
%patch -P1 -p1

cat <<'EOF' > run-tests.sh
#!/bin/sh
export NO_INTERACTION=1 REPORT_EXIT_STATUS=1 MALLOC_CHECK_=2
exec %{__make} test \
	PHP_EXECUTABLE=%{__php} \
	PHP_TEST_SHARED_SYSTEM_EXTENSIONS="%{?with_mysqlnd:mysqlnd}" \
	RUN_TESTS_SETTINGS="-q $*"
EOF
chmod +x run-tests.sh

xfail() {
	local t=$1
	test -f $t
	cat >> $t <<-EOF

	--XFAIL--
	Skip
	EOF
}

while read line; do
	t=${line##*\[}; t=${t%\]}
	xfail $t
done << 'EOF'
mysql_escape_string() [tests/mysql_escape_string.phpt]
mysql_get_client_info() [tests/mysql_get_client_info.phpt]
ReflectionFunction to check API [tests/mysql_reflection_functions.phpt]
EOF

%build
phpize
%configure \
	--with-mysql=shared,%{!?with_mysqlnd:/usr}%{?with_mysqlnd:mysqlnd} \
	--with-mysql-sock=/var/lib/mysql/mysql.sock \
	--with-zlib-dir=shared,/usr \

%{__make}

# simple module load test
%{__php} -n -q -d display_errors=off \
	-d extension_dir=modules \
%if %{with mysqlnd}
	-d extension=%{php_extensiondir}/mysqlnd.so \
%endif
	-d extension=%{modname}.so \
	-m > modules.log
grep "^%{modname}$" modules.log

%if %{with tests}
./run-tests.sh --show-diff
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
