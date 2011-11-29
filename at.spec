%define major_ver 3.1.10

%if %{?WITH_PAM:0}%{!?WITH_PAM:1}
%define WITH_PAM 1
%endif
Summary: Job spooling tools
Name: at
Version: 3.1.10
Release: 42%{?dist}
License: GPLv2+
Group: System Environment/Daemons
URL: http://ftp.debian.org/debian/pool/main/a/at
Source: http://ftp.debian.org/debian/pool/main/a/at/at_%{major_ver}.tar.gz
Source1: test.pl
Source2: atd.init
Source3: atd.sysconf
Source4: 56atd
Patch0: at-3.1.7-lockfile.patch
Patch1: at-3.1.10-makefile.patch
Patch2: at-3.1.10-man-timespec-path.patch
Patch3: at-3.1.7-sigchld.patch
Patch4: at-3.1.10-typo.patch
Patch5: at-3.1.8-perr.patch
Patch6: at-3.1.10-shell.patch
Patch7: at-3.1.8-t_option.patch
Patch8: at-3.1.10-pam.patch
Patch9: at-3.1.10-dont_fork.patch
Patch10: at-3.1.10-perm.patch
Patch11: at-3.1.10-opt_V.patch
Patch12: at-3.1.10-session.patch
Patch13: at-3.1.10-havepam.patch
# included in another pam patch
#Patch14: at-3.1.10-pam_keyring.patch
Patch15: at-3.1.10-PIE.patch
Patch16: at-3.1.10-pamfix.patch
Patch17: at-3.1.10-nonposix.patch
Patch18: at-3.1.10-selinux_mail.patch
Patch19: at-3.1.10-man_hyphen.patch
Patch20: at-3.1.10-different_shell.patch
Patch21: at-3.1.10-nowrap.patch

BuildRequires: fileutils chkconfig /etc/init.d
BuildRequires: flex bison autoconf
BuildRequires: libselinux-devel >= 1.27.9

%if %{WITH_PAM}
BuildRequires: pam-devel
%endif
Conflicts: crontabs <= 1.5
# No, I'm not kidding
BuildRequires: smtpdaemon
Buildroot: %{_tmppath}/%{name}-%{version}-%{release}-root-%(%{__id_u} -n)

%description
At and batch read commands from standard input or from a specified
file. At allows you to specify that a command will be run at a
particular time. Batch will execute commands when the system load
levels drop to a particular level. Both commands use user's shell.

You should install the at package if you need a utility for
time-oriented job control. Note: If it is a recurring job that will
need to be repeated at the same time every day/week, etc. you should
use crontab instead.

%prep
%setup -q

cp %{SOURCE1} .
%patch0 -p1 -b .lockfile
%patch1 -p1 -b .make
%patch2 -p1 -b .paths
%patch3 -p1 -b .sigchld
%patch4 -p1 -b .typo
%patch5 -p1 -b .perr
%patch6 -p1 -b .shell
%patch7 -p1 -b .t_option
%patch8 -p1 -b .pam
%patch9 -p1 -b .dont_fork
%patch10 -p1 -b .perm
%patch11 -p1 -b .opt_V
%patch12 -p1 -b .session
%patch13 -p1 -b .havepam
##%patch14 -p1 -b .pamkeyring
%patch15 -p1 -b .PIE
%patch16 -p1 -b .pamfix
%patch17 -p1 -b .nonposix
%patch18 -p1 -b .mailselinux
%patch19 -p1 -b .hyphen
%patch20 -p1 -b .fixshell
%patch21 -p1 -b .nowrap

%build
# patch10 touches configure.in
autoconf
# for patch11
rm -f lex.yy.* y.tab.*
%configure --with-atspool=%{_localstatedir}/spool/at/spool \
	--with-jobdir=%{_localstatedir}/spool/at \
	--with-daemon_username=root  \
	--with-daemon_groupname=root \
	--with-selinux \
%if %{WITH_PAM}
	--with-pam
%endif

make

%check
# don't run "make test" by default
%{?_without_check: %define _without_check 1}
%{!?_without_check: %define _without_check 1}

%if ! %{_without_check}
	LANG=C make test > /dev/null
%endif

%install
make install \
	DAEMON_USERNAME=`id -nu`\
	DAEMON_GROUPNAME=`id -ng` \
	DESTDIR=%{buildroot}\
	sbindir=%{buildroot}%{_prefix}/sbin\
	bindir=%{buildroot}%{_bindir}\
	prefix=%{buildroot}%{_prefix}\
	exec_prefix=%{buildroot}%{_prefix}\
	docdir=%{buildroot}/usr/doc\
	mandir=%{buildroot}%{_mandir}\
	etcdir=%{buildroot}%{_sysconfdir} \
	ATJOB_DIR=%{buildroot}%{_localstatedir}/spool/at \
	ATSPOOL_DIR=%{buildroot}%{_localstatedir}/spool/at/spool \
	INSTALL_ROOT_USER=`id -nu` \
	INSTALL_ROOT_GROUP=`id -nu`;

echo > %{buildroot}%{_sysconfdir}/at.deny
mkdir docs
cp  %{buildroot}/%{_prefix}/doc/at/* docs/

mkdir -p %{buildroot}%{_sysconfdir}/rc.d/init.d
install -m 755 %{SOURCE2} %{buildroot}%{_sysconfdir}/rc.d/init.d/atd

mv -f %{buildroot}/%{_mandir}/man5/at_allow.5 \
	%{buildroot}/%{_mandir}/man5/at.allow.5
rm -f %{buildroot}/%{_mandir}/man5/at_deny.5
#ln -s at.allow.5 %{buildroot}/%{_mandir}/man5/at.deny.5

mkdir -p %{buildroot}/etc/sysconfig
install -m 755 %{SOURCE3} %{buildroot}/etc/sysconfig/atd

mkdir -p %{buildroot}/%{_libdir}/pm-utils/sleep.d/
install -m 755 %{SOURCE4} %{buildroot}/%{_libdir}/pm-utils/sleep.d/56atd

# remove unpackaged files from the buildroot
rm -r  %{buildroot}%{_prefix}/doc

%clean
rm -rf %{buildroot}

%post
touch %{_localstatedir}/spool/at/.SEQ
chmod 600 %{_localstatedir}/spool/at/.SEQ
chown daemon:daemon %{_localstatedir}/spool/at/.SEQ
# must be in chkconfig on
/sbin/chkconfig --add atd

%preun
if [ "$1" = "0" ] ; then
	/sbin/service atd stop >/dev/null 2>&1 ||:
	/sbin/chkconfig --del atd
fi

%postun
if [ "$1" -ge "1" ]; then
	/sbin/service atd condrestart >/dev/null 2>&1 ||:
fi

%files
%defattr(-,root,root,-)
%doc docs/*
%attr(0644,root,root)       %config(noreplace) %{_sysconfdir}/at.deny
%config(noreplace)          %{_sysconfdir}/sysconfig/atd
%attr(0755,root,root)		%{_sysconfdir}/rc.d/init.d/atd
%attr(0700,daemon,daemon)	%dir %{_localstatedir}/spool/at
%attr(0600,daemon,daemon)	%verify(not md5 size mtime) %ghost %{_localstatedir}/spool/at/.SEQ
%attr(0700,daemon,daemon)	%dir %{_localstatedir}/spool/at/spool
%attr(0644,root,daemon)		%config(noreplace) %{_sysconfdir}/pam.d/atd
%{_sbindir}/atrun
%attr(0755,root,root)		%{_sbindir}/atd
%{_mandir}/man*/*
%{_bindir}/batch
%{_bindir}/atrm
%{_bindir}/atq
%attr(4755,root,root)		%{_bindir}/at
%attr(0755,root,root)		%{_libdir}/pm-utils/sleep.d/56atd

%changelog
* Tue Jun  8 2010 Marcela Mašláňová <mmaslano@redhat.com> - 3.1.10-42
- fix permissions in files section
- Resolves: rhbz#589099

* Fri Feb 12 2010 Marcela Mašláňová <mmaslano@redhat.com> - 3.1.10-41
- prevent arbitrary destruction of at jobs (based on 564243)
- Related: rhbz#543948

* Thu Jan 14 2010 Marcela Mašláňová <mmaslano@redhat.com> - 3.1.10-40
- there were missing apostrophes around delimiter
- Resolves: rhbz#546103

* Tue Oct 13 2009 Marcela Mašláňová <mmaslano@redhat.com> - 3.1.10-39
- 528582 add noreplace option into files section

* Tue Sep 29 2009 Tomas Mraz <tmraz@redhat.com> 3.1.10-38
- authentication PAM modules have to be configured for pam_setcred()

* Wed Sep 16 2009 Tomas Mraz <tmraz@redhat.com> 3.1.10-37
- improve the PAM configuration, use password-auth common stack

* Tue Aug 18 2009 Adam Jackson <ajax@redhat.com> 3.1.10-36
- Remove Requires: pm-utils-filesystem, dead package

* Fri Jul 24 2009 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 3.1.10-35
- Rebuilt for https://fedoraproject.org/wiki/Fedora_12_Mass_Rebuild

* Mon Jul  20 2009 Marcela Mašláňová <mmaslano@redhat.com> - 3.1.10-34
- require pm-utils-filesystem instead of pm-utils which should help
 minimal installation.

* Mon Jun  1 2009 Marcela Mašláňová <mmaslano@redhat.com> - 3.1.10-33
- clean cvs, check patches

* Wed Mar 18 2009 Marcela Mašláňová <mmaslano@redhat.com> - 3.1.10-32
- add the forgotten add delimiter thanks to Cong Ma

* Thu Feb 26 2009 Marcela Mašláňová <mmaslano@redhat.com> - 3.1.10-31
- preun script is sometimes failing. Add apostrofs around zero.

* Thu Feb 26 2009 Marcela Mašláňová <mmaslano@redhat.com> - 3.1.10-30
- 435765 and 486844 in some cases could be used bash for at commands
 even if user sets different default shell. Also bash4.0 fix Here Documents
 which breaks previous patch at-3.1.10-shell.patch.

* Mon Feb 23 2009 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 3.1.10-29
- Rebuilt for https://fedoraproject.org/wiki/Fedora_11_Mass_Rebuild

* Thu Feb 19 2009 Marcela Mašláňová <mmaslano@redhat.com> - 3.1.10-28
- 486227 add hyphen date into manual page.

* Wed Dec 3 2008 Marcela Mašláňová <mmaslano@redhat.com> - 3.1.10-27
- 464393 add script into pm-utils, because daemon wasn't taking all jobs 
	after suspend/hibernate

* Fri Oct 24 2008 Marcela Mašláňová <mmaslano@redhat.com> - 3.1.10-26
- update init script according to SysVInitScript

* Tue Sep 16 2008 Marcela Maslanova <mmaslano@redhat.com> - 3.1.10-25
- thanks dwalsh for selinux patch, which fix #460873

* Fri Jul 18 2008 Marcela Maslanova <mmaslano@redhat.com> - 3.1.10-24
- 446004 hope adding || into scriptlets fix removing old package after upgrade
- fixes for fuzz=0

* Tue Mar 25 2008 Marcela Maslanova <mmaslano@redhat.com> - 3.1.10-23
- 436952 use local instead of posix output date/time format.

* Thu Feb 28 2008 Marcela Maslanova <mmaslano@redhat.com> - 3.1.10-22
- #435250 mixed OPTS and OPTIONS variable in sysconfig

* Tue Feb 19 2008 Fedora Release Engineering <rel-eng@fedoraproject.org> - 3.1.10-21
- Autorebuild for GCC 4.3

* Tue Jan  8 2008 Marcela Maslanova <mmaslano@redhat.com> - 3.1.10-20
- used PIE instead of pie (with pie wasn't build on 64b successful)
- rewrite PAM fail check
- fix checking of settings setuid(s)

* Mon Dec  3 2007 Marcela Maslanova <mmaslano@redhat.com> - 3.1.10-19
- another problem with permission

* Fri Oct 30 2007 Marcela Maslanova <mmaslano@redhat.com> - 3.1.10-18
- Bug 398981: change on correct permissions

* Fri Oct 05 2007 Marcela Maslanova <mmaslano@redhat.com> - 3.1.10-17
- Bug 250147: add optional support for gnome-keyring to passwd pam stack

* Wed Aug 22 2007 Marcela Maslanova <mmaslano@redhat.com> - 3.1.10-16
- macro with_pam instead of have_pam
- license tag is gplv2+ because of license in source files

* Tue Jul 11 2007 Marcela Maslanova <mmaslano@redhat.com> - 3.1.10-15
- rewrite init script
- add own session - setsid
- Resolves: rhbz#247091

* Tue Jul  9 2007 Marcela Maslanova <mmaslano@redhat.com> - 3.1.10-14
- feature: add configuration file
- fix -V option
- fix init script

* Tue Jul  3 2007 Marcela Maslanova <mmaslano@redhat.com> - 3.1.10-13
- Resolves: rhbz#243064

* Tue Jul  3 2007 Marcela Maslanova <mmaslano@redhat.com> - 3.1.10-12
- crashing atd
- work only for root, still broken some functions
- Resolves: rhbz#243064

* Tue Mar 27 2007 Marcela Maslanova <mmaslano@redhat.com> - 3.1.10-11
- mistake in pam_atd
- rhbz#234120

* Tue Mar 05 2007 Marcela Maslanova <mmaslano@redhat.com> - 3.1.10-10
- rhbz#224597

* Mon Mar 03 2007 Marcela Maslanova <mmaslano@redhat.com> - 3.1.10-9
- review

* Wed Feb 20 2007 Marcela Maslanova <mmaslano@redhat.com> - 3.1.10-8
- review
- rhbz#225288

* Tue Jan 30 2007 Marcela Maslanova <mmaslano@redhat.com> - 3.1.10-7
- no debug file - useless
- new pam configuration
- rhbz#224597

* Tue Oct 27 2006 Marcela Maslanova <mmaslano@redhat.com> - 3.1.10-6
- fix daylight-saving again 
- fix #214759 - problem with seteuid

* Wed Oct 25 2006 Marcela Maslanova <mmaslano@redhat.com> - 3.1.10-5
- daylight-saving

* Tue Oct 24 2006 Marcela Maslanova <mmaslano@redhat.com> - 3.1.10-3
- new version from upstream 3.1.10

* Thu Aug 23 2006 Marcela Maslanova <mmaslano@redhat.com> - 3.1.8-82.fc6
- #176486 don't fork option added (patch from Enrico Scholz)

* Wed Jul 12 2006 Jesse Keating <jkeating@redhat.com> - 3.1.8-81.2
- rebuild

* Fri Feb 10 2006 Jesse Keating <jkeating@redhat.com> - 3.1.8-81.1
- bump again for double-long bug on ppc(64)

* Tue Feb 07 2006 Jason Vas Dias <jvdias@redhat.com> - 3.1.8-81
- rebuild for new gcc, glibc, glibc-kernheaders
- workaround new refusal of /usr/bin/install to chown

* Fri Dec 18 2005 Jason Vas Dias<jvdias@redhat.com> - 3.1.8-80.2
- rebuild for new flex

* Fri Dec 16 2005 Jesse Keating <jkeating@redhat.com>
- rebuilt for new gcj

* Fri Oct 14 2005 Dan Walsh <dwalsh@redhat.com> - 3.1.8-80
- Add seuserbyname support

* Fri Sep 30 2005 Tomas Mraz <tmraz@redhat.com> - 3.1.8-79
- use include instead of pam_stack in pam config

* Fri Jun 03 2005 Jason Vas Dias <jvdias@redhat.com> 3.1.8-78
- fix bug 159220: add pam_loginuid to pam session stack in /etc/pam.d/atd 
- fix bug 102341: add '-r' synonym for '-d' / atrm for POSIX / SuS conformance

* Fri Apr 08 2005 Jason Vas Dias <jvdias@redhat.com> 3.1.8-77
- always call pam_setcred(pamh, PAM_DELETE_CRED) before session 
- close

* Tue Apr 05 2005 Jason Vas Dias <jvdias@redhat.com> 3.1.8-70
- always call pam_close_session on PAM_FAIL or pam_end

* Tue Mar 08 2005 Jason Vas Dias <jvdias@redhat.com> 3.1.8-68
- Put PAM authentication check in 'check_permissions()', so
- user can know when using at(1) if PAM permission is denied.

* Tue Mar 08 2005 Jason Vas Dias <jvdias@redhat.com> 3.1.8-67
- better fix for bug 150131: change DAEMON_USERNAME and 
- DAEMON_GROUPNAME to 'root' .

* Mon Mar 07 2005 Jason Vas Dias <jvdias@redhat.com> 3.1.8-66
- fix bug 150131: atd should not relinquish root privilege if
- doing su(1) equivalent with PAM .

* Tue Jan 25 2005 Jason Vas Dias <jvdias@redhat.com> 3.1.8-64
- bugs 5160/146132: add PAM authentication control to atd

* Tue Oct 05 2004 Jason Vas Dias <jvdias@redhat.com> 3.1.8-60
- fix bug 131510: no_export env. var. blacklisting should not
- remove 'SHELL' when only 'SHELLOPTS' is blacklisted.
- at(1) man-page should not say 'commands are run with /bin/sh'
- and should explain usage of SHELL environement variable and
- details of blacklisted variables.

* Tue Sep 28 2004 Rik van Riel <riel@redhat.com> 3.1.8-58
- fix typo in man page, bug 112303 
- (regenerated at-3.1.8-man-timespec-path.patch with fix)

* Tue Aug 03 2004 Jason Vas Dias <jvdias@redhat.com>
- fixed bug 125634 - made usage() agree with manpage

* Thu Jul 29 2004 Jason Vas Dias <jvdias@redhat.com>
- Added POSIX.2 -t option for RFE 127485

*  Thu Jul 29 2004 Jason Vas Dias <jvdias@redhat.com>
- Had to disable the 'make test' for the build BEFORE
- any changes were made (building on FC2 - perl issue?)
- test.pl generates these 'errors' for what looks like
- valid output to me:
- $ ./test.pl 2>&1 | egrep -v '(^ok$)|(time_only)'
- 1..3656
- not ok
- 'Monday - 1 month': 'Fri Jul  2 18:29:00 2004' =? 'Sat Jul  3 18:29:00 2004'
- not ok
- 'Monday - 10 months': 'Thu Oct  2 18:29:00 2003' =? 'Fri Oct  3 18:29:00 2003'
- not ok
- 'next week - 1 month': 'Mon Jul  5 18:29:00 2004' =? 'Tue Jul  6 18:29:00 2004'
- not ok
- 'next week - 10 months': 'Sun Oct  5 18:29:00 2003' =? 'Mon Oct  6 18:29:00 2003'
- will investigate and fix for next release.

* Tue Jun 15 2004 Elliot Lee <sopwith@redhat.com>
- rebuilt

* Wed May 12 2004 Thomas Woerner <twoerner@redhat.com> - 3.1.8-54
- fixed pie patch: at is pie, now
- added build requires for libselinux-devel

* Tue May 4 2004 Dan Walsh <dwalsh@redhat.com> - 3.1.8-53
- Add fileentrypoint check

* Thu Apr 15 2004 Dan Walsh <dwalsh@redhat.com> - 3.1.8-52
- Fix SELinux patch

* Mon Feb 23 2004 Tim Waugh <twaugh@redhat.com>
- Use ':' instead of '.' as separator for chown.

* Fri Feb 13 2004 Elliot Lee <sopwith@redhat.com> - 3.1.8-50
- rebuilt

* Tue Dec  9 2003 Jens Petersen <petersen@redhat.com> - 3.1.8-49
- replace at-3.1.8-SHELL-91233.patch by at-3.1.8-SHELL-111386.patch which
  now executes $SHELL directly in the at shell script after all the variables
  have been setup with /bin/sh (#91233) [suggested by Göran Uddeborg]
- this changelog is now in utf-8

* Fri Nov  7 2003 Jens Petersen <petersen@redhat.com> - 3.1.8-48
- add at-3.1.8-pie.patch to build atd as pie (#108415) [Ulrich Drepper]

* Fri Oct 31 2003 Dan Walsh <dwalsh@redhat.com> - 3.1.8-47.sel

* Fri Jun 20 2003 Jens Petersen <petersen@redhat.com> - 3.1.8-46
- add at-3.1.8-atrun.8-typo-97697.patch to fix typo in atrun.8 (#97697)
- update at.1 description of shell behaviour (#91233)

* Tue Jun 17 2003 Jens Petersen <petersen@redhat.com> - 3.1.8-45
- make the job shell default to SHELL instead of "/bin/sh" (#91233)

* Wed Jun 04 2003 Elliot Lee <sopwith@redhat.com> - 3.1.8-44
- rebuilt

* Tue Jun  3 2003 Jens Petersen <petersen@redhat.com> - 3.1.8-43
- Replace redundant at-3.1.7-paths.patch by at-3.1.8-man-timespec-path.patch
  to fix timespec path

* Tue Jun  3 2003 Jens Petersen <petersen@redhat.com> - 3.1.8-41
- update source to at_3.1.8-11 from debian upstream
  - update source url
  - at-debian.patch no longer needed
  - at-3.1.7-paths.patch: the patch to "at.1.in" no longer needed
  - replace at-3.1.8-lexer.patch with at-3.1.8-11-lexer-parser.diff
  - at-3.1.8-dst.patch no longer needed
  - at-3.1.8-lsbdoc.patch no longer needed
  - at-3.1.8-o_excl.patch no longer needed
  - bump release number
- at-3.1.8-test.patch: move out test.pl to a separate source file
  - apply at-3.1.8-test-fix.patch to it and drop patch
- at-3.1.8-shell.patch: drop (#22216,#91233)
- run "make test" after building
- add "--without check" rpmbuild option
- fix autoconf comment to point to right patch
- use _sysconfdir, _sbindir, _bindir, and _localstatedir

* Wed Jan 22 2003 Tim Powers <timp@redhat.com> 3.1.8-33
- rebuilt

* Wed Nov 27 2002 Tim Powers <timp@redhat.com> 3.1.8-32
- remove unpackaged files from the buildroot

* Tue Jul 25 2002 Bill Huang <bhuang@redhat.com>
- Fixed delaying job execution and missing starting jobs..(bug#69595)
  (Thanks Bujor D Silaghi <bujor@cs.umd.edu> for his patch.)

* Fri Jul 19 2002 Bill Huang <bhuang@redhat.com>
- Fixed cleaning atq and  multiple atd daemon.(bug#67414)
  (Thanks Bujor D Silaghi <bujor@cs.umd.edu> for his patch.)

* Fri Jul 19 2002 Bill Huang <bhuang@redhat.com>
- Fixed error message output in atd.c

* Fri Jun 21 2002 Tim Powers <timp@redhat.com>
- automated rebuild

* Mon May 27 2002 Bill Huang <bhuang@redhat.com>
- Rebuild for Milan

* Thu May 23 2002 Tim Powers <timp@redhat.com>
- automated rebuild

* Fri Feb  1 2002 Bernhard Rosenkraenzer <bero@redhat.com> 3.1.8-25
- Require smtpdaemon rather than sendmail - postfix works just as well.

* Thu Jan 31 2002 Bill Nottingham <notting@redhat.com> 3.1.8-24
- rebuild in new env.

* Thu Jan 17 2002 Trond Eivind Glomsrød <teg@redhat.com> 3.1.8-23
- s/Copyright/License/

* Mon Jan 14 2002 Adrian Havill <havill@redhat.com> 3.1.8-21
- fix man page (#51253)
- fix env prop problem (#49491)
- .SEQ should not be executable (#52626)
- beefed up file creation perms against symlink exploits (O_EXCL)

* Thu Aug  2 2001 Crutcher Dunnavant <crutcher@redhat.com> 3.1.8-20
- updated patch update, still bug #46546

* Mon Jul 18 2001 Crutcher Dunnavant <crutcher@redhat.com>
- applied enrico.scholz@informatik.tu-chemnitz.de's change to the env patch to 
- address bug #46546

* Mon Jun 25 2001 Crutcher Dunnavant <crutcher@redhat.com>
- changed atd.init to start at 95, stop at 5, closing #15915
- applied mailto:wp@supermedia.pl's environment patch

* Sun Jun 24 2001 Elliot Lee <sopwith@redhat.com>
- Bump release + rebuild.

* Wed Apr  4 2001 Crutcher Dunnavant <crutcher@redhat.com>
- much love to David Kilzer <ddkilzer@lubricants-oil.com>
- who nailed UTC, Leap year, DST, and some other edge cases down
- he also wrote a test harness in perl
- bug #28448

* Fri Feb  2 2001 Trond Eivind Glomsrød <teg@redhat.com>
- i18nize initscript

* Wed Dec 12 2000 Bill Nottingham <notting@redhat.com>
- fix documentation of which shell commands will be run with (#22216)

* Wed Aug 23 2000 Crutcher Dunnavant <crutcher@redhat.com>
- Well, we will likely never really close the UTC issues,
- because of 1) fractional timezones, and 2) daylight savigns time.
- but there is a slight tweak to the handling of dst in the UTC patch.

* Wed Aug 23 2000 Crutcher Dunnavant <crutcher@redhat.com>
- fixed bug #15685
- which had at miscaluclating UTC times.

* Sat Jul 15 2000 Bill Nottingham <notting@redhat.com>
- move initscript back

* Wed Jul 12 2000 Prospector <bugzilla@redhat.com>
- automatic rebuild

* Thu Jul  6 2000 Bill Nottingham <notting@redhat.com>
- prereq /etc/init.d

* Sat Jul  1 2000 Nalin Dahyabhai <nalin@redhat.com>
- fix syntax error in init script

* Tue Jun 27 2000 Preston Brown <pbrown@redhat.com>
- don't prereq, only require initscripts

* Mon Jun 26 2000 Preston Brown <pbrown@redhat.com>
- move init script
- add condrestart directive
- fix post/preun/postun scripts
- prereq initscripts >= 5.20

* Sat Jun 17 2000 Bill Nottingham <notting@redhat.com>
- fix verify of /var/spool/at/.SEQ (#12262)

* Mon Jun 12 2000 Nalin Dahyabhai <nalin@redhat.com>
- fix status checking and syntax error in init script

* Fri Jun  9 2000 Bill Nottingham <notting@redhat.com>
- fix for long usernames (#11321)
- add some bugfixes from debian

* Mon May  8 2000 Bernhard Rosenkraenzer <bero@redhat.com>
- 3.1.8

* Wed Mar  1 2000 Bill Nottingham <notting@redhat.com>
- fix a couple of more typos, null-terminate some strings

* Thu Feb 10 2000 Bill Nottingham <notting@redhat.com>
- fix many-years-old typo in atd.c

* Thu Feb  3 2000 Bill Nottingham <notting@redhat.com>
- handle compressed man pages

* Mon Aug 16 1999 Bill Nottingham <notting@redhat.com>
- initscript munging, build as non-root user

* Sun Jun 13 1999 Jeff Johnson <jbj@redhat.com>
- correct perms for /var/spool/at after defattr.

* Mon May 24 1999 Jeff Johnson <jbj@redhat.com>
- reset SIGCHLD before exec (#3016).

* Sun Mar 21 1999 Cristian Gafton <gafton@redhat.com> 
- auto rebuild in the new build environment (release 8)

* Thu Mar 18 1999 Cristian Gafton <gafton@redhat.com>
- fix handling the 12:00 time

* Wed Jan 13 1999 Bill Nottingham <notting@redhat.com>
- configure fix for arm

* Wed Jan 06 1999 Cristian Gafton <gafton@redhat.com>
- build for glibc 2.1

* Tue May 05 1998 Prospector System <bugs@redhat.com>
- translations modified for de, fr, tr

* Wed Apr 22 1998 Michael K. Johnson <johnsonm@redhat.com>
- enhanced initscript

* Sun Nov 09 1997 Michael K. Johnson <johnsonm@redhat.com>
- learned to spell

* Wed Oct 22 1997 Michael K. Johnson <johnsonm@redhat.com>
- updated to at version 3.1.7
- updated lock and sequence file handling with ghost
- Use chkconfig and atd, now conflicts with old crontabs packages

* Thu Jun 19 1997 Erik Troan <ewt@redhat.com>
- built against glibc

