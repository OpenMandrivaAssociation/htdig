%define _disable_ld_as_needed 1
%define _disable_ld_no_undefined 1

%define betanum b6
%define contentdir /var/www

Summary:	A web indexing and searching system for a small domain or intranet
Name:		htdig
Version:	3.2.0
Release:	1
License:	GPL
Group:		Networking/WWW
URL:		https://www.htdig.org/
Source0:	%{name}-%{version}%{betanum}.tar.bz2
Source1:	htdig-dbgen
Source2:	%{name}-rundig-accents.patch
Patch0:		%{name}.patch
Patch1:		%{name}-accents.patch
Patch2:		rundig.emptydb.patch
Patch3:		%{name}-dblmax.patch
Patch4:		%{name}-memcpy.patch
Patch5:		%{name}-localconf.patch
Patch6:		%{name}-rundiginfos.patch
Patch50:	%{name}-enabledebug.patch
Patch85:	htdig-fix-Collection-dot-h.patch
BuildRequires:	flex >= 2.5.4a-13
BuildRequires:	libtool
BuildRequires:	gcc-c++
BuildRequires:	zlib-devel

%description
The ht://Dig system is a complete world wide web indexing and searching system 
for a small domain or intranet. This system is not meant to replace the need 
for powerful internet-wide search systems like Lycos, Infoseek, Webcrawler and 
AltaVista. Instead it is meant to cover the search needs for a single company, 
campus, or even a particular sub section of a web site.

As opposed to some WAIS-based or web-server based search engines, ht://Dig can 
span several web servers at a site. The type of these different web servers 
doesn't matter as long as they understand the HTTP 1.0 protocol.

ht://Dig was developed at San Diego State University as a way to search the
various web servers on the campus network.

%package	devel
Summary:	Libraries needed to develop for htdig
Group:		Development/C
Requires:	%{name} = %{version}

%description	devel
Libraries needed to develop for htdig.

%package	web
Summary:	Scripts and HTML code needed for using ht://Dig as a web search engine
Group:		Networking/WWW
Requires:	%{name} = %{version}
Requires:	webserver

%description	web
The ht://Dig system is a complete world wide web indexing and searching
system for a small domain or intranet. This system is not meant to replace
the need for powerful internet-wide search systems like Lycos, Infoseek,
Webcrawler and AltaVista. Instead it is meant to cover the search needs for
a single company, campus, or even a particular sub section of a web site. As
opposed to some WAIS-based or web-server based search engines, ht://Dig can
span several web servers at a site. The type of these different web servers
doesn't matter as long as they understand the HTTP 1.0 protocol.

The %{name}-web package includes CGI scripts and HTML code needed to use
ht://Dig on a website.

ht://Dig was developed at San Diego State University as a way to search the
various web servers on the campus network.


%prep

%setup -q -n %{name}-%{version}%{betanum}
chmod -R 0644 htdoc/*

%patch4 -p0 -b .memcpy
%patch5 -p1 -b .localconf
%patch6 -p1 -b .rundiginfos
%patch85 -p0 -b .compileprob


# Fix the flex output file for glibc 2.2 compatibility
cd htcommon
flex -oconf_lexer.cxx conf_lexer.lxx
cd ..

# Make it lib64 aware
perl -pi -e "m|LDFLAGS=| and s|/lib\b|/%{_lib}|g" configure */configure

%build
%serverbuild
export LDFLAGS="%{ldflags}"

./configure \
    --prefix=%{_prefix} \
    --libdir=%{_libdir} \
    --mandir=%{_mandir} \
    --enable-shared \
    --with-config-dir=%{_sysconfdir}/htdig \
    --with-common-dir=%{contentdir}/html/htdig \
    --with-database-dir=/var/lib/htdig \
    --localstatedir=/var/lib/htdig \
    --with-cgi-bin-dir=%{contentdir}/cgi-bin \
    --with-image-dir=%{contentdir}/html/htdig \
    --with-search-dir=%{contentdir}/html/htdig \
    --with-default-config-file=/etc/htdig/htdig.conf \
    --with-apache=/usr/sbin/httpd \
    --with-zlib=%{_prefix}

%make
mv htdoc/ChangeLog .


%install

%makeinstall_std

mkdir -p %{buildroot}/etc/cron.daily
cp %{SOURCE1} %{buildroot}/etc/cron.daily/htdig-dbgen

cp %{buildroot}%{contentdir}/cgi-bin/htsearch %{buildroot}%{_bindir}

chmod 644 %{buildroot}%{contentdir}/html/htdig/*

# pb with current rpm and symlinks (4.0.3-0.8mdk)
ln -sf ./search.html %{buildroot}%{contentdir}/html/htdig/index.html
#cp  %{buildroot}%{contentdir}/html/htdig/search.html  %{buildroot}%{contentdir}/html/htdig/index.html

# now get rid of the %{buildroot} paths in the conf files
for i in /etc/htdig.conf /usr/bin/rundig ; do
    perl -pi -e "s|%{buildroot}||g" %{buildroot}/$i
done

mkdir -p %{buildroot}%{_datadir}
mv %{buildroot}%{contentdir}/html/htdig %{buildroot}%{_datadir}
ln -sf ../../../usr/share/htdig %{buildroot}%{contentdir}/html/htdig

#ln -sf ../../../../usr/share/doc/htdig-%{PACKAGE_VERSION} \
#	%{buildroot}/var/www/html/htdig/htdoc

%pre
grep -E "^htdig:" /etc/group >/dev/null
if [ $? = 1 ]; then
		echo "adding htdig group"
		groupadd -r htdig
fi
grep -E "^htdig:" /etc/passwd >/dev/null
if [ $? = 1 ]; then
		echo "adding htdig user"
		useradd -r -g htdig -s "" -d /var/lib/htdig htdig 
fi
grep -E "^htdig:.*/var/lib/htdig:" /etc/passwd   >/dev/null
if [ $? = 1 ]; then
		echo "updating htdig homedir"
		perl -pi -e "s,^(htdig:.*:)[^:]+(:[^:]*)$,\1/var/lib/htdig\2," /etc/passwd
fi

%preun
# we're uninstalling
if [ $1 = 0 ]; then
		grep -E "^htdig:" /etc/passwd >/dev/null
		if [ $? = 0 ]; then
			echo "removing htdig user"
			userdel htdig # userdel seems to nuke the group too..
		fi

		grep -E "^htdig:" /etc/group >/dev/null
		if [ $? = 0 ]; then
			echo "removing htdig group"
			groupdel htdig
		fi
fi

%clean

%post web
# Only run this if installing for the first time
if [ "$1" = 1 ]; then
	if [ -f /etc/httpd/conf/httpd.conf ];then
	SERVERNAME="`grep '^ServerName' /etc/httpd/conf/httpd.conf | awk 'NR == 1 {print $2}'`"
	fi
	[ -z "$SERVERNAME" ] && SERVERNAME="`hostname -f`"
	[ -z "$SERVERNAME" ] && SERVERNAME="localhost"
	sed 's/^start_url:.*/#&\
# (See end of file for this parameter.)/' /etc/htdig/htdig.conf > /tmp/ht.$$
	cat /tmp/ht.$$ > /etc/htdig/htdig.conf
	rm /tmp/ht.$$
	cat >> /etc/htdig/htdig.conf <<!

# Automatically set up by htdig RPM, from your current Apache httpd.conf...
# Verify and configure these, and set maintainer above, before running
# /usr/bin/rundig.
# See /usr/doc/htdig*/attrs.html for descriptions of attributes.

# The URL(s) where htdig will start.  See also limit_urls_to above.
start_url:	http://$SERVERNAME/

# This makes sure that we don't spider the web
local_urls_only: true

# These attributes allow indexing server via local filesystem rather than HTTP.
local_urls:	http://$SERVERNAME/=/var/www/html/
local_user_urls:	http://$SERVERNAME/=/home/,/public_html/
!

fi

%files devel
%doc ChangeLog
%doc htdoc/*
%{_libdir}/htdig/*.a
%{_libdir}/htdig/*[a-z].so
%{_libdir}/htdig_db/*.a
%{_libdir}/htdig_db/*[a-z].so
%{_includedir}/*

%files web
%config(missingok, noreplace) %attr(0755,root,root) /etc/cron.daily/htdig-dbgen
%{contentdir}/html/htdig
%{contentdir}/cgi-bin/*

%files
%defattr(-,root,root,0755)
%dir %{_sysconfdir}/htdig
%config(noreplace) %{_sysconfdir}/htdig/cookies.txt
%config(noreplace) %{_sysconfdir}/htdig/htdig.conf
%config(noreplace) %{_sysconfdir}/htdig/HtFileType-magic.mime
%config(noreplace) %{_sysconfdir}/htdig/mime.types
%{_bindir}/*
%dir %{_libdir}/htdig
%dir %{_libdir}/htdig_db
%{_libdir}/htdig/*3.2.0.so
%{_libdir}/htdig_db/*3.2.0.so
%dir %attr(-,htdig,htdig) /var/lib/htdig
#%dir %{_datadir}/htdig
%dir %attr(-,htdig,root) %{_datadir}/htdig
%{_datadir}/htdig/*
%{_mandir}/man1/*
%{_mandir}/man8/*


