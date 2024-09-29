%global         forgeurl https://github.com/osbuild/osbuild
%global         selinuxtype targeted

Version:              110

%forgemeta

%global         pypi_name osbuild
%global         pkgdir %{_prefix}/lib/%{pypi_name}

Name:                 %{pypi_name}
Release:              1%{?dist}.rocky.0.2
License:              Apache-2.0

URL:                  %{forgeurl}

Source0:              %{forgesource}
BuildArch:            noarch
Summary:              A build system for OS images


BuildRequires:        make
BuildRequires:        python3-devel
BuildRequires:        python3-docutils
BuildRequires:        systemd

Requires:             bash
Requires:             bubblewrap
Requires:             coreutils
Requires:             curl
Requires:             dnf
Requires:             e2fsprogs
Requires:             glibc
Requires:             policycoreutils
Requires:             qemu-img
Requires:             systemd
Requires:             skopeo
Requires:             tar
Requires:             util-linux
Requires:             python3-%{pypi_name} = %{version}-%{release}
Requires:             (%{name}-selinux if selinux-policy-%{selinuxtype})

# This is required for `osbuild`, for RHEL-10 and above
# the stdlib toml package can be used instead
%if 0%{?rhel} < 10
Requires:             python3-tomli
%endif

# Turn off dependency generators for runners. The reason is that runners are
# tailored to the platform, e.g. on RHEL they are using platform-python. We
# don't want to pick up those dependencies on other platform.
%global __requires_exclude_from ^%{pkgdir}/(runners)/.*$

# Turn off shebang mangling on RHEL. brp-mangle-shebangs (from package
# redhat-rpm-config) is run on all executables in a package after the `install`
# section runs. The below macro turns this behavior off for:
#   - runners, because they already have the correct shebang for the platform
#     they're meant for, and
#   - stages and assemblers, because they are run within osbuild build roots,
#     which are not required to contain the same OS as the host and might thus
#     have a different notion of "platform-python".
# RHEL NB: Since assemblers and stages are not excluded from the dependency
# generator, this also means that an additional dependency on /usr/bin/python3
# will be added. This is intended and needed, so that in the host build root
# /usr/bin/python3 is present so stages and assemblers can be run.
%global __brp_mangle_shebangs_exclude_from ^%{pkgdir}/(assemblers|runners|stages)/.*$

%{?python_enable_dependency_generator}

%description
A build system for OS images

%package -n     python3-%{pypi_name}
Summary:              %{summary}
%{?python_provide:%python_provide python3-%{pypi_name}}

%description -n python3-%{pypi_name}
A build system for OS images

%package        lvm2
Summary:              LVM2 support
Requires:             %{name} = %{version}-%{release}
Requires:             lvm2

%description lvm2
Contains the necessary stages and device host
services to build LVM2 based images.

%package        luks2
Summary:              LUKS2 support
Requires:             %{name} = %{version}-%{release}
Requires:             cryptsetup

%description luks2
Contains the necessary stages and device host
services to build LUKS2 encrypted images.

%package        ostree
Summary:              OSTree support
Requires:             %{name} = %{version}-%{release}
Requires:             ostree
Requires:             rpm-ostree

%description ostree
Contains the necessary stages, assembler and source
to build OSTree based images.

%package        selinux
Summary:              SELinux policies
Requires:             %{name} = %{version}-%{release}
Requires:             selinux-policy-%{selinuxtype}
Requires(post): selinux-policy-%{selinuxtype}
BuildRequires:        selinux-policy-devel
%{?selinux_requires}

%description    selinux
Contains the necessary SELinux policies that allows
osbuild to use labels unknown to the host inside the
containers it uses to build OS artifacts.

%package        tools
Summary:              Extra tools and utilities
Requires:             %{name} = %{version}-%{release}
Requires:             python3-pyyaml

# These are required for `osbuild-dev`, only packaged for Fedora
%if 0%{?fedora}
Requires:             python3-rich
Requires:             python3-attrs
Requires:             python3-typer
%endif

%description    tools
Contains additional tools and utilities for development of
manifests and osbuild.

%package        depsolve-dnf
Summary:              Dependency solving support for DNF
Requires:             %{name} = %{version}-%{release}

# Fedora 40 and later use libdnf5, RHEL and Fedora < 40 use libdnf
%if 0%{?fedora} >= 40
Requires:             python3-libdnf5 >= 5.1.1
%else
Requires:             python3-libdnf
%endif

%description    depsolve-dnf
Contains depsolving capabilities for package managers.

%prep
%forgeautosetup -p1

ln -rs %{_builddir}/%{name}-%{version}/runners/org.osbuild.rhel82 %{_builddir}/%{name}-%{version}/runners/org.osbuild.rocky8
ln -rs %{_builddir}/%{name}-%{version}/runners/org.osbuild.centos9 %{_builddir}/%{name}-%{version}/runners/org.osbuild.rocky9
%build
%py3_build
make man

# SELinux
make -f /usr/share/selinux/devel/Makefile osbuild.pp
bzip2 -9 osbuild.pp

%pre selinux
%selinux_relabel_pre -s %{selinuxtype}

%install
%py3_install

mkdir -p %{buildroot}%{pkgdir}/stages
install -p -m 0755 $(find stages -type f -not -name "test_*.py") %{buildroot}%{pkgdir}/stages/

mkdir -p %{buildroot}%{pkgdir}/assemblers
install -p -m 0755 $(find assemblers -type f) %{buildroot}%{pkgdir}/assemblers/

mkdir -p %{buildroot}%{pkgdir}/runners
install -p -m 0755 $(find runners -type f -or -type l) %{buildroot}%{pkgdir}/runners

mkdir -p %{buildroot}%{pkgdir}/sources
install -p -m 0755 $(find sources -type f) %{buildroot}%{pkgdir}/sources

mkdir -p %{buildroot}%{pkgdir}/devices
install -p -m 0755 $(find devices -type f) %{buildroot}%{pkgdir}/devices

mkdir -p %{buildroot}%{pkgdir}/inputs
install -p -m 0755 $(find inputs -type f) %{buildroot}%{pkgdir}/inputs

mkdir -p %{buildroot}%{pkgdir}/mounts
install -p -m 0755 $(find mounts -type f) %{buildroot}%{pkgdir}/mounts

# mount point for bind mounting the osbuild library
mkdir -p %{buildroot}%{pkgdir}/osbuild

# schemata
mkdir -p %{buildroot}%{_datadir}/osbuild/schemas
install -p -m 0644 $(find schemas/*.json) %{buildroot}%{_datadir}/osbuild/schemas
ln -s %{_datadir}/osbuild/schemas %{buildroot}%{pkgdir}/schemas

# documentation
mkdir -p %{buildroot}%{_mandir}/man1
mkdir -p %{buildroot}%{_mandir}/man5
install -p -m 0644 -t %{buildroot}%{_mandir}/man1/ docs/*.1
install -p -m 0644 -t %{buildroot}%{_mandir}/man5/ docs/*.5

# SELinux
install -D -m 0644 -t %{buildroot}%{_datadir}/selinux/packages/%{selinuxtype} %{name}.pp.bz2
install -D -m 0644 -t %{buildroot}%{_mandir}/man8 selinux/%{name}_selinux.8
install -D -p -m 0644 selinux/osbuild.if %{buildroot}%{_datadir}/selinux/devel/include/distributed/%{name}.if

# Udev rules
mkdir -p %{buildroot}%{_udevrulesdir}
install -p -m 0755 data/10-osbuild-inhibitor.rules %{buildroot}%{_udevrulesdir}

# Remove `osbuild-dev` on non-fedora systems
%{!?fedora:rm %{buildroot}%{_bindir}/osbuild-dev}

# Install `osbuild-depsolve-dnf` into libexec
mkdir -p %{buildroot}%{_libexecdir}
# Fedora 40 and later use dnf5-json, RHEL and Fedora < 40 use dnf-json
%if 0%{?fedora} >= 40
install -p -m 0755 tools/osbuild-depsolve-dnf5 %{buildroot}%{_libexecdir}/osbuild-depsolve-dnf
%else
install -p -m 0755 tools/osbuild-depsolve-dnf %{buildroot}%{_libexecdir}/osbuild-depsolve-dnf
%endif

%check
exit 0
# We have some integration tests, but those require running a VM, so that would
# be an overkill for RPM check script.

%files
%license LICENSE
%{_bindir}/osbuild
%{_mandir}/man1/%{name}.1*
%{_mandir}/man5/%{name}-manifest.5*
%{_datadir}/osbuild/schemas
%{pkgdir}
%{_udevrulesdir}/*.rules
# the following files are in the lvm2 sub-package
%exclude %{pkgdir}/devices/org.osbuild.lvm2*
%exclude %{pkgdir}/stages/org.osbuild.lvm2*
# the following files are in the luks2 sub-package
%exclude %{pkgdir}/devices/org.osbuild.luks2*
%exclude %{pkgdir}/stages/org.osbuild.crypttab
%exclude %{pkgdir}/stages/org.osbuild.luks2*
# the following files are in the ostree sub-package
%exclude %{pkgdir}/assemblers/org.osbuild.ostree*
%exclude %{pkgdir}/inputs/org.osbuild.ostree*
%exclude %{pkgdir}/sources/org.osbuild.ostree*
%exclude %{pkgdir}/stages/org.osbuild.ostree*
%exclude %{pkgdir}/stages/org.osbuild.experimental.ostree*
%exclude %{pkgdir}/stages/org.osbuild.rpm-ostree

%files -n       python3-%{pypi_name}
%license LICENSE
%doc README.md
%{python3_sitelib}/%{pypi_name}-*.egg-info/
%{python3_sitelib}/%{pypi_name}/

%files lvm2
%{pkgdir}/devices/org.osbuild.lvm2*
%{pkgdir}/stages/org.osbuild.lvm2*

%files luks2
%{pkgdir}/devices/org.osbuild.luks2*
%{pkgdir}/stages/org.osbuild.crypttab
%{pkgdir}/stages/org.osbuild.luks2*

%files ostree
%{pkgdir}/assemblers/org.osbuild.ostree*
%{pkgdir}/inputs/org.osbuild.ostree*
%{pkgdir}/sources/org.osbuild.ostree*
%{pkgdir}/stages/org.osbuild.ostree*
%{pkgdir}/stages/org.osbuild.experimental.ostree*
%{pkgdir}/stages/org.osbuild.rpm-ostree

%files selinux
%{_datadir}/selinux/packages/%{selinuxtype}/%{name}.pp.bz2
%{_mandir}/man8/%{name}_selinux.8.*
%{_datadir}/selinux/devel/include/distributed/%{name}.if
%ghost %verify(not md5 size mode mtime) %{_sharedstatedir}/selinux/%{selinuxtype}/active/modules/200/%{name}

%post selinux
%selinux_modules_install -s %{selinuxtype} %{_datadir}/selinux/packages/%{selinuxtype}/%{name}.pp.bz2

%postun selinux
if [ $1 -eq 0 ]; then
    %selinux_modules_uninstall -s %{selinuxtype} %{name}
fi

%posttrans selinux
%selinux_relabel_post -s %{selinuxtype}

%files tools
%{_bindir}/osbuild-mpp
%{?fedora:%{_bindir}/osbuild-dev}

%files depsolve-dnf
%{_libexecdir}/osbuild-depsolve-dnf

%changelog
* Tue Apr 30 2024 Release Engineering <releng@rockylinux.org> - 110-1.rocky.0.2
- Add Rocky Linux runners

* Mon Feb 26 2024 imagebuilder-bot <imagebuilder-bots+imagebuilder-bot@redhat.com> - 110-1
- New upstream release

* Thu Feb 22 2024 imagebuilder-bot <imagebuilder-bots+imagebuilder-bot@redhat.com> - 109-1
- New upstream release

* Thu Feb 01 2024 imagebuilder-bot <imagebuilder-bots+imagebuilder-bot@redhat.com> - 106-1
- New upstream release

* Wed Jan 31 2024 imagebuilder-bot <imagebuilder-bots+imagebuilder-bot@redhat.com> - 105-1
- New upstream release

* Wed Jan 17 2024 Paweł Poławski <ppolawsk@redhat.com> - 104-2
- Fix unit tests in RHEL CI by backporting upstream fixes

* Tue Jan 16 2024 imagebuilder-bot <imagebuilder-bots+imagebuilder-bot@redhat.com> - 104-1
- New upstream release

* Wed Jan 03 2024 imagebuilder-bot <imagebuilder-bots+imagebuilder-bot@redhat.com> - 103-1
- New upstream release

* Wed Dec 20 2023 imagebuilder-bot <imagebuilder-bots+imagebuilder-bot@redhat.com> - 102-1
- New upstream release

* Mon Dec 11 2023 Paweł Poławski <ppolawsk@redhat.com> - 101-2
- Change unit-test timeout from 3h to 4h
- Rebuild after failed gating

* Wed Dec 06 2023 imagebuilder-bot <imagebuilder-bots+imagebuilder-bot@redhat.com> - 101-1
- New upstream release

* Fri Nov 24 2023 imagebuilder-bot <imagebuilder-bots+imagebuilder-bot@redhat.com> - 100-1
- New upstream release

* Wed Nov 08 2023 imagebuilder-bot <imagebuilder-bots+imagebuilder-bot@redhat.com> - 99-1
- New upstream release

* Wed Oct 25 2023 imagebuilder-bot <imagebuilder-bots+imagebuilder-bot@redhat.com> - 98-1
- New upstream release

* Wed Oct 11 2023 imagebuilder-bot <imagebuilder-bots+imagebuilder-bot@redhat.com> - 97-1
- New upstream release

* Wed Sep 27 2023 imagebuilder-bot <imagebuilder-bots+imagebuilder-bot@redhat.com> - 96-1
- New upstream release

* Wed Sep 13 2023 imagebuilder-bot <imagebuilder-bots+imagebuilder-bot@redhat.com> - 95-1
- New upstream release

* Wed Aug 30 2023 imagebuilder-bot <imagebuilder-bots+imagebuilder-bot@redhat.com> - 94-1
- New upstream release

* Wed Aug 23 2023 imagebuilder-bot <imagebuilder-bots+imagebuilder-bot@redhat.com> - 93-1
- New upstream release

* Thu Aug 17 2023 imagebuilder-bot <imagebuilder-bots+imagebuilder-bot@redhat.com> - 92-1
- New upstream release

* Wed Aug 02 2023 imagebuilder-bot <imagebuilder-bots+imagebuilder-bot@redhat.com> - 91-1
- New upstream release

* Thu Jul 20 2023 imagebuilder-bot <imagebuilder-bots+imagebuilder-bot@redhat.com> - 90-1
- New upstream release

* Tue Jun 27 2023 imagebuilder-bot <imagebuilder-bots+imagebuilder-bot@redhat.com> - 89-1
- New upstream release

* Tue Jun 27 2023 Tomáš Hozza <thozza@redhat.com> - 88-3
- Increase unit-test duration to 3h

* Fri Jun 23 2023 Tomáš Hozza <thozza@redhat.com> - 88-2
- Fix unit tests in RHEL CI and rebuild RPM

* Wed Jun 21 2023 imagebuilder-bot <imagebuilder-bots+imagebuilder-bot@redhat.com> - 88-1
- New upstream release

* Wed Jun 07 2023 imagebuilder-bot <imagebuilder-bots+imagebuilder-bot@redhat.com> - 87-1
- New upstream release

* Wed May 24 2023 imagebuilder-bot <imagebuilder-bots+imagebuilder-bot@redhat.com> - 86-1
- New upstream release

* Thu May 11 2023 imagebuilder-bot <imagebuilder-bots+imagebuilder-bot@redhat.com> - 85-1
- New upstream release

* Thu Apr 27 2023 imagebuilder-bot <imagebuilder-bots+imagebuilder-bot@redhat.com> - 84-1
- New upstream release

* Wed Mar 29 2023 imagebuilder-bot <imagebuilder-bots+imagebuilder-bot@redhat.com> - 82-1
- New upstream release

* Mon Feb 27 2023 imagebuilder-bot <imagebuilder-bots+imagebuilder-bot@redhat.com> - 81-1
- New upstream release

* Mon Feb 20 2023 imagebuilder-bot <imagebuilder-bots+imagebuilder-bot@redhat.com> - 80-1
- New upstream release

* Wed Feb 15 2023 imagebuilder-bot <imagebuilder-bots+imagebuilder-bot@redhat.com> - 79-1
- New upstream release

* Tue Feb 07 2023 imagebuilder-bot <imagebuilder-bots+imagebuilder-bot@redhat.com> - 78-1
- New upstream release

* Fri Jan 20 2023 imagebuilder-bot <imagebuilder-bots+imagebuilder-bot@redhat.com> - 77-1
- New upstream release

* Thu Jan 19 2023 imagebuilder-bot <imagebuilder-bots+imagebuilder-bot@redhat.com> - 76-1
- New upstream release

* Wed Jan 04 2023 imagebuilder-bot <imagebuilder-bots+imagebuilder-bot@redhat.com> - 75-1
- New upstream release

* Wed Dec 21 2022 imagebuilder-bot <imagebuilder-bots+imagebuilder-bot@redhat.com> - 74-1
- New upstream release

* Wed Dec 07 2022 imagebuilder-bot <imagebuilder-bots+imagebuilder-bot@redhat.com> - 73-1
- New upstream release

* Wed Nov 23 2022 imagebuilder-bot <imagebuilder-bots+imagebuilder-bot@redhat.com> - 72-1
- New upstream release

* Wed Nov 09 2022 imagebuilder-bot <imagebuilder-bots+imagebuilder-bot@redhat.com> - 71-1
- New upstream release

* Wed Oct 26 2022 imagebuilder-bots+imagebuilder-bot@redhat.com <imagebuilder-bot> - 70-1
- New upstream release

* Tue Oct 18 2022 imagebuilder-bots+imagebuilder-bot@redhat.com <imagebuilder-bot> - 69-1
- New upstream release

* Fri Aug 26 2022 imagebuilder-bot <imagebuilder-bots+imagebuilder-bot@redhat.com> - 65-1
- New upstream release

* Thu Aug 18 2022 imagebuilder-bot <imagebuilder-bots+imagebuilder-bot@redhat.com> - 64-1
- New upstream release

* Wed Aug 03 2022 imagebuilder-bot <imagebuilder-bots+imagebuilder-bot@redhat.com> - 63-1
- New upstream release

* Wed Jul 27 2022 imagebuilder-bot <imagebuilder-bots+imagebuilder-bot@redhat.com> - 62-1
- New upstream release

* Wed Jul 20 2022 imagebuilder-bot <imagebuilder-bots+imagebuilder-bot@redhat.com> - 61-1
- New upstream release

* Wed Jul 06 2022 imagebuilder-bot <imagebuilder-bots+imagebuilder-bot@redhat.com> - 60-1
- New upstream release

* Wed Jun 22 2022 imagebuilder-bot <imagebuilder-bots+imagebuilder-bot@redhat.com> - 59-1
- New upstream release

* Wed Jun 08 2022 imagebuilder-bot <imagebuilder-bots+imagebuilder-bot@redhat.com> - 58-1
- New upstream release

* Wed May 25 2022 imagebuilder-bot <imagebuilder-bots+imagebuilder-bot@redhat.com> - 57-1
- New upstream release

* Wed May 11 2022 imagebuilder-bot <imagebuilder-bots+imagebuilder-bot@redhat.com> - 56-1
- New upstream release

* Wed Apr 27 2022 imagebuilder-bot <imagebuilder-bots+imagebuilder-bot@redhat.com> - 55-1
- New upstream release

* Wed Apr 13 2022 imagebuilder-bot <imagebuilder-bots+imagebuilder-bot@redhat.com> - 54-1
- New upstream release

* Thu Mar 24 2022 imagebuilder-bot <imagebuilder-bots+imagebuilder-bot@redhat.com> - 53-1
- New upstream release

* Fri Mar 04 2022 Simon Steinbeiss <simon.steinbeiss@redhat.com> - 52-1
- New upstream release

* Sun Feb 27 2022 Simon Steinbeiss <simon.steinbeiss@redhat.com> - 50-1
- New upstream release

* Wed Feb 23 2022 Simon Steinbeiss <simon.steinbeiss@redhat.com> - 49-1
- New upstream release

* Wed Feb 16 2022 Chloe Kaubisch <chloe.kaubisch@gmail.com> - 48-1
- New upstream release

* Wed Feb 02 2022 Jacob Kozol <jacobdkozol@gmail.com> - 47-1
- New upstream release

* Wed Jan 19 2022 Simon Steinbeiss <simon.steinbeiss@redhat.com> - 46-1
- New upstream release

* Fri Jan 07 2022 Tomas Hozza <thozza@redhat.com> - 45-1
- New upstream release

* Thu Dec 16 2021 Simon Steinbeiss <simon.steinbeiss@redhat.com> - 44-1
- New upstream release

* Wed Dec 01 2021 Achilleas Koutsou <achilleas@koutsou.net> - 43-1
- New upstream release

* Wed Nov 17 2021 'Gianluca Zuccarelli' <'<gzuccare@redhat.com>'> - 42-1
- New upstream release

* Thu Oct 07 2021 Simon Steinbeiß <simon.steinbeiss@redhat.com> - 39-1
- New upstream release

* Sun Aug 29 2021 Tom Gundersen <tgunders@redhat.com> - 35-1
- Upstream release 35

* Sun Aug 29 2021 Tom Gundersen <tgunders@redhat.com> - 34-1
- Upstream release 34

* Wed Aug 25 2021 Tom Gundersen <tgunders@redhat.com> - 33-1
- Upstream release 33

* Tue Aug 24 2021 Tom Gundersen <tgunders@redhat.com> - 32-1
- Upstream release 32

* Mon Aug 23 2021 Tom Gundersen <tgunders@redhat.com> - 31-1
- Upstream release 31

* Thu Aug 12 2021 Ondřej Budai <ondrej@budai.cz> - 30-1
- Upstream release 30
- Many new stages for building ostree-based raw images
- Bootiso.mono stage was deprecated and split into smaller stages
- Mounts are now represented as an array in a manifest
- Various bug fixes and improvements to various stages

* Mon Aug 09 2021 Mohan Boddu <mboddu@redhat.com> - 29-2
- Rebuilt for IMA sigs, glibc 2.34, aarch64 flags
  Related: rhbz#1991688

* Tue Jun 29 2021 Ondřej Budai <ondrej@budai.cz> - 29-1
- Upstream release 29
- Adds host services
- Adds modprobe and logind stage

* Fri Apr 16 2021 Mohan Boddu <mboddu@redhat.com> - 27-3
- Rebuilt for RHEL 9 BETA on Apr 15th 2021. Related: rhbz#1947937

* Wed Mar 17 2021 Christian Kellner <ckellner@redhat.com> - 27-2
- Include Fedora 35 runner (upstream commit 337e0f0)

* Tue Mar 16 2021 Christian Kellner <ckellner@redhat.com> - 27-1
- Upstream release 27
- Various bug fixes related to the new container and installer
  stages introdcued in version 25 and 26.

* Sat Feb 20 2021 Christian Kellner <ckellner@redhat.com> - 26-1
- Upstream release 26
- Support for building boot isos
- Grub stage gained support for 'saved_entry' to fix grub tooling

* Fri Feb 12 2021 Christian Kellner <ckellner@redhat.com> - 25-1
- Upstream release 25
- First tech preview of the new manifest format. Includes
  various new stages and inputs to be able to build ostree
  commits contained in a oci archive.

* Thu Jan 28 2021 Christian Kellner <ckellner@redhat.com> - 24-1
- Upstream release 24
- Turn on dependency generator for everything but runners
- Include new 'input' binaries

* Tue Jan 26 2021 Fedora Release Engineering <releng@fedoraproject.org> - 23-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_34_Mass_Rebuild

* Fri Oct 23 2020 Christian Kellner <ckellner@redhat.com> - 23-1
- Upstream release 23
- Do not mangle shebangs for assemblers, runners & stages.

* Mon Oct 12 2020 Christian Kellner <ckellner@redhat.com> - 22-1
- Upstream release 22

* Thu Sep 10 2020 Christian Kellner <ckellner@redhat.com> - 21-1
- Upstream reelase 21

* Thu Aug 13 2020 Christian Kellner <ckellner@redhat.com> - 20-1
- Upstream reelase 20

* Fri Aug  7 2020 Christian Kellner <ckellner@redhat.com> - 19-1
- Upstream release 19
- Drop no-floats-in-sources.patch included in release 19
- bubblewrap replaced systemd-nspawn for sandboxing; change the
  requirements accordingly.

* Tue Jul 28 2020 Fedora Release Engineering <releng@fedoraproject.org> - 18-3
- Rebuilt for https://fedoraproject.org/wiki/Fedora_33_Mass_Rebuild

* Fri Jun 26 2020 Christian Kellner <ckellner@redhat.com> - 18-2
- Add patch to not pass floats to curl in the files source
  https://github.com/osbuild/osbuild/pull/459

* Tue Jun 23 2020 Christian Kellner <ckellner@redhat.com> - 18-1
- Upstream release 18
- All RHEL runners now use platform-python.

* Wed Jun 10 2020 Christian Kellner <ckellner@redhat.com> - 17-1
- new upstream relaese 17
- Add custom SELinux policy that lets osbuild set labels inside
  the build root that are unknown to the host.

* Thu Jun  4 2020 Christian Kellner <ckellner@redhat.com> - 16-1
- new upstream release 16
- Drop sources-fix-break-when-secrets-is-None.patch included in
  the new upstream reelase.

* Wed May 27 2020 Miro Hrončok <mhroncok@redhat.com> - 15-4
- Rebuilt for Python 3.9

* Tue May 26 2020 Christian Kellner <ckellner@redhat.com> - 15-3
- Add a patch to allow org.osbuild.files source in the new format
  but without actually containing the secrets key.
  Taken from merged PR: https://github.com/osbuild/osbuild/pull/416

* Tue May 26 2020 Miro Hrončok <mhroncok@redhat.com> - 15-2
- Rebuilt for Python 3.9

* Thu May 21 2020 Christian Kellner <ckellner@redhat.com> - 15-1
- new upstream release 15

* Wed May  6 2020 Christian Kellner <christian@kellner.me> - 14-2
- Install schemata to <datadir>/osbuild/schemas and include a
  symlink to it in /usr/lib/osbuild/schemas

* Wed May  6 2020 Christian Kellner <christian@kellner.me> - 14-1
- new upstream release 14
- The directories /usr/lib/osbuild/{assemblers, stages}/osbuild
  got removed. Changes to osbuild made them obsolete.

* Wed Apr 15 2020 Christian Kellner <ckellner@redhat.com> - 12-1
- new upstream release 12
- Specify the exact version in the 'python3-osbuild' requirement
  to avoid the library and the main binary being out of sync.
- osbuild-ostree sub-package with the necessary bits to create
  OSTree based images

* Thu Apr  2 2020 Christian Kellner <ckellner@redhat.com> - 11-1
- new upstream release 11
- Turn of dependency generator for internal components

* Thu Mar 19 2020 Christian Kellner <ckellner@redhat.com> - 10-1
- new upstream release 10
- build and include man pages, this adds 'make' and 'python3-docutils'
  to the build requirements
- add NEWS.md file with the release notes

* Thu Mar  5 2020 Christian Kellner <ckellner@redhat.com> - 9-1
- new upstream release: 9
- Remove host runner link, it now is being auto-detected
- Cleanup use of mixed use of spaces/tabs

* Wed Jan 29 2020 Fedora Release Engineering <releng@fedoraproject.org> - 7-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_32_Mass_Rebuild

* Mon Dec 16 2019 Packit Service <user-cont-team+packit-service@redhat.com> - 7-1
- new upstream release: 7

* Sat Nov 30 2019 Tom Gundersen <teg@jklm.no> - 6-1
- new upstream release: 6

* Wed Oct 30 2019 Lars Karlitski <lars@karlitski.net> - 5-1
- new upstream release: 5

* Wed Oct 16 2019 Tom Gundersen <tgunders@redhat.com> - 4-1
- new upstream release: 4

* Fri Oct 04 2019 Lars Karlitski <lars@karlitski.net> - 3-1
- new upstream release: 3

* Wed Sep 18 2019 Martin Sehnoutka <msehnout@redhat.com> - 2-1
- new upstream release: 2

* Mon Aug 19 2019 Miro Hrončok <mhroncok@redhat.com> - 1-3
- Rebuilt for Python 3.8

* Mon Jul 29 2019 Martin Sehnoutka <msehnout@redhat.com> - 1-2
- update upstream URL to the new Github organization

* Wed Jul 17 2019 Martin Sehnoutka <msehnout@redhat.com> - 1-1
- Initial package
