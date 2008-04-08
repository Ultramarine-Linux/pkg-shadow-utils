%if %{?WITH_SELINUX:0}%{!?WITH_SELINUX:1}
%define WITH_SELINUX 1
%endif

Summary: Utilities for managing accounts and shadow password files
Name: shadow-utils
Version: 4.0.18.1
Release: 22%{?dist}
Epoch: 2
URL: http://shadow.pld.org.pl/
Source0: ftp://ftp.pld.org.pl/software/shadow/shadow-%{version}.tar.bz2
Source1: shadow-4.0.17-login.defs
Source2: shadow-4.0.18.1-useradd
Source3: shadow-4.0.16-nscd.c

Patch0: shadow-4.0.17-redhat.patch
Patch1: shadow-4.0.3-noinst.patch
Patch2: shadow-4.0.11.1-vipw.patch
Patch3: shadow-4.0.14-goodname.patch
Patch4: shadow-4.0.13-newgrpPwd.patch
Patch5: shadow-4.0.16-lOption.patch
Patch6: shadow-4.0.17-notInheritFd.patch
Patch7: shadow-4.0.17-exitValues.patch
Patch8: shadow-4.0.17-auditLogging.patch
Patch9: shadow-4.0.18.1-gid.patch
Patch10: shadow-4.0.18.1-overflow.patch
Patch11: shadow-4.0.17-useradd.patch
Patch12: shadow-4.0.18.1-appendOption.patch
Patch13: shadow-4.0.18.1-sysAccount.patch
Patch14: shadow-4.0.18.1-findNewUidOnce.patch
Patch15: shadow-4.0.18.1-groupLoop.patch
Patch16: shadow-4.0.18.1-mtime.patch
Patch17: shadow-4.1.0-segfault.patch
Patch18: shadow-4.0.18.1-bflg.patch

License: BSD
Group: System Environment/Base
BuildRequires: autoconf, automake, libtool, gettext-devel
BuildRequires: libselinux-devel >= 1.25.2-1
BuildRequires: audit-libs-devel >= 1.0.10
Buildroot: %{_tmppath}/%{name}-%{version}-%{release}-root-%(%{__id_u} -n)
Requires: libselinux >= 1.25.2-1
Requires: audit-libs >= 1.0.10

%description
The shadow-utils package includes the necessary programs for
converting UNIX password files to the shadow password format, plus
programs for managing user and group accounts. The pwconv command
converts passwords to the shadow password format. The pwunconv command
unconverts shadow passwords and generates an npasswd file (a standard
UNIX password file). The pwck command checks the integrity of password
and shadow files. The lastlog command prints out the last login times
for all users. The useradd, userdel, and usermod commands are used for
managing user accounts. The groupadd, groupdel, and groupmod commands
are used for managing group accounts.

%prep
%setup -q -n shadow-%{version}
%patch0 -p1 -b .redhat
%patch1 -p1 -b .noinst
%patch2 -p1 -b .vipw
%patch3 -p1 -b .goodname
%patch4 -p1 -b .newgrpPwd
%patch5 -p1 -b .lOption

#replace whole file
cp %{SOURCE3} lib/nscd.c
%patch6 -p1 -b .notInheritFd

%patch7 -p1 -b .exitValues
%patch8 -p1 -b .auditLogging
%patch9 -p1 -b .gid
%patch10 -p1 -b .overflow
%patch11 -p1 -b .useradd
%patch12 -p1 -b .appendOption
%patch13 -p1 -b .sysAccount
%patch14 -p1 -b .findNewUidOnce
%patch15 -p1 -b .groupLoop
%patch16 -p1 -b .mtime
%patch17 -p1 -b .segfault
%patch18 -p1 -b .bflg

rm po/*.gmo
rm po/stamp-po

aclocal
libtoolize --force
automake -a
autoconf

%build
%configure \
	--disable-desrpc \
	--enable-shadowgrp \
	--without-libcrack \
	--with-libcrypt \
%if %{WITH_SELINUX}
	--with-selinux \
%endif
	--without-libpam \
	--disable-shared \
	--with-libaudit
make 

%install
rm -rf $RPM_BUILD_ROOT
make install DESTDIR=$RPM_BUILD_ROOT gnulocaledir=$RPM_BUILD_ROOT/%{_datadir}/locale MKINSTALLDIRS=`pwd`/mkinstalldirs
install -d -m 755 $RPM_BUILD_ROOT/%{_sysconfdir}/default
install -p -c -m 0644 %{SOURCE1} $RPM_BUILD_ROOT/%{_sysconfdir}/login.defs
install -p -c -m 0600 %{SOURCE2} $RPM_BUILD_ROOT/%{_sysconfdir}/default/useradd


ln -s useradd $RPM_BUILD_ROOT%{_sbindir}/adduser
#ln -s %{_mandir}/man8/useradd.8 $RPM_BUILD_ROOT/%{_mandir}/man8/adduser.8
ln -s useradd.8 $RPM_BUILD_ROOT/%{_mandir}/man8/adduser.8
for subdir in $RPM_BUILD_ROOT/%{_mandir}/{??,??_??,??_??.*}/man* ; do
	test -d $subdir && test -e $subdir/useradd.8 && echo ".so man8/useradd.8" > $subdir/adduser.8
done

# Remove binaries we don't use.
rm $RPM_BUILD_ROOT/%{_bindir}/chfn
rm $RPM_BUILD_ROOT/%{_bindir}/chsh
rm $RPM_BUILD_ROOT/%{_bindir}/expiry
rm $RPM_BUILD_ROOT/%{_bindir}/groups
rm $RPM_BUILD_ROOT/%{_bindir}/login
rm $RPM_BUILD_ROOT/%{_bindir}/passwd
rm $RPM_BUILD_ROOT/%{_bindir}/su
rm $RPM_BUILD_ROOT/%{_sysconfdir}/login.access
rm $RPM_BUILD_ROOT/%{_sysconfdir}/limits
rm $RPM_BUILD_ROOT/%{_sbindir}/logoutd
rm $RPM_BUILD_ROOT/%{_sbindir}/vipw
rm $RPM_BUILD_ROOT/%{_sbindir}/vigr
rm $RPM_BUILD_ROOT/%{_sbindir}/nologin
rm $RPM_BUILD_ROOT/%{_sbindir}/chgpasswd
rm $RPM_BUILD_ROOT/%{_mandir}/man1/chfn.*
rm $RPM_BUILD_ROOT/%{_mandir}/*/man1/chfn.*
rm $RPM_BUILD_ROOT/%{_mandir}/man1/chsh.*
rm $RPM_BUILD_ROOT/%{_mandir}/*/man1/chsh.*
rm $RPM_BUILD_ROOT/%{_mandir}/man1/expiry.*
rm $RPM_BUILD_ROOT/%{_mandir}/*/man1/expiry.*
rm $RPM_BUILD_ROOT/%{_mandir}/man1/groups.*
rm $RPM_BUILD_ROOT/%{_mandir}/*/man1/groups.*
rm $RPM_BUILD_ROOT/%{_mandir}/man1/login.*
rm $RPM_BUILD_ROOT/%{_mandir}/*/man1/login.*
rm $RPM_BUILD_ROOT/%{_mandir}/man1/passwd.*
rm $RPM_BUILD_ROOT/%{_mandir}/*/man1/passwd.*
rm $RPM_BUILD_ROOT/%{_mandir}/man1/su.*
rm $RPM_BUILD_ROOT/%{_mandir}/*/man1/su.*
rm $RPM_BUILD_ROOT/%{_mandir}/man5/limits.*
rm $RPM_BUILD_ROOT/%{_mandir}/*/man5/limits.*
rm $RPM_BUILD_ROOT/%{_mandir}/man5/login.access.*
rm $RPM_BUILD_ROOT/%{_mandir}/*/man5/login.access.*
rm $RPM_BUILD_ROOT/%{_mandir}/man5/passwd.*
rm $RPM_BUILD_ROOT/%{_mandir}/*/man5/passwd.*
rm $RPM_BUILD_ROOT/%{_mandir}/man5/porttime.*
rm $RPM_BUILD_ROOT/%{_mandir}/*/man5/porttime.*
rm $RPM_BUILD_ROOT/%{_mandir}/man5/suauth.*
rm $RPM_BUILD_ROOT/%{_mandir}/*/man5/suauth.*
rm $RPM_BUILD_ROOT/%{_mandir}/man8/logoutd.*
rm $RPM_BUILD_ROOT/%{_mandir}/*/man8/logoutd.*
rm $RPM_BUILD_ROOT/%{_mandir}/man8/vipw.*
rm $RPM_BUILD_ROOT/%{_mandir}/*/man8/vipw.*
rm $RPM_BUILD_ROOT/%{_mandir}/man8/nologin.*
rm $RPM_BUILD_ROOT/%{_mandir}/*/man8/nologin.*
rm $RPM_BUILD_ROOT/%{_mandir}/man8/vigr.*
rm $RPM_BUILD_ROOT/%{_mandir}/*/man8/vigr.*
rm $RPM_BUILD_ROOT/%{_mandir}/man8/chgpasswd.*
rm $RPM_BUILD_ROOT/%{_mandir}/*/man8/chgpasswd.*

%find_lang shadow
find $RPM_BUILD_ROOT%{_mandir} -depth -type d -empty -delete
for dir in $(ls -1d $RPM_BUILD_ROOT%{_mandir}/{??,??_??}) ; do
    dir=$(echo $dir | sed -e "s|^$RPM_BUILD_ROOT||")
    lang=$(basename $dir)
    echo "%%lang($lang) $dir/man*/*" >> shadow.lang
done

%clean
rm -rf $RPM_BUILD_ROOT

%files -f shadow.lang
%defattr(-,root,root)
%doc NEWS doc/HOWTO README
%dir %{_sysconfdir}/default
%attr(0644,root,root)	%config(noreplace) %{_sysconfdir}/login.defs
%attr(0600,root,root)	%config(noreplace) %{_sysconfdir}/default/useradd
%{_bindir}/sg
%{_bindir}/chage
%{_bindir}/faillog
%{_bindir}/gpasswd
%{_bindir}/lastlog
%{_bindir}/newgrp
%{_sbindir}/adduser
%attr(0750,root,root)	%{_sbindir}/user*
%attr(0750,root,root)	%{_sbindir}/group*
%{_sbindir}/grpck
%{_sbindir}/pwck
%{_sbindir}/*conv
%{_sbindir}/chpasswd
%{_sbindir}/newusers
%{_mandir}/man1/chage.1*
%{_mandir}/man1/gpasswd.1*
%{_mandir}/man1/sg.1*
%{_mandir}/man1/newgrp.1*
%{_mandir}/man3/shadow.3*
%{_mandir}/man3/getspnam.3*
%{_mandir}/man5/shadow.5*
%{_mandir}/man5/login.defs.5*
%{_mandir}/man5/gshadow.5*
%{_mandir}/man5/faillog.5*
%{_mandir}/man8/adduser.8*
%{_mandir}/man8/group*.8*
%{_mandir}/man8/user*.8*
%{_mandir}/man8/pwck.8*
%{_mandir}/man8/grpck.8*
%{_mandir}/man8/chpasswd.8*
%{_mandir}/man8/newusers.8*
%{_mandir}/man8/*conv.8*
%{_mandir}/man8/lastlog.8*
%{_mandir}/man8/faillog.8*

%changelog
* Tue Apr 08 2008 Peter Vrabec <pvrabec@redhat.com> 2:4.0.18.1-22
- fix "-b" option (#441460)

* Tue Feb 19 2008 Peter Vrabec <pvrabec@redhat.com> 2:4.0.18.1-21
- fix groupmems segmentation fault (#430813)

* Thu Nov 29 2007 Peter Vrabec <pvrabec@redhat.com> 2:4.0.18.1-20
- do not create mail spool entries for system accounts (#402351)

* Thu Oct 18 2007 Peter Vrabec <pvrabec@redhat.com> 2:4.0.18.1-19
- fix timestamps when moving home dirs to another file system (#278571)

* Mon Oct 08 2007 Peter Vrabec <pvrabec@redhat.com> 2:4.0.18.1-18
- mark localized man pages with %%lang

* Wed Aug 22 2007 Peter Vrabec <pvrabec@redhat.com> 2:4.0.18.1-17
- rebuild

* Tue Jun 26 2007 Peter Vrabec <pvrabec@redhat.com> 2:4.0.18.1-16
- fix "CAVEATS" section of groupadd man page (#245590)

* Tue Jun 06 2007 Peter Vrabec <pvrabec@redhat.com> 2:4.0.18.1-15
- fix infinitive loop if there are duplicate entries
  in /etc/group (#240915)

* Tue Jun 06 2007 Peter Vrabec <pvrabec@redhat.com> 2:4.0.18.1-14
- do not run find_new_uid() twice and use getpwuid() to check
  UID uniqueness (#236871)

* Tue Apr 10 2007 Peter Vrabec <pvrabec@redhat.com> 2:4.0.18.1-13
- fix useradd dump core when build without WITH_SELINUX (#235641)

* Mon Mar 26 2007 Peter Vrabec <pvrabec@redhat.com> 2:4.0.18.1-12
- create user's mailbox file by default (#231311)

* Fri Mar 16 2007 Peter Vrabec <pvrabec@redhat.com> 2:4.0.18.1-11
- assign system dynamic UID/GID from the top of available UID/GID (#190523)

* Wed Feb 28 2007 Peter Vrabec <pvrabec@redhat.com> 2:4.0.18.1-10
- spec file fixes to meet fedora standarts.
- fix useless call of restorecon(). (#222159) 

* Sun Jan 14 2007 Peter Vrabec <pvrabec@redhat.com> 2:4.0.18.1-9
- fix append option in usermod (#222540).

* Thu Dec 21 2006 Dan Walsh <dwalsh@redhat.com> 2:4.0.18.1-8
- Fix execution and creation of Home Directories under SELinux
- Resolves: rhbz#217441

* Thu Dec 14 2006 Peter Vrabec <pvrabec@redhat.com> 2:4.0.18.1-7
- fix rpmlint issues

* Wed Dec 06 2006 Peter Vrabec <pvrabec@redhat.com> 2:4.0.18.1-6
- use MD5 encryption by default (#218629).

* Thu Nov 30 2006 Steve Grubb <sgrubb@redhat.com> 2:4.0.18.1-5
- Fix SELinux context on home directories created with useradd (#217441)

* Tue Nov 14 2006 Peter Vrabec <pvrabec@redhat.com> 2:4.0.18.1-4
- fix chpasswd and chgpasswd stack overflow (#213052)

* Sat Nov 04 2006 Peter Vrabec <pvrabec@redhat.com> 2:4.0.18.1-3
- fix "-g" and "-G" option.

* Fri Nov 03 2006 Peter Vrabec <pvrabec@redhat.com> 2:4.0.18.1-2
- improve audit logging (#211659)
- improve "-l" option. Do not reset faillog if it's used (#213450).
 
* Wed Nov 01 2006 Peter Vrabec <pvrabec@redhat.com> 2:4.0.18.1-1
- upgrade

* Wed Oct 25 2006 Peter Vrabec <pvrabec@redhat.com> 2:4.0.17-7
- add dist-tag

* Wed Oct 04 2006 Peter Vrabec <pvrabec@redhat.com> 2:4.0.17-6
- fix regression. Permissions on user* group* binaries 
  should be 0750, because of CAPP/LSPP certification
- fix groupdel man page

* Fri Aug 11 2006 Peter Vrabec <pvrabec@redhat.com> 2:4.0.17-5
- fix bug introduced with UIG_GID.patch (#201991)

* Sat Aug 05 2006 Peter Vrabec <pvrabec@redhat.com> 2:4.0.17-4
- fix userdel, it didn't delete user's group (#201379)

* Fri Aug 04 2006 Peter Vrabec <pvrabec@redhat.com> 2:4.0.17-3
- fix UID/GID overflow in user* group* (#198920)

* Fri Aug 04 2006 Peter Vrabec <pvrabec@redhat.com> 2:4.0.17-2
- do not inherit file desc. in execve(nscd)

* Mon Jul 17 2006 Peter Vrabec <pvrabec@redhat.com> 2:4.0.17-1
- upgrade

* Wed Jul 12 2006 Jesse Keating <jkeating@redhat.com> - 2:4.0.16-3.1
- rebuild

* Tue Jun 13 2006 Peter Vrabec <pvrabec@redhat.com> 2:4.0.16-3
- call "nscd -i" to flush nscd cache (#191464)

* Sat Jun 10 2006 Peter Vrabec <pvrabec@redhat.com> 2:4.0.16-2
- "useradd -r" must create a system group (#194728)

* Tue Jun 06 2006 Peter Vrabec <pvrabec@redhat.com> 2:4.0.16-1
- upgrade
- do not replace login.defs file (#190014)

* Sat Apr 08 2006 Peter Vrabec <pvrabec@redhat.com> 2:4.0.15-3
- fix typo in shadow-4.0.15-login.defs (#188263)

* Tue Apr 04 2006 Peter Vrabec <pvrabec@redhat.com> 2:4.0.15-2
- properly notify nscd to flush its cache(#186803)

* Mon Apr 03 2006 Peter Vrabec <pvrabec@redhat.com> 2:4.0.15-1
- upgrade

* Fri Mar 10 2006 Peter Vrabec <pvrabec@redhat.com> 2:4.0.14-4
- fix lrename() function to handle relative symlinks too

* Tue Mar 07 2006 Peter Vrabec <pvrabec@redhat.com> 2:4.0.14-3
- set default umask to 077 in login.defs

* Mon Mar 06 2006 Peter Vrabec <pvrabec@redhat.com> 2:4.0.14-2
- use lrename() function, which follow a destination symbolic link(#181977)

* Fri Feb 10 2006 Jesse Keating <jkeating@redhat.com> - 2:4.0.14-1.2
- bump again for double-long bug on ppc(64)

* Tue Feb 07 2006 Jesse Keating <jkeating@redhat.com> - 2:4.0.14-1.1
- rebuilt for new gcc4.1 snapshot and glibc changes

* Fri Jan 06 2006 Peter Vrabec <pvrabec@redhat.com> 2:4.0.14-1
- upgrade

* Fri Dec 09 2005 Jesse Keating <jkeating@redhat.com>
- rebuilt

* Tue Nov 29 2005 Peter Vrabec <pvrabec@redhat.com> 2:4.0.13-4
- fix incorrect audit record in userdel (#174392)

* Wed Nov 16 2005 Peter Vrabec <pvrabec@redhat.com> 2:4.0.13-3
- fix useradd segfaults (#173241)

* Sat Nov 5 2005 Steve Grubb <sgrubb@redhat.com> 2:4.0.13-2
- Update audit communication to standard format messages

* Fri Oct 21 2005 Peter Vrabec <pvrabec@redhat.com> 2:4.0.13-1
- upgrade

* Fri Sep 23 2005 Peter Vrabec <pvrabec@redhat.com> 2:4.0.12-4
- add useradd -l option back, it was removed by mistake

* Tue Sep 20 2005 Peter Vrabec <pvrabec@redhat.com> 2:4.0.12-3
- provide login.defs man page
- adjust audit patch

* Tue Aug 30 2005 Peter Vrabec <pvrabec@redhat.com> 2:4.0.12-2
- audit support

* Sat Aug 27 2005 Peter Vrabec <pvrabec@redhat.com> 2:4.0.12-1
- upgrade 

* Sat Aug 13 2005 Dan Walsh <dwalsh@redhat.com> 2:4.0.11.1-5
- Change to use new selinux api for selinux_check_passwd_access

* Tue Aug 09 2005 Peter Vrabec <pvrabec@redhat.com> 2:4.0.11.1-4
- change the password last changed field in the shadow file
  when "usermod -p" is used (#164943)

* Mon Aug 08 2005 Peter Vrabec <pvrabec@redhat.com> 2:4.0.11.1-3
- provide getspnam.3 man page(#162476)
- fix useradd man page(#97131)

* Mon Aug 08 2005 Peter Vrabec <pvrabec@redhat.com> 2:4.0.11.1-2
- do not copy files from skel directory if home directory 
  already exist (#89591,#80242)

* Fri Aug 05 2005 Peter Vrabec <pvrabec@redhat.com> 2:4.0.11.1-1
- upgrade 

* Mon May 23 2005 Peter Vrabec <pvrabec@redhat.com> 2:4.0.7-9
- remove vigr binary

* Mon May 23 2005 Peter Vrabec <pvrabec@redhat.com> 2:4.0.7-8
- fix nscd socket path

* Fri Apr 29 2005 Jeremy Katz <katzj@redhat.com> - 2:4.0.7-7
- don't assume selinux is enabled if is_selinux_enabled() returns -1

* Mon Apr 18 2005 Peter Vrabec <pvrabec@redhat.com> 2:4.0.7-6
- fix chage -l option (#109499, #137498)

* Mon Apr 04 2005 Peter Vrabec <pvrabec@redhat.com> 2:4.0.7-5
- fix memory leak, and CPU spinning when grp_update() and 
  duplicate group entries in /etc/group (#151484)

* Mon Mar 29 2005 Peter Vrabec <pvrabec@redhat.com>  2:4.0.7-4
- use newgrp binary
- newgrp don't ask for password if user's default GID = group ID,
  ask for password if there is some in /etc/gshadow 
  and in /etc/group is 'x' (#149997)

* Mon Mar 14 2005 Peter Vrabec <pvrabec@redhat.com>
- gcc4 fix (#150994) 2:4.0.7-3

* Mon Mar 07 2005 Peter Vrabec <pvrabec@redhat.com>
- man pages cs,es,ko,ru,zh_CN,zh_TW to UTF-8

* Wed Mar 02 2005 Peter Vrabec <pvrabec@redhat.com>
- upgrade 2:4.0.7-1

* Fri Feb 25 2005 Peter Vrabec <pvrabec@redhat.com> 2:4.0.3-59
- static limit on group count to dynamic (#125510, #148994, #147742)

* Mon Feb 21 2005 Peter Vrabec <pvrabec@redhat.com> 2:4.0.3-58
- add "-l" option #146214

* Mon Feb 14 2005 Adrian Havill <havill@redhat.com>
- rebuilt

* Wed Feb 9 2005 Dan Walsh <dwalsh@redhat.com> 2:4.0.3-39
- Change useradd to use matchpathcon

* Thu Oct 21 2004 Dan Walsh <dwalsh@redhat.com> 2:4.0.3-37
- Add matchpathcon to create the files correctly when they do not exist.

* Mon Oct 18 2004 Miloslav Trmac <mitr@redhat.com> - 2:4.0.3-36
- Change symlink ownership when copying from /etc/skel (#66819, patch by
  Michael Weiser)

* Fri Oct 15 2004 Adrian Havill <havill@redhat.com> 2:4.0.3-35
- make the limit for the group name the same as the username (determined
  by the header files, rather than a constant) (#56850)

* Wed Oct 13 2004 Adrian Havill <havill@redhat.com> 2:4.0.3-33
- allow for mixed case and dots in usernames (#135401)
- all man pages to UTF-8, not just Japanese (#133883)
- add Polish blurb for useradd -n man page option (#82177)

* Tue Oct 12 2004 Adrian Havill <havill@redhat.com> 2:4.0.3-31
- check for non-standard legacy place for ncsd HUP (/var/run/nscd.pid) and
  then the std FHS place (/var/run/nscd.pid) (#125421)

* Fri Oct 1 2004 Dan Walsh <dwalsh@redhat.com> 2:4.0.3-30
- Add checkPasswdAccess for chage in SELinux

* Sun Sep 26 2004 Adrian Havill <riel@redhat.com> 2:4.0.3-29
- always unlock all files on any exit (#126709)

* Tue Aug 24 2004 Warren Togami <wtogami@redhat.com> 2:4.0.3-26
- #126596 fix Req and BuildReqs

* Sun Aug  1 2004 Alan Cox <alan@redhat.com> 4.0.3-25
- Fix build deps etc, move to current auto* (Steve Grubb)

* Sat Jul 10 2004 Alan Cox <alan@redhat.com> 4.0.3-24
- Fix nscd path. This fixes various stale data caching bugs (#125421)

* Thu Jun 17 2004 Dan Walsh <dwalsh@redhat.com> 4.0.3-23
- Add get_enforce checks
- Clean up patch for potential upstream submission
- Add removemalloc patch to get it to build on 3.4

* Tue Jun 15 2004 Elliot Lee <sopwith@redhat.com>
- rebuilt

* Tue Mar 30 2004 Nalin Dahyabhai <nalin@redhat.com> 4.0.3-21
- rebuild

* Tue Mar 30 2004 Nalin Dahyabhai <nalin@redhat.com> 4.0.3-20
- make /etc/default world-readable, needed for #118338

* Fri Feb 13 2004 Elliot Lee <sopwith@redhat.com>
- rebuilt

* Wed Jan 21 2004 Dan Walsh <dwalsh@redhat.com> 4.0.3-18
- Fix selinux relabel of /etc/passwd file

* Wed Jan  7 2004 Nalin Dahyabhai <nalin@redhat.com> 4.0.3-17
- fix use of uninitialized memory in useradd (#89145)

* Tue Dec 16 2003 Nalin Dahyabhai <nalin@redhat.com> 4.0.3-16
- back to UTF-8 again
- remove getspnam(3) man page, now conflicts with man-pages 1.64

* Thu Nov 13 2003 Nalin Dahyabhai <nalin@redhat.com> 4.0.3-15
- don't convert man pages to UTF-8 for RHEL 3, conditionalized using macro
- fixup dangling man page references

* Mon Nov 10 2003 Nalin Dahyabhai <nalin@redhat.com> 4.0.3-14
- lastlog: don't pass a possibly-smaller field to localtime (#109648)
- configure: call AC_SYS_LARGEFILE to get large file support

* Fri Nov 7 2003 Dan Walsh <dwalsh@redhat.com> 4.0.3-13.sel
- turn on SELinux support

* Wed Oct 22 2003 Nalin Dahyabhai <nalin@redhat.com> 4.0.3-12
- convert ja man pages to UTF-8 (#106051)
- override MKINSTALLDIRS at install-time (#107476)

* Mon Sep 8 2003 Dan Walsh <dwalsh@redhat.com>
- turn off SELinux support

* Thu Sep 4 2003 Dan Walsh <dwalsh@redhat.com> 4.0.3-11.sel
- build with SELinux support

* Fri Jul 28 2003 Dan Walsh <dwalsh@redhat.com> 4.0.3-10
- Add SELinux support

* Wed Jun 04 2003 Elliot Lee <sopwith@redhat.com>
- rebuilt

* Wed Jun  4 2003 Nalin Dahyabhai <nalin@redhat.com> 4.0.3-8
- rebuild

* Tue Jun  3 2003 Nalin Dahyabhai <nalin@redhat.com> 4.0.3-7
- run autoconf to generate updated configure at compile-time

* Wed Feb 12 2003 Nalin Dahyabhai <nalin@redhat.com> 4.0.3-6
- adjust mailspool patch to complain if no group named "mail" exists, even
  though that should never happen

* Tue Feb 11 2003 Nalin Dahyabhai <nalin@redhat.com> 4.0.3-5
- fix perms on mailspools created by useradd to be owned by the "mail"
  group (#59810)

* Wed Jan 22 2003 Tim Powers <timp@redhat.com>
- rebuilt

* Mon Dec  9 2002 Nalin Dahyabhai <nalin@redhat.com> 4.0.3-3
- install the shadow.3 man page

* Mon Nov 25 2002 Nalin Dahyabhai <nalin@redhat.com> 4.0.3-2
- disable use of cracklib at build-time
- fixup reserved-account changes for useradd

* Thu Nov 21 2002 Nalin Dahyabhai <nalin@redhat.com> 4.0.3-1
- update to 4.0.3, bumping epoch

* Mon Nov 18 2002 Nalin Dahyabhai <nalin@redhat.com> 20000902-14
- remove man pages which conflict with the man-pages package(s)

* Fri Nov 15 2002 Nalin Dahyabhai <nalin@redhat.com> 20000902-13
- prevent libshadow from being built more than once, to keep automake happy
- change how md5 and md5crypt are enabled, to keep autoconf happy
- remove unpackaged files after %%install

* Thu Aug 29 2002 Nalin Dahyabhai <nalin@redhat.com> 20000902-12
- force .mo files to be regenerated with current gettext to flush out possible
  problems
- fixup non-portable encodings in translations
- make sv translation header non-fuzzy so that it will be included (#71281)

* Fri Aug 23 2002 Nalin Dahyabhai <nalin@redhat.com> 20000902-11
- don't apply aging parameters when creating system accounts (#67408)

* Fri Jun 21 2002 Tim Powers <timp@redhat.com>
- automated rebuild

* Sun May 26 2002 Tim Powers <timp@redhat.com>
- automated rebuild

* Fri May 17 2002 Nalin Dahyabhai <nalin@redhat.com> 20000902-8
- rebuild in new environment

* Wed Mar 27 2002 Nalin Dahyabhai <nalin@redhat.com> 20000902-7
- rebuild with proper defines to get support for large lastlog files (#61983)

* Fri Feb 22 2002 Nalin Dahyabhai <nalin@redhat.com> 20000902-6
- rebuild

* Fri Jan 25 2002 Nalin Dahyabhai <nalin@redhat.com> 20000902-5
- fix autoheader breakage and random other things autotools complain about

* Mon Aug 27 2001 Nalin Dahyabhai <nalin@redhat.com> 20000902-4
- use -O0 instead of -O on ia64
- build in source directory
- don't leave lock files on the filesystem when useradd creates a group for
  the user (#50269)
- fix the -o option to check for duplicate UIDs instead of login names (#52187)

* Thu Jul 26 2001 Bill Nottingham <notting@redhat.com> 20000902-3
- build with -O on ia64

* Fri Jun 08 2001 Than Ngo <than@redhat.com> 20000902-2
- fixup broken specfile

* Tue May 22 2001 Bernhard Rosenkraenzer <bero@redhat.com> 20000902-1
- Create an empty mailspool when creating a user so non-setuid/non-setgid
  MDAs (postfix+procmail) can deliver mail (#41811)
- 20000902
- adapt patches

* Fri Mar  9 2001 Nalin Dahyabhai <nalin@redhat.com>
- don't overwrite user dot files in useradd (#19982)
- truncate new files when moving overwriting files with the contents of other
  files while moving directories (keeps files from looking weird later on)
- configure using %%{_prefix} as the prefix

* Fri Feb 23 2001 Trond Eivind Glomsrxd <teg@redhat.com>
- langify

* Wed Aug 30 2000 Bernhard Rosenkraenzer <bero@redhat.com>
- Fix up chage behavior (Bug #15883)

* Wed Aug 30 2000 Bernhard Rosenkraenzer <bero@redhat.com>
- 20000826
- Fix up useradd man page (Bug #17036)

* Tue Aug  8 2000 Bernhard Rosenkraenzer <bero@redhat.com>
- check for vipw lock before adding or deleting users (Bug #6489)

* Mon Aug  7 2000 Nalin Dahyabhai <nalin@redhat.com>
- take LOG_CONS out of the openlog() call so that we don't litter the
  screen during text-mode upgrades

* Tue Jul 18 2000 Bernhard Rosenkraenzer <bero@redhat.com>
- Remove a fixed-size buffer that caused problems when adding a huge number
  of users to a group (>8192 bytes) (Bugs #3809, #11930)

* Tue Jul 18 2000 Bernhard Rosenkraenzer <bero@redhat.com>
- remove dependency on util-linux because it causes prereq loops

* Tue Jul 18 2000 Nalin Dahyabhai <nalin@redhat.com>
- change symlinked man pages to includers
- require /usr/bin/newgrp (util-linux) so that /usr/bin/sg isn't left dangling

* Wed Jul 12 2000 Prospector <bugzilla@redhat.com>
- automatic rebuild

* Sun Jun 18 2000 Matt Wilson <msw@redhat.com>
- use mandir for FHS
- added patches in src/ and po/ to honor DESTDIR
- use make install DESTDIR=$RPM_BUILD_ROOT

* Wed Feb 16 2000 Bernhard Rosenkraenzer <bero@redhat.com>
- Fix up usermod's symlink behavior (Bug #5458)

* Fri Feb 11 2000 Cristian Gafton <gafton@redhat.com>
- get rid of mkpasswd

* Mon Feb  7 2000 Nalin Dahyabhai <nalin@redhat.com>
- fix usermod patch to check for shadow before doing any shadow-specific stuff
  and merge it into the pwlock patch

* Sat Feb  5 2000 Bernhard Rosenkraenzer <bero@redhat.com>
- fix man symlinks

* Wed Feb  2 2000 Nalin Dahyabhai <gafton@redhat.com>
- make -p only change shadow password (bug #8923)

* Mon Jan 31 2000 Cristian Gafton <gafton@redhat.com>
- rebuild to fix dependeencies
- man pages are compressed

* Wed Jan 19 2000 Bernhard Rosenkraenzer <bero@redhat.com>
- Fix a security bug (adduser could overwrite previously existing
  groups, Bug #8609)

* Sun Jan  9 2000 Bernhard Rosenkraenzer <bero@redhat.com>
- unset LINGUAS before building
- Fix typo in newusers manpage (Bug #8258)
- libtoolize

* Wed Sep 22 1999 Cristian Gafton <gafton@redhat.com>
- fix segfault for userdel when the primary group for the user is not
  defined

* Tue Sep 21 1999 Cristian Gafton <gafton@redhat.com>
- Serial: 1 because now we are using 19990827 (why the heck can't they have
  a normal version just like everybody else?!)
- ported all patches to the new code base

* Thu Apr 15 1999 Bill Nottingham <notting@redhat.com>
- SIGHUP nscd from usermod, too

* Fri Apr 09 1999 Michael K. Johnson <johnsonm@redhat.com>
- added usermod password locking from Chris Adams <cadams@ro.com>

* Thu Apr 08 1999 Bill Nottingham <notting@redhat.com>
- have things that modify users/groups SIGHUP nscd on exit

* Wed Mar 31 1999 Michael K. Johnson <johnsonm@redhat.com>
- have userdel remove user private groups when it is safe to do so
- allow -f to force user removal even when user appears busy in utmp

* Tue Mar 23 1999 Preston Brown <pbrown@redhat.com>
- edit out unused CHFN fields from login.defs.

* Sun Mar 21 1999 Cristian Gafton <gafton@redhat.com> 
- auto rebuild in the new build environment (release 7)

* Wed Jan 13 1999 Bill Nottingham <notting@redhat.com>
- configure fix for arm

* Wed Dec 30 1998 Cristian Gafton <gafton@redhat.com>
- build against glibc 2.1

* Fri Aug 21 1998 Jeff Johnson <jbj@redhat.com>
- Note that /usr/sbin/mkpasswd conflicts with /usr/bin/mkpasswd;
  one of these (I think /usr/sbin/mkpasswd but other opinions are valid)
  should probably be renamed.  In any case, mkpasswd.8 from this package
  needs to be installed. (problem #823)

* Fri May 08 1998 Prospector System <bugs@redhat.com>
- translations modified for de, fr, tr

* Tue Apr 21 1998 Cristian Gafton <gafton@redhat.com>
- updated to 980403
- redid the patches

* Tue Dec 30 1997 Cristian Gafton <gafton@redhat.com>
- updated the spec file
- updated the patch so that new accounts created on shadowed system won't
  confuse pam_pwdb anymore ('!!' default password instead on '!')
- fixed a bug that made useradd -G segfault
- the check for the ut_user is now patched into configure

* Thu Nov 13 1997 Erik Troan <ewt@redhat.com>
- added patch for XOPEN oddities in glibc headers
- check for ut_user before checking for ut_name -- this works around some
  confusion on glibc 2.1 due to the utmpx header not defining the ut_name
  compatibility stuff. I used a gross sed hack here because I couldn't make
  automake work properly on the sparc (this could be a glibc 2.0.99 problem
  though). The utuser patch works fine, but I don't apply it.
- sleep after running autoconf

* Thu Nov 06 1997 Cristian Gafton <gafton@redhat.com>
- added forgot lastlog command to the spec file

* Mon Oct 26 1997 Cristian Gafton <gafton@redhat.com>
- obsoletes adduser

* Thu Oct 23 1997 Cristian Gafton <gafton@redhat.com>
- modified groupadd; updated the patch

* Fri Sep 12 1997 Cristian Gafton <gafton@redhat.com>
- updated to 970616
- changed useradd to meet RH specs
- fixed some bugs

* Tue Jun 17 1997 Erik Troan <ewt@redhat.com>
- built against glibc
